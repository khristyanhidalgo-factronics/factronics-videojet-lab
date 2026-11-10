# -*- coding: utf-8 -*-
"""Estructura las partes CIJ de los IPL 1000VJ legibles.

Parser v5.1 por lineas-ancla y celdas reales:
- Usa las corridas (y, x, texto) del extractor visual.
- Los saltos de columna de los TJ vienen marcados con \\x1f (separador de celda).
- La cantidad se une desde toda la ultima celda: cubre cantidades partidas en
  varias corridas ('1' + '0' = 10) y evita que el '1' contamine la descripcion.
- Las tablas de variantes P/N | descripcion | idiomas o pais usan el mismo
  parser sin item ni cantidad (p. ej. Table 10-4 del 1620E).
- Ancla = linea con item, o con designador + descripcion, o con P/N + descripcion.
- El rango de fila llega hasta la siguiente ancla; dentro del rango se recogen
  todos los P/N de la columna P/N (soporta varios P/N apilados y variantes).
- Las descripciones compartidas se asignan a todos los P/N de la fila.
- Estado honesto: verificado si >=2 documentos coinciden en descripcion;
  borrador si solo aparece en uno; sin-pn para items sin numero de parte.

Uso:
  python tools/estructurar_partes_cij.py
  python tools/estructurar_partes_cij.py --debug "1210_1510 - Illustrated Parts List.pdf" 26
"""
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leer_pdf_cifrado as L

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
           r'\VIDEOJET DOCUMENTOS 1000VJ---------------------------'
           r'\ILUSTRACION DE PARTES 1000VJ')
SALIDA = os.path.join(RAIZ, 'datos', 'partes_cij.json')

# Solo los IPL con numeros de parte legibles en el texto extraido.
DOCUMENTOS = [
    ('1210_1510 - Illustrated Parts List.pdf', '1210/1510'),
    ('1220 1520 - Illustrated Parts List.pdf', '1220/1520'),
    ('1520E - Illustrated Parts List.pdf', '1520E'),
    ('1610 DH - Illustrated Parts List.pdf', '1610 DH'),
    ('1620E - Illustrated Parts List.pdf', '1620E'),
    ('1650_1650 UHS HR - Illustrated parts List.pdf', '1650/1650 UHS'),
]

PAT_PN = re.compile(
    r'(?:\d{3}-\d{4}-\d{3}'          # 500-0036-578
    r'|(?:SP|TL)\d{6,8}[A-Z*]?'      # SP500074, SP399597W
    r'|\d{6,8}(?:-\d{2,4}){0,2}[A-Z*]?)')  # 378192, 356841-02, 80000008
PAT_PN_ESTRICTO = re.compile(
    r'^(?:\d{3}-\d{4}-\d{3}'
    r'|(?:SP|TL)\d{6,8}[A-Z*]?'
    r'|\d{6,8}(?:-\d{2,4}){0,2}[A-Z*]?)$')
PAT_ITEM = re.compile(r'^\d{1,3}\*?$')
PAT_QTY = re.compile(r'^\d{1,2}$')
PAT_DESIG = re.compile(r'^[A-Z]$')
PAT_TABLA = re.compile(r'^Table\s+([\d\-]+):\s*(.+?)(\s*\(Continued\))?$')
PAT_TITULO_CAP = re.compile(r'^(Table|Figure)\s+[\d\-]+:', re.I)
PAT_NOTA = re.compile(r'^(?:Refer to|See|Note|Notes|\*|\(\s*See)', re.I)
PAT_CALIFICADOR = re.compile(
    r'^(?:IP\d{2}|UHS(?:\s+HR)?|FG|.*\bFG\b|.*\bmicron\b|'
    r'Optional for .*|Videojet .*|.*\b(?:1510|1210|1520|1220|1610|1620|1650)\b.*)$',
    re.I)
PAT_QUAL = re.compile(r'\([^)]*\)')

# Calificadores que SI forman parte de la descripcion (no se deben quitar).
QUAL_VALIDOS = re.compile(
    r'^(?:Videojet[^)]*|.*\bFG\b|IP\d{2}|UHS(?:\s+HR)?|'
    r'.*\bmicron\b|Optional for [^)]*|[^)]*\b(?:1510|1210|1520|1220|1610|1620|1650)\b[^)]*)$',
    re.I)


def mediana(valores, defecto=0.0):
    return statistics.median(valores) if valores else defecto


def moda(valores, defecto=0.0):
    if not valores:
        return defecto
    conteo = {}
    for v in valores:
        k = round(v * 2) / 2.0
        conteo[k] = conteo.get(k, 0) + 1
    return max(conteo.items(), key=lambda kv: (kv[1], -abs(kv[0])))[0]


def agrupar_lineas(runs, tol=6.0):
    """Agrupa corridas por linea visual. Respeta el orden de emision dentro
    de la linea (item -> P/N -> descripcion -> cantidad)."""
    ordenados = sorted(enumerate(runs), key=lambda z: (-z[1][0], z[0]))
    lineas = []
    for pos, (y, x, txt) in ordenados:
        if not lineas or abs(lineas[-1]['y'] - y) > tol:
            lineas.append({'y': y, 'runs': [(x, txt, pos)]})
        else:
            lineas[-1]['runs'].append((x, txt, pos))
    for linea in lineas:
        linea['runs'].sort(key=lambda r: r[2])
    return lineas


def dividir_celdas(linea):
    """Separa las corridas de una linea en celdas usando el separador \\x1f."""
    celdas = [[]]
    for x, txt, pos in linea['runs']:
        if txt == '\x1f':
            celdas.append([])
        else:
            celdas[-1].append((x, txt, pos))
    return [c for c in celdas if c]


def texto_de_celda(celda):
    return ''.join(t for _, t, _ in celda)


def texto_de_linea(linea):
    return ''.join(t for _, t, _ in linea['runs'] if t != '\x1f')


