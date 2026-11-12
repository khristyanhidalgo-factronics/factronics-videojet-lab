# -*- coding: utf-8 -*-
"""Reconstruye tablas de partes desde el OCR con coordenadas de Windows.

Lee los JSON generados por tools/ocr_pdf_paginas.py, detecta la cabecera
(Item / P/N / Description / Qty), agrupa celdas por linea y produce registros
planos + un consolidado por P/N.

Estado honesto: los P/N y descripciones obtenidos por OCR quedan como
`borrador-decodificado`; no se convierten en `verificado` sin cotejo humano
o contra otra fuente digital. Se conserva `descripcion_ocr` como evidencia.

Uso:
  python tools/estructurar_partes_cij_ocr.py \
      datos/extraccion/ocr_cij_ipl_1550.json \
      datos/extraccion/ocr_cij_ipl_1710.json
"""
import difflib
import json
import os
import re
import sys
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'datos')
EXTRACCION = os.path.join(DATOS, 'extraccion')
SALIDA_PARTES = os.path.join(DATOS, 'partes_cij_ocr.json')
SALIDA_REGISTROS = os.path.join(EXTRACCION, 'partes_cij_ocr_registros.json')

HEADER_PATTERNS = {
    'item': re.compile(r'^item(?:\s*(?:number|no\.?|n[o°]\.?))?$', re.I),
    'pn': re.compile(r'^(?:p\s*/?\s*n|pin|part(?:\s*(?:number|no\.?))?)$', re.I),
    'desc': re.compile(r'^description$', re.I),
    'qty': re.compile(r'^(?:qty|quantity)$', re.I),
}

EXCLUIR_LINEA = re.compile(
    r'^(?:Videojet\s+.*?(?:Service Manual|Printer)|Rev\s+AA|'
    r'Table\s+\d|Figure\s+\d|Illustrated Parts List|'
    r'How to Read the IPL|This section describes)\b', re.I)

CONFUSION_PN = str.maketrans({'O': '0', 'o': '0', 'I': '1', 'l': '1',
                              'S': '5', 'B': '8', 'Z': '2'})


def norm(t):
    return re.sub(r'\s+', ' ', (t or '')).strip()


def centro(linea):
    return linea['y'] + linea['h'] / 2.0


def cargar_json(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)


def pns_conocidos():
    conocidos = set()
    ruta = os.path.join(DATOS, 'partes_cij.json')
    if os.path.exists(ruta):
        for p in cargar_json(ruta).get('partes', []):
            if p.get('pn'):
                conocidos.add(str(p['pn']))
    return conocidos


def detectar_cabecera(page):
    """Devuelve ({columna: x}, y_cabecera) o (None, None)."""
    eventos = []
    for linea in page.get('lineas', []):
        palabras = linea.get('palabras') or [{'t': linea.get('texto', ''),
                                               'x': linea.get('x', 0)}]
        # primero el texto completo de la linea (cubre "Item Number")
        t = norm(linea.get('texto', '')).strip(' .:')
        for clave, patron in HEADER_PATTERNS.items():
            if patron.match(t):
                eventos.append((centro(linea), clave, linea['x']))
                break
        else:
            for palabra in palabras:
                w = norm(palabra.get('t', '')).strip(' .:')
                for clave, patron in HEADER_PATTERNS.items():
                    if patron.match(w):
                        eventos.append((centro(linea), clave, palabra['x']))
                        break

    if not eventos:
        return None, None

    mejor = None
    for ancla in eventos:
        cluster = [e for e in eventos if abs(e[0] - ancla[0]) <= 28]
        claves = {e[1] for e in cluster}
        if 'pn' in claves and 'desc' in claves:
            puntaje = (len(claves), -abs(ancla[0] - min(e[0] for e in cluster)))
            if mejor is None or puntaje > mejor[0]:
                mejor = (puntaje, cluster)
    if mejor is None:
        return None, None

    cluster = mejor[1]
    x_por_clave = {}
    for _, clave, x in cluster:
        x_por_clave.setdefault(clave, []).append(x)
    x_por_clave = {k: min(v) for k, v in x_por_clave.items()}
    y_cabecera = sum(e[0] for e in cluster) / float(len(cluster))
    return x_por_clave, y_cabecera


