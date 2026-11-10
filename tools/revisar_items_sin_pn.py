# -*- coding: utf-8 -*-
"""Agrupa y clasifica los items sin P/N de los IPL CIJ para revision visual.

No inventa datos: cada descripcion, tabla, item y cantidad sale de
datos/partes_cij.json. La categoria es una ayuda heuristica (borrador) para
que el revisor humano encuentre rapido los grupos.

Genera:
  datos/analisis/items_sin_pn.csv
  datos/analisis/items_sin_pn_resumen.json
"""
import collections
import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(RAIZ, 'datos', 'partes_cij.json')
SALIDA_DIR = os.path.join(RAIZ, 'datos', 'analisis')
CSV_SALIDA = os.path.join(SALIDA_DIR, 'items_sin_pn.csv')
JSON_SALIDA = os.path.join(SALIDA_DIR, 'items_sin_pn_resumen.json')

CATEGORIAS = [
    ('sujetador', r'\b(screw|washer|nut|bolt|rivet|clip|bracket|clamp|tie|'
                  r'standoff|spacer|pin|nyloc|cap-head|pan-head|socket-head)\b'),
    ('cable/conector', r'\b(cable|connector|plug|wire|harness|socket|'
                       r'terminal|usb|ethernet)\b'),
    ('filtro/junta', r'\b(filter|gasket|seal|o-ring|oring|ring)\b'),
    ('placa/electronica', r'\b(pcb|board|assembly|module|sensor|detector|'
                          r'switch|fuse|relay|psu|pib|eht|lcd|fib)\b'),
    ('tuberia/neumatica', r'\b(tube|hose|fitting|valve|pump|manifold|'
                          r'connector|air|ink core)\b'),
    ('cubierta/estructura', r'\b(cover|door|panel|plate|housing|cabinet|'
                            r'shell|frame|stand|mount)\b'),
    ('nota', r'^(refer|see|note|\*)'),
]


def normalizar(texto):
    t = (texto or '').strip().lower()
    t = re.sub(r'\s+', ' ', t)
    return t


def categoria(desc):
    low = normalizar(desc)
    for nombre, patron in CATEGORIAS:
        if re.search(patron, low, re.I):
            return nombre
    return 'otro'


def main():
    with open(ENTRADA, encoding='utf-8') as f:
        datos = json.load(f)
    items = datos.get('items_sin_pn', [])

    grupos = {}
    for it in items:
        clave = normalizar(it.get('descripcion'))
        if not clave:
            clave = '(sin descripcion)'
        g = grupos.setdefault(clave, {
            'descripcion': it.get('descripcion') or '',
            'apariciones': 0,
            'documentos': set(),
            'modelos': set(),
            'tablas': set(),
            'grupos': set(),
            'items': [],
            'cantidades': [],
            'ejemplo_documento': it.get('documento'),
            'ejemplo_bloque': it.get('bloque'),
        })
        g['apariciones'] += 1
        if it.get('documento'):
            g['documentos'].add(it['documento'])
        if it.get('modelo'):
            g['modelos'].add(it['modelo'])
        if it.get('tabla'):
            g['tablas'].add(it['tabla'])
        if it.get('grupo'):
            g['grupos'].add(it['grupo'])
        if it.get('item') and it['item'] not in g['items']:
            g['items'].append(it['item'])
        if it.get('cantidad') and it['cantidad'] not in g['cantidades']:
            g['cantidades'].append(it['cantidad'])

    filas = []
    for clave, g in grupos.items():
        filas.append({
            'descripcion': g['descripcion'],
            'categoria_heuristica': categoria(g['descripcion']),
            'apariciones': g['apariciones'],
            'documentos': len(g['documentos']),
            'modelos': ', '.join(sorted(g['modelos'])),
            'tablas': ' | '.join(sorted(g['tablas'])),
            'grupos': ' | '.join(sorted(g['grupos'])),
            'items': ', '.join(g['items'][:12]),
            'cantidades': ', '.join(g['cantidades'][:12]),
            'ejemplo_documento': g['ejemplo_documento'] or '',
            'ejemplo_bloque': g['ejemplo_bloque'],
        })
    filas.sort(key=lambda r: (-r['apariciones'], r['descripcion'].lower()))

    os.makedirs(SALIDA_DIR, exist_ok=True)
    with open(CSV_SALIDA, 'w', encoding='utf-8-sig', newline='') as f:
        campos = ['descripcion', 'categoria_heuristica', 'apariciones',
                  'documentos', 'modelos', 'tablas', 'grupos', 'items',
                  'cantidades', 'ejemplo_documento', 'ejemplo_bloque']
        w = csv.DictWriter(f, fieldnames=campos, delimiter=';')
        w.writeheader()
        w.writerows(filas)

    por_categoria = collections.Counter(r['categoria_heuristica'] for r in filas)
    por_documento = collections.Counter(i.get('documento') for i in items)
    resumen = {
        'generado': '2026-11-10',
        'fuente': 'datos/partes_cij.json (items_sin_pn)',
        'estado': 'borrador',
        'nota': ('Agrupacion por descripcion normalizada. La categoria es una '
                 'ayuda heuristica, no un dato del manual. No se reconstruyen '
                 'P/N: estos items no tienen numero en el documento.'),
        'total_items': len(items),
        'descripciones_unicas': len(filas),
        'por_categoria': dict(por_categoria.most_common()),
        'por_documento': dict(por_documento.most_common()),
        'archivo_csv': 'datos/analisis/items_sin_pn.csv',
    }
    with open(JSON_SALIDA, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print('items=%d descripciones_unicas=%d' % (len(items), len(filas)))
    print('por categoria:')
    for k, v in por_categoria.most_common():
        print('  %-22s %3d' % (k, v))
    print('OK', os.path.relpath(CSV_SALIDA, RAIZ))
    print('OK', os.path.relpath(JSON_SALIDA, RAIZ))


if __name__ == '__main__':
    main()
