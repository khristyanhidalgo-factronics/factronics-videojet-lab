# -*- coding: utf-8 -*-
"""OCR de los PDFs escaneados del lote laser que traen JPEG embebido.

Pipeline: extraer JPEGs del PDF -> OCR con Windows.Media.Ocr (PowerShell WinRT)
-> texto concatenado en datos/extraccion/laser_<slug>_ocr.txt.
Actualiza _lote_laser_resumen.json con ocr_imagenes / ocr_chars / estado_ocr.
Sin dependencias externas: solo PowerShell del sistema.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_jpegs_pdf import extraer_jpegs  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
LASER = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
         r'\CARPETA A MEJORAR\hacer notebookllm\documentacion laser')
RESUMEN = os.path.join(EXTRACCION, '_lote_laser_resumen.json')
OCR_PS1 = os.path.join(RAIZ, 'tools', 'ocr_windows.ps1')


def slug_de(relativo):
    sin_ext = re.sub(r'\.pdf$', '', relativo, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', sin_ext.lower()).strip('_')[:120]


def ocr_imagen(ruta_jpg, ruta_txt):
    try:
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                        '-File', OCR_PS1, '-RutaImagen', ruta_jpg,
                        '-Salida', ruta_txt],
                       check=True, capture_output=True, timeout=120)
        with open(ruta_txt, 'r', encoding='utf-8-sig', errors='replace') as f:
            return f.read().strip()
    except (subprocess.SubprocessError, OSError):
        return ''


def main():
    datos = json.load(open(RESUMEN, 'r', encoding='utf-8'))
    pendientes = []
    for r in datos['resultados']:
        if r['estado'] != 'sin-texto':
            continue
        completo = os.path.join(LASER, r['archivo'])
        try:
            b = open(completo, 'rb').read()
        except OSError:
            continue
        if b'DCTDecode' not in b:
            continue
        pendientes.append(r)
    print('PDFs escaneados con JPEG a OCR:', len(pendientes))

    hechos = 0
    for r in pendientes:
        completo = os.path.join(LASER, r['archivo'])
        with tempfile.TemporaryDirectory(prefix='ocr_laser_') as tmp:
            jpgs = extraer_jpegs(completo, tmp, 'pag')
            textos = []
            for jpg in jpgs:
                salida_txt = os.path.splitext(jpg)[0] + '.txt'
                texto = ocr_imagen(jpg, salida_txt)
                if len(texto) > 40:
                    textos.append(texto)
            contenido = '\n\n'.join(textos)
        r['ocr_imagenes'] = len(jpgs)
        r['ocr_chars'] = len(contenido)
        r['estado_ocr'] = ('ok' if len(contenido) >= 200 else
                           'escaso' if contenido else 'sin-resultado')
        if contenido:
            destino = os.path.join(EXTRACCION,
                                   'laser_%s_ocr.txt' % slug_de(r['archivo']))
            with open(destino, 'w', encoding='utf-8') as f:
                f.write('# OCR (Windows.Media.Ocr) - fuente: %s\n' % r['archivo'])
                f.write('# imagenes=%d caracteres=%d\n\n' % (len(jpgs), len(contenido)))
                f.write(contenido)
        hechos += 1
        print('  [%d/%d] %-60s imgs=%d chars=%d (%s)'
              % (hechos, len(pendientes), r['archivo'][:58], len(jpgs),
                 len(contenido), r['estado_ocr']))

    json.dump(datos, open(RESUMEN, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    con = sum(1 for r in datos['resultados'] if r.get('ocr_chars'))
    print('RESUMEN OCR: %d PDFs con texto OCR; chars totales=%d'
          % (con, sum(r.get('ocr_chars', 0) for r in datos['resultados'])))


if __name__ == '__main__':
    main()
