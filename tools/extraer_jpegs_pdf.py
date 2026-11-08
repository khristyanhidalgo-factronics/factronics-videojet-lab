# -*- coding: utf-8 -*-
"""Extrae los JPEG (DCTDecode) embebidos en un PDF a archivos .jpg."""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def extraer_jpegs(ruta_pdf, carpeta_salida, prefijo):
    b = open(ruta_pdf, 'rb').read()
    salidas = []
    # dict contiene /DCTDecode justo antes del stream
    for m in re.finditer(rb'stream\r?\n', b):
        cabecera = b[max(0, m.start() - 500):m.start()]
        if b'DCTDecode' not in cabecera:
            continue
        inicio = m.end()
        fin = b.find(b'endstream', inicio)
        if fin < 0:
            continue
        datos = b[inicio:fin].rstrip(b'\r\n')
        # el JPEG empieza con FFD8 y termina con FFD9
        p8 = datos.find(b'\xff\xd8')
        if p8 < 0:
            continue
        datos = datos[p8:]
        p9 = datos.rfind(b'\xff\xd9')
        if p9 >= 0:
            datos = datos[:p9 + 2]
        if len(datos) < 2000:
            continue
        destino = os.path.join(carpeta_salida, '%s_%02d.jpg' % (prefijo, len(salidas)))
        with open(destino, 'wb') as f:
            f.write(datos)
        salidas.append(destino)
    return salidas


if __name__ == '__main__':
    import tempfile
    pdf = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='ocr_')
    os.makedirs(salida, exist_ok=True)
    archivos = extraer_jpegs(pdf, salida, 'pag')
    print('jpegs extraidos:', len(archivos))
    for a in archivos:
        print(a)