def rangos_columnas(x_por_clave, ancho):
    orden = sorted(x_por_clave.items(), key=lambda kv: kv[1])
    rangos = {}
    for i, (clave, x) in enumerate(orden):
        izquierda = x - 20
        if clave == 'pn' and 'item' not in x_por_clave:
            izquierda = 0
        derecha = (orden[i + 1][1] - 20) if i + 1 < len(orden) else ancho
        rangos[clave] = (izquierda, derecha)
    return rangos


def columna_de(x, rangos):
    for clave, (izq, der) in rangos.items():
        if izq <= x < der:
            return clave
    return None


def agrupar_filas(lineas, tolerancia=20):
    filas = []
    for linea in sorted(lineas, key=lambda l: (centro(l), l['x'])):
        c = centro(linea)
        if filas and abs(c - filas[-1]['y']) <= tolerancia:
            filas[-1]['lineas'].append(linea)
        else:
            filas.append({'y': c, 'lineas': [linea]})
    return filas


def texto_celda(lineas):
    return norm(' '.join(l['texto'] for l in sorted(lineas, key=lambda l: l['x'])))


def limpiar_item(texto):
    m = re.match(r'^\s*(\d{1,3}[A-Z]?\*?)\b', texto or '')
    return m.group(1) if m else ''


def limpiar_qty(texto):
    m = re.search(r'\b(\d{1,3})\b', texto or '')
    return m.group(1) if m else ''


def corregir_desc(texto):
    """Correcciones OCR conservadoras, documentadas en `correcciones`."""
    original = texto
    cambios = []
    reglas = [
        (r'\bM[I1]O\b', 'M10'),
        (r'\bMio\b', 'M10'),
        (r'\bM1O\b', 'M10'),
        (r'\bT[I1]O\b', 'T10'),
        (r'\bNo\.l\b', 'No.1'),
        (r'\b112 inch\b', '1/2 inch'),
        (r'\bI/4(["\u2033])', r'1/4\1'),
        # confusiones visuales documentadas en los IPL 1550/1710
        (r'\bPiate\b', 'Plate'),
        (r'\bBottie\b', 'Bottle'),
        (r'\bOnlStandby\b', 'On/Standby'),
        (r'\b1/0\b', 'I/O'),
    ]
    for patron, reemplazo in reglas:
        nuevo = re.sub(patron, reemplazo, texto)
        if nuevo != texto:
            cambios.append('%s -> %s' % (patron, reemplazo))
            texto = nuevo
    return norm(texto), (cambios if texto != original else [])


PN_PATRON = re.compile(
    r'(?<![A-Z0-9])([A-Z]{0,3}\d{5,7}(?:[-/]\d{1,3})?[A-Z]?)(?![A-Z0-9])')


def normalizar_pn(texto, conocidos):
    """Devuelve (pn, corregido, texto_ocr).

    Conserva prefijos alfabeticos (SP399089 != 399089). Solo aplica confusiones
    OCR (O->0, I->1...) al tramo numerico, nunca al prefijo.
    """
    if not texto:
        return None, False, ''
    plano = re.sub(r'(?<=[A-Z])\s+(?=\d)', '', texto)
    plano = re.sub(r'(?<=\d)\s+(?=\d)', '', plano)
    plano = norm(plano).strip('.,;:')
    m = PN_PATRON.search(plano.upper())
    if m:
        return m.group(1), False, texto
    # confusiones OCR: separar prefijo alfabetico del tramo numerico
    upper = plano.upper()
    mp = re.match(r'^([A-Z]{1,3})(?=\d)', upper)
    prefijo = mp.group(1) if mp else ''
    resto = upper[len(prefijo):]
    traducido = prefijo + resto.translate(CONFUSION_PN)
    m = PN_PATRON.search(traducido)
    if m:
        candidato = m.group(1)
        if candidato in conocidos or len(re.sub(r'\D', '', candidato)) >= 6:
            return candidato, True, texto
    return None, False, texto


