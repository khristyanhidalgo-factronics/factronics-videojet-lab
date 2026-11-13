# -*- coding: utf-8 -*-
"""Verifica que los artefactos de revision sigan cuadrando con los datos.

No genera nada: comprueba que `datos/analisis/` no se haya quedado atras
respecto a `partes_cij_ocr.json` y `cij_velocidades.json`.

Uso:
  python tools/test_revision_pendientes.py
"""
import csv
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALISIS = os.path.join(RAIZ, 'datos', 'analisis')
OCR = os.path.join(RAIZ, 'datos', 'partes_cij_ocr.json')
VELOCIDADES = os.path.join(RAIZ, 'datos', 'cij_velocidades.json')


def leer_csv(nombre, delimitador=';'):
    with open(os.path.join(ANALISIS, nombre), encoding='utf-8-sig',
              newline='') as f:
        return list(csv.DictReader(f, delimiter=delimitador))


def leer_texto(nombre):
    with open(os.path.join(ANALISIS, nombre), encoding='utf-8') as f:
        return f.read()


def main():
    fallos = []
    with open(OCR, encoding='utf-8') as f:
        ocr = json.load(f)
    with open(VELOCIDADES, encoding='utf-8') as f:
        vel = json.load(f)
    resumen = json.loads(leer_texto('revision_pendientes_resumen.json'))

    partes = ocr.get('partes', [])
    revision = leer_csv('partes_cij_ocr_revision.csv')
    apariciones = leer_csv('partes_cij_ocr_apariciones.csv')
    if len(revision) != len(partes):
        fallos.append('revision.csv: %d filas; se esperaban %d'
                      % (len(revision), len(partes)))
    if len(revision) != 193:
        fallos.append('revision.csv: %d filas; se esperaban 193'
                      % len(revision))
    if len(apariciones) != 275:
        fallos.append('apariciones.csv: %d filas; se esperaban 275'
                      % len(apariciones))
    suma_apariciones = sum(int(f.get('apariciones') or 0) for f in revision)
    if suma_apariciones != 275:
        fallos.append('revision.csv: suma de apariciones %d; se esperaban 275'
                      % suma_apariciones)
    conflictos = [f for f in revision if f.get('conflicto') == 'si']
    if len(conflictos) != 5:
        fallos.append('revision.csv: %d conflictos; se esperaban 5'
                      % len(conflictos))
    nuevos = [f for f in revision if f.get('nuevo') == 'si']
    if len(nuevos) != 92:
        fallos.append('revision.csv: %d nuevos; se esperaban 92'
                      % len(nuevos))
    if any(not f.get('pn') for f in revision):
        fallos.append('revision.csv: hay filas sin P/N')
    if any(not f.get('pn_ocr') for f in revision):
        fallos.append('revision.csv: hay filas sin pn_ocr')

    pns_fuente = {p.get('pn') for p in partes}
    pns_revision = {f.get('pn') for f in revision}
    if pns_fuente != pns_revision:
        fallos.append('revision.csv: los P/N no coinciden con la fuente')

    md_conflictos = leer_texto('conflictos_cij_ocr.md')
    for pn in ('395898', '395899', '399474', '399475', 'SP234081'):
        if pn not in md_conflictos:
            fallos.append('conflictos_cij_ocr.md: falta %s' % pn)

    avisos = leer_csv('velocidades_cij_avisos.csv', delimitador=',')
    if len(avisos) != 56:
        fallos.append('velocidades_cij_avisos.csv: %d filas; se esperaban 56'
                      % len(avisos))
    conteo = {'boquilla': 0, 'modelo': 0, 'fuente': 0}
    for fila in avisos:
        for tipo in (fila.get('tipos_aviso') or '').split(';'):
            if tipo:
                conteo[tipo] = conteo.get(tipo, 0) + 1
    if conteo != {'boquilla': 22, 'modelo': 31, 'fuente': 3}:
        fallos.append('velocidades_cij_avisos.csv: conteo %r' % conteo)
    if sum(conteo.values()) != 56:
        fallos.append('velocidades_cij_avisos.csv: total %d; se esperaban 56'
                      % sum(conteo.values()))
    if len(vel.get('entradas', [])) != 266:
        fallos.append('cij_velocidades.json: %d entradas'
                      % len(vel.get('entradas', [])))

    tablero = leer_texto('PENDIENTES_REVISION.md')
    for texto in ('193', '277', '275', '5', '56', 'SP234081', '120'):
        if texto not in tablero:
            fallos.append('PENDIENTES_REVISION.md: falta %r' % texto)

    if resumen.get('partes_cij_ocr', {}).get('partes') != 193:
        fallos.append('resumen: partes_cij_ocr.partes incorrecto')
    if resumen.get('partes_cij_ocr', {}).get('registros') != 277:
        fallos.append('resumen: partes_cij_ocr.registros incorrecto')
    if resumen.get('velocidades_cij', {}).get('total_avisos') != 56:
        fallos.append('resumen: velocidades_cij.total_avisos incorrecto')

    if fallos:
        print('FALLO: %d incidencias' % len(fallos))
        for fallo in fallos:
            print('  -', fallo)
        return 1
    print('Revision OK: 193 P/N OCR (92 nuevos), 275 apariciones, '
          '5 conflictos, 56 avisos de velocidades')
    return 0


if __name__ == '__main__':
    sys.exit(main())
