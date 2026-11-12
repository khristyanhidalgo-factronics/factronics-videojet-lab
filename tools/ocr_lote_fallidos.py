# -*- coding: utf-8 -*-
"""OCR por rasterizado de los PDFs escaneados que quedaron sin texto.

Usa Windows.Data.Pdf + Windows.Media.Ocr (sin instalar nada) pagina a pagina,
con timeout y reintento a menor resolucion. Actualiza los resumenes de lote y
deja el texto en datos/extraccion/<lote>_<slug>_ocr.txt.

Uso:
  python -u tools/ocr_lote_fallidos.py --lote todos
  python -u tools/ocr_lote_fallidos.py --lote tto --limite 5
  python -u tools/ocr_lote_fallidos.py --lote laser --reforzar

Selecciona los estados `sin-texto` y `texto-escaso` (los PDFs escaneados).
"""
import argparse
import json
import os
import re
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
LOTES = {
    'laser': {
        'resumen': os.path.join(EXTRACCION, '_lote_laser_resumen.json'),
        'clave_base': 'carpeta',
        'prefijo': 'laser',
    },
    'tto': {
        'resumen': os.path.join(EXTRACCION, '_lote_tto_resumen.json'),
        'clave_base': 'base',
        'prefijo': 'tto',
    },
}
OBJETIVO = {'sin-texto', 'texto-escaso', 'error'}


