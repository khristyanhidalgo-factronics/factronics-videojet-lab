# -*- coding: utf-8 -*-
"""Agrega traducciones it/zh al banco TTO de la app.

El banco original conserva es/en/pt. Este script toma el espanol como fuente,
traduce q, opciones, explicaciones, respuestas modelo y etiquetas de campos, y
agrega las claves i.it / i.zh. Las respuestas (ids de opcion, numeros, texto
aceptado) no se tocan.

La memoria es incremental: datos/traducciones_banco_tto.json.

Uso:
  python tools/traducir_banco_tto.py
  python tools/traducir_banco_tto.py --idiomas it
"""
import argparse
import copy
import json
import os
import re
import sys
import time

from traducir_contenido import normalizar, traducir_lote

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, 'docs', 'app', 'banco_tto.js')
MEMORIA = os.path.join(RAIZ, 'datos', 'traducciones_banco_tto.json')
IDIOMAS = ('it', 'zh')

# Etiquetas cortas que Google confunde con otros conceptos. Se revisan a mano.
OVERRIDES = {
    'Rollos': {'it': 'Rotoli', 'zh': '卷'},
    'Rollos necesarios': {'it': 'Rotoli necessari', 'zh': '所需卷数'},
    'Rollo máximo': {'it': 'Rotolo massimo', 'zh': '最大卷长'},
    'Puerto': {'it': 'Porta', 'zh': '端口'},
    'Mantello': {'it': 'Manicotto', 'zh': '护套'},
    'Consumo': {'it': 'Consumo', 'zh': '消耗量'},
    'Consumo total': {'it': 'Consumo totale', 'zh': '总消耗量'},
    'Costo por 1000': {'it': 'Costo per 1000', 'zh': '每 1000 次成本'},
    'Horas': {'it': 'Ore', 'zh': '小时'},
    'Impresiones por minuto': {'it': 'Impressioni al minuto', 'zh': '每分钟打印次数'},
    'Kit': {'it': 'Kit', 'zh': '套件'},
    'Rodillo': {'it': 'Rullo', 'zh': '滚筒'},
    'Capa': {'it': 'Strato', 'zh': '层'},
    'Ahorro': {'it': 'Risparmio', 'zh': '节省'},
    'Acción': {'it': 'Azione', 'zh': '操作'},
    'Extensión': {'it': 'Estensione', 'zh': '扩展名'},
}


def cargar_banco():
    texto = open(BANCO, encoding='utf-8').read()
    m = re.search(r'window\.BANCO_TTO\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.BANCO_TTO en banco_tto.js')
    return json.loads(m.group(1))


def guardar_banco(banco):
    with open(BANCO, 'w', encoding='utf-8', newline='') as f:
        f.write('window.BANCO_TTO = ' + json.dumps(banco, ensure_ascii=False,
                                                   separators=(',', ':')) + ';\n')


def cargar_memoria():
    if not os.path.exists(MEMORIA):
        return {}
    return json.load(open(MEMORIA, encoding='utf-8')).get('entradas', {})


