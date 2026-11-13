# -*- coding: utf-8 -*-
"""Extrae las velocidades CIJ de los «CIJ Line Speed Calculator v9.7».

Recorre los PDF simples (no `_EXPERT`) de la carpeta `velocidades cij`, hace OCR
de la pagina 1 con Windows.Data.Pdf + Windows.Media.Ocr (sin instalar nada) y
consolida modelo, boquilla, fuente, velocidad nominal [m/min] y caracteres por
segundo (o columnas por segundo en los calculadores Expert).

Honestidad del dato:
  - El valor se lee por OCR de un PDF oficial: queda `borrador-decodificado` y
    conserva la evidencia (archivo + lineas OCR).
  - Si el OCR y el nombre del archivo discrepan en boquilla, se conserva el
    valor del OCR (evidencia visual) y se marca `conflicto_boquilla`.
  - En la carpeta `1880_UHS-boquilla 50` los PDF dicen 50 um aunque el nombre
    diga `_60_`: la carpeta corrige esa variante UHS. Los HR conservan su 40 um.
  - Si dos calculadores repiten la misma combinacion con valores distintos, se
    marca `conflicto` y no se elige uno a mano.
  - La tabla resumen `v9.7z.pdf` (8 paginas, sin cabecera de calculador) se
    registra como descartada, no como calculador.

Uso:
  python -u tools/extraer_velocidades_cij.py --limite 3
  python -u tools/extraer_velocidades_cij.py
  python -u tools/extraer_velocidades_cij.py --reanudar
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import ocr_pdf_paginas as O  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

BASE_POR_DEFECTO = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
                    r'\DOCUMENTOS VIDEOJET ETERNOSSSSSSSSSSSSSSSSSSSSS'
                    r'\velocidades cij')
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
CACHE = os.path.join(EXTRACCION, 'velocidades_cij_ocr')
SALIDA = os.path.join(RAIZ, 'datos', 'cij_velocidades.json')
CSV_SALIDA = os.path.join(RAIZ, 'datos', 'analisis', 'velocidades_cij.csv')
ANCHO = 1600
IDIOMA = 'es-MX'
BOQUILLAS = (40, 50, 60, 70)


def norm(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


def numero_es(valor):
    """Convierte un numero con formato es (1.778 = 1778; 97,7 = 97.7)."""
    t = norm(valor).replace(' ', '')
    if not t:
        return None
    t = re.sub(r'[^0-9.,-]', '', t)
    if not t:
        return None
    if ',' in t and '.' in t:
        # El ultimo separador manda: 1.234,5 o 1,234.5
        if t.rfind(',') > t.rfind('.'):
            t = t.replace('.', '').replace(',', '.')
        else:
            t = t.replace(',', '')
    elif ',' in t:
        t = t.replace(',', '.')
    elif re.search(r'^\d{1,3}(\.\d{3})+$', t):
        t = t.replace('.', '')
    try:
        return float(t)
    except ValueError:
        return None


def valor_derecha(lineas, etiqueta, tolerancia=14):
    """Devuelve el texto de la celda a la derecha de una etiqueta."""
    objetivo = None
    for linea in lineas:
        if norm(linea.get('texto', '')).lower().startswith(etiqueta.lower()):
            objetivo = linea
            break
    if not objetivo:
        return None
    y = objetivo.get('y', 0)
    x = objetivo.get('x', 0)
    candidatos = [l for l in lineas
                  if abs(l.get('y', 0) - y) <= tolerancia
                  and l.get('x', 0) > x + 80]
    if not candidatos:
        return None
    candidatos.sort(key=lambda l: l.get('x', 0))
    return norm(candidatos[0].get('texto', ''))


def valor_derecha_desde(lineas, etiqueta, y_min):
    """Como valor_derecha, pero busca la etiqueta mas cercana por debajo de y_min."""
    candidatos = []
    for linea in lineas:
        if norm(linea.get('texto', '')).lower().startswith(etiqueta.lower()):
            if linea.get('y', 0) >= y_min:
                candidatos.append(linea)
    if not candidatos:
        return None
    objetivo = min(candidatos, key=lambda l: l.get('y', 0))
    y = objetivo.get('y', 0)
    x = objetivo.get('x', 0)
    valores = [l for l in lineas
               if abs(l.get('y', 0) - y) <= 14 and l.get('x', 0) > x + 80]
    if not valores:
        return None
    valores.sort(key=lambda l: l.get('x', 0))
    return norm(valores[0].get('texto', ''))


def _tokens_nombre(nombre):
    """Separa el nombre del calculador en tokens utiles."""
    tallo = os.path.splitext(os.path.basename(nombre))[0]
    tallo = re.sub(r'^CIJ Line Speed Calculator v9\.7[._]?', '', tallo,
                   flags=re.I)
    tallo = tallo.lstrip('._ ')
    return [t for t in tallo.split('_') if t]


def _indice_fuente(tokens):
    """Indice del primer token que empieza una fuente (5x5, 10x16, 21 QR...)."""
    for i, token in enumerate(tokens):
        bajo = token.lower()
        if re.match(r'^\d{1,2}x\d{1,2}', bajo):
            return i
        if (re.match(r'^\d{2}$', bajo) and i + 1 < len(tokens)
                and tokens[i + 1].lower() in ('qr', 'code', 'qrcode')):
            return i
    return None


def _indice_boquilla(tokens, indice_fuente):
    for i in range(indice_fuente - 1, -1, -1):
        if tokens[i] in {str(b) for b in BOQUILLAS}:
            return i
    return None


def _unir_modelo(tokens):
    """Une tokens numericos con guion y los de letras con espacio."""
    if not tokens:
        return ''
    salida = tokens[0]
    for token in tokens[1:]:
        ultimo = salida.split()[-1]
        if re.match(r'^\d+$', ultimo) and re.match(r'^\d+$', token):
            salida += '-' + token
        else:
            salida += ' ' + token
    return salida


def normalizar_modelo(texto):
    t = norm(texto).upper()
    t = t.replace('_', '-').replace('/', '-')
    t = re.sub(r'\s*-\s*', '-', t)
    return re.sub(r'\s+', ' ', t).strip()


def canon_modelo(texto):
    """Forma canonica para comparar modelos: separadores equivalentes."""
    t = normalizar_modelo(texto)
    t = re.sub(r'[\s/_-]+', '-', t)
    return re.sub(r'-+', '-', t).strip('-')


def paginas_pdf(pdf):
    """Numero de paginas del PDF (se usa solo al descartar una tabla resumen)."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix='pdf_pag_') as tmp:
        aviso = O.renderizar(pdf, 1, os.path.join(tmp, 'p1.png'), 200, 30)
    m = re.search(r'\((\d+)\s+paginas\)', aviso or '')
    return int(m.group(1)) if m else None


