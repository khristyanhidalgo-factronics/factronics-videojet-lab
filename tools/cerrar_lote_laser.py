# -*- coding: utf-8 -*-
"""Cierra el lote laser: reclasifica los 14 PDFs que quedaron sin texto.

Casos:
  - 4 articulos de conocimiento de fibra: OCR normal a 1600 px.
  - 2 diagramas apaisados: si el OCR devuelve 0 lineas se rota la imagen
    90/270 grados y se conserva la orientacion con mas texto.
  - 7 planos/3D sin rotulos: se comprueba que el OCR devuelve 0 lineas por
    diseno (no por fallo del rasterizador) y se marcan `sin-texto-por-diseno`.
  - MedidoresPortenciaCO2.pdf: Windows.Data.Pdf no puede rasterizarlo; se
    extrae la imagen JPEG incrustada (obj 21), se guarda como evidencia y se
    registra la lectura visual de los displays sin inventar texto OCR.

Actualiza datos/extraccion/_lote_laser_resumen.json y deja el texto en
datos/extraccion/laser_<slug>_ocr.txt.

Uso:
  python -u tools/cerrar_lote_laser.py
  python -u tools/cerrar_lote_laser.py --solo medidores
  python -u tools/cerrar_lote_laser.py --solo recuperables --reforzar
"""
import argparse
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import ocr_pdf_paginas as O  # noqa: E402

EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
RESUMEN = os.path.join(EXTRACCION, '_lote_laser_resumen.json')
ROTAR = os.path.join(RAIZ, 'tools', 'rotar_imagen.ps1')
ANCHO = 1600
IDIOMA = 'es-MX'
TIMEOUT = 90

RECUPERABLES = [
    r'manuales fibra\Nueva carpeta\18030-Working Distance 7230, 7330, 7320, 7220 (Eng).pdf',
    r'manuales fibra\Nueva carpeta\18032-Marking Fields and Working Distances 7340, 7440 (Eng).pdf',
    r'manuales fibra\Nueva carpeta\18035-Locating Fault Messages in Laser Unit Interfaces (Eng).pdf',
    r'manuales fibra\Nueva carpeta\18037-Laser User Interface Devices and Software (Eng).pdf',
    r'accesorios laser\Extraction Accesories.pdf',
    r'accesorios laser\k30 wiring diagram.pdf',
]

SIN_TEXTO = [
    r'accesorios laser\07130.PDF',
    r'accesorios laser\AL-SP71082_Drehgebereinheit.pdf',
    r'drawings co2\OG5052 3d drawing.pdf',
    r'drawings co2\Soporte Laser Fiber.pdf',
    r'drawings co2\Soporte laser CO2.pdf',
    r'drawings co2\prueba.pdf',
    r'drawings co2\pruebaaaaaaaaaaaaaaaaaaaaaaaaa.pdf',
]

DANADO = r'accesorios laser\MedidoresPortenciaCO2.pdf'