def slug_de(relativo):
    sin_ext = re.sub(r'\.pdf$', '', relativo, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', sin_ext.lower()).strip('_')[:120]


def guardar_json(ruta, datos):
    temporal = ruta + '.tmp'
    with open(temporal, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(temporal, ruta)


def procesar_pdf(pdf, ancho, ancho_reintento, timeout, idioma):
    """Devuelve (paginas, omitidas, lineas, texto)."""
    with tempfile.TemporaryDirectory(prefix='ocr_lote_') as tmp:
        primera = os.path.join(tmp, 'p001.png')
        aviso = O.renderizar(pdf, 1, primera, ancho, timeout)
        m = re.search(r'\((\d+)\s+paginas\)', aviso)
        if not m:
            raise RuntimeError('no se pudo leer el numero de paginas: %r' % aviso)
        total = int(m.group(1))

        paginas = 0
        omitidas = []
        lineas_total = 0
        bloques = []
        for pagina in range(1, total + 1):
            png = os.path.join(tmp, 'p%03d.png' % pagina)
            js = os.path.join(tmp, 'p%03d.json' % pagina)
            datos = None
            for ancho_prueba in (ancho, ancho_reintento):
                try:
                    O.renderizar(pdf, pagina, png, ancho_prueba, timeout)
                    datos = O.ocr(png, js, idioma, timeout)
                    break
                except RuntimeError:
                    continue
            if datos is None:
                omitidas.append(pagina)
                continue
            lineas = sorted(datos.get('lineas', []),
                            key=lambda l: (l.get('y', 0), l.get('x', 0)))
            texto = '\n'.join((l.get('texto') or '').strip()
                              for l in lineas if (l.get('texto') or '').strip())
            if texto:
                bloques.append('===== PAGINA %d =====\n%s' % (pagina, texto))
            paginas += 1
            lineas_total += len(lineas)
            print('    pagina %d/%d: %d lineas%s'
                  % (pagina, total, len(lineas),
                     ' (reintento %d px)' % ancho_prueba
                     if ancho_prueba != ancho else ''), flush=True)
    return paginas, omitidas, lineas_total, '\n\n'.join(bloques)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lote', choices=['laser', 'tto', 'todos'], default='todos')
    ap.add_argument('--limite', type=int, default=0)
    ap.add_argument('--ancho', type=int, default=2200)
    ap.add_argument('--ancho-reintento', type=int, default=1400)
    ap.add_argument('--timeout-pagina', type=int, default=60)
    ap.add_argument('--idioma', default='es-MX')
    ap.add_argument('--reforzar', action='store_true')
    args = ap.parse_args()

    lotes = ['laser', 'tto'] if args.lote == 'todos' else [args.lote]
    procesados = 0
    for nombre in lotes:
        cfg = LOTES[nombre]
        if not os.path.exists(cfg['resumen']):
            print('AVISO: falta %s' % cfg['resumen'])
            continue
        with open(cfg['resumen'], 'r', encoding='utf-8') as f:
            datos = json.load(f)
        base = datos.get(cfg['clave_base'], '')
        pendientes = []
        for r in datos.get('resultados', []):
            if r.get('estado') not in OBJETIVO:
                continue
            # Reanudacion: cualquier resultado previo se conserva. Para
            # reintentar un PDF concreto o todo el lote se usa --reforzar.
            if not args.reforzar and r.get('estado_ocr'):
                continue
            completo = os.path.join(base, r['archivo'])
            if not os.path.exists(completo):
                continue
            pendientes.append((r, completo))
        if args.limite:
            pendientes = pendientes[:args.limite]
        print('\n%s: %d PDFs escaneados por OCR' % (nombre, len(pendientes)),
              flush=True)

        for i, (r, completo) in enumerate(pendientes, 1):
            slug = slug_de(r['archivo'])
            print('  [%d/%d] %s' % (i, len(pendientes), r['archivo'][:90]),
                  flush=True)
            try:
                paginas, omitidas, lineas, texto = procesar_pdf(
                    completo, args.ancho, args.ancho_reintento,
                    args.timeout_pagina, args.idioma)
            except Exception as exc:  # noqa: BLE001 - el lote no debe abortar
                r['estado_ocr'] = 'error'
                r['ocr_error'] = str(exc)[:300]
                # El mensaje de PowerShell puede traer caracteres que la
                # consola cp1252 no representa; se sanea solo al imprimir.
                aviso = str(exc).encode('ascii', 'replace').decode('ascii')
                print('    ERROR: %s' % aviso[:200], flush=True)
                guardar_json(cfg['resumen'], datos)
                continue

            r['ocr_paginas'] = paginas
            r['ocr_lineas'] = lineas
            r['ocr_chars'] = len(texto)
            r['ocr_omitidas'] = omitidas
            r['estado_ocr'] = ('ok' if len(texto) >= 200 else
                               'escaso' if texto else 'sin-resultado')
            if omitidas:
                r['estado_ocr'] = ('parcial' if len(texto) >= 200 else
                                   r['estado_ocr'])
            if texto:
                destino = os.path.join(
                    EXTRACCION, '%s_%s_ocr.txt' % (cfg['prefijo'], slug))
                with open(destino, 'w', encoding='utf-8') as f:
                    f.write('# OCR Windows.Data.Pdf + Windows.Media.Ocr - fuente: %s\n'
                            % r['archivo'])
                    f.write('# paginas=%d lineas=%d caracteres=%d omitidas=%s\n\n'
                            % (paginas, lineas, len(texto), omitidas))
                    f.write(texto)
                r['txt_ocr'] = os.path.relpath(destino, RAIZ).replace('\\', '/')
            guardar_json(cfg['resumen'], datos)
            procesados += 1
            print('    -> paginas=%d lineas=%d chars=%d omitidas=%s (%s)'
                  % (paginas, lineas, len(texto), omitidas, r['estado_ocr']),
                  flush=True)

    print('\nOK: %d PDFs procesados por OCR' % procesados, flush=True)
    for nombre in lotes:
        cfg = LOTES[nombre]
        if not os.path.exists(cfg['resumen']):
            continue
        datos = json.load(open(cfg['resumen'], encoding='utf-8'))
        con = [r for r in datos.get('resultados', []) if r.get('ocr_chars')]
        print('  %s: %d con texto OCR, %d caracteres'
              % (nombre, len(con), sum(r.get('ocr_chars', 0) for r in con)))


if __name__ == '__main__':
    main()
