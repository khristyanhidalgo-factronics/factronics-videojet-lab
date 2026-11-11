# -*- coding: utf-8 -*-
"""Corrige traducciones de cadenas cuyo idioma original no es el declarado.

La memoria de contenido se construyo asumiendo ingles/espanol, pero algunos
suministros TTO traen descripciones en japones y algunos repuestos laser traen
descripciones mixtas aleman/ingles. Este script detecta esos casos, retraduce
desde el idioma real y sobrescribe las traducciones erroneas.

Tambien repara valores donde Google dejo un centinela ZXQnQZX sin restaurar.

Uso:
  python tools/corregir_traducciones_cjk.py
"""
import json
import os
import sys
import time

from traducir_contenido import (SALIDA, detectar_fuente, guardar, normalizar,
                                traducir_lote)

IDIOMAS = ('es', 'en', 'pt', 'it', 'zh')


def fuente_de(texto, reg):
    detectada = detectar_fuente(texto, '')
    if detectada:
        return detectada
    for idioma in IDIOMAS:
        if reg.get(idioma) == texto:
            return idioma
    return 'en'


def main():
    if not os.path.exists(SALIDA):
        print('No existe la memoria de traducciones.')
        return
    datos = json.load(open(SALIDA, encoding='utf-8'))
    entradas = datos.get('entradas', {})
    pendientes = []
    origenes_detectados = 0
    for texto, reg in entradas.items():
        # Las traducciones manuales revisadas no se pisan con Google.
        if reg.get('manual'):
            continue
        origen = detectar_fuente(texto, '')
        if origen:
            origenes_detectados += 1
            reg[origen] = texto
            reg['fuente'] = origen
            reg['fuente_detectada'] = origen
        else:
            origen = fuente_de(texto, reg)
        for destino in IDIOMAS:
            if destino == origen or (origen == 'zh-CN' and destino == 'zh'):
                continue
            actual = reg.get(destino) or ''
            # Las cadenas de otro idioma se rehacen completas; las latinas solo
            # si quedaron con un centinela sin restaurar.
            if detectar_fuente(texto, '') or 'ZXQ' in actual.upper():
                pendientes.append((texto, origen, destino))

    print('Cadenas con origen detectado (ja/zh/ru/ar/de): %d | traducciones a corregir: %d'
          % (origenes_detectados, len(pendientes)))

    grupos = {}
    for texto, origen, destino in pendientes:
        grupos.setdefault((origen, destino), []).append(texto)

    total = 0
    for (origen, destino), textos in sorted(grupos.items()):
        print('  %s -> %s: %d cadenas' % (origen, destino, len(textos)))
        for i in range(0, len(textos), 20):
            lote = textos[i:i + 20]
            trads = None
            for intento in range(4):
                try:
                    trads = traducir_lote(lote, origen, destino)
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
                    entradas[texto][destino] = trad
                    total += 1
            guardar(entradas)
            time.sleep(0.8)
    guardar(entradas)
    print('Correcciones aplicadas: %d' % total)


if __name__ == '__main__':
    main()
