# -*- coding: utf-8 -*-
"""Validador del repositorio: JSON, notas con SHA-256, app y enlaces locales.

Uso: python tools/validar_repo.py   (exit 0 = OK; exit 1 = fallos)
Pensado para ejecutarse en local y en CI (.github/workflows/validar.yml).
"""
import hashlib
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fallos = []
avisos = []


def ruta(*partes):
    return os.path.join(RAIZ, *partes)


def sha256(archivo):
    # Huella estable entre Windows (CRLF) y Linux (LF): se normaliza a LF.
    with open(archivo, 'rb') as f:
        datos = f.read().replace(b'\r\n', b'\n')
    return hashlib.sha256(datos).hexdigest()


def validar_json():
    carpeta = ruta('datos')
    total = 0
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith('.json'):
            continue
        total += 1
        try:
            json.load(open(os.path.join(carpeta, nombre), encoding='utf-8'))
        except (ValueError, OSError) as e:
            fallos.append('JSON invalido: datos/%s -> %s' % (nombre, e))
    print('JSON de datos: %d archivos' % total)


def validar_notas():
    indice = ruta('versions', 'INDICE.json')
    if not os.path.exists(indice):
        fallos.append('Falta versions/INDICE.json (ejecuta tools/publicar_notas.py)')
        return
    datos = json.load(open(indice, encoding='utf-8'))
    for v in datos.get('versiones', []):
        for clave, rel in v.get('notas', {}).items():
            if not rel:
                continue
            archivo = ruta(*rel.split('/'))
            if not os.path.exists(archivo):
                fallos.append('Nota inexistente: %s' % rel)
                continue
            esperado = v.get('sha256', {}).get(clave)
            if esperado and sha256(archivo) != esperado:
                fallos.append('SHA-256 no coincide (nota modificada): %s' % rel)
    version = json.load(open(ruta('version.json'), encoding='utf-8'))
    if version.get('version') != datos.get('version_actual'):
        avisos.append('version.json (%s) != INDICE.version_actual (%s)'
                      % (version.get('version'), datos.get('version_actual')))
    docs_version = ruta('docs', 'version.json')
    if not os.path.exists(docs_version):
        fallos.append('Falta docs/version.json (version.json publicado en Pages)')
    else:
        publicado = json.load(open(docs_version, encoding='utf-8'))
        if publicado.get('version') != version.get('version'):
            fallos.append('docs/version.json desactualizado (%s != %s)'
                          % (publicado.get('version'), version.get('version')))
        if publicado.get('construccion') != version.get('construccion'):
            fallos.append('docs/version.json build distinto (%s != %s)'
                          % (publicado.get('construccion'), version.get('construccion')))
    print('Notas: %d versiones verificadas' % len(datos.get('versiones', [])))


def validar_app():
    app = ruta('docs', 'app')
    requeridos = ['index.html', 'datos.js', 'banco_tto.js',
                  'manifest.webmanifest', 'sw.js']
    for nombre in requeridos:
        if not os.path.exists(os.path.join(app, nombre)):
            fallos.append('Falta docs/app/%s' % nombre)
    datos = open(os.path.join(app, 'datos.js'), encoding='utf-8').read(200)
    if 'window.DATOS' not in datos:
        fallos.append('docs/app/datos.js no define window.DATOS')
    banco = open(os.path.join(app, 'banco_tto.js'), encoding='utf-8').read(200)
    if 'window.BANCO_TTO' not in banco:
        fallos.append('docs/app/banco_tto.js no define window.BANCO_TTO')
    print('App: %d archivos requeridos' % len(requeridos))


def validar_enlaces():
    pagina = ruta('docs', 'index.html')
    html = open(pagina, encoding='utf-8').read()
    refs = re.findall(r'(?:href|src)="([^"]+)"', html)
    locales = 0
    for ref in refs:
        if ref.startswith(('http', '#', 'mailto:', 'javascript:')) or ref.startswith('data:'):
            continue
        limpio = ref.split('#')[0].split('?')[0]
        if not limpio:
            continue
        destino = os.path.join(os.path.dirname(pagina), limpio)
        if os.path.isdir(destino):
            destino = os.path.join(destino, 'index.html')
        if not os.path.exists(destino):
            fallos.append('Enlace local roto en docs/index.html: %s' % ref)
        locales += 1
    print('Enlaces locales de la landing: %d revisados' % locales)


def main():
    validar_json()
    validar_notas()
    validar_app()
    validar_enlaces()
    for a in avisos:
        print('AVISO:', a)
    if fallos:
        print('\nFALLOS (%d):' % len(fallos))
        for f in fallos:
            print('  -', f)
        sys.exit(1)
    print('\nTODO OK')


if __name__ == '__main__':
    main()