def normalizar_fuente(texto):
    t = norm(texto).lower()
    t = t.replace('_', ' ').replace('-', ' ')
    t = t.replace('singlepdf', 'single')
    t = re.sub(r'\bpdf\b', ' ', t)
    t = re.sub(r'\bsingl\b', 'single', t)
    return re.sub(r'\s+', ' ', t).strip()


def modelo_desde_nombre(nombre):
    tokens = _tokens_nombre(nombre)
    indice = _indice_fuente(tokens)
    if indice is None:
        return ''
    boquilla = _indice_boquilla(tokens, indice)
    modelo = _unir_modelo(tokens[:boquilla] if boquilla is not None
                          else tokens[:indice])
    return normalizar_modelo(modelo)


def boquilla_desde_nombre(nombre):
    tokens = _tokens_nombre(nombre)
    indice = _indice_fuente(tokens)
    if indice is None:
        return None
    boquilla = _indice_boquilla(tokens, indice)
    return int(tokens[boquilla]) if boquilla is not None else None


def fuente_desde_nombre(nombre):
    tokens = _tokens_nombre(nombre)
    indice = _indice_fuente(tokens)
    if indice is None:
        return ''
    return normalizar_fuente(' '.join(tokens[indice:]))


def boquilla_desde_carpeta(pdf):
    carpeta = os.path.basename(os.path.dirname(pdf))
    m = re.search(r'boquilla\s*(\d{2,3})', carpeta, re.I)
    if m and int(m.group(1)) in BOQUILLAS:
        return int(m.group(1))
    return None


