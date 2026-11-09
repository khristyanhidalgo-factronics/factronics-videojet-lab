# -*- coding: utf-8 -*-
"""Pruebas del banco de preguntas TTO incluido en la app.

Valida docs/app/banco_tto.js (estructura compacta):
  - 372 preguntas y los 3 idiomas en todas.
  - Tipos conocidos y campos requeridos por tipo.
  - Respuestas de seleccion existen entre las opciones; numeros con tolerancia.
Uso: python tools/test_banco_tto.py   (exit 0 = OK)
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO = os.path.join(RAIZ, 'docs', 'app', 'banco_tto.js')
TIPOS = {'single', 'multi', 'fill', 'calc', 'describe', 'errorfix', 'errmap'}
fallos = []


def cargar():
    texto = open(ARCHIVO, encoding='utf-8').read()
    m = re.search(r'window\.BANCO_TTO\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.BANCO_TTO en el archivo')
    return json.loads(m.group(1))


def main():
    banco = cargar()
    preguntas = banco.get('preguntas', [])
    if len(preguntas) != banco.get('total'):
        fallos.append('total (%s) != preguntas (%d)' % (banco.get('total'), len(preguntas)))
    if len(preguntas) < 372:
        fallos.append('se esperaban 372 preguntas, hay %d' % len(preguntas))

    for q in preguntas:
        qid = q.get('id', '?')
        tipo = q.get('t')
        if tipo not in TIPOS:
            fallos.append('%s: tipo desconocido %r' % (qid, tipo))
        for idioma in ('es', 'en', 'pt'):
            d = (q.get('i') or {}).get(idioma)
            if not d or not d.get('q'):
                fallos.append('%s: falta idioma %s' % (qid, idioma))
                continue
            if tipo in ('single', 'multi', 'errmap'):
                opciones = d.get('o') or []
                ids = {o[0] for o in opciones}
                respuestas = d.get('a') or []
                if len(opciones) < 2:
                    fallos.append('%s/%s: menos de 2 opciones' % (qid, idioma))
                if not respuestas or not set(respuestas) <= ids:
                    fallos.append('%s/%s: respuesta fuera de opciones' % (qid, idioma))
                if tipo != 'multi' and len(respuestas) != 1:
                    fallos.append('%s/%s: respuesta unica esperada' % (qid, idioma))
            if tipo in ('fill', 'calc'):
                campos = d.get('f') or []
                if not campos:
                    fallos.append('%s/%s: sin campos' % (qid, idioma))
                for campo in campos:
                    respuestas = campo[2] if len(campo) > 2 else []
                    if not respuestas:
                        fallos.append('%s/%s: campo sin respuestas' % (qid, idioma))
                    elif not (all(isinstance(x, (int, float)) for x in respuestas)
                              or all(isinstance(x, str) and x.strip() for x in respuestas)):
                        fallos.append('%s/%s: respuestas de tipo mixto/invalido' % (qid, idioma))
            if tipo in ('describe', 'errorfix') and not d.get('mod'):
                fallos.append('%s/%s: falta respuesta modelo' % (qid, idioma))

    if fallos:
        print('FALLOS (%d):' % len(fallos))
        for f in fallos[:40]:
            print('  -', f)
        sys.exit(1)
    tipos = {}
    for q in preguntas:
        tipos[q['t']] = tipos.get(q['t'], 0) + 1
    print('Banco TTO OK: %d preguntas, 3 idiomas, tipos=%s'
          % (len(preguntas), tipos))


if __name__ == '__main__':
    main()