def plano(texto):
    return re.sub(r'\s+', '', texto)


def es_tabla_header(texto):
    p = plano(texto).lower()
    return ('itemnumber' in p and 'p/n' in p and 'description' in p)


def es_titulo_tabla(texto):
    return bool(PAT_TABLA.match(texto.strip()))


def es_titulo_seccion(texto):
    """Cabecera de seccion dentro de una tabla (Encoders, PCB Assemblies)."""
    t = texto.strip()
    if not t or len(t) > 60:
        return False
    if re.search(r'\d|\(|\)|/', t):
        return False
    if re.match(r'^(IP\d|Optional|Videojet|FG\b|UHS\b)', t, re.I):
        return False
    return 1 <= len(t.split()) <= 6


def es_continuacion_desc(texto):
    """Linea que continua la descripcion anterior aunque el hueco sea mayor.

    En algunas tablas la descripcion ocupa dos lineas separadas 22-26 pt
    (p. ej. 'connectors to new DIN connectors').  Las cabeceras de seccion
    y los calificadores IP empiezan en mayuscula y no deben fusionarse.
    """
    t = texto.strip()
    if not t:
        return False
    return bool(re.match(r'^(?:[a-z(]|For\b|To\b|With\b|and\b|or\b)', t))


def nombre_tabla(titulo):
    """Nombre de la seccion de la tabla, sin el 'Table X-Y:'."""
    if not titulo:
        return None
    m = re.match(r'^Table\s+[\d\-]+:\s*(.+)$', titulo)
    return m.group(1).strip() if m else titulo


def es_header_pie(texto):
    p = texto.strip()
    if not p:
        return True
    if 'Service Manual' in p or re.match(r'^Rev\s', p):
        return True
    if re.match(r'^\d{1,2}-\d{1,3}\s', p):
        return True
    if re.match(r'^(Illustrated Parts List|The Illustrated Part List|'
                r'How to Read the IPL|This section describes)', p, re.I):
        return True
    return False


def inferir_columnas(lineas):
    """Infiere item_x, pn_x y desc_x de las lineas de una pagina.

    desc_x se calcula solo con filas estandar (item + descripcion + qty),
    porque en los encabezados con P/N la descripcion puede empezar pegada
    al P/N (x~165-210) y contaminaria la inferencia."""
    item_xs = []
    pn_xs = []
    desc_xs = []
    for linea in lineas:
        runs = [r for r in linea['runs'] if r[1] != '\x1f']
        if not runs:
            continue
        texto = ''.join(t for _, t, _ in runs)
        if PAT_PN.search(texto):
            limites = []
            acum = 0
            for i, (x, t, pos) in enumerate(runs):
                limites.append((acum, acum + len(t), i))
                acum += len(t)
            for pn, ini, _ in buscar_pns(texto):
                for a, b, i in limites:
                    if a <= ini < b:
                        pn_xs.append(runs[i][0])
                        break
        x0, t0, _ = runs[0]
        if not (PAT_ITEM.match(t0.strip()) and x0 < 145):
            continue
        if len(runs) < 2:
            continue
        if not (PAT_QTY.match(runs[-1][1].strip()) and runs[-1][0] > 350):
            continue
        item_xs.append(x0)
        # primera corrida con letras a la derecha de x=220 (puede ser una
        # sola letra: 'S' de Spring, 'R' de Ribbon)
        for x, t, _ in runs[1:]:
            tt = t.strip()
            if not tt or PAT_PN_ESTRICTO.match(tt):
                continue
            if x > 220 and re.search(r'[A-Za-z]', tt):
                if not re.match(r'^(?:Refer|See|Note|\*|Items?\b)', tt,
                                re.I):
                    desc_xs.append(x)
                break
    item_x = moda(item_xs, 116.4)
    pn_x = moda(pn_xs, item_x + 40)
    desc_x = moda(desc_xs, pn_x + 130)
    return item_x, pn_x, desc_x


def segmentos_de_tabla(lineas):
    """Devuelve segmentos [(y_header, y_fin, titulo)] por pagina."""
    headers = []
    titulos = []
    for linea in lineas:
        texto = texto_de_linea(linea)
        if es_tabla_header(texto):
            headers.append(linea['y'])
        m = PAT_TABLA.match(texto.strip())
        if m:
            titulos.append((linea['y'], m.group(1), m.group(2).strip()))
    headers.sort(reverse=True)
    segmentos = []
    for i, yh in enumerate(headers):
        yfin = headers[i + 1] if i + 1 < len(headers) else -1e9
        # titulo mas cercano por debajo del header y por encima del siguiente
        candidatos = [(yt, num, tit) for yt, num, tit in titulos
                      if yfin < yt < yh]
        if candidatos:
            yt, num, tit = max(candidatos, key=lambda c: c[0])
            titulo = 'Table %s: %s' % (num, tit)
        else:
            titulo = None
        segmentos.append((yh, yfin, titulo))
    return segmentos


def titulo_de(y, segmentos):
    for yh, yfin, titulo in segmentos:
        if yfin < y <= yh:
            return titulo
    return None


