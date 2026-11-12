# -*- coding: utf-8 -*-
"""OCR de un PDF pagina a pagina con Windows.Data.Pdf + Windows.Media.Ocr.

No instala nada: usa PowerShell/WinRT del sistema. Renderiza cada pagina a PNG
(3000 px de ancho por defecto) y guarda las lineas OCR con coordenadas para
poder reconstruir tablas.

Blindaje:
- timeout por pagina (el rasterizador de Windows se cuelga con algunas laminas
  vectoriales patologicas); al vencer, mata el proceso y reintenta a menor ancho;
- si vuelve a vencer, registra la pagina como `error: render-timeout` y sigue;
- guarda el JSON incrementalmente tras cada pagina (no se pierde el avance).

Uso:
  python -u tools/ocr_pdf_paginas.py "C:\\...\\1550 - Illustrated Parts List.pdf" \
      datos/extraccion/ocr_cij_ipl_1550.json --slug cij_ipl_1550

Salida:
  { fuente, slug, ancho, idioma, paginas: [
      { pagina, ancho, alto, lineas: [ {texto,x,y,w,h,palabras:[...]} ] }
  ] }
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(RAIZ, 'tools', 'render_pdf_pagina.ps1')
OCR = os.path.join(RAIZ, 'tools', 'ocr_windows_lineas.ps1')
POWERSHELL = 'powershell.exe'


def ejecutar(args, timeout):
    """Ejecuta y devuelve (returncode, stdout, stderr). Mata el proceso al vencer."""
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return None, '', 'timeout %ss' % timeout


def renderizar(pdf, pagina, salida, ancho, timeout):
    codigo, salida_txt, err = ejecutar(
        [POWERSHELL, '-NoProfile', '-ExecutionPolicy', 'Bypass',
         '-File', RENDER, '-RutaPdf', pdf, '-Pagina', str(pagina),
         '-Salida', salida, '-Ancho', str(ancho)], timeout)
    if codigo != 0:
        raise RuntimeError('render pagina %d (ancho %d): %s'
                           % (pagina, ancho, (err or salida_txt).strip()[:300]))
    return salida_txt


def ocr(imagen, salida, idioma, timeout):
    codigo, salida_txt, err = ejecutar(
        [POWERSHELL, '-NoProfile', '-ExecutionPolicy', 'Bypass',
         '-File', OCR, '-RutaImagen', imagen, '-Salida', salida,
         '-Idioma', idioma], timeout)
    if codigo != 0:
        raise RuntimeError('ocr: %s' % (err or salida_txt).strip()[:300])
    with open(salida, 'r', encoding='utf-8') as f:
        return json.load(f)


def guardar(ruta, datos):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    temporal = ruta + '.tmp'
    with open(temporal, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(temporal, ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('salida')
    ap.add_argument('--slug', default='')
    ap.add_argument('--ancho', type=int, default=3000)
    ap.add_argument('--ancho-reintento', type=int, default=1500)
    ap.add_argument('--idioma', default='es-MX')
    ap.add_argument('--desde', type=int, default=1)
    ap.add_argument('--hasta', type=int, default=0)
    ap.add_argument('--timeout-pagina', type=int, default=90)
    ap.add_argument('--omitir', default='',
                    help='paginas a omitir, separadas por coma (laminas que cuelgan el render)')
    ap.add_argument('--reanudar', action='store_true',
                    help='conserva las paginas ya presentes en la salida')
    args = ap.parse_args()
    omitir = {int(x) for x in args.omitir.split(',') if x.strip().isdigit()}

    slug = args.slug or re.sub(r'[^a-z0-9]+', '_',
                               os.path.splitext(os.path.basename(args.pdf))[0].lower()).strip('_')
    previas = {}
    if args.reanudar and os.path.exists(args.salida):
        try:
            with open(args.salida, 'r', encoding='utf-8') as f:
                for p in json.load(f).get('paginas', []):
                    previas[p.get('pagina')] = p
        except (ValueError, OSError):
            previas = {}

    with tempfile.TemporaryDirectory(prefix='ocr_pdf_') as tmp:
        primera = os.path.join(tmp, 'p1.png')
        aviso = renderizar(args.pdf, 1, primera, args.ancho, args.timeout_pagina)
        m = re.search(r'\((\d+)\s+paginas\)', aviso)
        if not m:
            raise RuntimeError('no se pudo leer el numero de paginas: %r' % aviso)
        total = int(m.group(1))
        hasta = args.hasta or total
        hasta = min(hasta, total)
        print('%s: %d paginas; OCR %d..%d' % (slug, total, args.desde, hasta),
              flush=True)

        paginas = []
        for pagina in range(args.desde, hasta + 1):
            if pagina in previas:
                paginas.append(previas[pagina])
                print('  pagina %3d/%d: ya estaba (%d lineas)'
                      % (pagina, total, len(previas[pagina].get('lineas', []))),
                      flush=True)
                continue
            if pagina in omitir:
                datos = {'pagina': pagina, 'ancho': 0, 'alto': 0, 'lineas': [],
                         'error': 'omitida-manual',
                         'detalle': 'lamina vectorial que cuelga Windows.Data.Pdf'}
                paginas.append(datos)
                print('  pagina %3d/%d: OMITIDA por --omitir'
                      % (pagina, total), flush=True)
                guardar(args.salida, {
                    'fuente': os.path.basename(args.pdf),
                    'ruta': args.pdf,
                    'slug': slug,
                    'ancho_render': args.ancho,
                    'idioma_ocr': args.idioma,
                    'paginas': paginas,
                })
                continue
            png = os.path.join(tmp, 'p%03d.png' % pagina)
            js = os.path.join(tmp, 'p%03d.json' % pagina)
            datos = None
            ultimo_error = ''
            for ancho in (args.ancho, args.ancho_reintento):
                try:
                    renderizar(args.pdf, pagina, png, ancho, args.timeout_pagina)
                    datos = ocr(png, js, args.idioma, args.timeout_pagina)
                    datos['ancho_render'] = ancho
                    break
                except RuntimeError as exc:
                    ultimo_error = str(exc)
                    print('  pagina %3d/%d: fallo a %d px: %s'
                          % (pagina, total, ancho, ultimo_error), flush=True)
            if datos is None:
                datos = {'pagina': pagina, 'ancho': 0, 'alto': 0, 'lineas': [],
                         'error': 'render-timeout',
                         'detalle': ultimo_error}
                print('  pagina %3d/%d: OMITIDA (render colgado)'
                      % (pagina, total), flush=True)
            else:
                print('  pagina %3d/%d: %d lineas'
                      % (pagina, total, len(datos.get('lineas', []))), flush=True)
            datos['pagina'] = pagina
            paginas.append(datos)
            guardar(args.salida, {
                'fuente': os.path.basename(args.pdf),
                'ruta': args.pdf,
                'slug': slug,
                'ancho_render': args.ancho,
                'idioma_ocr': args.idioma,
                'paginas': paginas,
            })

    salida = {
        'fuente': os.path.basename(args.pdf),
        'ruta': args.pdf,
        'slug': slug,
        'ancho_render': args.ancho,
        'idioma_ocr': args.idioma,
        'paginas': paginas,
    }
    guardar(args.salida, salida)
    omitidas = [p['pagina'] for p in paginas if p.get('error')]
    print('OK %s: %d paginas OCR%s'
          % (args.salida, len(paginas),
             ('; omitidas: %s' % omitidas) if omitidas else ''), flush=True)


if __name__ == '__main__':
    main()
