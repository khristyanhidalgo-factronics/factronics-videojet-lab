# -*- coding: utf-8 -*-
"""Publica las notas de version con huella SHA-256 (no modificables) y version.json.

Genera/actualiza:
  - versions/INDICE.json  (indice maestro con hashes por archivo)
  - docs/notas.html       (pagina publica de notas en Pages)
  - version.json          (raiz: version legible por maquina)
Uso: python tools/publicar_notas.py
"""
import hashlib
import json
import os
import re
import sys
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONES = os.path.join(RAIZ, 'versions')
DOCS = os.path.join(RAIZ, 'docs')
REPO_URL = 'https://github.com/khristyanhidalgo-factronics/factronics-videojet-lab'
APP_URL = 'https://khristyanhidalgo-factronics.github.io/factronics-videojet-lab/app/'
NOTAS_URL = 'https://khristyanhidalgo-factronics.github.io/factronics-videojet-lab/notas.html'
VERSION_ACTUAL = 'v0.2.0-alpha'
CONSTRUCCION = 17


def sha256(ruta):
    # Huella estable entre Windows (CRLF) y Linux (LF): se normaliza a LF.
    with open(ruta, 'rb') as f:
        datos = f.read().replace(b'\r\n', b'\n')
    return hashlib.sha256(datos).hexdigest()


def recopilar():
    versiones = []
    for nombre in sorted(os.listdir(VERSIONES)):
        carpeta = os.path.join(VERSIONES, nombre)
        if not (os.path.isdir(carpeta) and re.fullmatch(r'v\d+\.\d+\.\d+', nombre)):
            continue
        notas = {}
        hashes = {}
        etiquetas = {'PLAN': 'plan', 'BITACORA': 'bitacora',
                     'HECHO': 'hecho', 'PENDIENTE': 'pendiente'}
        for archivo in sorted(os.listdir(carpeta)):
            m = re.match(r'(PLAN|BITACORA|HECHO|PENDIENTE)-%s\.md$' % re.escape(nombre), archivo)
            if not m:
                continue
            clave = etiquetas[m.group(1)]
            ruta = os.path.join(carpeta, archivo)
            notas[clave] = 'versions/%s/%s' % (nombre, archivo)
            hashes[clave] = sha256(ruta)
        roadmap = os.path.join(VERSIONES, 'ROADMAP.md')
        hashes['roadmap_global'] = sha256(roadmap) if os.path.exists(roadmap) else None
        notas['roadmap_global'] = 'versions/ROADMAP.md'
        versiones.append({'id': nombre, 'notas': notas, 'sha256': hashes})
    return versiones


def escribir_indice(versiones):
    ruta = os.path.join(VERSIONES, 'INDICE.json')
    datos = {
        'producto': 'Factronics Videojet Lab',
        'actualizado': date.today().isoformat(),
        'version_actual': VERSION_ACTUAL,
        'estado_actual': 'alfa',
        'nota': ('Indice maestro de versiones. Incluye SHA-256 de cada nota: si un archivo '
                 'cambia, el hash deja de coincidir (las notas publicadas no se editan). '
                 'La huella se calcula sobre el contenido normalizado a LF para que sea '
                 'identica en Windows y Linux.'),
        'tipos_de_nota': {
            'PLAN': 'versions/vX.Y.Z/PLAN-vX.Y.Z.md',
            'BITACORA': 'versions/vX.Y.Z/BITACORA-vX.Y.Z.md',
            'HECHO': 'versions/vX.Y.Z/HECHO-vX.Y.Z.md',
            'PENDIENTE': 'versions/vX.Y.Z/PENDIENTE-vX.Y.Z.md',
            'ROADMAP': 'versions/ROADMAP.md (+ copia congelada por version)',
        },
        'versiones': versiones,
        'reglas': [
            'Las notas publicadas (congeladas) no se editan nunca',
            'El PENDIENTE de cada version alimenta el PLAN de la siguiente',
            'Los SHA-256 publicados permiten detectar cualquier cambio posterior',
            'La huella se calcula sobre el contenido normalizado a LF (estable Windows/Linux)',
        ],
    }
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return datos