def boquilla_desde_ocr(lineas):
    valor = valor_derecha(lineas, 'Nozzle Size')
    if not valor:
        return None
    digitos = re.sub(r'\D', '', valor)
    for conocido in BOQUILLAS:
        if digitos.startswith(str(conocido)):
            return conocido
    return None


def fuente_desde_ocr(lineas):
    for etiqueta in ('Font - Lines', 'Font - Cines', 'Font Lines'):
        valor = valor_derecha(lineas, etiqueta)
        if valor:
            return normalizar_fuente(valor)
    return ''


def clave_fuente(fuente):
    t = norm(fuente).lower()
    return re.sub(r'[^a-z0-9]+', '_', t).strip('_')


def escenarios(lineas):
    """Recoge los escenarios de ejemplo impresos en el calculador."""
    salida = []
    actual = None
    for linea in lineas:
        t = norm(linea.get('texto', ''))
        m = re.match(r'^Scenario\s+(\d+)$', t, re.I)
        if m:
            actual = {'numero': int(m.group(1)), 'valores': {},
                      'y': linea.get('y', 0)}
            salida.append(actual)
            continue
        if not actual:
            continue
        etiquetas = {
            'No. of Characters (per line)': 'caracteres_por_linea',
            'No. of Columns (Strokes per Message)': 'columnas_por_mensaje',
            'Print Width [mm]': 'ancho_impresion_mm',
            'Max. Line Speed [m/min]': 'velocidad_maxima_m_min',
            'Line Speed [m/min]': 'velocidad_linea_m_min',
            'Min. Print Width [mm]': 'ancho_minimo_mm',
            'Max. No. of Characters (per line)': 'max_caracteres_por_linea',
        }
        for etiqueta, clave in etiquetas.items():
            if t.lower().startswith(etiqueta.lower()) and clave not in actual['valores']:
                valor = valor_derecha_desde(lineas, etiqueta, actual['y'])
                actual['valores'][clave] = numero_es(valor) if valor else None
                break
    for e in salida:
        e.pop('y', None)
    return [e for e in salida if any(v is not None for v in e['valores'].values())]


def ocr_pagina(pdf, ruta_cache, reanudar):
    if reanudar and os.path.exists(ruta_cache):
        try:
            with open(ruta_cache, 'r', encoding='utf-8') as f:
                return json.load(f), True
        except (ValueError, OSError):
            pass
    png = ruta_cache + '.png'
    O.renderizar(pdf, 1, png, ANCHO, 60)
    datos = O.ocr(png, ruta_cache + '.json', IDIOMA, 90)
    datos['pagina'] = 1
    datos['ancho_render'] = ANCHO
    O.guardar(ruta_cache, datos)
    try:
        os.remove(png)
        os.remove(ruta_cache + '.json')
    except OSError:
        pass
    return datos, False