def clasificar_linea(linea, item_x, pn_x, desc_x):
    """Devuelve (item, designador, pn_runs, desc_runs, qty).

    Si el PDF inserta un separador de celda justo despues del P/N, se usa
    como frontera real: la primera letra de la descripcion puede quedar a
    la izquierda del umbral por coordenadas (p. ej. 'C' de Control).
    """
    runs = list(linea['runs'])
    qty = None
    no_sep = [i for i, r in enumerate(runs) if r[1] != '\x1f']
    if no_sep:
        # La cantidad puede venir partida en varias corridas dentro de la
        # ultima celda ('1' + '0' = 10).  Si hay separador de celda, se une
        # todo el texto de la ultima celda antes de decidir.
        contexto = False
        j0 = no_sep[0]
        if (PAT_ITEM.match(runs[j0][1].strip())
                and runs[j0][0] < item_x + 10):
            contexto = True
        if not contexto:
            texto_izq = ''.join(r[1] for r in runs
                                if r[1] != '\x1f' and r[0] < desc_x - 12)
            contexto = bool(buscar_pns(texto_izq))
        seps = [i for i, r in enumerate(runs) if r[1] == '\x1f']
        if seps and contexto:
            i0 = seps[-1] + 1
            qty_runs = [i for i in range(i0, len(runs))
                        if runs[i][1] != '\x1f']
            qty_texto = ''.join(runs[i][1] for i in qty_runs).strip()
            if qty_texto and PAT_QTY.match(qty_texto):
                qty = qty_texto
                for i in reversed(qty_runs):
                    runs.pop(i)
                no_sep = [j for j, r in enumerate(runs) if r[1] != '\x1f']
        if qty is None:
            i = no_sep[-1]
            x, t, pos = runs[i]
            # La columna Qty no siempre conserva la misma x entre objetos de
            # texto (1220/1520 b33: la qty de la fila 30 queda en x=329.3).
            # Si el numero va tras un separador de celda y la linea tiene item
            # o P/N, es cantidad aunque la x no llegue al umbral.
            tras_sep = i > 0 and runs[i - 1][1] == '\x1f'
            if (PAT_QTY.match(t.strip())
                    and (x > desc_x + 120 or (tras_sep and contexto))):
                # Sin separador de celda la cantidad tambien puede venir
                # partida ('1' + '4' = 14).  Se unen las corridas numericas
                # contiguas que estan en la columna de cantidad.
                qty_runs = [i]
                j = i - 1
                while j >= 0 and runs[j][1] != '\x1f':
                    px, pt, _ = runs[j]
                    if (PAT_QTY.match(pt.strip()) and px > desc_x + 80
                            and abs(x - px) <= 15):
                        qty_runs.insert(0, j)
                        x = px
                        j -= 1
                    else:
                        break
                qty = ''.join(runs[k][1] for k in qty_runs).strip()
                for k in reversed(qty_runs):
                    runs.pop(k)
                no_sep = [j for j, r in enumerate(runs) if r[1] != '\x1f']
    item = None
    if no_sep:
        i = no_sep[0]
        x, t, pos = runs[i]
        if PAT_ITEM.match(t.strip()) and x < item_x + 10:
            item = t.strip()
            runs.pop(i)
    designador = None
    for i, (x, t, pos) in enumerate(runs):
        if t != '\x1f' and PAT_DESIG.match(t.strip()) and x < item_x - 15:
            designador = t.strip()
            runs.pop(i)
            break
    # posicion del ultimo caracter del ultimo P/N de la CELDA de P/N
    # (no de las referencias que aparecen dentro de la descripcion)
    mapa = []
    acum = 0
    for i, (x, t, pos) in enumerate(runs):
        if t == '\x1f':
            continue
        if x >= desc_x - 12:
            continue
        mapa.append((acum, acum + len(t), i))
        acum += len(t)
    texto_celda = ''.join(runs[i][1] for _, _, i in mapa)
    pns = buscar_pns(texto_celda)
    frontera = None
    if pns:
        _, _, fin = pns[-1]
        idx_pn = None
        for a, b, i in mapa:
            if a <= fin - 1 < b:
                idx_pn = i
                break
        if idx_pn is not None and idx_pn + 1 < len(runs):
            if runs[idx_pn + 1][1] == '\x1f':
                frontera = idx_pn + 2
            elif idx_pn > 0 and runs[idx_pn - 1][1] == '\x1f':
                # el regex se llevo la primera letra de la descripcion
                # (US, UK, PCB...): el P/N termina antes del separador
                frontera = idx_pn
    pn_runs = []
    desc_runs = []
    for i, (x, t, pos) in enumerate(runs):
        if t == '\x1f':
            continue
        if frontera is not None:
            (pn_runs if i < frontera else desc_runs).append((x, t, pos))
        elif x < desc_x - 12:
            pn_runs.append((x, t, pos))
        else:
            desc_runs.append((x, t, pos))
    return item, designador, pn_runs, desc_runs, qty


def buscar_pns(texto):
    """P/Ns del texto, separando la letra inicial de la descripcion.

    En los IPL el P/N y la descripcion a veces van pegados
    ('234116Adapter Plate'); si el match termina en letra y le sigue una
    minuscula, esa letra pertenece a la descripcion.
    """
    resultados = []
    for m in PAT_PN.finditer(texto):
        pn = m.group(0)
        ini, fin = m.start(), m.end()
        if pn[-1].isalpha():
            siguiente = texto[fin] if fin < len(texto) else ''
            if siguiente.islower():
                # '234116Adapter' -> '234116' + 'Adapter'
                pn = pn[:-1]
                fin -= 1
            elif siguiente.isupper() and pn[-1] != 'W':
                # 'SP500096PCB 3' / '399251US 120V': la letra final es
                # el inicio de la descripcion, no un sufijo del P/N
                pn = pn[:-1]
                fin -= 1
        resultados.append((pn, ini, fin))
    return resultados


def pns_de_runs(runs):
    """Extrae P/Ns y calificadores de un conjunto de corridas."""
    texto = ''.join(t for _, t, _ in runs)
    return [pn for pn, _, _ in buscar_pns(texto)], texto


