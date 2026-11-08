# -*- coding: utf-8 -*-
"""Inventario completo de la carpeta 'documentacion laser' (1900+ archivos).

Registra por archivo: ruta relativa, bytes, extension, subcarpeta de nivel 1 y estado
de extraccion (leyendo _lote_laser_resumen.json si ya existe). Salida:
datos/laser_inventario.json
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
           r'\CARPETA A MEJORAR\hacer notebookllm\documentacion laser')
DESTINO = os.path.join(RAIZ, 'datos', 'laser_inventario.json')
RESUMEN_LOTE = os.path.join(RAIZ, 'datos', 'extraccion', '_lote_laser_resumen.json')


def main():
    estados = {}
    if os.path.exists(RESUMEN_LOTE):
        try:
            d = json.load(open(RESUMEN_LOTE, 'r', encoding='utf-8'))
            for r in d.get('resultados', []):
                estados[r['archivo']] = r
        except (OSError, ValueError):
            pass

    archivos = []
    por_ext = Counter()
    por_sub = Counter()
    por_estado = Counter()
    for raiz, _, nombres in os.walk(CARPETA):
        for nombre in sorted(nombres):
            completo = os.path.join(raiz, nombre)
            rel = os.path.relpath(completo, CARPETA)
            partes = rel.split(os.sep)
            sub = partes[0] if len(partes) > 1 else '(raiz)'
            ext = os.path.splitext(nombre)[1].lower() or '(sin)'
            try:
                tam = os.path.getsize(completo)
            except OSError:
                tam = 0
            estado = 'pendiente-extraccion'
            if rel in estados:
                estado = estados[rel].get('estado', 'pendiente-extraccion')
            por_ext[ext] += 1
            por_sub[sub] += 1
            por_estado[estado] += 1
            archivos.append({'ruta': rel, 'bytes': tam, 'ext': ext,
                             'subcarpeta': sub, 'estado_extraccion': estado})
    datos = {
        'producto': 'Inventario de documentacion laser (Videojet)',
        'schema': 1,
        'carpeta': CARPETA,
        'total_archivos': len(archivos),
        'resumen_por_extension': dict(por_ext.most_common()),
        'resumen_por_subcarpeta': dict(por_sub.most_common()),
        'resumen_estado_extraccion': dict(por_estado.most_common()),
        'nota': ('Inventario completo del arbol. La extraccion de texto se hace con '
                 'tools/lote_laser.py (PDFs, extractor visual v3, sirve cifrado y no '
                 'cifrado); este archivo se regenera tras cada lote para reflejar '
                 'chars/estado por PDF.'),
        'archivos': archivos,
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | archivos=%d' % (os.path.relpath(DESTINO, RAIZ), len(archivos)))
    print('por extension:', dict(por_ext.most_common(10)))
    print('por subcarpeta:', dict(por_sub.most_common(10)))
    print('estado extraccion:', dict(por_estado.most_common()))


if __name__ == '__main__':
    main()
