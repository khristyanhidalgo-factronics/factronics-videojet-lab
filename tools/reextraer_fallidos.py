# -*- coding: utf-8 -*-
"""Re-extrae SOLO los PDFs fallidos de los lotes laser y TTO (error / cifrado).

Actualiza los resumenes JSON y escribe los txt con el mismo esquema de nombres.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf_cifrado import extraer_visual  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
LASER = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
         r'\CARPETA A MEJORAR\hacer notebookllm\documentacion laser')
TTO = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
       r'\CURSO BRASILLinformacion-------------------------------------\TTO 6x30')


def slug_de(relativo):
    sin_ext = re.sub(r'\.pdf$', '', relativo, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', sin_ext.lower()).strip('_')[:120]


def limpiar(texto):
    texto = re.sub(r'[ \t]+', ' ', texto)
    return re.sub(r'\n{3,}', '\n\n', texto).strip()


def procesar(nombre_json, base, prefijo):
    ruta_json = os.path.join(EXTRACCION, nombre_json)
    datos = json.load(open(ruta_json, 'r', encoding='utf-8'))
    fallidos = [r for r in datos['resultados']
                if r['estado'] in ('error', 'cifrado-no-soportado')]
    print('%s: fallidos=%d' % (nombre_json, len(fallidos)))
    recuperados = 0
    for registro in fallidos:
        completo = os.path.join(base, registro['archivo'])
        try:
            partes, bloques, cifrado = extraer_visual(completo)
            texto = limpiar('\n\n'.join(partes))
            registro['chars'] = len(texto)
            registro['cifrado'] = cifrado
            registro['bloques'] = bloques
            registro['estado'] = ('ok' if len(texto) >= 200 else
                                  'texto-escaso' if texto else 'sin-texto')
            registro.pop('error', None)
            destino = os.path.join(EXTRACCION, '%s_%s_visual.txt'
                                   % (prefijo, slug_de(registro['archivo'])))
            with open(destino, 'w', encoding='utf-8') as f:
                f.write('# EXTRAIDO POR tools/leer_pdf_cifrado.py v3 VISUAL '
                        '(stdlib) - fuente: %s\n' % registro['archivo'])
                f.write('# cifrado=%s bloques=%d caracteres=%d\n\n'
                        % (cifrado, bloques, len(texto)))
                f.write(texto)
            if registro['estado'] == 'ok':
                recuperados += 1
        except Exception as e:
            registro['estado'] = 'error'
            registro['error'] = '%s: %s' % (type(e).__name__, e)
    json.dump(datos, open(ruta_json, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    cuentas = {}
    for r in datos['resultados']:
        cuentas[r['estado']] = cuentas.get(r['estado'], 0) + 1
    print('  recuperados_ok=%d | estados finales: %s' % (recuperados, cuentas))


if __name__ == '__main__':
    procesar('_lote_laser_resumen.json', LASER, 'laser')
    procesar('_lote_tto_resumen.json', TTO, 'tto')