def normalizar_calificador(texto):
    t = texto.strip()
    t = t.strip('()').strip()
    t = re.sub(r'\bVideojet(?=\d)', 'Videojet ', t)
    t = re.sub(r'/\s+', '/', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def calificadores_de(texto):
    return [normalizar_calificador(q.group(0)) for q in PAT_QUAL.finditer(texto)]


def resto_tras_pn(texto):
    """Texto que sigue al ultimo P/N de una celda P/N.

    Si la celda no contiene un P/N, no es una celda P/N: devolver vacio
    evita que una continuacion entre parentesis ('FG)') se confunda con
    descripcion.
    """
    pns = buscar_pns(texto)
    if not pns:
        return ''
    return texto[pns[-1][2]:].strip()


def limpiar_desc(texto):
    """Normaliza espacios sin inventar contenido."""
    t = re.sub(r'\s+', ' ', texto).strip()
    # espacios perdidos entre palabras (concatenaciones del PDF)
    t = re.sub(r'(?<=[a-z])(?=[A-Z][a-z])', ' ', t)
    t = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', t)
    t = re.sub(r'(?<=\d{2})(?=[A-Z][a-z])', ' ', t)
    t = re.sub(r'(?<=\))(?=[A-Za-z])', ' ', t)
    t = re.sub(r'(?<=[a-z])(?=\()', ' ', t)
    # contracciones frecuentes del PDF (andFront, withMount, ofThe...)
    t = re.sub(r'\b(and|or|of|for|the|with|to|in|on)(?=[A-Z][a-z])',
               r'\1 ', t)
    t = re.sub(r'\bnumbersof\b', 'numbers of', t, flags=re.I)
    t = re.sub(r'\bonpage\b', 'on page', t, flags=re.I)
    t = re.sub(r'\bforpart\b', 'for part', t, flags=re.I)
    t = re.sub(r'\bonthe\b', 'on the', t, flags=re.I)
    t = re.sub(r'\bDisplaydoor\b', 'Display door', t, flags=re.I)
    t = re.sub(r'\bdoorwith\b', 'door with', t, flags=re.I)
    t = re.sub(r'\bwithkeypad\b', 'with keypad', t, flags=re.I)
    t = re.sub(r'\bIP\s+(\d{2})\b', r'IP\1', t, flags=re.I)
    t = re.sub(r'\bpage(?=\d)', 'page ', t, flags=re.I)
    t = re.sub(r'(?<=\d)(?=[A-Z][a-z])', ' ', t)
    t = re.sub(r'\b(RS\s*\d{3})(\d)\s*m\b', r'\1 \2m', t)
    t = re.sub(r'(?<=[a-z])(?=\d{4}\b)', ' ', t)
    t = re.sub(r'(?<=[a-z])(?=[A-Z]{2}\b)', ' ', t)
    t = re.sub(r'\b(\d+)m\b', r'\1 m', t)
    t = re.sub(r'\bCLA\s*Ri\s*TY\b', 'CLARiTY', t, flags=re.I)
    t = re.sub(r'\bC\s+ontrol\b', 'Control', t)
    t = re.sub(r'\bD\s*I\s*N(?=[a-z]{3})', 'DIN ', t)
    t = re.sub(r'\bwith(?=\d)', 'with ', t)
    t = re.sub(r'(?<=[a-z]{3})(?=\d)', ' ', t)
    t = re.sub(r'(?<=\d)(?=[a-z]{2,}\b)', ' ', t)
    t = re.sub(r'(?<=\d)(?=[A-Z]{2,}\b)', ' ', t)
    t = re.sub(r'(?<=[a-z])(?=[A-Z]\b)', ' ', t)
    t = re.sub(r'\bChipand\b', 'Chip and', t, flags=re.I)
    t = re.sub(r'\bfrom(?=[a-z]{2,}\b)', 'from ', t)
    t = re.sub(r'\buse(?=with\b)', 'use ', t, flags=re.I)
    t = re.sub(r'\bBeam(?=fiber\b)', 'Beam ', t)
    t = re.sub(r'\bdetector(?=and\b)', 'detector ', t, flags=re.I)
    t = re.sub(r'\bPrint\s+head\b', 'Printhead', t, flags=re.I)
    t = re.sub(r'\bPhoto\s+[Cc]ell\b', 'Photocell', t, flags=re.I)
    t = re.sub(r'(?<!\d),(?=[A-Za-z0-9])', ', ', t)
    t = re.sub(r'(?<=[a-z])-\s+', ' - ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def unir_desc(partes):
    t = limpiar_desc(' '.join(p for p in partes if p))
    # parentesis desbalanceados por la extraccion (p. ej. "Videojet 1210)")
    while t.count(')') > t.count('('):
        i = t.rfind(')')
        t = t[:i] + t[i + 1:]
    t = re.sub(r'\b(Videojet\s+\d+)\s*$', r'(\1)', t)
    return t


def es_calificador_corto(texto):
    t = limpiar_desc(texto)
    if not t:
        return False
    return bool(re.match(r'^(?:IP\d{2}|UHS(?:\s+HR)?|FG|'
                         r'\(.*\)|Optional for .*|Videojet .*)$', t, re.I))


PALABRAS_VACIAS = {
    'the', 'and', 'with', 'for', 'of', 'to', 'in', 'on', 'a', 'an', 'or',
    'assembly', 'kit', 'unit', 'system', 'module', 'part', 'spare',
}


def palabras_clave(texto):
    return {w.lower() for w in re.findall(r'[A-Za-z]{3,}', texto)
            if w.lower() not in PALABRAS_VACIAS}


def similitud_palabras(a, b):
    """Jaccard de palabras clave (ignora numeros y palabras vacias)."""
    A, B = palabras_clave(a), palabras_clave(b)
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))


def es_variante_desc(desc, desc_fila):
    return similitud_palabras(desc, desc_fila) >= 0.5


