# -*- coding: utf-8 -*-
"""Re-extrae los 9 IPL 1000VJ con el extractor VISUAL v3 (coordenadas + ToUnicode)."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf_cifrado import extraer_visual  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
           r'\VIDEOJET DOCUMENTOS 1000VJ---------------------------'
           r'\ILUSTRACION DE PARTES 1000VJ')
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
RESUMEN = os.path.join(EXTRACCION, '_lote_ipl_visual_resumen.json')


def slug_de(nombre):
    stem = re.sub(r'\.pdf$', '', nombre, flags=re.I)
    stem = re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')
    stem = stem.replace('illustrated_parts_list', '').replace('illustrated_parts', '')
    stem = stem.replace('ipl_eng', '').strip('_')
    return stem or 'ipl'


def limpiar(texto):
    texto = re.sub(r'[ \t]+', ' ', texto)
    return re.sub(r'\n{3,}', '\n\n', texto).strip()


def main():
    resultados = []
    for nombre in sorted(os.listdir(CARPETA)):
        if not nombre.lower().endswith('.pdf'):
            continue
        ruta = os.path.join(CARPETA, nombre)
        slug = slug_de(nombre)
        registro = {'archivo': nombre, 'slug': slug, 'chars': 0, 'estado': 'error'}
        try:
            partes, bloques, cifrado = extraer_visual(ruta)
            texto = limpiar('\n\n'.join(partes))
            registro.update({'chars': len(texto), 'bloques': bloques,
                             'cifrado': cifrado,
                             'estado': 'ok' if len(texto) >= 200 else 'sin-texto'})
            destino = os.path.join(EXTRACCION, 'cij_ipl_%s_visual.txt' % slug)
            with open(destino, 'w', encoding='utf-8') as f:
                f.write('# EXTRAIDO POR tools/leer_pdf_cifrado.py v3 VISUAL '
                        '(stdlib) - fuente: %s\n' % nombre)
                f.write('# cifrado=%s bloques=%d caracteres=%d\n\n'
                        % (cifrado, bloques, len(texto)))
                f.write(texto)
        except Exception as e:
            registro['error'] = '%s: %s' % (type(e).__name__, e)
        resultados.append(registro)
        print('%-45s %-8s chars=%d' % (nombre[:43], registro['estado'], registro['chars']))
    with open(RESUMEN, 'w', encoding='utf-8') as f:
        json.dump({'carpeta': CARPETA, 'resultados': resultados}, f,
                  ensure_ascii=False, indent=1)
    print('OK %s' % os.path.relpath(RESUMEN, RAIZ))


if __name__ == '__main__':
    main()
