# -*- coding: utf-8 -*-
"""Estructura las partes LASER (numeros AL-xxxxx) de los manuales extraidos.

Fuente principal: SpareParts3320_3120 (recuperado por descifrado AES) y el resto de
textos laser. La extraccion visual intercala columnas (posicion/numero/descripcion),
por eso el dataset es CONSERVADOR: se guarda el numero de parte y la descripcion
adyacente SIN reconstruir la tabla; estado borrador.
Salida: datos/laser_partes.json
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'laser_partes.json')
DECODIFICADO = os.path.join(EXTRACCION, 'medidores_portencia_co2',
                            'medidores_portencia_co2_texto.txt')
RE_PARTE = re.compile(r'\b(AL-(?:SP)?\d{4,6})\b')
RE_FICHERO = re.compile(r'\b(AL-(?:SP)?\d{4,6})\b')


def limpiar_descripcion(texto):
    texto = re.split(r'\n', texto)[0]
    texto = re.sub(r'^[\d\s\.\-]+', '', texto)      # posiciones/digitos pegados
    texto = re.sub(r'\s+', ' ', texto).strip(' .;-')
    return texto[:90]


def descripcion_valida(desc):
    return bool(desc) and len(desc) >= 3 and re.search(r'[A-Za-zÄÖÜäöüß]', desc)


def aplicar_texto_decodificado(partes):
    """Sobrescribe descripciones con la capa de texto original decodificada."""
    if not os.path.exists(DECODIFICADO):
        return 0
    aplicados = 0
    for linea in open(DECODIFICADO, encoding='utf-8'):
        linea = linea.strip()
        if not linea or linea.startswith('#'):
            continue
        m = re.match(r'^(AL-(?:SP)?\d{4,6})\s*(?:-\s*)?(.+)$', linea)
        if not m:
            continue
        codigo, desc = m.group(1), m.group(2).strip()
        if not descripcion_valida(desc):
            continue
        registro = partes.setdefault(codigo, {
            'numero_parte': codigo, 'descripcion': None, 'archivos': []})
        if registro.get('descripcion') and not registro.get('descripcion_ocr'):
            registro['descripcion_ocr'] = registro['descripcion']
        registro['descripcion'] = desc
        registro['origen_descripcion'] = 'texto-decodificado-cmap'
        registro['evidencia'] = os.path.relpath(DECODIFICADO, RAIZ).replace('\\', '/')
        nombre = os.path.basename(DECODIFICADO)
        if nombre not in registro['archivos']:
            registro['archivos'].append(nombre)
        aplicados += 1
    return aplicados


def main():
    partes = {}
    archivos_fuente = set()

    for nombre in sorted(os.listdir(EXTRACCION)):
        if not (nombre.startswith('laser_') and nombre.endswith('_visual.txt')):
            continue
        texto = open(os.path.join(EXTRACCION, nombre), encoding='utf-8',
                     errors='replace').read()
        cuerpo = '\n'.join(l for l in texto.splitlines() if not l.startswith('#'))
        coincidencias = list(RE_PARTE.finditer(cuerpo))
        for i, m in enumerate(coincidencias):
            codigo = m.group(1)
            fin = coincidencias[i + 1].start() if i + 1 < len(coincidencias) else len(cuerpo)
            desc = limpiar_descripcion(cuerpo[m.end():min(fin, m.end() + 110)])
            if not descripcion_valida(desc):
                desc = None
            registro = partes.get(codigo)
            if registro is None:
                partes[codigo] = {'numero_parte': codigo, 'descripcion': desc,
                                  'archivos': [nombre]}
            else:
                if nombre not in registro['archivos']:
                    registro['archivos'].append(nombre)
                if desc and (not registro['descripcion'] or
                             len(desc) > len(registro['descripcion'])):
                    registro['descripcion'] = desc
        if coincidencias:
            archivos_fuente.add(nombre)

    # numeros citados en nombres de archivo (dibujos: 'AL-86140-AA 7920 wiring...')
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not (nombre.startswith('laser_') and nombre.endswith('_visual.txt')):
            continue
        for m in RE_FICHERO.finditer(nombre):
            codigo = m.group(1)
            if codigo not in partes:
                partes[codigo] = {'numero_parte': codigo, 'descripcion': None,
                                  'archivos': [nombre]}

    decodificados = aplicar_texto_decodificado(partes)
    con_desc = sum(1 for p in partes.values() if p['descripcion'])
    datos = {
        'producto': 'Partes LASER (numeros AL-xxxxx) detectadas en la documentacion',
        'schema': 1,
        'total': len(partes),
        'con_descripcion': con_desc,
        'estado_general': 'borrador (numeros directos; descripcion adyacente sujeta a revision)',
        'fuente': ('textos laser extraidos (SpareParts 3320/3120 recuperado por descifrado '
                   'AES, manuales y dibujos). La tabla original intercala columnas de '
                   'posicion: no se reconstruye, solo se registra numero + contexto.'),
        'nota_descripciones_decodificadas': (
            'AL-67438 y AL-66517 usan la capa de texto original decodificada de '
            'MedidoresPortenciaCO2.pdf; descripcion_ocr conserva la lectura OCR previa.'),
        'partes': sorted(partes.values(), key=lambda p: p['numero_parte']),
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | partes=%d con_descripcion=%d decodificadas=%d fuentes=%d'
          % (os.path.relpath(DESTINO, RAIZ), len(partes), con_desc,
             decodificados, len(archivos_fuente)))
    for p in datos['partes'][:8]:
        print('  %-11s %s' % (p['numero_parte'], (p['descripcion'] or '')[:70]))


if __name__ == '__main__':
    main()