def parsear_bloque(num, runs, texto, doc, modelo, titulo_previo, debug=False,
                   bloque_idx=None):
    lineas = agrupar_lineas(runs)
    if not lineas:
        return [], titulo_previo
    item_x, pn_x, desc_x = inferir_columnas(lineas)
    segmentos = segmentos_de_tabla(lineas)
    y_tope = max((yh for yh, _, _ in segmentos), default=None)
    if debug:
        print('  item_x=%.1f pn_x=%.1f desc_x=%.1f segmentos=%s'
              % (item_x, pn_x, desc_x, segmentos))
    # pagina impresa (10-26, 11-8, ...)
    pagina = None
    for linea in lineas:
        t = texto_de_linea(linea).strip()
        m = re.match(r'^(\d{1,2}-\d{1,3})\b', t)
        if m:
            pagina = m.group(1)
            break
    filas = []
    fila = None
    ultimo_pn = None
    grupo_actual = None
    conjunto_actual = None
    designador_pendiente = None
    notas_grupo = []
    titulo_actual = titulo_previo
    pn_continuacion = None
    nota_actual = None

    def cerrar_fila():
        nonlocal fila
        if fila is not None:
            filas.append(fila)
            fila = None

    def nueva_fila(y, item, designador, desc, qty, tabla, tipo, grupo, conjunto):
        nonlocal fila, ultimo_pn, pn_continuacion
        cerrar_fila()
        fila = {
            'y': y,
            'item': item,
            'designador': designador,
            'desc_partes': [desc] if desc else [],
            'qty': qty,
            'tabla': tabla,
            'tipo': tipo,
            'grupo': grupo,
            'conjunto': conjunto,
            'pns': [],
            'notas': [],
            'bloque': bloque_idx if bloque_idx is not None else num,
            'objeto': num,
            'pagina': pagina,
            'documento': doc,
            'modelo': modelo,
        }
        ultimo_pn = None
        pn_continuacion = None

    def agregar_pn(pn, calificadores=None, desc_extra=None, tipo=None,
                   reemplaza=False):
        nonlocal ultimo_pn, pn_continuacion
        if fila is None:
            return
        limpio = pn.strip()
        no_mostrado = limpio.endswith('*')
        limpio = limpio.rstrip('*')
        reg = {
            'pn': limpio,
            'calificadores': list(calificadores or []),
            'desc_extra': desc_extra or '',
            'reemplaza_desc': bool(reemplaza),
            'tipo': tipo or fila['tipo'],
            'no_mostrado_en_figura': no_mostrado,
        }
        # si el mismo P/N ya esta en la fila, solo completar datos
        for existente in fila['pns']:
            if existente['pn'] == limpio:
                for c in reg['calificadores']:
                    if c not in existente['calificadores']:
                        existente['calificadores'].append(c)
                if reg['desc_extra'] and not existente['desc_extra']:
                    existente['desc_extra'] = reg['desc_extra']
                    existente['reemplaza_desc'] = reg['reemplaza_desc']
                ultimo_pn = existente
                return
        fila['pns'].append(reg)
        ultimo_pn = reg
        pn_continuacion = None

    for linea in lineas:
        y = linea['y']
        texto_linea = texto_de_linea(linea).strip()
        if not texto_linea:
            continue
        if y_tope is not None and y > y_tope + 2:
            # figura o etiqueta por encima de la cabecera de la tabla
            continue
        if es_header_pie(texto_linea):
            continue
        if es_tabla_header(texto_linea):
            continue
        if es_titulo_tabla(texto_linea):
            m = PAT_TABLA.match(texto_linea)
            titulo_actual = 'Table %s: %s' % (m.group(1), m.group(2).strip())
            continue
        if PAT_TITULO_CAP.match(texto_linea):
            continue
        # notas de tabla (Refer to..., See Table...)
        if PAT_NOTA.match(texto_linea):
            nota = limpiar_desc(texto_linea)
            if fila is not None:
                fila['notas'].append(nota)
                nota_actual = {'texto': nota, 'y': y, 'fila': fila,
                               'indice': len(fila['notas']) - 1}
            else:
                notas_grupo.append(nota)
                nota_actual = {'texto': nota, 'y': y, 'fila': None,
                               'indice': None}
            continue

        item, designador, pn_runs, desc_runs, qty = clasificar_linea(
            linea, item_x, pn_x, desc_x)
        texto_pn = ''.join(t for _, t, _ in pn_runs)
        texto_desc = ''.join(t for _, t, _ in desc_runs)
        pns, _ = pns_de_runs(pn_runs)
        califs_pn = calificadores_de(texto_pn)
        desc_limpia = limpiar_desc(texto_desc)
        resto_pn = resto_tras_pn(texto_pn)
        if resto_pn:
            if resto_pn.startswith('('):
                if not califs_pn:
                    califs_pn = [normalizar_calificador(resto_pn)]
            else:
                # texto de descripcion pegado al P/N en la misma celda
                desc_limpia = limpiar_desc(resto_pn + ' ' + desc_limpia)
        desc_limpia = limpiar_desc(desc_limpia)

        # continuacion de una nota (linea de descripcion sin item/P/N/qty)
        if (nota_actual is not None and not item and not pns and not qty
                and not designador and desc_limpia
                and 0 <= (nota_actual['y'] - y) <= 16):
            nota_actual['texto'] = limpiar_desc(
                nota_actual['texto'] + ' ' + desc_limpia)
            nota_actual['y'] = y
            if nota_actual['fila'] is not None:
                nota_actual['fila']['notas'][nota_actual['indice']] = \
                    nota_actual['texto']
            continue
        nota_actual = None

        # continuacion de un P/N entre parentesis partido en dos lineas
        if (pn_continuacion is not None and not pns and not item
                and not desc_limpia and texto_pn.strip()):
            if pn_continuacion['calificadores']:
                ult = pn_continuacion['calificadores'][-1]
                pn_continuacion['calificadores'][-1] = \
                    normalizar_calificador(ult + ' ' + texto_pn.strip())
            else:
                pn_continuacion['calificadores'].append(
                    normalizar_calificador(texto_pn))
            pn_continuacion = None
            continue

        # linea solo designador
        if designador and not item and not pns and not desc_limpia and not qty:
            designador_pendiente = designador
            continue

        # linea de nota entre parentesis (See Table...)
        if (desc_limpia.startswith('(') and re.search(r'\bSee\b', desc_limpia, re.I)
                and not item and not pns and not qty):
            if fila is not None:
                fila['notas'].append(desc_limpia)
            continue

        tabla = titulo_de(y, segmentos) or titulo_actual
        if tabla:
            titulo_actual = tabla

        # 1) fila con item (parte o item sin P/N)
        if item is not None:
            tipo = 'parte' if pns else 'sin-pn'
            grupo = nombre_tabla(tabla) or grupo_actual
            conjunto = grupo
            nueva_fila(y, item, designador or designador_pendiente, desc_limpia,
                       qty, tabla, tipo, grupo, conjunto)
            designador_pendiente = None
            for pn in pns:
                agregar_pn(pn, califs_pn)
            if texto_pn.count('(') > texto_pn.count(')'):
                pn_continuacion = ultimo_pn
            continue

        # 2) designador + descripcion (cabecera de conjunto)
        if designador and desc_limpia and not pns and not qty:
            grupo_actual = nombre_tabla(tabla) or desc_limpia
            conjunto_actual = desc_limpia
            nueva_fila(y, None, designador, desc_limpia, None, tabla,
                       'conjunto', grupo_actual, conjunto_actual)
            designador_pendiente = None
            continue

        # 3) P/N + descripcion (cabecera de conjunto con P/N o variante)
        if pns and desc_limpia and not item and not qty:
            desc_fila = unir_desc(fila['desc_partes']) if fila else ''
            if es_calificador_corto(desc_limpia):
                # variante de la fila actual (IP65, IP55, UHS...)
                if fila is not None:
                    if fila['tipo'] == 'conjunto' and not fila['pns']:
                        # el P/N del propio conjunto viene en la linea
                        # siguiente con su calificador (399238 | IP65)
                        for pn in pns:
                            agregar_pn(pn, califs_pn + [desc_limpia],
                                       tipo='conjunto')
                    else:
                        for pn in pns:
                            agregar_pn(pn, califs_pn + [desc_limpia],
                                       tipo='variante')
                continue
            if (fila is not None and not designador
                    and not designador_pendiente
                    and es_variante_desc(desc_limpia, desc_fila)):
                # variante con descripcion propia (PCB 0 vs PCB 1, etc.)
                for pn in pns:
                    agregar_pn(pn, califs_pn, desc_extra=desc_limpia,
                               tipo='variante', reemplaza=True)
                if texto_pn.count('(') > texto_pn.count(')'):
                    pn_continuacion = ultimo_pn
                continue
            # cabecera de conjunto (con o sin designador)
            grupo_actual = nombre_tabla(tabla) or grupo_actual
            conjunto_actual = desc_limpia
            nueva_fila(y, None, designador or designador_pendiente,
                       desc_limpia, None, tabla, 'conjunto',
                       grupo_actual, conjunto_actual)
            designador_pendiente = None
            for pn in pns:
                agregar_pn(pn, califs_pn, tipo='conjunto')
            if texto_pn.count('(') > texto_pn.count(')'):
                pn_continuacion = ultimo_pn
            continue

        # 3b) P/N + descripcion + cantidad sin item (fila suelta)
        if pns and desc_limpia and not item and qty:
            if fila is not None and es_calificador_corto(desc_limpia):
                for pn in pns:
                    agregar_pn(pn, califs_pn + [desc_limpia],
                               tipo='variante')
                continue
            grupo = nombre_tabla(tabla) or grupo_actual
            nueva_fila(y, None, designador or designador_pendiente,
                       desc_limpia, qty, tabla, 'parte', grupo, grupo)
            designador_pendiente = None
            for pn in pns:
                agregar_pn(pn, califs_pn, tipo='parte')
            if texto_pn.count('(') > texto_pn.count(')'):
                pn_continuacion = ultimo_pn
            continue

        # 4) solo P/N (continuacion o variante de la fila actual)
        if pns and not desc_limpia and not item and not qty:
            if fila is not None:
                # un P/N adicional en la misma celda comparte la
                # descripcion propia de la variante anterior
                heredar = ''
                reemplaza = False
                if (ultimo_pn is not None and ultimo_pn.get('desc_extra')
                        and ultimo_pn.get('reemplaza_desc')):
                    heredar = ultimo_pn['desc_extra']
                    reemplaza = True
                for pn in pns:
                    agregar_pn(pn, califs_pn, desc_extra=heredar,
                               reemplaza=reemplaza)
            else:
                # P/N suelto antes de cualquier ancla: abrir fila de conjunto
                nueva_fila(y, None, designador_pendiente, '', None, tabla,
                           'conjunto', grupo_actual, conjunto_actual)
                designador_pendiente = None
                for pn in pns:
                    agregar_pn(pn, califs_pn, tipo='conjunto')
            # si el calificador quedo abierto, preparar continuacion
            if texto_pn.count('(') > texto_pn.count(')'):
                pn_continuacion = ultimo_pn
            continue

        # 5) solo calificadores en la columna P/N (Videojet 1510), etc.)
        if califs_pn and not pns and not desc_limpia and not item and not qty:
            if fila is not None and ultimo_pn is not None:
                for c in califs_pn:
                    ultimo_pn['calificadores'].append(c)
            continue

        # 6) solo descripcion: continuacion de la fila o cabecera sin designador
        if desc_limpia and not pns and not item and not qty:
            gap = (fila['y'] - y) if fila is not None else 999
            if (fila is not None and not designador
                    and (0 <= gap <= 18
                         or (gap <= 32 and es_continuacion_desc(desc_limpia)))):
                fila['desc_partes'].append(desc_limpia)
            elif (fila is not None and gap > 18
                  and es_titulo_seccion(desc_limpia)):
                # cabecera de seccion: agrupa, no es una parte
                grupo_actual = desc_limpia
                conjunto_actual = desc_limpia
                cerrar_fila()
                designador_pendiente = None
            else:
                grupo_actual = nombre_tabla(tabla) or desc_limpia
                conjunto_actual = desc_limpia
                nueva_fila(y, None, designador or designador_pendiente,
                           desc_limpia, None, tabla, 'conjunto',
                           grupo_actual, conjunto_actual)
                designador_pendiente = None
            continue

        # 7) linea con item y descripcion vacia: la descripcion viene despues
        if item is not None and not desc_limpia:
            continue

    cerrar_fila()
    return filas, titulo_actual


