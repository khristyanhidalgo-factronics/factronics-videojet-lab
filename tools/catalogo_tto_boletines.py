# -*- coding: utf-8 -*-
"""Indice estructurado de los boletines tecnicos TTO, con puntuacion de legibilidad.

La extraccion puede devolver fuentes subset sin ToUnicode (texto no fiable). Se marca:
  legible      (>=70% de caracteres latinos normales)
  dudoso       (40-70%)
  no-legible   (<40% -> solo se registra el archivo y la evidencia)
El titulo solo se asigna si el estado es legible.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'tto_boletines.json')
PERMITIDOS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  'ÁÉÍÓÚÜÑáéíóúüñ0123456789 .,:;%()/-_+°ºª&')


def legibilidad(texto):
    if not texto:
        return 0.0
    buenos = sum(1 for c in texto if c in PERMITIDOS)
    return buenos / len(texto)


def normalizar_espaciado(linea):
    tokens = linea.split()
    if len(tokens) >= 10 and sum(1 for t in tokens if len(t) == 1) / len(tokens) > 0.6:
        return linea.replace(' ', '')
    return linea


def parece_texto_real(linea):
    letras = [c for c in linea if c.isalpha()]
    if len(letras) < 8:
        return False
    vocales = sum(1 for c in letras if c.lower() in 'aeiouáéíóúü')
    return vocales / len(letras) >= 0.25


def titulo_de(texto):
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    candidatas = []
    for l in lineas[:14]:
        if len(l) <= 12:
            continue
        l = normalizar_espaciado(l)
        if legibilidad(l) >= 0.80 and parece_texto_real(l):
            candidatas.append(l)
    if not candidatas:
        return None
    return max(candidatas[:6], key=len)


def main():
    boletines = []
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not (nombre.startswith('tto_boletines_tecnicos_')
                and nombre.endswith('_visual.txt')):
            continue
        contenido = open(os.path.join(EXTRACCION, nombre), encoding='utf-8',
                         errors='replace').read()
        cuerpo = '\n'.join(l for l in contenido.splitlines()
                           if not l.startswith('#'))
        score = round(legibilidad(cuerpo.strip()), 3)
        estado = ('legible' if score >= 0.70 else
                  'dudoso' if score >= 0.40 else 'no-legible')
        boletines.append({
            'archivo_txt': nombre,
            'titulo': titulo_de(cuerpo) if estado == 'legible' else None,
            'caracteres': len(cuerpo.strip()),
            'legibilidad': score,
            'estado_texto': estado,
        })
    cuentas = {}
    for b in boletines:
        cuentas[b['estado_texto']] = cuentas.get(b['estado_texto'], 0) + 1
    datos = {
        'producto': 'Indice de boletines tecnicos TTO (curso 6x30)',
        'schema': 2,
        'total': len(boletines),
        'resumen_estado_texto': cuentas,
        'nota': ('La extraccion visual resuelve ToUnicode cuando el PDF lo trae; los '
                 'boletines con fuentes subset sin ToUnicode quedan marcados como '
                 'no-legibles (se conserva la evidencia, no se inventan titulos).'),
        'boletines': boletines,
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | total=%d %s' % (os.path.relpath(DESTINO, RAIZ), len(boletines),
                                   cuentas))
    for b in boletines:
        if b['estado_texto'] == 'legible' and b['titulo']:
            print('  -', b['titulo'][:90])
            break


if __name__ == '__main__':
    main()
