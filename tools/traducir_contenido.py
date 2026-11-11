# -*- coding: utf-8 -*-
"""Genera la memoria de traduccion de contenido de la app.

La app conserva el texto original (evidencia) y muestra la traduccion del
idioma activo. Este script recoge las cadenas visibles de docs/app/datos.js,
las traduce con Google Translate y guarda datos/traducciones_contenido.json.

Caracteristicas:
  - Cache incremental: no vuelve a traducir lo que ya existe.
  - Protege P/N, placeholders, unidades y marcas antes de traducir.
  - Aprovecha las descripciones TTO que ya vienen en es/en/pt.
  - Informa cobertura por idioma y categoria.

Uso:
  python tools/traducir_contenido.py                 # todo (es,pt,it,zh)
  python tools/traducir_contenido.py --idiomas es,pt # solo esos idiomas
  python tools/traducir_contenido.py --solo cij,errores --limite 40
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'datos')
APP = os.path.join(RAIZ, 'docs', 'app', 'datos.js')
SALIDA = os.path.join(DATOS, 'traducciones_contenido.json')
IDIOMAS = ['es', 'en', 'pt', 'it', 'zh']
URL = 'https://translate.googleapis.com/translate_a/t'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) FactronicsVideojetLab/1.0'

# Marcas y terminos que no se traducen.
NO_TRADUCIR = [
    'Videojet', 'DataFlex', 'Clarity', 'iAssure', 'CodeSoft', 'Zebra', 'SATO',
    'ICE', 'MEK', 'PCB', 'TTO', 'CIJ', 'LASER', 'P/N', 'IP55', 'IP65',
    'USB', 'LED', 'LCD', 'PET', 'PTFE', 'EPDM', 'PEEK', 'PVC', 'ABS',
]
RE_NO_TRADUCIR = re.compile(
    r'\b(?:' + '|'.join(re.escape(x) for x in NO_TRADUCIR) + r')\b'
)
RE_PROTEGER = [
    re.compile(r'\{[a-zA-Z_]+\}'),                       # placeholders
    re.compile(r'_{2,}'),                                 # espacios para completar
    re.compile(r'\bAL-\d{3,}[A-Z0-9-]*\b'),               # AL-00174
    re.compile(r'\bVJ\d{3,}[A-Z0-9-]*\b'),                # VJ1210
    re.compile(r'\bV\d{3,}[A-Z0-9-]*\b'),                 # V401
    re.compile(r'\b\d{3,}[A-Z]{2,}[A-Z0-9-]*\b'),         # 700776CM
    re.compile(r'\b[A-Z]{2,}\d{2,}[A-Z0-9-]*\b'),         # ICE100
    re.compile(r'\bM\d+\s*[xX]\s*\d+\b'),                 # M4 x 10
    re.compile(r'\b(?:ASTM|OECD|ISO|DIN|ANSI|UL|CE|RoHS)\s?[A-Z0-9.-]*\b'),
]


def normalizar(texto):
    return re.sub(r'\s+', ' ', str(texto or '')).strip()


# Marcadores alemanes que aparecen en descripciones mixtas de repuestos laser.
# Se usan como subcadenas: cubren plurales y palabras compuestas (Kabelbaum,
# Sicherungssatz, Montageanleitung, Trag-schiene, etc.).
ALEMAN_MARCADORES = [
    'reibrad', 'zoll', 'sicherung', 'versorgung', 'schraube', 'kabel',
    'austausch', 'lüfter', 'anleitung', 'betriebsan', 'einheit', 'stecker',
    'stift', 'dichtung', 'schlauch', 'deckel', 'gehäuse', 'leitung',
    'befestigung', 'montage', 'anschluss', 'schaltnetzteil', 'netzteil',
    'tragschiene', 'trag-schiene', 'steuereinheit', 'vorkonfektioniert',
    'isolationshauben', 'sicherungssatz', 'kabelbaum', 'walze', 'träger',
    'halter', 'platte', 'führung', 'wechsel', 'umbau', 'ausbau', 'einbau',
    'reinigung', 'wartung', 'störung', 'bitte', 'beachten', 'wird', 'werden',
    'nicht', 'für', 'arrettierung', 'verklebten', 'ineinigen', 'kundenliz',
    'betriebsan', 'lüfters', 'versorgungseinheit', 'wasser', 'wasserschl',
    'stilliert',
]
ALEMAN_EXACTO = {'und', 'der', 'die', 'das', 'von', 'auf', 'mit', 'ist',
                 'sind', 'wird', 'werden', 'nicht', 'für'}


def es_aleman(texto):
    if re.search(r'[äöüßÄÖÜ]', texto):
        return True
    minusculas = texto.lower()
    if minusculas.strip() in ALEMAN_EXACTO:
        return True
    return any(marcador in minusculas for marcador in ALEMAN_MARCADORES)


def detectar_fuente(texto, declarada):
    """Corrige la fuente cuando el texto visible no esta en el idioma declarado."""
    if re.search(r'[\u3040-\u30ff]', texto):
        return 'ja'
    if re.search(r'[\u4e00-\u9fff]', texto):
        return 'zh-CN'
    if re.search(r'[\u0400-\u04ff]', texto):
        return 'ru'
    if re.search(r'[\u0600-\u06ff]', texto):
        return 'ar'
    if es_aleman(texto):
        return 'de'
    return declarada


def cargar_datos_app():
    texto = open(APP, encoding='utf-8').read()
    m = re.search(r'window\.DATOS\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.DATOS en docs/app/datos.js')
    return json.loads(m.group(1))


def cargar_tto_conocidas():
    """Mapa texto -> {idioma: texto} con las descripciones TTO ya traducidas."""
    ruta = os.path.join(DATOS, 'partes_tto.json')
    if not os.path.exists(ruta):
        return {}
    datos = json.load(open(ruta, encoding='utf-8'))
    mapa = {}
    equivalencias = {'espanol': 'es', 'ingles': 'en', 'portugues': 'pt'}
    for p in datos.get('partes', []):
        textos = {}
        for d in p.get('descripciones') or []:
            idioma = equivalencias.get(d.get('idioma'))
            if idioma and d.get('texto'):
                textos[idioma] = normalizar(d['texto'])
        if not textos:
            continue
        for texto in textos.values():
            mapa.setdefault(texto, {}).update(textos)
    return mapa


def recolectar(datos, solo=None):
    """Devuelve {texto: {'categoria': str, 'fuente': 'en'|'es'|'pt'}}."""
    items = {}

    def add(texto, categoria, fuente='en', conocidas=None):
        texto = normalizar(texto)
        if not texto:
            return
        if solo and categoria not in solo:
            return
        fuente = detectar_fuente(texto, fuente)
        reg = items.setdefault(texto, {'categoria': categoria, 'fuente': fuente})
        if conocidas:
            reg.setdefault('conocidas', {}).update(conocidas)

    tto = cargar_tto_conocidas()
    for p in datos.get('partes', []):
        texto = normalizar(p.get('d'))
        if not texto:
            continue
        conocidas = tto.get(texto)
        fuente = 'en'
        if conocidas:
            # Si el texto canonico no es ingles, la fuente es su idioma.
            for idioma, valor in conocidas.items():
                if valor == texto:
                    fuente = idioma
                    break
        add(texto, 'partes_' + str(p.get('t', '')).lower(), fuente, conocidas)

    for e in datos.get('errores', []):
        add(e.get('x'), 'errores', 'en')
        add(e.get('cl'), 'errores_clase', 'en')

    for t in (datos.get('mant') or {}).get('tareas', []):
        add(t.get('x'), 'mantenimiento', 'en')
        add(t.get('iv'), 'mantenimiento_intervalo', 'en')

    rib = datos.get('ribbons') or {}
    for g in rib.get('grados', []):
        add(g.get('g'), 'ribbons_grado', 'en')
        add(g.get('tipo'), 'ribbons_tipo', 'en')
        add(g.get('col'), 'ribbons_color', 'en')
        add(g.get('film'), 'ribbons_film', 'en')
        add(g.get('desc'), 'ribbons_descripcion', 'en')
    for item in rib.get('items', []):
        if isinstance(item, list) and len(item) > 1:
            add(item[1], 'ribbons_item', 'en')

    for t in (datos.get('tintas') or {}).values():
        for b in t.get('b') or []:
            add(b, 'tinta_base', 'en')
        add(t.get('col'), 'tinta_color', 'en')
        for f in t.get('fichas') or []:
            for c in f.get('comp') or []:
                add(c.get('n'), 'tinta_componente', 'es')
            for k, v in (f.get('props') or {}).items():
                if isinstance(v, str):
                    add(v, 'tinta_propiedad', 'es')

    for s in datos.get('solventes', []):
        add(s.get('b'), 'solvente_base', 'en')
        add(s.get('e'), 'estado', 'es')

    meta = datos.get('meta') or {}
    add(meta.get('aviso'), 'meta_aviso', 'es')
    for v in (meta.get('fuentes') or {}).values():
        add(v, 'meta_fuente', 'es')

    return items


def proteger(texto, contador):
    """Sustituye tokens delicados por centinelas ZXQnQZX."""
    reemplazos = []

    def guardar(m):
        token = 'ZXQ%dQZX' % len(reemplazos)
        reemplazos.append((token, m.group(0)))
        return token

    for patron in RE_PROTEGER:
        texto = patron.sub(guardar, texto)
    texto = RE_NO_TRADUCIR.sub(guardar, texto)
    return texto, reemplazos


def restaurar(texto, reemplazos):
    for token, original in reemplazos:
        texto = texto.replace(token, original)

    # Google a veces altera el centinela (espacios, minusculas o lo duplica).
    def reponer(m):
        try:
            indice = int(m.group(1))
            return reemplazos[indice][1]
        except (ValueError, IndexError):
            return m.group(0)

    return re.sub(r'ZXQ\s*(\d+)\s*QZX', reponer, texto, flags=re.I)


def traducir_lote(textos, origen, destino):
    """Traduce una lista de textos (una linea cada uno). Devuelve lista."""
    protegidos = []
    reemplazos = []
    for t in textos:
        p, r = proteger(t, len(reemplazos))
        protegidos.append(p)
        reemplazos.append(r)
    consulta = '\n'.join(protegidos)
    datos = urllib.parse.urlencode({'q': consulta}).encode('utf-8')
    url = '%s?client=gtx&sl=%s&tl=%s&dt=t' % (URL, origen, destino)
    req = urllib.request.Request(url, data=datos, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        crudo = resp.read().decode('utf-8')
    salida = json.loads(crudo)
    if isinstance(salida, list) and salida and isinstance(salida[0], list):
        # Formato antiguo de translate_a/single: segmentos.
        lineas = ''.join(seg[0] for seg in salida[0]).split('\n')
    elif isinstance(salida, list) and salida and isinstance(salida[0], str):
        # translate_a/t: una sola cadena con los saltos de linea.
        lineas = salida[0].split('\n')
    elif isinstance(salida, str):
        lineas = salida.split('\n')
    else:
        raise ValueError('respuesta de traduccion no reconocida')
    if len(lineas) != len(textos):
        if len(textos) > 1:
            mitad = len(textos) // 2
            return (traducir_lote(textos[:mitad], origen, destino)
                    + traducir_lote(textos[mitad:], origen, destino))
        raise ValueError('lineas %d != textos %d' % (len(lineas), len(textos)))
    return [restaurar(x, reemplazos[i]) for i, x in enumerate(lineas)]


def guardar(entradas):
    datos = {
        'producto': 'Factronics Videojet Lab',
        'schema': 1,
        'actualizado': time.strftime('%Y-%m-%d'),
        'estado': 'borrador-de-traduccion',
        'metodo': 'Google Translate + proteccion de P/N, marcas y placeholders',
        'nota': ('Traduccion del contenido visible de la app. El texto original '
                 'se conserva en los datos y en la clave de esta memoria. '
                 'Revisar antes de usar como traduccion oficial.'),
        'idiomas': IDIOMAS,
        'entradas': entradas,
    }
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--idiomas', default=','.join(IDIOMAS))
    ap.add_argument('--solo', default='')
    ap.add_argument('--limite', type=int, default=0)
    ap.add_argument('--lote', type=int, default=35)
    args = ap.parse_args()
    destinos = [x.strip() for x in args.idiomas.split(',') if x.strip() in IDIOMAS]
    solo = {x.strip() for x in args.solo.split(',') if x.strip()} or None

    datos = cargar_datos_app()
    items = recolectar(datos, solo)
    if args.limite:
        items = dict(list(items.items())[:args.limite])

    entradas = {}
    if os.path.exists(SALIDA):
        entradas = json.load(open(SALIDA, encoding='utf-8')).get('entradas', {})

    pendientes = []
    for texto, reg in items.items():
        reg_actual = entradas.setdefault(texto, {})
        reg_actual.setdefault(reg['fuente'], texto)
        for conocidas in [reg.get('conocidas') or {}]:
            for idioma, valor in conocidas.items():
                if idioma in IDIOMAS:
                    reg_actual.setdefault(idioma, valor)
        for idioma in destinos:
            if not reg_actual.get(idioma):
                pendientes.append((texto, reg['fuente'], idioma))

    print('Cadenas visibles: %d | traducciones pendientes: %d | idiomas: %s'
          % (len(items), len(pendientes), ','.join(destinos)))

    # Agrupar por idioma destino y fuente.
    grupos = {}
    for texto, fuente, idioma in pendientes:
        grupos.setdefault((fuente, idioma), []).append(texto)

    total = 0
    for (fuente, idioma), textos in sorted(grupos.items()):
        print('  %s -> %s: %d cadenas' % (fuente, idioma, len(textos)))
        for i in range(0, len(textos), args.lote):
            lote = textos[i:i + args.lote]
            for intento in range(4):
                try:
                    trads = traducir_lote(lote, fuente, idioma)
                    break
                except Exception as e:
                    if intento == 3:
                        print('    FALLO lote %d: %s' % (i, e))
                        trads = None
                    else:
                        espera = 30 * (intento + 1) if '429' in str(e) else 2 * (intento + 1)
                        time.sleep(espera)
            if not trads:
                continue
            for texto, trad in zip(lote, trads):
                trad = normalizar(trad)
                if trad:
                    entradas[texto][idioma] = trad
                    total += 1
            guardar(entradas)
            time.sleep(0.8)
        print('    acumulado: %d traducciones' % total)

    guardar(entradas)

    # Cobertura
    faltan = 0
    for texto in items:
        for idioma in IDIOMAS:
            if not entradas.get(texto, {}).get(idioma):
                faltan += 1
    print('Memoria: %d entradas | cobertura %d/%d | faltan %d'
          % (len(entradas), len(entradas) * len(IDIOMAS) - faltan,
             len(entradas) * len(IDIOMAS), faltan))
    if faltan:
        print('  (ejecuta de nuevo para completar; la cache es incremental)')


if __name__ == '__main__':
    main()