def construir_registros(filas):
    registros = []
    for fila in filas:
        desc = unir_desc(fila['desc_partes'])
        if not fila['pns']:
            if fila['item'] and desc:
                registros.append({
                    'pn': None,
                    'descripcion': desc,
                    'item': fila['item'],
                    'designador': fila['designador'],
                    'cantidad': fila['qty'],
                    'tabla': fila['tabla'],
                    'grupo': fila['grupo'],
                    'conjunto': fila['conjunto'],
                    'tipo': 'sin-pn',
                    'estado': 'sin-pn',
                    'documento': fila['documento'],
                    'modelo': fila['modelo'],
                    'bloque': fila['bloque'],
                    'objeto': fila.get('objeto'),
                    'pagina': fila['pagina'],
                    'notas': fila['notas'],
                })
            continue
        for reg in fila['pns']:
            if reg.get('reemplaza_desc') and reg['desc_extra']:
                # la descripcion propia de la variante sustituye a la base
                partes_desc = [reg['desc_extra']]
            else:
                partes_desc = [desc]
                if reg['desc_extra']:
                    partes_desc.append(reg['desc_extra'])
            for c in reg['calificadores']:
                if c and not re.search(r'\bSee\b', c, re.I):
                    if c.lower() in ' '.join(partes_desc).lower():
                        continue
                    partes_desc.append('(%s)' % c)
            descripcion = unir_desc(partes_desc)
            registros.append({
                'pn': reg['pn'],
                'descripcion': descripcion,
                'item': fila['item'],
                'designador': fila['designador'],
                'cantidad': fila['qty'],
                'tabla': fila['tabla'],
                'grupo': fila['grupo'],
                'conjunto': desc if fila['tipo'] == 'conjunto'
                            else fila['conjunto'],
                'tipo': reg['tipo'],
                'estado': 'borrador',
                'documento': fila['documento'],
                'modelo': fila['modelo'],
                'bloque': fila['bloque'],
                'objeto': fila.get('objeto'),
                'pagina': fila['pagina'],
                'no_mostrado_en_figura': reg['no_mostrado_en_figura'],
                'notas': fila['notas'],
                'idiomas': fila.get('idiomas'),
            })
    return registros


