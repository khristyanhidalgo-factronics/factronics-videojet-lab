# -*- coding: utf-8 -*-
"""Estructura los codigos de error encontrados en los textos extraidos (LASER y TTO).

Fuentes:
  - TTO: boletines tecnicos (titulos con codigo E####/W#### y descripcion).
  - LASER: listas de codigos (18234 Laser Error Codes, Error List 3140/3340/3640,
    error_messages_blueberry) + menciones en manuales.
Salida: datos/codigos_error.json (estado borrador: codigo + contexto, sin inventar).

Notas de calidad: los PDFs de tablas vienen con letras espaciadas por kerning
('W arning'); se normaliza para clasificar (Warning/Fatal/Error/Info). El mensaje
completo de causa/remedio NO se reconstruye: se guarda la linea de contexto.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'codigos_error.json')

RE_CODIGO_TTO = re.compile(r'\b([EW])\s?(\d{4,5})\b')
RE_ID_LASER = re.compile(r'(?<!\d)(0\d{4})(?!\d)')
RE_CLASE = re.compile(r'(W\s*arning|F\s*atal|E\s*rror|I\s*nfo|S\s*top)', re.I)


def normalizar_espaciado(linea):
    tokens = linea.split()
    if len(tokens) >= 8 and sum(1 for t in tokens if len(t) == 1) / len(tokens) > 0.6:
        return linea.replace(' ', '')
    return linea


def contexto(texto, pos, radio=110):
    ini = max(0, pos - radio // 2)
    fin = min(len(texto), pos + radio)
    frag = re.sub(r'\s+', ' ', texto[ini:fin]).strip()
    return frag


def main():
    codigos = {}
    fuentes = []

    # ---------- TTO: todos los textos (boletines, manuales, instrucciones) ----------
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not (nombre.startswith('tto_') and nombre.endswith('_visual.txt')):
            continue
        texto = open(os.path.join(EXTRACCION, nombre), encoding='utf-8',
                     errors='replace').read()
        cuerpo = '\n'.join(l for l in texto.splitlines() if not l.startswith('#'))
        for linea in cuerpo.splitlines():
            linea_norm = normalizar_espaciado(linea.strip())
            if len(linea_norm) < 6:
                continue
            for m in RE_CODIGO_TTO.finditer(linea_norm):
                codigo = '%s%s' % (m.group(1).upper(), m.group(2))
                registro = codigos.get(codigo)
                if registro is None:
                    codigos[codigo] = {
                        'codigo': codigo,
                        'tecnologia': 'TTO',
                        'descripcion_contexto': linea_norm[:200],
                        'archivos': [nombre],
                        'estado': 'borrador',
                    }
                else:
                    if nombre not in registro['archivos']:
                        registro['archivos'].append(nombre)

    # ---------- LASER: documentos de listas de error ----------
    docs_error = [n for n in os.listdir(EXTRACCION)
                  if n.startswith('laser_') and n.endswith('_visual.txt')
                  and re.search(r'error|blueberry', n)]
    for nombre in sorted(docs_error):
        texto = open(os.path.join(EXTRACCION, nombre), encoding='utf-8',
                     errors='replace').read()
        cuerpo = '\n'.join(l for l in texto.splitlines() if not l.startswith('#'))
        # IDs de 5 digitos con clase cerca (tablas)
        for m in RE_ID_LASER.finditer(cuerpo):
            codigo = m.group(1)
            entorno = cuerpo[max(0, m.start() - 60):m.start() + 200]
            mc = RE_CLASE.search(entorno)
            clase = None
            if mc:
                clase = re.sub(r'\s+', '', mc.group(1)).capitalize()
            registro = codigos.get(codigo)
            if registro is None:
                codigos[codigo] = {
                    'codigo': codigo,
                    'tecnologia': 'LASER',
                    'clase': clase,
                    'descripcion_contexto': contexto(cuerpo, m.start()),
                    'archivos': [nombre],
                    'estado': 'borrador',
                }
            else:
                if nombre not in registro['archivos']:
                    registro['archivos'].append(nombre)
                if clase and not registro.get('clase'):
                    registro['clase'] = clase
        # codigos E/W en manuales y notas
        for m in RE_CODIGO_TTO.finditer(cuerpo):
            codigo = '%s%s' % (m.group(1).upper(), m.group(2))
            if codigo in codigos:
                if nombre not in codigos[codigo]['archivos']:
                    codigos[codigo]['archivos'].append(nombre)
                continue
            codigos[codigo] = {
                'codigo': codigo,
                'tecnologia': 'LASER',
                'descripcion_contexto': contexto(cuerpo, m.start()),
                'archivos': [nombre],
                'estado': 'borrador',
            }

    # ---------- codigos en NOMBRES de archivo (boletines/manuales) ----------
    RE_NOMBRE = re.compile(r'(?i)(?:^|[_-])(e|w)(\d{4,5})(?=[_\-.]|$)')
    RE_NOMBRE_ERR = re.compile(r'(?i)(?:erro(?:re)?|falha|fault)([ew]?)(\d{4,5})')

    def registrar_codigo(codigo, tecnologia, descripcion, nombre):
        registro = codigos.get(codigo)
        if registro is None:
            codigos[codigo] = {
                'codigo': codigo,
                'tecnologia': tecnologia,
                'descripcion_contexto': descripcion[:200],
                'archivos': [nombre],
                'estado': 'borrador',
            }
        else:
            if nombre not in registro['archivos']:
                registro['archivos'].append(nombre)
            if tecnologia != registro['tecnologia']:
                registro.setdefault('tecnologias_adicionales', [])
                if tecnologia not in registro['tecnologias_adicionales']:
                    registro['tecnologias_adicionales'].append(tecnologia)

    for nombre in sorted(os.listdir(EXTRACCION)):
        if not (nombre.endswith('_visual.txt')
                and (nombre.startswith('tto_') or nombre.startswith('laser_'))):
            continue
        tecnologia = 'TTO' if nombre.startswith('tto_') else 'LASER'
        descripcion = (nombre.replace('tto_', '').replace('laser_', '')
                       .replace('_visual.txt', '').replace('_', ' '))
        for m in RE_NOMBRE.finditer(nombre):
            registrar_codigo('%s%s' % (m.group(1).upper(), m.group(2)),
                             tecnologia, descripcion, nombre)
        for m in RE_NOMBRE_ERR.finditer(nombre):
            letra = (m.group(1) or 'E').upper()
            registrar_codigo('%s%s' % (letra, m.group(2)),
                             tecnologia, descripcion, nombre)

    por_tec = {}
    for c in codigos.values():
        por_tec[c['tecnologia']] = por_tec.get(c['tecnologia'], 0) + 1
    datos = {
        'producto': 'Codigos de error LASER y TTO detectados en la documentacion',
        'schema': 1,
        'total': len(codigos),
        'por_tecnologia': por_tec,
        'nota': ('Extraccion automatica conservadora: se registra el codigo y una '
                 'ventana de contexto; NO se reconstruyen tablas de causa/remedio. '
                 'Los codigos E/W de TTO provienen del titulo del boletin; los IDs de '
                 '5 digitos de LASER, de las listas de error (con clase cuando aparece '
                 'Warning/Fatal/Error/Info). Estado: borrador - revisar antes de publicar '
                 'como dato firme.'),
        'codigos': sorted(codigos.values(), key=lambda c: (c['tecnologia'], c['codigo'])),
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | total=%d %s' % (os.path.relpath(DESTINO, RAIZ), len(codigos), por_tec))
    for c in datos['codigos'][:6]:
        print('  %-8s %-6s %s' % (c['codigo'], c['tecnologia'],
                                  (c.get('descripcion_contexto') or '')[:80]))


if __name__ == '__main__':
    main()