def guardar_memoria(entradas):
    datos = {
        'producto': 'Factronics Videojet Lab - banco TTO',
        'schema': 1,
        'actualizado': time.strftime('%Y-%m-%d'),
        'estado': 'borrador-de-traduccion',
        'fuente': 'es',
        'idiomas': list(IDIOMAS),
        'nota': ('Traduccion del banco TTO al italiano y chino. El es/en/pt '
                 'original se conserva. Revisar antes de usar como traduccion '
                 'oficial.'),
        'entradas': entradas,
    }
    with open(MEMORIA, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def recolectar(banco):
    cadenas = set()

    def add(texto):
        texto = normalizar(texto)
        if texto:
            cadenas.add(texto)

    for q in banco.get('preguntas', []):
        d = (q.get('i') or {}).get('es') or {}
        add(d.get('q'))
        for opcion in d.get('o') or []:
            if isinstance(opcion, list) and len(opcion) > 1:
                add(opcion[1])
        # Las explicaciones se traducen parrafo a parrafo (igual que mod):
        # asi los saltos de linea se conservan y la memoria incremental
        # encuentra cada parrafo.
        for parrafo in str(d.get('x') or '').split('\n'):
            add(parrafo)
        for parrafo in str(d.get('mod') or '').split('\n'):
            add(parrafo)
        for campo in d.get('f') or []:
            if isinstance(campo, list) and campo:
                add(campo[0])
                if len(campo) > 1:
                    add(campo[1])
    return sorted(cadenas)


def traducir(texto, idioma, memoria):
    clave = normalizar(texto)
    return memoria.get(clave, {}).get(idioma) or texto


def traducir_parrafos(texto, idioma, memoria):
    partes = str(texto or '').split('\n')
    return '\n'.join(traducir(p, idioma, memoria) if p.strip() else p
                     for p in partes)


def aplicar(banco, idioma, memoria):
    for q in banco.get('preguntas', []):
        fuente = copy.deepcopy((q.get('i') or {}).get('es') or {})
        if not fuente:
            continue
        destino = copy.deepcopy(fuente)
        destino['q'] = traducir(fuente.get('q'), idioma, memoria)
        if 'o' in fuente:
            destino['o'] = [[op[0], traducir(op[1], idioma, memoria)]
                            for op in fuente['o']]
        if 'x' in fuente:
            destino['x'] = traducir_parrafos(fuente['x'], idioma, memoria)
        if 'mod' in fuente:
            destino['mod'] = traducir_parrafos(fuente['mod'], idioma, memoria)
        if 'f' in fuente:
            campos = []
            for campo in fuente['f']:
                nuevo = copy.deepcopy(campo)
                nuevo[0] = traducir(campo[0], idioma, memoria)
                # La unidad se conserva tal como esta impresa (mm, ppm, PPR,
                # TCP, min, USD...). Traducirla produce errores tecnicos.
                if len(nuevo) > 1:
                    nuevo[1] = campo[1]
                campos.append(nuevo)
            destino['f'] = campos
        q.setdefault('i', {})[idioma] = destino


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--idiomas', default=','.join(IDIOMAS))
    ap.add_argument('--lote', type=int, default=25)
    args = ap.parse_args()
    destinos = [x.strip() for x in args.idiomas.split(',') if x.strip() in IDIOMAS]

    banco = cargar_banco()
    memoria = cargar_memoria()
    for texto, valores in OVERRIDES.items():
        memoria.setdefault(normalizar(texto), {}).update(valores)
    cadenas = recolectar(banco)
    pendientes = [(texto, idioma) for idioma in destinos for texto in cadenas
                  if not memoria.get(texto, {}).get(idioma)]
    print('Cadenas del banco: %d | pendientes: %d | idiomas: %s'
          % (len(cadenas), len(pendientes), ','.join(destinos)))

    total = 0
    for idioma in destinos:
        textos = [x for x in cadenas if not memoria.get(x, {}).get(idioma)]
        print('  es -> %s: %d cadenas' % (idioma, len(textos)))
        for i in range(0, len(textos), args.lote):
            lote = textos[i:i + args.lote]
            trads = None
            for intento in range(4):
                try:
                    trads = traducir_lote(lote, 'es', idioma)
                    break
                except Exception as e:
                    if intento == 3:
                        print('    FALLO lote %d: %s' % (i, e))
                    else:
                        espera = 30 * (intento + 1) if '429' in str(e) else 2 * (intento + 1)
                        time.sleep(espera)
            if not trads:
                continue
            for texto, trad in zip(lote, trads):
                trad = normalizar(trad)
                if trad:
                    memoria.setdefault(texto, {})[idioma] = trad
                    total += 1
            guardar_memoria(memoria)
            time.sleep(0.8)
        print('    acumulado: %d traducciones' % total)

    aplicar(banco, 'it', memoria)
    aplicar(banco, 'zh', memoria)
    banco['traduccion'] = {
        'it': 'borrador-de-traduccion',
        'zh': 'borrador-de-traduccion',
        'metodo': 'Google Translate desde es; P/N, numeros y marcas protegidos',
        'fecha': time.strftime('%Y-%m-%d'),
    }
    guardar_banco(banco)
    print('Banco actualizado: %d preguntas | memoria: %d cadenas | nuevas: %d'
          % (len(banco.get('preguntas', [])), len(memoria), total))


if __name__ == '__main__':
    main()