def normalizar_desc(texto):
    t = limpiar_desc(texto).lower()
    t = re.sub(r'\([^)]*\)', ' ', t)
    t = re.sub(r'[^a-z0-9]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def desc_compatible(a, b):
    na, nb = normalizar_desc(a), normalizar_desc(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    return similitud_palabras(na, nb) >= 0.8


def consolidar(registros):
    por_pn = {}
    sin_pn = []
    for reg in registros:
        if reg['pn'] is None:
            sin_pn.append(reg)
            continue
        por_pn.setdefault(reg['pn'], []).append(reg)
    partes = []
    for pn, regs in sorted(por_pn.items()):
        descs = {}
        for r in regs:
            d = r['descripcion']
            if not d:
                continue
            clave = normalizar_desc(d)
            if not clave:
                continue
            descs.setdefault(clave, []).append(d)
        # descripcion canonica: la mas repetida; a igualdad, la mas completa
        canonica = ''
        if descs:
            lista = sorted(descs.items(),
                           key=lambda kv: (-len(kv[1]), -len(kv[1][0])))
            canonica = sorted(lista[0][1], key=len, reverse=True)[0]
        docs = {}
        for r in regs:
            docs.setdefault(r['documento'], []).append(r)
        # verificado: >=2 documentos con descripcion compatible
        docs_con_desc = set()
        for r in regs:
            if canonica and desc_compatible(r['descripcion'], canonica):
                docs_con_desc.add(r['documento'])
        estado = 'verificado' if len(docs_con_desc) >= 2 else 'borrador'
        if not canonica:
            estado = 'por-definir'
        apariciones = []
        vistos = set()
        for r in regs:
            clave = (r['documento'], r['bloque'], r['item'], r['cantidad'],
                     r['descripcion'])
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
                'bloque': r['bloque'],
                'pagina': r['pagina'],
                'no_mostrado_en_figura': r.get('no_mostrado_en_figura', False),
            })
        variantes = sorted({d for r in regs for d in [r['descripcion']] if d})
        # descripciones incompatibles para el mismo P/N: no se puede dar
        # por verificado aunque la mayoria de documentos coincida
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
        if conflicto and estado == 'verificado':
            estado = 'borrador'
        partes.append({
            'pn': pn,
            'descripcion': canonica,
            'descripciones': variantes,
            'calificadores': sorted({c for r in regs
                                     for c in re.findall(r'\(([^)]*)\)', r['descripcion'])}),
            'tipo': sorted({r['tipo'] for r in regs}),
            'estado': estado,
            'conflicto_descripciones': conflicto,
            'documentos': sorted(docs.keys()),
            'modelos': sorted({r['modelo'] for r in regs}),
            'apariciones': apariciones,
        })
    return partes, sin_pn


def detectar_header_idiomas(runs):
    """Devuelve la y de la cabecera de la tabla de idiomas, o None.

    Ademas de la tabla clasica P/N | Languages, el IPL 1620E trae una
    tabla P/N | Display Door with Keypad (EXCEL) | Country.  Ambas son
    tablas de variantes sin item ni cantidad y comparten el mismo parser.
    """
    for linea in agrupar_lineas(runs):
        p = plano(texto_de_linea(linea)).lower()
        if 'partnumber' in p and ('languages' in p or 'country' in p):
            return linea['y']
    return None


