# -*- coding: utf-8 -*-
"""Valida datos/partes_cij_ocr.json (IPL 1550/1710 leidos por OCR).

Comprueba estructura, estados honestos, formato/unicidad de P/N, evidencia por
aparicion y que el consolidado no sea una prueba de una sola pagina.

Uso: python tools/test_partes_cij_ocr.py   (exit 0 = OK)
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, 'datos', 'partes_cij_ocr.json')

ESTADOS = {'borrador-decodificado', 'por-definir'}
PN = re.compile(r'^[A-Z]{0,3}\d{5,7}(?:[-/]\d{1,3})?[A-Z]?$')
CONOCIDOS = {'399362', '399086', '399474', '399099', '234116', 'SP399089'}


def main():
    fallos = []

    def exigir(cond, mensaje):
        if not cond:
            fallos.append(mensaje)

    if not os.path.exists(RUTA):
        print('FALLO: falta %s' % os.path.relpath(RUTA, RAIZ))
        return 1
    with open(RUTA, 'r', encoding='utf-8') as f:
        d = json.load(f)

    for clave in ('generado', 'fuente', 'metodo', 'resumen', 'documentos',
                  'partes', 'items_sin_pn'):
        exigir(clave in d, 'falta la clave %r' % clave)
    if fallos:
        for f in fallos:
            print('FALLO:', f)
        return 1

    docs = {x.get('archivo', '') for x in d['documentos']}
    exigir(any('1550' in x for x in docs), 'no aparece el IPL 1550')
    exigir(any('1710' in x for x in docs), 'no aparece el IPL 1710')

    resumen = d['resumen']
    paginas = resumen.get('paginas_ocr', 0)
    exigir(paginas >= 100, 'paginas_ocr=%r: parece una prueba incompleta' % paginas)
    exigir(resumen.get('partes') == len(d['partes']),
           'resumen.partes=%r != %d' % (resumen.get('partes'), len(d['partes'])))
    exigir(resumen.get('documentos') == len(d['documentos']),
           'resumen.documentos no coincide')
    omitidas = d.get('paginas_omitidas') or []
    exigir(resumen.get('paginas_omitidas') == len(omitidas),
           'resumen.paginas_omitidas no coincide')
    for o in omitidas:
        exigir(o.get('documento'), 'pagina omitida sin documento')
        exigir(o.get('pagina'), 'pagina omitida sin numero')
        exigir(o.get('error'), 'pagina omitida sin motivo')

    vistos = set()
    for p in d['partes']:
        pn = str(p.get('pn') or '')
        exigir(pn, 'parte sin P/N')
        exigir(PN.match(pn), 'P/N con formato inesperado: %r' % pn)
        exigir(pn not in vistos, 'P/N duplicado: %r' % pn)
        vistos.add(pn)
        exigir(p.get('estado') in ESTADOS,
               '%s: estado no permitido para OCR: %r' % (pn, p.get('estado')))
        exigir(not p.get('estado') == 'verificado',
               '%s: el OCR no puede ascender a verificado' % pn)
        if p.get('estado') == 'borrador-decodificado':
            exigir(bool((p.get('descripcion') or '').strip()),
                   '%s: borrador sin descripcion' % pn)
        exigir(bool(p.get('modelos')), '%s: sin modelo' % pn)
        apariciones = p.get('apariciones') or []
        exigir(bool(apariciones), '%s: sin apariciones/evidencia' % pn)
        for a in apariciones:
            exigir(bool(a.get('documento')), '%s: aparicion sin documento' % pn)
            exigir(a.get('metodo'), '%s: aparicion sin metodo' % pn)
            exigir(a.get('pagina'), '%s: aparicion sin pagina' % pn)
            if a.get('pn_corregido_ocr'):
                exigir(a.get('pn_ocr') and a.get('pn_ocr') != pn,
                       '%s: correccion OCR sin texto original' % pn)

    faltan = sorted(CONOCIDOS - vistos)
    if faltan:
        print('AVISO: P/N conocidos que el OCR no leyo: %s' % ', '.join(faltan))

    for x in d['items_sin_pn']:
        exigir(x.get('descripcion'), 'item sin P/N sin descripcion')
        exigir(x.get('documento'), 'item sin P/N sin documento')

    if fallos:
        for f in fallos[:40]:
            print('FALLO:', f)
        print('%d fallo(s)' % len(fallos))
        return 1
    print('OK partes_cij_ocr: %d partes, %d items sin P/N, %d paginas OCR, '
          '%d modelos'
          % (len(d['partes']), len(d['items_sin_pn']), paginas,
             len({m for p in d['partes'] for m in p.get('modelos', [])})))
    return 0


if __name__ == '__main__':
    sys.exit(main())
