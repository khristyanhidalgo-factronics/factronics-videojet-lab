# -*- coding: utf-8 -*-
"""Pruebas de la calculadora CIJ y de la referencia VJ1210/V401.

Valida docs/app/datos.js (paquete que consume la PWA):
  - 802 curvas de solvente con estado y curva 10-40 C.
  - La referencia de cada curva coincide con su punto de la tabla.
  - VJ1210 / V401 @ 30 C = 11,2 ml/h (referencia verificada del documento).
  - La app formatea la referencia y no vuelve a imprimir objetos ([object Object]).

Uso: python tools/test_app_calculo.py   (exit 0 = OK)
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_JS = os.path.join(RAIZ, 'docs', 'app', 'datos.js')
INDEX = os.path.join(RAIZ, 'docs', 'app', 'index.html')
ESTADOS = {'verificado', 'borrador', 'borrador-decodificado',
           'por-definir', 'sin-datos-en-documento'}
fallos = []


def cargar_datos():
    texto = open(DATOS_JS, encoding='utf-8').read()
    m = re.search(r'window\.DATOS\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.DATOS en datos.js')
    return json.loads(m.group(1))


def main():
    datos = cargar_datos()
    solventes = datos.get('solventes', [])
    if len(solventes) != 802:
        fallos.append('se esperaban 802 curvas, hay %d' % len(solventes))

    referencias = 0
    for s in solventes:
        etiqueta = '%s %s / %s' % (s.get('m'), s.get('v') or '', s.get('t'))
        estado = s.get('e')
        if estado not in ESTADOS:
            fallos.append('%s: estado desconocido %r' % (etiqueta, estado))
        curva = s.get('c') or []
        if estado == 'sin-datos-en-documento':
            if curva:
                fallos.append('%s: sin datos pero con curva' % etiqueta)
            continue
        if not curva:
            fallos.append('%s: curva vacia' % etiqueta)
            continue
        temps = [p[0] for p in curva]
        if temps != sorted(temps) or len(set(temps)) != len(temps):
            fallos.append('%s: temperaturas desordenadas o repetidas' % etiqueta)
        if temps[0] != 10 or temps[-1] != 40:
            fallos.append('%s: rango %s-%s (se esperaba 10-40)' % (etiqueta, temps[0], temps[-1]))
        if any(not isinstance(p[1], (int, float)) or p[1] <= 0 for p in curva):
            fallos.append('%s: uso no numerico o <= 0' % etiqueta)

        r = s.get('r')
        if r is None:
            fallos.append('%s: falta referencia @30 C' % etiqueta)
            continue
        if not isinstance(r, dict) or 'temp_c' not in r or 'uso_ml_hr' not in r:
            fallos.append('%s: referencia con formato inesperado %r' % (etiqueta, r))
            continue
        referencias += 1
        punto = [p[1] for p in curva if p[0] == r['temp_c']]
        if not punto or abs(punto[0] - r['uso_ml_hr']) > 1e-9:
            fallos.append('%s: referencia %s no coincide con la curva %s'
                          % (etiqueta, r['uso_ml_hr'], punto))

    vj = [s for s in solventes
          if s.get('m') == 'VJ1210' and not s.get('v') and s.get('t') == 'V401']
    if len(vj) != 1:
        fallos.append('VJ1210/V401: se esperaba 1 curva, hay %d' % len(vj))
    else:
        s = vj[0]
        if s.get('e') != 'verificado':
            fallos.append('VJ1210/V401: estado %r (se esperaba verificado)' % s.get('e'))
        if not isinstance(s.get('r'), dict) or s['r'].get('uso_ml_hr') != 11.2:
            fallos.append('VJ1210/V401: referencia distinta de 11,2 ml/h')
        punto = [p[1] for p in s.get('c', []) if p[0] == 30]
        if punto != [11.2]:
            fallos.append('VJ1210/V401 @30 C: %r (se esperaba 11,2)' % punto)

    # Velocidades de linea CIJ (calculadores v9.7) en el paquete de la app.
    vel = datos.get('velocidades') or {}
    entradas_vel = vel.get('entradas') or []
    if len(entradas_vel) != 266:
        fallos.append('velocidades: se esperaban 266 entradas, hay %d'
                      % len(entradas_vel))
    if len(vel.get('modelos') or []) != 12:
        fallos.append('velocidades: se esperaban 12 modelos')
    if (vel.get('meta') or {}).get('estado') != 'borrador-decodificado':
        fallos.append('velocidades: estado general distinto de borrador-decodificado')
    if (vel.get('meta') or {}).get('conflictos') != 0:
        fallos.append('velocidades: hay conflictos de valores')
    for e in entradas_vel:
        etiqueta = '%s/%s/%s' % (e.get('m'), e.get('b'), e.get('f'))
        if not e.get('m') or e.get('b') not in (40, 50, 60) or not e.get('f'):
            fallos.append('%s: modelo/boquilla/fuente incompletos' % etiqueta)
        if e.get('v') is None:
            fallos.append('%s: sin velocidad' % etiqueta)
        if e.get('c') is None and e.get('col') is None:
            fallos.append('%s: sin caracteres/s ni columnas/s' % etiqueta)
        if e.get('e') != 'borrador-decodificado':
            fallos.append('%s: estado %r' % (etiqueta, e.get('e')))
        if e.get('t') not in ('simple', 'experto'):
            fallos.append('%s: tipo %r' % (etiqueta, e.get('t')))
        if not e.get('a'):
            fallos.append('%s: sin archivo fuente' % etiqueta)
    duplicados = [e for e in entradas_vel if ';' in (e.get('a') or '')]
    if len(duplicados) != 4:
        fallos.append('velocidades: se esperaban 4 duplicados, hay %d'
                      % len(duplicados))
    expertos = [e for e in entradas_vel if e.get('t') == 'experto']
    if len(expertos) != 1:
        fallos.append('velocidades: se esperaba 1 calculador experto')
    else:
        e = expertos[0]
        if (e.get('m'), e.get('b'), e.get('f')) != ('1620-50 UHS', 50, '4x5 single'):
            fallos.append('velocidades: experto inesperado %r' % e)
        if (e.get('v'), e.get('c'), e.get('col')) != (508, 3333, 16667):
            fallos.append('velocidades: valores del experto distintos')
    uhs = [e for e in entradas_vel if e.get('m') == '1880 UHS']
    hr = [e for e in entradas_vel if e.get('m') == '1880 HR']
    if len(uhs) != 19 or any(e.get('b') != 50 for e in uhs):
        fallos.append('velocidades: 1880 UHS no son 19 entradas de 50 um')
    if len(hr) != 19 or any(e.get('b') != 40 for e in hr):
        fallos.append('velocidades: 1880 HR no son 19 entradas de 40 um')

    html = open(INDEX, encoding='utf-8').read()
    for aguja, mensaje in [
        ('entrada.r||', 'la calculadora aun imprime la referencia como objeto'),
        ('String(s.r)', 'el examen de nivel 4 aun usa el objeto de referencia'),
    ]:
        if aguja in html:
            fallos.append(mensaje)
    for funcion in ('function fmtNum(', 'function refTexto(', 'function refUso(',
                    'function renderVel(', 'function calcularVel('):
        if funcion not in html:
            fallos.append('falta %s en index.html' % funcion)
    for aguja in ('id="vel_m"', 'id="vel_b"', 'id="vel_f"', 'vel_aviso_boquilla'):
        if aguja not in html:
            fallos.append('falta %s en index.html' % aguja)
    if html.count('vel_t:') != 5:
        fallos.append('vel_t no esta traducido en los 5 idiomas')

    if fallos:
        print('FALLOS (%d):' % len(fallos))
        for f in fallos[:40]:
            print('  -', f)
        sys.exit(1)
    print('Calculadora OK: %d curvas, %d referencias @30 C; VJ1210/V401 = 11,2 ml/h; '
          '%d velocidades CIJ (%d modelos)'
          % (len(solventes), referencias, len(entradas_vel),
             len(vel.get('modelos') or [])))


if __name__ == '__main__':
    main()
