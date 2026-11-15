# -*- coding: utf-8 -*-
"""Audita la asociacion P/N <-> descripcion en el OCR 1550/1710.

Para cada aparicion de `datos/partes_cij_ocr.json`:
  - localiza la linea del P/N en la pagina OCR;
  - reune las lineas de la misma banda vertical (+-35 px);
  - comprueba que al menos el 80 % de las palabras de la descripcion
    aparezcan en esa banda.

No modifica datos. Sirve como evidencia de la revision por coordenadas.

Uso:
  python tools/auditar_ocr_coordenadas.py [--json]
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = os.path.join(RAIZ, 'datos', 'partes_cij_ocr.json')
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DOCS = {
    '1550 - Illustrated Parts List.pdf': 'ocr_cij_ipl_1550.json',
    '1710_IPL(ENG).pdf': 'ocr_cij_ipl_1710.json',
}


def norm(texto):
    texto = str(texto or '').upper().replace('—', '-').replace('–', '-')
    return re.sub(r'\s+', ' ', texto).strip()


def palabras(texto):
    return re.findall(r'[A-Z0-9]{3,}', norm(texto))


def auditar():
    with open(OCR, encoding='utf-8') as f:
        ocr = json.load(f)
    paginas = {}
    for documento, archivo in DOCS.items():
        with open(os.path.join(EXTRACCION, archivo), encoding='utf-8') as f:
            paginas[documento] = json.load(f)['paginas']

    filas = []
    for parte in ocr.get('partes', []):
        pn = str(parte.get('pn') or '')
        ok = fallos = 0
        detalles = []
        for aparicion in parte.get('apariciones') or []:
            documento = aparicion.get('documento')
            bloque = aparicion.get('bloque')
            pn_ocr = norm(aparicion.get('pn_ocr') or pn)
            descripcion = norm(aparicion.get('descripcion_ocr') or
                               aparicion.get('descripcion') or '')
            if documento not in paginas or not isinstance(bloque, int) \
                    or bloque < 1 or bloque > len(paginas[documento]):
                fallos += 1
                detalles.append('sin-documento/pagina')
                continue
            lineas = paginas[documento][bloque - 1]['lineas']
            hits = [l for l in lineas if pn_ocr in norm(l['texto'])]
            if not hits:
                fallos += 1
                detalles.append('pn-no-esta-en-linea')
                continue
            y = hits[0]['y']
            banda = ' '.join(norm(l['texto']) for l in lineas
                             if abs(l['y'] - y) <= 35)
            esperadas = palabras(descripcion)
            if not esperadas:
                fallos += 1
                detalles.append('descripcion-vacia')
                continue
            encontradas = sum(1 for w in esperadas if w in banda)
            if encontradas >= max(1, int(len(esperadas) * 0.8)):
                ok += 1
            else:
                fallos += 1
                detalles.append('fila %d/%d palabras' % (encontradas,
                                                          len(esperadas)))
        filas.append({'pn': pn, 'ok': ok, 'fallos': fallos,
                      'detalles': detalles[:3]})
    return filas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    filas = auditar()
    limpias = [f for f in filas if f['ok'] and not f['fallos']]
    fallas = [f for f in filas if f['fallos']]
    if args.json:
        print(json.dumps({'total': len(filas), 'limpias': len(limpias),
                          'con_falla': len(fallas), 'filas': filas},
                         ensure_ascii=False, indent=2))
        return 0
    print('OCR: %d P/N, %d con todas las apariciones en fila, %d con fallas'
          % (len(filas), len(limpias), len(fallas)))
    for f in fallas[:40]:
        print('  %s: %s' % (f['pn'], '; '.join(f['detalles'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