def pagina_impresa(page):
    """Numero impreso en el pie (no el 'Table 10-3' del titulo)."""
    candidatos = []
    for linea in page.get('lineas', []):
        t = norm(linea.get('texto', ''))
        if re.match(r'^(?:Table|Figure)\b', t, re.I):
            continue
        if re.search(r'\b(?:Videojet|Service Manual|Rev)\b', t, re.I):
            continue
        m = re.search(r'\b(\d{1,2}-\d{1,3})\b', t)
        if m:
            candidatos.append((linea.get('y', 0), m.group(1)))
    if not candidatos:
        return str(page.get('pagina', ''))
    # el pie de pagina es la ultima linea con un numero de pagina
    candidatos.sort()
    return candidatos[-1][1]


def titulo_tabla(page, y_cabecera):
    candidatos = []
    for linea in page.get('lineas', []):
        t = norm(linea.get('texto', ''))
        if re.match(r'^Table\s+\d+', t, re.I):
            candidatos.append((abs(centro(linea) - y_cabecera), t))
    if not candidatos:
        return ''
    return sorted(candidatos)[0][1]


def grupo_de(titulo):
    t = re.sub(r'^Table\s+[\d-]+\s*:\s*', '', titulo, flags=re.I)
    t = re.sub(r'\s*\(Continued\)\s*$', '', t, flags=re.I)
    t = re.sub(r'\s+\d{1,2}-\d{1,3}\s*$', '', t)
    return norm(t)


