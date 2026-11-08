# -*- coding: utf-8 -*-
"""Importa el banco de preguntas TTO (Factronics TTO Lab, cuenta personal) a la app.

Fuente: referencia/tto_bank.json (descargado del repo emanuelindustri-source/factronics-tto-lab,
propiedad del mismo dueño). Se compacta y conserva es/en/pt, tipos, campos y explicaciones.
Salida: docs/app/banco_tto.js  ->  window.BANCO_TTO = {...}

Uso: python tools/importar_banco_tto.py
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, 'referencia', 'tto_bank.json')
DESTINO = os.path.join(RAIZ, 'docs', 'app', 'banco_tto.js')


def compactar_pregunta(q):
    salida = {
        'id': q.get('id'),
        't': q.get('type'),
        'd': q.get('difficulty'),
        'm': q.get('models') or [],
        'i': {},
    }
    for idioma in ('es', 'en', 'pt'):
        datos = (q.get('i18n') or {}).get(idioma)
        if not datos:
            continue
        item = {'q': datos.get('q', '')}
        if datos.get('options'):
            item['o'] = [[o.get('id'), o.get('text')] for o in datos['options']]
        if datos.get('answer'):
            item['a'] = datos['answer']
        if datos.get('fields'):
            item['f'] = [[f.get('label'), f.get('unit'),
                          f.get('answers') or [], f.get('tolerance')]
                         for f in datos['fields']]
        if datos.get('explanation'):
            item['x'] = datos['explanation']
        if datos.get('model'):
            item['mod'] = datos['model']
        salida['i'][idioma] = item
    return salida


def main():
    banco = json.load(open(ORIGEN, 'r', encoding='utf-8'))
    preguntas = [compactar_pregunta(q) for q in banco.get('questions', [])]
    datos = {
        'version': banco.get('version'),
        'generated': banco.get('generated'),
        'origen': 'Factronics TTO Lab (emanuelindustri-source) — contenido propio del autor',
        'total': len(preguntas),
        'preguntas': preguntas,
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        f.write('// Generado por tools/importar_banco_tto.py - NO editar a mano.\n')
        f.write('window.BANCO_TTO = ')
        json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
    tipos = {}
    for p in preguntas:
        tipos[p['t']] = tipos.get(p['t'], 0) + 1
    print('OK %s (%.1f KB) | preguntas=%d tipos=%s'
          % (os.path.relpath(DESTINO, RAIZ), os.path.getsize(DESTINO) / 1024.0,
             len(preguntas), tipos))


if __name__ == '__main__':
    main()
