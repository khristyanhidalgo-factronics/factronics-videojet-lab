# -*- coding: utf-8 -*-
"""Censo de cifrado PDF en la carpeta 'ficha de tintas' (564 PDFs).

Clasifica cada PDF por parametros del handler de seguridad estandar:
encrypt (si/no), R (revision), V, CFM del stream filter, Longitud de clave.
Salida: resumen por consola + datos/extraccion/_censo_cifrado_fichas.json
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CARPETA = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
           r'\DOCUMENTOS VIDEOJET ETERNOSSSSSSSSSSSSSSSSSSSSS\ficha de tintas')
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, 'datos', 'extraccion', '_censo_cifrado_fichas.json')

PATRON_R = re.compile(rb'/R\s+(\d+)')
PATRON_V = re.compile(rb'/V\s+(\d+)')
PATRON_CFM = re.compile(rb'/CFM\s*/(\w+)')
PATRON_LEN = re.compile(rb'/Length\s+(\d+)')


def parametros(b):
    d = {'cifrado': b'/Encrypt' in b}
    if not d['cifrado']:
        return d
    # localizar el objeto Encrypt real para leer SOLO sus parametros
    mref = re.search(rb'/Encrypt\s+(\d+)\s+(\d+)\s+R', b)
    if mref:
        num = int(mref.group(1))
        mobj = re.search(rb'(?:^|[\r\n\s])%d\s+0\s+obj\b(.*?)endobj' % num, b, re.S)
        d['obj_encrypt'] = num
        if mobj:
            b = mobj.group(1)  # el resto de campos se leen del dict Encrypt
    m = PATRON_R.search(b)
    d['R'] = int(m.group(1)) if m else None
    m = PATRON_V.search(b)
    d['V'] = int(m.group(1)) if m else None
    m = PATRON_CFM.search(b)
    d['CFM'] = m.group(1).decode() if m else None
    m = re.search(rb'/Length\s+(\d+)', b)
    d['Longitud_clave_bits'] = int(m.group(1)) if m else None
    d['ObjStm'] = b'/ObjStm' in b
    return d


def main():
    resumen = Counter()
    fichas = []
    for nombre in sorted(os.listdir(CARPETA)):
        if not nombre.lower().endswith('.pdf'):
            continue
        ruta = os.path.join(CARPETA, nombre)
        try:
            b = open(ruta, 'rb').read()
        except OSError:
            continue
        p = parametros(b)
        clave = 'sin-cifrado'
        if p['cifrado']:
            clave = 'R%s-V%s-%s-%sbit%s' % (p.get('R'), p.get('V'),
                                            p.get('CFM'), p.get('Longitud_clave_bits'),
                                            '+ObjStm' if p.get('ObjStm') else '')
        resumen[clave] += 1
        fichas.append({'archivo': nombre, **p, 'clase': clave})
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump({'carpeta': CARPETA, 'total': len(fichas),
                   'resumen': dict(resumen), 'fichas': fichas},
                  f, ensure_ascii=False, indent=1)
    print('total PDFs:', len(fichas))
    for k, n in resumen.most_common():
        print('  %-28s %d' % (k, n))
    print('escrito:', os.path.relpath(DESTINO, RAIZ))


if __name__ == '__main__':
    main()