def parsear_pagina(page, documento, modelo, conocidos, diagn):
    x_por_clave, y_cabecera = detectar_cabecera(page)
    if not x_por_clave:
        return [], []
    rangos = rangos_columnas(x_por_clave, page.get('ancho', 3000))
    lineas_datos = []
    for linea in page.get('lineas', []):
        t = norm(linea.get('texto', ''))
        if centro(linea) <= y_cabecera + 12:
            continue
        if EXCLUIR_LINEA.match(t):
            continue
        if re.match(r'^\d{1,2}-\d{1,3}$', t):
            continue
        lineas_datos.append(linea)
    if not lineas_datos:
        return [], []

    titulo = titulo_tabla(page, y_cabecera)
    grupo = grupo_de(titulo)
    pagina = pagina_impresa(page)
    filas = agrupar_filas(lineas_datos)
    alturas = [l['h'] for l in lineas_datos if l.get('h')]
    altura_media = sorted(alturas)[len(alturas) // 2] if alturas else 45.0

    registros = []
    sin_pn = []
    fila_previa = None
    y_previa = None

    for fila in filas:
        celdas = {}
        for linea in fila['lineas']:
            clave = columna_de(linea['x'], rangos)
            if clave:
                celdas.setdefault(clave, []).append(linea)
        item = limpiar_item(texto_celda(celdas.get('item', [])))
        pn_texto = texto_celda(celdas.get('pn', []))
        desc_ocr = texto_celda(celdas.get('desc', []))
        qty = limpiar_qty(texto_celda(celdas.get('qty', [])))

        if not desc_ocr or len(desc_ocr) < 3:
            continue
        if EXCLUIR_LINEA.match(desc_ocr):
            continue

        pn, corregido, pn_ocr = normalizar_pn(pn_texto, conocidos)
        desc, correcciones = corregir_desc(desc_ocr)

        # Continuacion de una descripcion partida en dos lineas OCR.
        if not item and not pn and not qty:
            if (fila_previa is not None and fila_previa.get('descripcion')
                    and y_previa is not None
                    and abs(fila['y'] - y_previa) <= altura_media * 1.6
                    and len(desc.split()) <= 6):
                fila_previa['descripcion'] = norm(
                    fila_previa['descripcion'] + ' ' + desc)
                continue
            # nota o titulo suelto: no es una fila de partes
            continue

        base = {
            'pn': pn,
            'descripcion': desc,
            'descripcion_ocr': desc_ocr,
            'correcciones_ocr': correcciones,
            'item': item or None,
            'designador': None,
            'cantidad': qty or None,
            'tabla': titulo or ('OCR pagina %s' % page.get('pagina')),
            'grupo': grupo,
            'conjunto': grupo,
            'tipo': 'parte' if pn else 'sin-pn',
            'documento': documento,
            'modelo': modelo,
            'bloque': page.get('pagina'),
            'pagina': pagina,
            'metodo': 'OCR Windows.Media.Ocr',
        }
        if pn:
            base['pn_ocr'] = pn_ocr
            base['pn_corregido_ocr'] = corregido
            registros.append(base)
        elif desc:
            base['estado'] = 'sin-pn'
            sin_pn.append(base)
            if pn_texto:
                diagn.append('%s p.%s: P/N no legible %r (%r)'
                             % (documento, page.get('pagina'), pn_texto, desc[:60]))
        fila_previa = base
        y_previa = fila['y']

    return registros, sin_pn


def consolidar(registros):
    por_pn = {}
    for reg in registros:
        por_pn.setdefault(reg['pn'], []).append(reg)
    partes = []
    for pn, regs in sorted(por_pn.items()):
        descs = {}
        for r in regs:
            if r['descripcion']:
                descs.setdefault(normalizar_desc(r['descripcion']), []).append(
                    r['descripcion'])
        canonica = ''
        if descs:
            lista = sorted(descs.items(),
                           key=lambda kv: (-len(kv[1]), -len(kv[1][0])))
            canonica = sorted(lista[0][1], key=len, reverse=True)[0]
        variantes = sorted({d for r in regs for d in [r['descripcion']] if d})
        conflicto = False
        claves = list(descs.keys())
        for i in range(len(claves)):
            for j in range(i + 1, len(claves)):
                if not desc_compatible(descs[claves[i]][0],
                                       descs[claves[j]][0]):
                    conflicto = True
                    break
            if conflicto:
                break
        apariciones = []
        vistos = set()
        for r in regs:
            clave = (r['documento'], r['bloque'], r['item'],
                     r['cantidad'], r['descripcion'])
            if clave in vistos:
                continue
            vistos.add(clave)
            apariciones.append({
                'documento': r['documento'],
                'modelo': r['modelo'],
                'tabla': r['tabla'],
                'item': r['item'],
                'cantidad': r['cantidad'],
                'designador': r['designador'],
                'grupo': r['grupo'],
                'conjunto': r['conjunto'],
                'tipo': r['tipo'],
                'descripcion': r['descripcion'],
                'descripcion_ocr': r.get('descripcion_ocr'),
                'bloque': r['bloque'],
                'pagina': r['pagina'],
                'metodo': r['metodo'],
                'pn_ocr': r.get('pn_ocr'),
                'pn_corregido_ocr': r.get('pn_corregido_ocr', False),
                'correcciones_ocr': r.get('correcciones_ocr', []),
                'no_mostrado_en_figura': False,
            })
        partes.append({
            'pn': pn,
            'descripcion': canonica,
            'descripciones': variantes,
            'calificadores': sorted({c for r in regs
                                     for c in re.findall(r'\(([^)]*)\)',
                                                         r['descripcion'])}),
            'tipo': ['parte'],
            'estado': 'borrador-decodificado' if canonica else 'por-definir',
            'conflicto_descripciones': conflicto,
            'origen': 'OCR',
            'documentos': sorted({r['documento'] for r in regs}),
            'modelos': sorted({r['modelo'] for r in regs}),
            'apariciones': apariciones,
        })
    return partes


def normalizar_desc(texto):
    t = norm(texto).lower()
    t = re.sub(r'\([^)]*\)', ' ', t)
    t = re.sub(r'[^a-z0-9]+', ' ', t)
    return norm(t)


def palabras_clave(texto):
    vacias = {'the', 'and', 'with', 'for', 'of', 'to', 'in', 'on', 'a', 'an',
              'or', 'assembly', 'kit', 'unit', 'system', 'module', 'part',
              'spare'}
    return {w.lower() for w in re.findall(r'[A-Za-z]{3,}', texto)
            if w.lower() not in vacias}


def desc_compatible(a, b):
    na, nb = normalizar_desc(a), normalizar_desc(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    A, B = palabras_clave(na), palabras_clave(nb)
    if not A or not B:
        return False
    if len(A & B) / float(len(A | B)) >= 0.8:
        return True
    # Tolerar erratas OCR de una letra ("Bottie" vs "Bottle"): se considera
    # que dos palabras coinciden si su similitud es alta y su longitud casi
    # igual; luego se exige la misma proporcion de coincidencia que arriba.
    coincidencias = 0
    for palabra in A:
        mejor = max((difflib.SequenceMatcher(None, palabra, otra).ratio()
                     for otra in B), default=0.0)
        if mejor >= 0.85 and any(
                abs(len(palabra) - len(otra)) <= 2
                and difflib.SequenceMatcher(None, palabra, otra).ratio() >= 0.85
                for otra in B):
            coincidencias += 1
    return coincidencias / float(len(A | B)) >= 0.8


def escribir_texto(paginas, ruta):
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write('# OCR Windows.Media.Ocr (sin instalar nada) - coordenadas y texto\n')
        for page in paginas:
            f.write('\n\n===== PAGINA %s =====\n' % page.get('pagina'))
            for linea in sorted(page.get('lineas', []),
                                key=lambda l: (l['y'], l['x'])):
                f.write('%s\n' % norm(linea.get('texto', '')))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    conocidos = pns_conocidos()
    registros = []
    sin_pn = []
    documentos = []
    paginas_por_doc = []
    paginas_omitidas = []
    diagn = []

    for ruta in sys.argv[1:]:
        datos = cargar_json(ruta)
        doc = datos.get('fuente') or os.path.basename(ruta)
        slug = datos.get('slug') or ''
        modelo = '1550' if '1550' in slug else ('1710' if '1710' in slug else slug)
        documentos.append({'archivo': doc, 'modelo': modelo,
                           'metodo': 'OCR Windows.Media.Ocr',
                           'json_ocr': os.path.relpath(ruta, RAIZ).replace('\\', '/')})
        paginas_doc = datos.get('paginas', [])
        paginas_por_doc.append((doc, paginas_doc))
        regs_doc = 0
        sins_doc = 0
        for page in paginas_doc:
            if page.get('error'):
                paginas_omitidas.append({
                    'documento': doc,
                    'pagina': page.get('pagina'),
                    'error': page.get('error'),
                    'detalle': page.get('detalle'),
                })
                continue
            regs, sins = parsear_pagina(page, doc, modelo, conocidos, diagn)
            registros.extend(regs)
            sin_pn.extend(sins)
            regs_doc += len(regs)
            sins_doc += len(sins)
        print('%s: %d paginas, %d registros con P/N, %d sin P/N'
              % (doc, len(paginas_doc), regs_doc, sins_doc))

    partes = consolidar(registros)
    nuevos = [p for p in partes if p['pn'] not in conocidos]
    resumen = {
        'documentos': len(documentos),
        'paginas_ocr': sum(len(p) for _, p in paginas_por_doc),
        'registros': len(registros),
        'partes': len(partes),
        'borrador_decodificado': sum(1 for p in partes
                                     if p['estado'] == 'borrador-decodificado'),
        'por_definir': sum(1 for p in partes if p['estado'] == 'por-definir'),
        'pn_nuevos': len(nuevos),
        'items_sin_pn': len(sin_pn),
        'conflictos': sum(1 for p in partes if p['conflicto_descripciones']),
        'paginas_omitidas': len(paginas_omitidas),
    }
    salida = {
        'generado': date.today().isoformat(),
        'fuente': 'Illustrated Parts Lists 1550 y 1710 (OCR de los PDF del dueno)',
        'metodo': ('Render Windows.Data.Pdf 3000 px + Windows.Media.Ocr; '
                   'filas reconstruidas por coordenadas; estado honesto '
                   'borrador-decodificado'),
        'resumen': resumen,
        'documentos': documentos,
        'partes': partes,
        'items_sin_pn': sin_pn,
        'paginas_omitidas': paginas_omitidas,
    }
    os.makedirs(EXTRACCION, exist_ok=True)
    with open(SALIDA_PARTES, 'w', encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    with open(SALIDA_REGISTROS, 'w', encoding='utf-8') as f:
        json.dump({'generado': date.today().isoformat(),
                   'registros': registros, 'items_sin_pn': sin_pn},
                  f, ensure_ascii=False, indent=1)
    # texto de evidencia por documento
    for doc, paginas in paginas_por_doc:
        escribir_texto(paginas, os.path.join(
            EXTRACCION, 'ocr_%s.txt' % re.sub(r'[^a-z0-9]+', '_',
                                               doc.lower()).strip('_')[:80]))
    if diagn:
        with open(os.path.join(EXTRACCION, 'partes_cij_ocr_diagnostico.txt'),
                  'w', encoding='utf-8') as f:
            f.write('\n'.join(diagn))
    print('OK %s' % os.path.relpath(SALIDA_PARTES, RAIZ))
    print('   %s' % json.dumps(resumen, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