def main():
    global ANCHO
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=BASE_POR_DEFECTO)
    ap.add_argument('--limite', type=int, default=0)
    ap.add_argument('--reanudar', action='store_true')
    ap.add_argument('--ancho', type=int, default=ANCHO)
    args = ap.parse_args()
    ANCHO = args.ancho

    if not os.path.isdir(args.base):
        print('FALLO: no existe la carpeta %s' % args.base)
        return 2
    pdfs = []
    for raiz, _dirs, archivos in os.walk(args.base):
        for nombre in archivos:
            if not nombre.lower().endswith('.pdf'):
                continue
            if 'line speed calculator' not in nombre.lower():
                continue
            if '_expert' in nombre.lower():
                continue
            pdfs.append(os.path.join(raiz, nombre))
    pdfs.sort()
    if args.limite:
        pdfs = pdfs[:args.limite]
    print('calculadores simples: %d' % len(pdfs), flush=True)

    os.makedirs(CACHE, exist_ok=True)
    entradas = []
    errores = []
    descartados = []
    for i, pdf in enumerate(pdfs, 1):
        nombre = os.path.basename(pdf)
        slug = re.sub(r'[^a-z0-9]+', '_', nombre.lower()).strip('_')[:120]
        ruta_cache = os.path.join(CACHE, slug + '.json')
        try:
            datos, cacheado = ocr_pagina(pdf, ruta_cache, args.reanudar)
        except Exception as exc:  # noqa: BLE001 - el lote no debe abortar
            aviso = str(exc).encode('ascii', 'replace').decode('ascii')
            print('  [%d/%d] %s: ERROR %s' % (i, len(pdfs), nombre, aviso[:160]),
                  flush=True)
            errores.append({'archivo': os.path.relpath(pdf, args.base),
                            'error': str(exc)[:300]})
            continue
        lineas = datos.get('lineas', [])
        modelo_ocr_txt = valor_derecha(lineas, 'Printer Type')
        modelo_ocr = normalizar_modelo(modelo_ocr_txt)
        if not (modelo_ocr and re.search(r'\d', modelo_ocr)
                and len(modelo_ocr) <= 30
                and not re.search(r'[^A-Z0-9+\- ]', modelo_ocr)):
            modelo_ocr = ''
        modelo_archivo = modelo_desde_nombre(nombre)
        if modelo_archivo and not re.search(r'\d', modelo_archivo):
            modelo_archivo = ''
        modelo = modelo_ocr or modelo_archivo

        boquilla_archivo = boquilla_desde_nombre(nombre)
        boquilla_ocr = boquilla_desde_ocr(lineas)
        boquilla_carpeta = boquilla_desde_carpeta(pdf)
        boquilla = boquilla_ocr or boquilla_archivo or boquilla_carpeta
        # La carpeta `1880_UHS-boquilla 50` corrige los nombres `_60_` de esa
        # variante; los HR conservan su boquilla del nombre.
        if (boquilla_ocr is None and boquilla_carpeta
                and boquilla_archivo
                and boquilla_archivo != boquilla_carpeta
                and 'UHS' in nombre.upper()):
            boquilla = boquilla_carpeta
        conflicto_boquilla = bool(
            (boquilla_ocr and boquilla_archivo
             and boquilla_ocr != boquilla_archivo)
            or (boquilla_ocr is None and boquilla_carpeta and boquilla_archivo
                and boquilla_archivo != boquilla_carpeta
                and 'UHS' in nombre.upper()))

        fuente_ocr = fuente_desde_ocr(lineas)
        fuente_archivo = fuente_desde_nombre(nombre)
        fuente = fuente_ocr or fuente_archivo
        conflicto_fuente = bool(
            fuente_ocr and fuente_archivo and fuente_ocr != fuente_archivo)
        conflicto_modelo = bool(
            modelo_ocr and modelo_archivo
            and canon_modelo(modelo_ocr) != canon_modelo(modelo_archivo))

        vel_txt = valor_derecha(lineas, 'Speed @ nominal cpi')
        cps_txt = valor_derecha(lineas, 'Characters per Sec.')
        cols_txt = valor_derecha(lineas, 'Columns per Sec.')
        velocidad = numero_es(vel_txt)
        cps = numero_es(cps_txt)
        cols = numero_es(cols_txt)
        es_experto = cols is not None or any(
            'expert' in norm(l.get('texto', '')).lower() for l in lineas)

        # La tabla resumen `v9.7z.pdf` no tiene cabecera de calculador y su
        # nombre tampoco aporta modelo ni fuente: se descarta como calculador.
        tiene_cabecera = any(
            norm(l.get('texto', '')).lower().startswith('printer type')
            for l in lineas)
        if (not tiene_cabecera and not modelo and not fuente
                and _indice_fuente(_tokens_nombre(nombre)) is None):
            descartados.append({
                'archivo': os.path.relpath(pdf, args.base),
                'motivo': ('no es un calculador: tabla resumen sin cabecera '
                           'Printer Type/Font'),
                'paginas': paginas_pdf(pdf),
            })
            print('  [%d/%d] %s: DESCARTADO (no es calculador)'
                  % (i, len(pdfs), nombre), flush=True)
            continue

        entrada = {
            'modelo': modelo,
            'modelo_impreso': modelo_ocr_txt or '',
            'boquilla_um': boquilla,
            'fuente': fuente,
            'clave': '%s|%s|%s' % (modelo, boquilla, clave_fuente(fuente)),
            'velocidad_nominal_m_min': velocidad,
            'caracteres_por_segundo': cps,
            'columnas_por_segundo': cols,
            'tipo_calculador': 'experto' if es_experto else 'simple',
            'escenarios': escenarios(lineas),
            'estado': 'borrador-decodificado',
            'origen': 'CIJ Line Speed Calculator v9.7 (PDF oficial)',
            'archivo': os.path.relpath(pdf, args.base),
            'conflicto_boquilla': conflicto_boquilla,
            'conflicto_modelo': conflicto_modelo,
            'conflicto_fuente': conflicto_fuente,
            'evidencia_clave': {
                'modelo_archivo': modelo_archivo,
                'modelo_ocr': modelo_ocr_txt,
                'boquilla_archivo': boquilla_archivo,
                'boquilla_ocr': boquilla_ocr,
                'boquilla_carpeta': boquilla_carpeta,
                'fuente_archivo': fuente_archivo,
                'fuente_ocr': fuente_ocr,
            },
            'evidencia_ocr': {
                'modelo': modelo_ocr_txt,
                'boquilla': valor_derecha(lineas, 'Nozzle Size'),
                'fuente': valor_derecha(lineas, 'Font - Lines')
                          or valor_derecha(lineas, 'Font - Cines'),
                'velocidad': vel_txt,
                'caracteres_por_segundo': cps_txt,
                'columnas_por_segundo': cols_txt,
                'lineas_cabecera': [
                    norm(l.get('texto', '')) for l in lineas
                    if 200 <= l.get('y', 0) <= 430
                ][:16],
            },
        }
        entradas.append(entrada)
        print('  [%d/%d] %s -> %s/%s/%s | %s m/min | c/s=%s cols/s=%s%s%s'
              % (i, len(pdfs), nombre, modelo, boquilla, fuente, velocidad,
                 cps, cols, ' (cache)' if cacheado else '',
                 ' CONFLICTO-BOQUILLA' if conflicto_boquilla else ''),
              flush=True)
        if i % 10 == 0:
            guardar_parcial(entradas, errores, descartados, len(pdfs))

    guardar_parcial(entradas, errores, descartados, len(pdfs))
    print('OK %s | entradas=%d descartados=%d errores=%d'
          % (os.path.relpath(SALIDA, RAIZ), len(entradas), len(descartados),
             len(errores)))
    return 0