def parsear_tabla_idiomas(num, runs, doc, modelo, y_header, bloque_idx=None):
    """Tabla 10-4: P/N | descripcion | idiomas (sin item ni cantidad)."""
    lineas = agrupar_lineas(runs)
    pagina = None
    for linea in lineas:
        m = re.match(r'^(\d{1,2}-\d{1,3})\b', texto_de_linea(linea).strip())
        if m:
            pagina = m.group(1)
            break
    filas = []
    actual = None
    for linea in lineas:
        if linea['y'] >= y_header - 1:
            continue
        texto = texto_de_linea(linea).strip()
        if not texto or es_header_pie(texto):
            continue
        if es_titulo_tabla(texto):
            continue
        textos = [limpiar_desc(texto_de_celda(c))
                  for c in dividir_celdas(linea)]
        textos = [t for t in textos if t]
        if not textos:
            continue
        if PAT_PN_ESTRICTO.match(textos[0]):
            if actual is not None:
                filas.append(actual)
            pn = textos[0].rstrip('*')
            desc = textos[1] if len(textos) > 1 else ''
            idiomas = textos[2] if len(textos) > 2 else ''
            actual = {
                'y': linea['y'],
                'item': None,
                'designador': None,
                'desc_partes': [desc],
                'qty': None,
                'tabla': 'Table 10-4: Display Door with Keypad',
                'tipo': 'parte',
                'grupo': 'Display Door with Keypad',
                'conjunto': 'Display Door with Keypad',
                'pns': [{
                    'pn': pn,
                    'calificadores': [],
                    'desc_extra': '',
                    'reemplaza_desc': False,
                    'tipo': 'parte',
                    'no_mostrado_en_figura': False,
                }],
                'notas': [],
                'idiomas': [idiomas] if idiomas else [],
                'bloque': bloque_idx if bloque_idx is not None else num,
                'objeto': num,
                'pagina': pagina,
                'documento': doc,
                'modelo': modelo,
            }
        elif actual is not None:
            actual['idiomas'].append(' '.join(textos))
    if actual is not None:
        filas.append(actual)
    for fila in filas:
        if fila['idiomas']:
            fila['idiomas'] = unir_desc(fila['idiomas'])
    return filas


def procesar_documento(nombre, modelo, debug=False, solo_bloque=None):
    ruta = os.path.join(CARPETA, nombre)
    bloques, _ = L.extraer_runs_visual(ruta)
    filas_todas = []
    titulo = None
    for idx, (num, runs, texto) in enumerate(bloques):
        if solo_bloque is not None and idx != solo_bloque:
            continue
        plano_txt = plano(texto)
        if not ('ItemNumber' in plano_txt and 'P/N' in plano_txt
                and 'Description' in plano_txt):
            continue
        if debug:
            print('=' * 80)
            print(nombre, 'bloque', idx, 'obj', num)
        y_idiomas = detectar_header_idiomas(runs)
        if y_idiomas is not None:
            runs_arriba = [r for r in runs if r[0] > y_idiomas]
            runs_idiomas = [r for r in runs if r[0] < y_idiomas]
            filas, titulo = parsear_bloque(num, runs_arriba, texto, nombre,
                                           modelo, titulo, debug=debug,
                                           bloque_idx=idx)
            filas_idiomas = parsear_tabla_idiomas(num, runs_idiomas, nombre,
                                                  modelo, y_idiomas,
                                                  bloque_idx=idx)
            filas = filas + filas_idiomas
        else:
            filas, titulo = parsear_bloque(num, runs, texto, nombre, modelo,
                                           titulo, debug=debug,
                                           bloque_idx=idx)
        filas_todas.extend(filas)
        if debug:
            for f in filas:
                print('  %7.1f item=%-4s desig=%-2s qty=%-3s tipo=%-9s '
                      'pn=%-28s desc=%s'
                      % (f['y'], f['item'] or '', f['designador'] or '',
                         f['qty'] or '', f['tipo'],
                         ','.join(p['pn'] for p in f['pns'])[:28],
                         unir_desc(f['desc_partes'])[:70]))
    return filas_todas


def main():
    debug = '--debug' in sys.argv
    solo = None
    bloque_debug = None
    if debug:
        args = [a for a in sys.argv[1:] if a != '--debug']
        if args:
            solo = args[0]
        if len(args) > 1:
            bloque_debug = int(args[1])
    todos = []
    for nombre, modelo in DOCUMENTOS:
        if solo and solo not in nombre:
            continue
        print('Procesando', nombre)
        filas = procesar_documento(nombre, modelo, debug=debug,
                                    solo_bloque=bloque_debug)
        regs = construir_registros(filas)
        print('  filas=%d registros=%d pns=%d'
              % (len(filas), len(regs), len({r['pn'] for r in regs if r['pn']})))
        todos.extend(regs)
    if debug:
        return
    partes, sin_pn = consolidar(todos)
    resumen = {
        'documentos': len(DOCUMENTOS),
        'registros': len(todos),
        'partes': len(partes),
        'verificadas': sum(1 for p in partes if p['estado'] == 'verificado'),
        'borradores': sum(1 for p in partes if p['estado'] == 'borrador'),
        'por_definir': sum(1 for p in partes if p['estado'] == 'por-definir'),
        'items_sin_pn': len(sin_pn),
    }
    datos = {
        'generado': '2026-11-10',
        'fuente': ('Illustrated Parts Lists Videojet 1000VJ (%d documentos '
                   'legibles)' % len(DOCUMENTOS)),
        'metodo': 'Parser v5.1 por lineas-ancla y celdas reales del PDF',
        'resumen': resumen,
        'documentos': [
            {'archivo': n, 'modelo': m} for n, m in DOCUMENTOS
        ],
        'partes': partes,
        'items_sin_pn': sin_pn,
    }
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('OK', SALIDA)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