def escribir_version_json(versiones):
    actual = next((v for v in versiones if v['id'] == 'v0.2.0'), versiones[-1])
    datos = {
        'producto': 'Factronics Videojet Lab',
        'version': VERSION_ACTUAL,
        'canal': 'alpha',
        'construccion': CONSTRUCCION,
        'fecha': date.today().isoformat(),
        'app_web': {
            'url': APP_URL,
            'ruta': 'docs/app/index.html',
            'offline': True,
            'idiomas': ['es', 'en', 'pt', 'it', 'zh'],
            'banco_preguntas_tto': 372,
        },
        'apk': None,
        'notas': {
            'indice': 'versions/INDICE.json',
            'pagina': NOTAS_URL,
            'hashes': actual.get('sha256', {}),
        },
        'repo': REPO_URL,
    }
    with open(os.path.join(RAIZ, 'version.json'), 'w', encoding='utf-8', newline='') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    # Copia publicada en Pages (la raiz del sitio es docs/).
    with open(os.path.join(DOCS, 'version.json'), 'w', encoding='utf-8', newline='') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return datos


def escribir_notas_html(versiones):
    filas = []
    for v in versiones:
        enlaces = []
        for clave, etiqueta in (('plan', 'PLAN'), ('bitacora', 'BITÁCORA'),
                                ('hecho', 'HECHO'), ('pendiente', 'PENDIENTE')):
            ruta = v['notas'].get(clave)
            if ruta:
                enlaces.append('<a href="%s/blob/main/%s" target="_blank" rel="noopener">%s</a>'
                               % (REPO_URL, ruta, etiqueta))
        hashes = ''.join('<li><code>%s</code>: <span class="h">%s</span></li>'
                         % (k, (h or '—'))
                         for k, h in v['sha256'].items())
        filas.append(
            '<article class="ver"><h2>%s</h2><p>%s</p>'
            '<details><summary>Huellas SHA-256</summary><ul>%s</ul></details></article>'
            % (v['id'], ' · '.join(enlaces) or '(sin notas)', hashes))
    html = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notas de versión — Factronics Videojet Lab</title>
<style>
body{margin:0;background:#0b1220;color:#e2e8f0;font:16px/1.6 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:26px} a{color:#60a5fa}
.ver{background:#111a2c;border:1px solid #1e293b;border-radius:14px;padding:16px 18px;margin:14px 0}
h2{margin:4px 0 8px;font-size:20px}
code{color:#fbbf24} .h{color:#4ade80;word-break:break-all;font-size:12px}
.rules{background:#111a2c;border:1px solid #1e293b;border-radius:14px;padding:12px 18px}
</style></head><body><main>
<h1>📓 Notas de versión</h1>
<p>Historial permanente del proyecto. Las notas publicadas no se editan: cada archivo lleva su
huella <b>SHA-256</b>, de modo que cualquier cambio posterior queda a la vista.</p>
<p><a href="index.html">← Volver a la landing</a> · <a href="app/">Abrir la app</a> ·
<a href="version.json">version.json</a></p>
<div class="rules"><b>Reglas:</b> las notas congeladas no se editan · el PENDIENTE alimenta el PLAN siguiente ·
los hashes permiten auditar cambios.</div>
%s
<p style="margin-top:24px;font-size:13px;color:#94a3b8">Actualizado: %s · Producto de Factronics Venezuela para uso interno del equipo.</p>
</main></body></html>
""" % ('\n'.join(filas), date.today().isoformat())
    with open(os.path.join(DOCS, 'notas.html'), 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    versiones = recopilar()
    escribir_indice(versiones)
    escribir_version_json(versiones)
    escribir_notas_html(versiones)
    print('OK | versiones=%d | INDICE.json + notas.html + version.json actualizados'
          % len(versiones))
    for v in versiones:
        print('  ', v['id'], 'notas=', len(v['notas']), 'hash_plan=',
              (v['sha256'].get('plan') or '')[:16])


if __name__ == '__main__':
    main()
