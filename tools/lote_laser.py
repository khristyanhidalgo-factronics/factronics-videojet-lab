# -*- coding: utf-8 -*-
"""Lote: extrae texto de TODOS los PDFs de la carpeta 'documentacion laser'.

Usa tools/leer_pdf_cifrado.py en modo VISUAL (sirve para cifrados y no cifrados).
Guarda datos/extraccion/laser_<slug>_visual.txt y un resumen JSON con el estado de
cada archivo. Los PDFs > 80 MB se omiten por seguridad (quedan registrados).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf_cifrado import extraer_visual  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
           r'\CARPETA A MEJORAR\hacer notebookllm\documentacion laser')
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
RESUMEN = os.path.join(EXTRACCION, '_lote_laser_resumen.json')
LIMITE_MB = 80


def slug_de(relativo):
    sin_ext = re.sub(r'\.pdf$', '', relativo, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', sin_ext.lower()).strip('_')[:120]


def limpiar(texto):
    texto = re.sub(r'[ \t]+', ' ', texto)
    return re.sub(r'\n{3,}', '\n\n', texto).strip()


def main():
    resultados = []
    pendientes = []
    for raiz, _, archivos in os.walk(CARPETA):
        for nombre in sorted(archivos):
            if not nombre.lower().endswith('.pdf'):
                continue
            completo = os.path.join(raiz, nombre)
            rel = os.path.relpath(completo, CARPETA)
            pendientes.append((rel, completo))
    print('PDFs a procesar:', len(pendientes))

    for i, (rel, completo) in enumerate(pendientes, 1):
        registro = {'archivo': rel, 'bytes': os.path.getsize(completo),
                    'chars': 0, 'estado': 'error'}
        try:
            if registro['bytes'] > LIMITE_MB * 1024 * 1024:
                registro['estado'] = 'omitido-grande'
            else:
                partes, bloques, cifrado = extraer_visual(completo)
                texto = limpiar('\n\n'.join(partes))
                registro['chars'] = len(texto)
                registro['cifrado'] = cifrado
                registro['bloques'] = bloques
                registro['estado'] = ('ok' if len(texto) >= 200 else
                                      'texto-escaso' if texto else 'sin-texto')
                destino = os.path.join(EXTRACCION,
                                       'laser_%s_visual.txt' % slug_de(rel))
                with open(destino, 'w', encoding='utf-8') as f:
                    f.write('# EXTRAIDO POR tools/leer_pdf_cifrado.py v3 VISUAL '
                            '(stdlib) - fuente: %s\n' % rel)
                    f.write('# cifrado=%s bloques=%d caracteres=%d\n\n'
                            % (cifrado, bloques, len(texto)))
                    f.write(texto)
        except RuntimeError as e:
            registro['estado'] = 'cifrado-no-soportado'
            registro['error'] = str(e)
        except Exception as e:
            registro['estado'] = 'error'
            registro['error'] = '%s: %s' % (type(e).__name__, e)
        resultados.append(registro)
        if i % 50 == 0:
            print('... %d/%d' % (i, len(pendientes)))

    with open(RESUMEN, 'w', encoding='utf-8') as f:
        json.dump({
            'carpeta': CARPETA,
            'total_pdfs': len(resultados),
            'herramienta': 'tools/leer_pdf_cifrado.py v3 visual + lote_laser.py',
            'limite_mb': LIMITE_MB,
            'resultados': resultados,
        }, f, ensure_ascii=False, indent=1)

    cuentas = {}
    for r in resultados:
        cuentas[r['estado']] = cuentas.get(r['estado'], 0) + 1
    print('RESUMEN:', cuentas)
    print('chars totales:', sum(r['chars'] for r in resultados))


if __name__ == '__main__':
    main()
