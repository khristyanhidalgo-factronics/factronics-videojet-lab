# -*- coding: utf-8 -*-
"""Verifica que todo el contenido visible de la app tenga traduccion.

Comprueba las cadenas de docs/app/datos.js contra la memoria
datos/traducciones_contenido.json para es/en/pt/it/zh. Falla si falta alguna
cadena con letras o si quedo un centinela ZXQnQZX sin restaurar.

Uso:
  python tools/test_traducciones.py
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_JS = os.path.join(RAIZ, 'docs', 'app', 'datos.js')
MEMORIA = os.path.join(RAIZ, 'datos', 'traducciones_contenido.json')
IDIOMAS = ('es', 'en', 'pt', 'it', 'zh')


def normalizar(texto):
    return re.sub(r'\s+', ' ', str(texto or '')).strip()


def cargar_datos():
    texto = open(DATOS_JS, encoding='utf-8').read()
    m = re.search(r'window\.DATOS\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.DATOS en datos.js')
    return json.loads(m.group(1))


def visibles(datos):
    cadenas = set()

    def add(texto):
        texto = normalizar(texto)
        if texto:
            cadenas.add(texto)

    for p in datos.get('partes', []):
        add(p.get('d'))
    for e in datos.get('errores', []):
        add(e.get('x'))
        add(e.get('cl'))
    for t in (datos.get('mant') or {}).get('tareas', []):
        add(t.get('x'))
        add(t.get('iv'))
    ribbons = datos.get('ribbons') or {}
    for g in ribbons.get('grados', []):
        for clave in ('g', 'tipo', 'col', 'film', 'desc'):
            add(g.get(clave))
    for item in ribbons.get('items', []):
        if isinstance(item, list) and len(item) > 1:
            add(item[1])
    for t in (datos.get('tintas') or {}).values():
        for base in t.get('b') or []:
            add(base)
        add(t.get('col'))
        for ficha in t.get('fichas') or []:
            for comp in ficha.get('comp') or []:
                add(comp.get('n'))
            for valor in (ficha.get('props') or {}).values():
                if isinstance(valor, str):
                    add(valor)
    for s in datos.get('solventes', []):
        add(s.get('b'))
    add((datos.get('meta') or {}).get('aviso'))
    return cadenas


def main():
    datos = cargar_datos()
    memoria = json.load(open(MEMORIA, encoding='utf-8')).get('entradas', {})
    cadenas = visibles(datos)
    errores = 0
    for idioma in IDIOMAS:
        faltan = [x for x in sorted(cadenas)
                  if re.search(r'[A-Za-zÀ-ÿ\u4e00-\u9fff]', x)
                  and not memoria.get(x, {}).get(idioma)]
        if faltan:
            errores += len(faltan)
            print('%s: faltan %d traducciones' % (idioma, len(faltan)))
            for x in faltan[:8]:
                print('  %r' % x[:120])
        else:
            print('%s: cobertura completa (%d cadenas)' % (idioma, len(cadenas)))

    con_centinela = []
    for texto, reg in memoria.items():
        for idioma in IDIOMAS:
            valor = reg.get(idioma) or ''
            if 'ZXQ' in valor.upper():
                con_centinela.append((texto, idioma, valor))
    if con_centinela:
        errores += len(con_centinela)
        print('Centinelas sin restaurar: %d' % len(con_centinela))
        for texto, idioma, valor in con_centinela[:5]:
            print('  %s %r -> %r' % (idioma, texto[:60], valor[:80]))

    if errores:
        print('FALLO: %d incidencias de traduccion' % errores)
        return 1
    print('OK: contenido visible traducido en %s' % ', '.join(IDIOMAS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
