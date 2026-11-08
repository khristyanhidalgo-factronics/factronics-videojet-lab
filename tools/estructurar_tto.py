"""Estructura los listados de partes TTO extraidos (leer_excel.py) en un dataset limpio.

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Uso:
  python tools/estructurar_tto.py            -> procesa y escribe datos/partes_tto.json
Reglas:
  - Solo convierte lo que existe en las extracciones; NINGUN dato inventado.
  - Filas validas: columna B = numero de parte (5-7 digitos).
  - Los ANCHOS de banda se derivan de la PROPIA descripcion de cada parte (regex "NNmm");
    si la descripcion no declara ancho, se usa el ancho de cabecera de esa fuente.
  - Cuando una misma parte aparece en varios archivos, se conserva cada descripcion y
    cada recomendacion de spares por separado, identificado por su fuente (sin fusion
    que pudiera inventar combinaciones que no existen en los originales).
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_EX = os.path.join(RAIZ, 'datos', 'extraccion')
SALIDA = os.path.join(RAIZ, 'datos', 'partes_tto.json')

ARCHIVOS = {
    'tto_partes_basicas_6330.json': 'basicas-6330',
    'tto_partes_basicas_6530.json': 'basicas-6530',
    'tto_parts_list_6330.json': 'parts-list-6330',
}
VALIDO_ANCHOS = (32, 53, 107)


def es_parte(v):
    return bool(v) and v.strip().isdigit() and 5 <= len(v.strip()) <= 7


def modelos_de(nombre_hoja):
    for ch in ('6210', '6230', '6320', '6330', '6420', '6530'):
        if ch in nombre_hoja:
            return [ch]
    return []


def anchos_de(descripcion, ancho_hoja):
    anchos = sorted({int(m) for m in re.findall(r'(\d{2,3})\s*mm', descripcion) if int(m) in VALIDO_ANCHOS})
    return anchos if anchos else list(ancho_hoja)


def anchos_cabecera(nombre_hoja, primeras_filas):
    texto = nombre_hoja + ' ' + ' '.join(
        str(c) for fila in primeras_filas[:2] for c in fila.get('celdas', {}).values())
    return sorted({int(m) for m in re.findall(r'(\d{2,3})\s*mm', texto) if int(m) in VALIDO_ANCHOS})


def idioma_de(nombre_hoja):
    if 'Port' in nombre_hoja:
        return 'portugues'
    if 'Esp' in nombre_hoja:
        return 'espanol'
    return 'ingles'


def procesar(nombre, fuente):
    with open(os.path.join(DIR_EX, nombre), 'r', encoding='utf-8') as f:
        datos = json.load(f)
    out = []
    for nombre_hoja, hoja in datos.items():
        filas = hoja.get('contenido', [])
        ancho_hoja = anchos_cabecera(nombre_hoja, filas)
        for fila in filas:
            celdas = fila.get('celdas', {})
            b = str(celdas.get('B', '')).strip()
            if not es_parte(b):
                continue
            descripcion = str(celdas.get('C', '')).strip()
            cant = []
            for col in ('E', 'F', 'G', 'H'):
                v = str(celdas.get(col, '')).strip()
                cant.append(int(v) if v.isdigit() else None)
            out.append({
                'parte': b,
                'descripcion': descripcion,
                'idioma': idioma_de(nombre_hoja),
                'fuente': fuente,
                'modelos': modelos_de(nombre_hoja),
                'anchos_mm': anchos_de(descripcion, ancho_hoja),
                'spares_recomendados': {
                    '5_equipos': cant[0], '10_equipos': cant[1],
                    '20_equipos': cant[2], '40_equipos': cant[3],
                },
            })
    return out


def principal():
    registros = []
    for nombre, fuente in ARCHIVOS.items():
        p = procesar(nombre, fuente)
        registros.extend(p)
        print(f"  {fuente}: filas_parte={len(p)}")
    # fusion por numero de parte: NO se inventan datos; se preserva por (fuente, idioma)
    fusion = {}
    for r in registros:
        d = fusion.setdefault(r['parte'], {
            'parte': r['parte'], 'descripciones': [], 'modelos_por_fuente': {},
            'fuentes': [],
        })
        clave = r['fuente'] + '|' + r['idioma']
        if not any(x.get('_clave') == clave for x in d['descripciones']):
            d['descripciones'].append({
                '_clave': clave, 'idioma': r['idioma'], 'fuente': r['fuente'],
                'texto': r['descripcion'], 'anchos_mm': r['anchos_mm'],
            })
        existentes = d['modelos_por_fuente'].setdefault(r['fuente'], [])
        for m in r['modelos']:
            if m not in existentes:
                existentes.append(m)
        if r['fuente'] not in d['fuentes']:
            d['fuentes'].append(r['fuente'])
        guardo = r['spares_recomendados']
        sp = d.setdefault('spares_por_fuente', {})
        if r['fuente'] not in sp or any(v is None for v in sp[r['fuente']].values()):
            sp[r['fuente']] = guardo
    lista = sorted(fusion.values(), key=lambda x: x['parte'])
    for r in lista:
        for desc in r['descripciones']:
            desc.pop('_clave', None)
    salida = {
        'producto': 'Factronics Videojet Lab',
        'schema': 2,
        'actualizado': '2026-11-08',
        'estado_general': 'borrador',
        'nota': 'Partes TTO 6x30 estructuradas desde los Excel de curso (material interno del equipo). '
                'Sin datos inventados: cada descripcion y spares se conserva identificado por su fuente. '
                'Estado borrador hasta cruzar contra las Official Parts Lists PDF. '
                'anchos_mm se toman de la descripcion de cada parte (hereda cabecera solo si no los declara).',
        'fuentes': list(ARCHIVOS.values()),
        'total_partes_unicas': len(lista),
        'partes': lista,
    }
    with open(SALIDA, 'w', encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print('OK', os.path.relpath(SALIDA, RAIZ), '| partes unicas:', len(lista))
    por_modelo = {}
    for r in lista:
        for ms in r['modelos_por_fuente'].values():
            for m in ms:
                por_modelo[m] = por_modelo.get(m, 0) + 1
    bilingual = sum(1 for r in lista if len({d['idioma'] for d in r['descripciones']}) >= 2)
    print('por_modelo:', por_modelo, '| con descripcion bilingue:', bilingual)
    for r in lista[:8]:
        print(f"  {r['parte']} fuentes={r['fuentes']}")
        for d in r['descripciones'][:2]:
            print(f"    [{d['idioma']}] {d['texto'][:78]} anchos={d['anchos_mm']}")


if __name__ == '__main__':
    principal()
