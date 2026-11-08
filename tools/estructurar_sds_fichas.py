# -*- coding: utf-8 -*-
"""Estructura la seccion 3 (composicion) de las fichas SDS descifradas + metadatos.

Entrada: datos/extraccion/cij_tinta_*_descifrado.txt (564 fichas)
Salida:  datos/sds_composicion.json
Estado del dato: 'borrador' (extraccion automatica de plantilla Videojet; revision
humana pendiente contra el PDF original, regla del proyecto: nada inventado).

Plantilla observada (SDS Videojet multi-pagina, formato SGA):
    SECCIÓN 3: Composición / información sobre los componentes
    1) <nombre componente>
    CAS: 78-93-3
    40 - <50
    <frases de clasificacion GHS...>
    2) ...
El parser es conservador: solo acepta bloques con CAS valido; el porcentaje solo si
la linea inmediata es un rango numerico.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'sds_composicion.json')

SEC3 = re.compile(r'SECCI[ÓO]N\s+3\s*[:\-]', re.I)
SEC4 = re.compile(r'SECCI[ÓO]N\s+4\s*[:\-]', re.I)
CABECERA = re.compile(r'^(\d{1,2})\)\s*(.+)$', re.MULTILINE)
CAS = re.compile(r'CAS:\s*([0-9]{2,7}\s*-\s*[0-9]{2}\s*-\s*[0-9])')
RANGO = re.compile(r'^([<>≤≥]?\s*\d+(?:[.,]\d+)?)\s*-\s*([<>≤≥]?\s*\d+(?:[.,]\d+)?)\s*$')
VERSION = re.compile(r'N[úu]mero de versi[óo]n\s*:?\s*\n?:?\s*([0-9]+(?:\.[0-9]+)?)')
FECHA = re.compile(r'Fecha de emisi[óo]n/\s*Fecha de\s*\n?\s*revisi[óo]n\s*:?\s*\n?:?\s*'
                   r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})')


def limpiar_nombre(nombre_cabecera, bloque_lineas):
    """Nombre del componente: texto de la cabecera 'N)' + lineas de continuacion
    antes del CAS (nombres largos ocupan 2 lineas, p.ej. colorantes)."""
    partes = [nombre_cabecera.strip()]
    for linea in bloque_lineas:
        linea = linea.strip()
        if not linea or linea.startswith('CAS'):
            break
        if RANGO.match(linea) or re.fullmatch(r'[<>≤≥]?\s*\d+(?:[.,]\d+)?', linea):
            break
        if linea.isupper() and len(linea) > 12:
            break
        partes.append(linea)
        if len(' '.join(partes)) > 140:
            break
    return ' '.join(partes).strip()


def parsear_seccion3(texto):
    m3 = SEC3.search(texto)
    if not m3:
        return None
    resto = texto[m3.end():]
    m4 = SEC4.search(resto)
    if m4:
        resto = resto[:m4.start()]
    # dividir en bloques por cabeceras 'N)'
    cabeceras = list(CABECERA.finditer(resto))
    componentes = []
    for i, cab in enumerate(cabeceras):
        inicio = cab.end()
        fin = cabeceras[i + 1].start() if i + 1 < len(cabeceras) else len(resto)
        bloque = resto[inicio:fin]
        lineas = [l.strip() for l in bloque.splitlines() if l.strip()]
        nombre = limpiar_nombre(cab.group(2), lineas)
        mcas = CAS.search(bloque)
        if not nombre or not mcas:
            continue
        cas = re.sub(r'\s+', '', mcas.group(1))
        # porcentaje: primera linea tras el CAS que sea un rango numerico
        porcentaje = None
        idx_cas = next((k for k, l in enumerate(lineas) if l.startswith('CAS')), None)
        if idx_cas is not None:
            for linea in lineas[idx_cas + 1: idx_cas + 3]:
                mr = RANGO.match(linea)
                if mr:
                    porcentaje = '%s - %s' % (mr.group(1).strip(), mr.group(2).strip())
                    break
                if re.fullmatch(r'[<>≤≥]?\s*\d+(?:[.,]\d+)?', linea):
                    porcentaje = linea
                    break
        # clasificaciones GHS: lineas restantes con 'Categor' o MAYUSCULAS, unidas
        # cuando la linea anterior termina en '-'
        ghs = []
        inicio_ghs = (idx_cas + 1) if idx_cas is not None else 0
        pendiente = ''
        for linea in lineas[inicio_ghs:]:
            if porcentaje and linea == porcentaje:
                continue
            candidata = (pendiente + ' ' + linea).strip() if pendiente else linea
            if 'Categor' in linea or (linea.isupper() and len(linea) > 8):
                if linea.endswith('-'):
                    pendiente = candidata
                    continue
                ghs.append(candidata)
                pendiente = ''
        componentes.append({
            'componente': nombre,
            'cas': cas,
            'porcentaje': porcentaje,
            'clasificacion_ghs': ghs[:6],
        })
    return componentes


def metadatos(texto):
    v = VERSION.search(texto)
    f = FECHA.search(texto)
    return {'version_sds': v.group(1) if v else None,
            'fecha_revision': f.group(1) if f else None}


def main():
    resultados = []
    sin_seccion = 0
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not nombre.startswith('cij_tinta_') or not nombre.endswith('_descifrado.txt'):
            continue
        ruta = os.path.join(EXTRACCION, nombre)
        texto = open(ruta, 'r', encoding='utf-8', errors='replace').read()
        slug = nombre[len('cij_tinta_'):-len('_descifrado.txt')]
        componentes = parsear_seccion3(texto)
        meta = metadatos(texto)
        entrada = {
            'archivo_txt': nombre,
            'slug': slug,
            'codigo_tinta': slug.split('_')[0].replace('_', '-').upper(),
            'version_sds': meta['version_sds'],
            'fecha_revision': meta['fecha_revision'],
            'componentes': componentes or [],
            'estado': ('borrador' if componentes else 'sin-seccion-3'),
            'fuente': 'ficha QSS cifrada descifrada con tools/leer_pdf_cifrado.py v2',
        }
        if not componentes:
            sin_seccion += 1
        resultados.append(entrada)

    con = sum(1 for r in resultados if r['componentes'])
    total_componentes = sum(len(r['componentes']) for r in resultados)
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump({
            'producto': 'Composicion SDS de tintas CIJ (seccion 3)',
            'schema': 1,
            'estado_general': 'borrador (extraccion automatica; pendiente revision humana)',
            'nota': ('Seccion 3 de las SDS Videojet descifradas (RC4 + CMaps ToUnicode). '
                     'Solo se registran bloques con CAS valido y nombre; el porcentaje '
                     'solo si la linea es un rango numerico. Sin datos inventados.'),
            'total_fichas': len(resultados),
            'fichas_con_componentes': con,
            'total_componentes': total_componentes,
            'fichas': resultados,
        }, f, ensure_ascii=False, indent=1)
    print('OK %s | fichas=%d con_componentes=%d sin_seccion3=%d componentes=%d'
          % (os.path.relpath(DESTINO, RAIZ), len(resultados), con, sin_seccion,
             total_componentes))
    # muestra V471
    for r in resultados:
        if r['slug'] == 'v471_d':
            print('V471-D:', json.dumps(r['componentes'], ensure_ascii=False, indent=1)[:800])


if __name__ == '__main__':
    main()