def slug_de(relativo):
    sin_ext = re.sub(r'\.pdf$', '', relativo, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', sin_ext.lower()).strip('_')[:120]


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    temporal = ruta + '.tmp'
    with open(temporal, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(temporal, ruta)


def rotar_imagen(origen, destino, grados):
    codigo, salida, err = O.ejecutar(
        [O.POWERSHELL, '-NoProfile', '-ExecutionPolicy', 'Bypass',
         '-File', ROTAR, '-RutaImagen', origen, '-Salida', destino,
         '-Grados', str(grados)], TIMEOUT)
    if codigo != 0:
        raise RuntimeError('rotar %d grados: %s' % (grados, (err or salida).strip()[:200]))


def lineas_a_texto(lineas):
    ordenadas = sorted(lineas, key=lambda l: (l.get('y', 0), l.get('x', 0)))
    return '\n'.join((l.get('texto') or '').strip()
                     for l in ordenadas if (l.get('texto') or '').strip())


def ocr_pagina(pdf, pagina, tmp, probar_rotacion=False):
    """Renderiza y hace OCR; en paginas sueltas con poco texto prueba 90/270."""
    png = os.path.join(tmp, 'p%03d.png' % pagina)
    js = os.path.join(tmp, 'p%03d.json' % pagina)
    aviso = O.renderizar(pdf, pagina, png, ANCHO, TIMEOUT)
    datos = O.ocr(png, js, IDIOMA, TIMEOUT)
    lineas = datos.get('lineas', [])
    rotacion = None
    texto_normal = lineas_a_texto(lineas)
    if probar_rotacion and len(texto_normal) < 200:
        mejor = lineas
        mejor_texto = texto_normal
        for grados in (90, 270):
            png_rot = os.path.join(tmp, 'p%03d_r%d.png' % (pagina, grados))
            js_rot = os.path.join(tmp, 'p%03d_r%d.json' % (pagina, grados))
            try:
                rotar_imagen(png, png_rot, grados)
                datos_rot = O.ocr(png_rot, js_rot, IDIOMA, TIMEOUT)
            except RuntimeError as exc:
                print('      rotacion %d fallo: %s' % (grados, exc), flush=True)
                continue
            texto_rot = lineas_a_texto(datos_rot.get('lineas', []))
            if len(texto_rot) > len(mejor_texto):
                mejor = datos_rot.get('lineas', [])
                mejor_texto = texto_rot
                rotacion = grados
        lineas = mejor
    return lineas, aviso, rotacion


def procesar_pdf(pdf, tmp, todas_las_paginas=True):
    """Devuelve (paginas, lineas, texto, rotaciones, omitidas)."""
    primera = os.path.join(tmp, 'p001.png')
    aviso = O.renderizar(pdf, 1, primera, ANCHO, TIMEOUT)
    m = re.search(r'\((\d+)\s+paginas\)', aviso)
    if not m:
        raise RuntimeError('no se pudo leer el numero de paginas: %r' % aviso)
    total = int(m.group(1))
    hasta = total if todas_las_paginas else 1
    bloques = []
    lineas_total = 0
    rotaciones = {}
    omitidas = []
    for pagina in range(1, hasta + 1):
        try:
            lineas, _, rotacion = ocr_pagina(
                pdf, pagina, tmp, probar_rotacion=(hasta == 1))
        except RuntimeError as exc:
            omitidas.append(pagina)
            print('      pagina %d omitida: %s' % (pagina, str(exc)[:160]),
                  flush=True)
            continue
        texto = lineas_a_texto(lineas)
        if texto:
            bloques.append('===== PAGINA %d =====\n%s' % (pagina, texto))
        lineas_total += len(lineas)
        if rotacion:
            rotaciones[str(pagina)] = rotacion
        print('      pagina %d/%d: %d lineas%s'
              % (pagina, total, len(lineas),
                 (' (rotada %d grados)' % rotacion) if rotacion else ''),
              flush=True)
    return hasta, lineas_total, '\n\n'.join(bloques), rotaciones, omitidas


def guardar_texto(relativo, paginas, lineas, texto, rotaciones, omitidas):
    slug = slug_de(relativo)
    destino = os.path.join(EXTRACCION, 'laser_%s_ocr.txt' % slug)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('# OCR Windows.Data.Pdf + Windows.Media.Ocr - fuente: %s\n'
                % relativo)
        f.write('# paginas=%d lineas=%d caracteres=%d omitidas=%s rotaciones=%s\n\n'
                % (paginas, lineas, len(texto), omitidas, rotaciones))
        f.write(texto)
    return os.path.relpath(destino, RAIZ).replace('\\', '/')


def actualizar_entrada(datos, relativo, **campos):
    for r in datos.get('resultados', []):
        if r.get('archivo') == relativo:
            r.update(campos)
            return r
    raise KeyError('no esta en el resumen: %s' % relativo)


def extraer_jpeg(pdf, numero_objeto, destino):
    """Extrae el stream de un objeto JPEG sin dependencias externas."""
    with open(pdf, 'rb') as f:
        b = f.read()
    m = re.search(rb'(?s)(?:^|\n)%d\s+0\s+obj(.*?)endobj' % numero_objeto, b)
    if not m:
        raise RuntimeError('no se encontro el objeto %d' % numero_objeto)
    body = m.group(1)
    sm = re.search(rb'stream\r?\n', body)
    if not sm:
        raise RuntimeError('el objeto %d no tiene stream' % numero_objeto)
    raw = re.sub(rb'\r?\nendstream\s*$', b'', body[sm.end():])
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'wb') as f:
        f.write(raw)
    return len(raw)


def medidores(datos, base):
    pdf = os.path.join(base, DANADO)
    print('  [danado] %s' % DANADO, flush=True)
    campos = {'estado_ocr': 'imagen-extraida', 'ocr_paginas': None,
              'ocr_lineas': None, 'ocr_chars': None, 'ocr_omitidas': None}
    try:
        with tempfile.TemporaryDirectory(prefix='laser_med_') as tmp:
            O.renderizar(pdf, 1, os.path.join(tmp, 'p1.png'), ANCHO, TIMEOUT)
        campos['nota'] = 'Windows.Data.Pdf si lo renderizo en esta pasada.'
        actualizar_entrada(datos, DANADO, **campos)
        return
    except RuntimeError as exc:
        campos['ocr_error'] = str(exc)[:300]
        print('    rasterizado fallo: %s' % str(exc)[:180], flush=True)

    carpeta = os.path.join(EXTRACCION, 'medidores_portencia_co2')
    destino = os.path.join(carpeta, 'obj21.jpg')
    try:
        bytes_jpg = extraer_jpeg(pdf, 21, destino)
        print('    imagen extraida: obj21.jpg (%d bytes)' % bytes_jpg,
              flush=True)
    except RuntimeError as exc:
        campos['ocr_error'] += ' | ' + str(exc)
        actualizar_entrada(datos, DANADO, **campos)
        return

    js = os.path.join(carpeta, 'obj21_ocr.json')
    try:
        d = O.ocr(destino, js, IDIOMA, TIMEOUT)
        lineas = d.get('lineas', [])
        texto = lineas_a_texto(lineas)
        campos['ocr_lineas'] = len(lineas)
        campos['ocr_chars'] = len(texto)
        campos['imagenes_extraidas'] = [{
            'archivo': 'datos/extraccion/medidores_portencia_co2/obj21.jpg',
            'bytes': bytes_jpg,
            'ancho': 810,
            'alto': 426,
            'ocr_lineas': len(lineas),
            'ocr_texto': texto,
        }]
    except RuntimeError as exc:
        campos['ocr_error'] += ' | OCR imagen: ' + str(exc)
    campos['lectura_visual'] = {
        'display_superior': '029',
        'display_inferior': '581',
        'nota': ('Lectura visual de obj21.jpg; el OCR no transcribe los digitos. '
                 'El punto decimal del display superior no queda resuelto. '
                 'No se usa como dato tecnico firme.'),
    }
    campos['nota'] = ('PDF Ghostscript 8.15 con miles de imagenes inline CMYK; '
                      'Windows.Data.Pdf falla al cargar/renderizar y Edge imprime '
                      'en blanco. Se conserva la imagen incrustada como evidencia.')
    actualizar_entrada(datos, DANADO, **campos)
    print('    OCR de la imagen: %s lineas, %s chars'
          % (campos.get('ocr_lineas'), campos.get('ocr_chars')), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo', choices=['recuperables', 'sin-texto', 'medidores',
                                       'todos'], default='todos')
    ap.add_argument('--reforzar', action='store_true')
    args = ap.parse_args()

    with open(RESUMEN, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    base = datos.get('carpeta', '')
    if not base or not os.path.isdir(base):
        raise SystemExit('falta la carpeta base del lote laser: %r' % base)

    grupos = []
    if args.solo in ('recuperables', 'todos'):
        grupos.append(('recuperables', RECUPERABLES))
    if args.solo in ('sin-texto', 'todos'):
        grupos.append(('sin-texto', SIN_TEXTO))

    for nombre, archivos in grupos:
        print('\n%s: %d PDFs' % (nombre, len(archivos)), flush=True)
        for relativo in archivos:
            pdf = os.path.join(base, relativo)
            if not os.path.exists(pdf):
                print('  AVISO: falta %s' % pdf, flush=True)
                continue
            print('  [%s] %s' % (nombre, relativo), flush=True)
            try:
                with tempfile.TemporaryDirectory(prefix='laser_cierre_') as tmp:
                    paginas, lineas, texto, rotaciones, omitidas = procesar_pdf(
                        pdf, tmp, todas_las_paginas=True)
            except RuntimeError as exc:
                actualizar_entrada(datos, relativo, estado_ocr='error',
                                   ocr_error=str(exc)[:300])
                guardar_json(RESUMEN, datos)
                print('    ERROR: %s' % str(exc)[:180], flush=True)
                continue

            campos = {
                'ocr_paginas': paginas,
                'ocr_lineas': lineas,
                'ocr_chars': len(texto),
                'ocr_omitidas': omitidas,
            }
            if rotaciones:
                campos['ocr_rotacion'] = rotaciones
            if texto:
                campos['txt_ocr'] = guardar_texto(
                    relativo, paginas, lineas, texto, rotaciones, omitidas)
            if nombre == 'sin-texto' and not texto:
                campos['estado_ocr'] = 'sin-texto-por-diseno'
                campos['nota'] = ('Plano/3D sin rotulos: el OCR devuelve 0 lineas '
                                  'por diseno, no por fallo del rasterizador.')
            elif nombre == 'sin-texto' and texto:
                campos['estado_ocr'] = 'ok'
                campos['nota'] = 'Se recupero texto no previsto en un plano.'
            else:
                if len(texto) >= 200:
                    campos['estado_ocr'] = 'ok-rotado' if rotaciones else 'ok'
                elif texto:
                    campos['estado_ocr'] = 'escaso'
                else:
                    campos['estado_ocr'] = 'sin-resultado'
            actualizar_entrada(datos, relativo, **campos)
            guardar_json(RESUMEN, datos)
            print('    -> %s: %d paginas, %d lineas, %d chars, rotaciones=%s'
                  % (campos['estado_ocr'], paginas, lineas, len(texto),
                     rotaciones), flush=True)

    if args.solo in ('medidores', 'todos'):
        print('\nmedidores: 1 PDF', flush=True)
        medidores(datos, base)

    resultados = datos.get('resultados', [])
    conteo = collections.Counter(r.get('estado_ocr') or r.get('estado')
                                 for r in resultados)
    datos['conteo_ocr'] = dict(sorted(conteo.items()))
    recuperados = [r for r in resultados
                   if r.get('archivo') in (RECUPERABLES + SIN_TEXTO)
                   and r.get('ocr_chars')]
    datos['cierre_lote_laser'] = {
        'fecha': '2026-11-13',
        'casos_revisados': len(RECUPERABLES) + len(SIN_TEXTO) + 1,
        'recuperados_con_texto': len(recuperados),
        'chars_recuperados': sum(r.get('ocr_chars') or 0 for r in recuperados),
        'sin_texto_por_diseno': sum(
            1 for r in resultados
            if r.get('estado_ocr') == 'sin-texto-por-diseno'),
        'danado_rasterizado': sum(
            1 for r in resultados
            if r.get('estado_ocr') == 'imagen-extraida'),
        'nota': ('Los 14 casos del cierre quedan clasificados; no se asciende '
                 'ningun dato tecnico a verificado.'),
    }
    guardar_json(RESUMEN, datos)
    print('\nOK: %s' % json.dumps(datos['conteo_ocr'], ensure_ascii=False))
    print('   cierre: %s'
          % json.dumps(datos['cierre_lote_laser'], ensure_ascii=False))


if __name__ == '__main__':
    main()
