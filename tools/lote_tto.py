# -*- coding: utf-8 -*-
"""Lote: extrae texto de los PDFs del curso TTO 6x30 (boletines, manuales, etc.).

Subcarpetas: Boletines Tecnicos, Manuales, Instrucciones, Dibujos-Desenhos, Partes-Pecas.
Salida: datos/extraccion/tto_<slug>_visual.txt + _lote_tto_resumen.json
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf_cifrado import extraer_visual  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
        r'\CURSO BRASILLinformacion-------------------------------------\TTO 6x30')
SUBCARPETAS = ['Boletines Tecnicos', 'Manuales', 'Instrucciones',
               'Dibujos-Desenhos', 'Partes-Pecas']
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
RESUMEN = os.path.join(EXTRACCION, '_lote_tto_resumen.json')
LIMITE_MB = 80


def slug_de(relativo):
    sin_ext = re.sub(r'\.pdf$', '', relativo, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', sin_ext.lower()).strip('_')[:120]


def limpiar(texto):
    texto = re.sub(r'[ \t]+', ' ', texto)
    return re.sub(r'\n{3,}', '\n\n', texto).strip()


def main():
    pendientes = []
    for sub in SUBCARPETAS:
        raiz_sub = os.path.join(BASE, sub)
        if not os.path.isdir(raiz_sub):
            continue
        for raiz, _, archivos in os.walk(raiz_sub):
            for nombre in sorted(archivos):
                if nombre.lower().endswith('.pdf'):
                    pendientes.append((sub, os.path.join(raiz, nombre)))
    print('PDFs a procesar:', len(pendientes))

    resultados = []
    for i, (sub, completo) in enumerate(pendientes, 1):
        rel = os.path.relpath(completo, BASE)
        registro = {'archivo': rel, 'subcarpeta': sub,
                    'bytes': os.path.getsize(completo), 'chars': 0, 'estado': 'error'}
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
                destino = os.path.join(EXTRACCION, 'tto_%s_visual.txt' % slug_de(rel))
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
        if i % 25 == 0:
            print('... %d/%d' % (i, len(pendientes)))

    with open(RESUMEN, 'w', encoding='utf-8') as f:
        json.dump({'base': BASE, 'total_pdfs': len(resultados), 'resultados': resultados},
                  f, ensure_ascii=False, indent=1)
    cuentas = {}
    for r in resultados:
        cuentas[r['estado']] = cuentas.get(r['estado'], 0) + 1
    print('RESUMEN:', cuentas)
    print('chars totales:', sum(r['chars'] for r in resultados))


if __name__ == '__main__':
    main()