def guardar_parcial(entradas, errores, descartados, total):
    """Consolida por clave; solo marca conflicto si dos valores difieren."""
    por_clave = {}
    for e in entradas:
        clave = e['clave']
        actual = por_clave.get(clave)
        if not actual:
            actual = {
                'clave': clave,
                'modelo': e['modelo'],
                'modelo_impreso': e.get('modelo_impreso') or '',
                'boquilla_um': e['boquilla_um'],
                'fuente': e['fuente'],
                'velocidad_nominal_m_min': e['velocidad_nominal_m_min'],
                'caracteres_por_segundo': e['caracteres_por_segundo'],
                'columnas_por_segundo': e['columnas_por_segundo'],
                'tipo_calculador': e['tipo_calculador'],
                'escenarios': e['escenarios'],
                'estado': e['estado'],
                'origen': e['origen'],
                'archivos': [e['archivo']],
                'evidencias_ocr': [e['evidencia_ocr']],
                'evidencias_clave': [e['evidencia_clave']],
                'conflicto': False,
                'conflicto_boquilla': e['conflicto_boquilla'],
                'conflicto_modelo': e['conflicto_modelo'],
                'conflicto_fuente': e['conflicto_fuente'],
            }
            por_clave[clave] = actual
            continue
        actual['archivos'].append(e['archivo'])
        actual['evidencias_ocr'].append(e['evidencia_ocr'])
        actual['evidencias_clave'].append(e['evidencia_clave'])
        if not actual.get('modelo_impreso') and e.get('modelo_impreso'):
            actual['modelo_impreso'] = e['modelo_impreso']
        actual['conflicto_boquilla'] = (actual['conflicto_boquilla']
                                        or e['conflicto_boquilla'])
        actual['conflicto_modelo'] = (actual['conflicto_modelo']
                                      or e['conflicto_modelo'])
        actual['conflicto_fuente'] = (actual['conflicto_fuente']
                                      or e['conflicto_fuente'])
        if e['tipo_calculador'] == 'experto' or e['columnas_por_segundo'] is not None:
            actual['tipo_calculador'] = 'experto'
        campos = ('velocidad_nominal_m_min', 'caracteres_por_segundo',
                  'columnas_por_segundo')
        for campo in campos:
            nuevo = e[campo]
            if nuevo is None:
                continue
            if actual[campo] is None:
                actual[campo] = nuevo
            elif actual[campo] != nuevo:
                # Solo es conflicto si el mismo dato tiene dos valores
                # distintos; c/s y columnas/s son metricas complementarias.
                actual['conflicto'] = True
                actual.setdefault('valores_alternativos', []).append({
                    'campo': campo,
                    'valor': nuevo,
                    'archivo': e['archivo'],
                })

    for p in por_clave.values():
        if not p['modelo'] or not p['boquilla_um'] or not p['fuente']:
            p['estado'] = 'por-definir'
        elif p['velocidad_nominal_m_min'] is None:
            p['estado'] = 'sin-datos-en-documento'
        else:
            p['estado'] = 'borrador-decodificado'

    partes = sorted(por_clave.values(),
                    key=lambda p: (str(p['modelo']), p['boquilla_um'] or 0,
                                   clave_fuente(p['fuente'])))
    conflictos = [p for p in partes if p['conflicto']]
    conflictos_boquilla = [p for p in partes if p['conflicto_boquilla']]
    conflictos_modelo = [p for p in partes if p['conflicto_modelo']]
    conflictos_fuente = [p for p in partes if p['conflicto_fuente']]
    sin_datos = [p for p in partes if p['velocidad_nominal_m_min'] is None]
    sin_cps = [p for p in partes if p['caracteres_por_segundo'] is None
               and p['columnas_por_segundo'] is None]

    notas = []

    def nota(tipo, modelo, detalle):
        if not any(n['tipo'] == tipo and n['modelo'] == modelo for n in notas):
            notas.append({'tipo': tipo, 'modelo': modelo,
                          'detalle': detalle})

    if any(p['modelo'] == '1880 UHS' and p['conflicto_boquilla']
           for p in partes):
        nota('boquilla', '1880 UHS',
             'El PDF y la carpeta 1880_UHS-boquilla 50 indican 50 um; '
             'varios nombres de archivo dicen _60_. Se conserva el valor '
             'impreso (50 um) y se marca el nombre desactualizado.')
    if any(p['modelo'] == '1620-50 UHS' and p['conflicto_boquilla']
           for p in partes):
        nota('boquilla', '1620-50 UHS',
             'Los PDF 1620-50 UHS imprimen 50 um; algunos nombres dicen _60_. '
             'Se conserva el valor impreso/carpeta (50 um).')
    if any(p['modelo'] == '1240-1280' and p['conflicto_modelo']
           for p in partes):
        nota('modelo', '1240-1280',
             'El PDF imprime Printer Type 1240/1280; algunos nombres de '
             'archivo dicen solo 1280. Se conserva el valor impreso.')
    if any(p['modelo'] == '1580 C' and p['conflicto_modelo']
           for p in partes):
        nota('modelo', '1580 C',
             'El PDF imprime Printer Type 1580 C; los nombres de archivo '
             'dicen 1580_CC. Se conserva el valor impreso.')
    if any(p['modelo'] == '1610-20-50-DH' and p['conflicto_modelo']
           for p in partes):
        nota('modelo', '1610-20-50-DH',
             'El PDF imprime 1610/20/50/DH y el nombre usa guiones; es la '
             'misma familia. Se normalizan los separadores para comparar.')
    if any(p['modelo'] == '1710' and p['conflicto_fuente']
           for p in partes):
        nota('fuente', '1710',
             'El PDF imprime la fuente real (5x7, 7x9 o 10x16); algunos '
             'nombres conservan _4x7. Se conserva la fuente impresa.')

    salida = {
        'fuente': 'CIJ Line Speed Calculator v9.7 (PDF oficiales Videojet)',
        'metodo': 'OCR Windows.Data.Pdf + Windows.Media.Ocr (1600 px, es-MX)',
        'fecha': datetime.date.today().isoformat(),
        'estado_general': 'borrador-decodificado',
        'resumen': {
            'calculadores_leidos': len(entradas),
            'pdfs_leidos': total,
            'calculadores_objetivo': total - len(descartados),
            'descartados': len(descartados),
            'entradas': len(partes),
            'duplicados': max(0, len(entradas) - len(partes)),
            'modelos': len({p['modelo'] for p in partes if p['modelo']}),
            'boquillas': sorted({p['boquilla_um'] for p in partes
                                 if p['boquilla_um']}),
            'fuentes': sorted({p['fuente'] for p in partes if p['fuente']}),
            'conflictos': len(conflictos),
            'conflictos_boquilla': len(conflictos_boquilla),
            'conflictos_modelo': len(conflictos_modelo),
            'conflictos_fuente': len(conflictos_fuente),
            'sin_datos': len(sin_datos),
            'sin_cps': len(sin_cps),
            'expertos': sum(1 for p in partes
                            if p['tipo_calculador'] == 'experto'),
            'errores': len(errores),
        },
        'conflictos_documentados': notas,
        'entradas': partes,
        'descartados': descartados,
        'errores': errores,
    }
    O.guardar(SALIDA, salida)
    os.makedirs(os.path.dirname(CSV_SALIDA), exist_ok=True)
    with open(CSV_SALIDA, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['modelo', 'modelo_impreso', 'boquilla_um', 'fuente',
                    'velocidad_nominal_m_min', 'caracteres_por_segundo',
                    'columnas_por_segundo', 'tipo_calculador', 'estado',
                    'conflicto', 'conflicto_boquilla', 'conflicto_modelo',
                    'conflicto_fuente', 'boquilla_ocr', 'boquilla_archivo',
                    'boquilla_carpeta', 'archivos'])
        for p in partes:
            clave = p['evidencias_clave'][0] if p['evidencias_clave'] else {}
            w.writerow([p['modelo'], p.get('modelo_impreso') or '',
                        p['boquilla_um'], p['fuente'],
                        p['velocidad_nominal_m_min'],
                        p['caracteres_por_segundo'],
                        p['columnas_por_segundo'], p['tipo_calculador'],
                        p['estado'], 'si' if p['conflicto'] else 'no',
                        'si' if p['conflicto_boquilla'] else 'no',
                        'si' if p['conflicto_modelo'] else 'no',
                        'si' if p['conflicto_fuente'] else 'no',
                        clave.get('boquilla_ocr'),
                        clave.get('boquilla_archivo'),
                        clave.get('boquilla_carpeta'),
                        ' | '.join(p['archivos'])])


if __name__ == '__main__':
    sys.exit(main())
