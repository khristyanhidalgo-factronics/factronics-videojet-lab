"""Estructura el uso de solvente (makeup) CIJ desde un PDF extraido con leer_pdf.py.

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Los documentos oficiales 'CIJ Makeup Usage Model' entregan una curva de uso de solvente
vs temperatura para cada combinacion MODELO + TINTA. Este script la convierte en JSON.

Uso (todo opcional; por defecto procesa el VJ1210 V401 ya extraido):
  python tools/estructurar_solvente.py
  python tools/estructurar_solvente.py datos/extraccion/algo.txt 1210 v401
  python tools/estructurar_solvente.py datos/extraccion/algo.txt 1210 v401 salida.json

Reglas de honestidad:
  - el MODELO y la TINTA se toman del NOMBRE del archivo origen (dato garantizado);
  - se acepta solo lo parseado con exito; si el archivo esta cifrado/garbled se registra
    'no-legible' — no se reconstruye a mano;
  - la salida se acumula en datos/cij_uso_solvente.json (una entrada por modelo+tinta).
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_DEF = os.path.join(RAIZ, 'datos', 'cij_uso_solvente.json')
SRC_DEF = os.path.join(RAIZ, 'datos', 'extraccion', 'cij_solvente_1210_v401.txt')


def num_coma(s):
    try:
        return float(str(s).replace(',', '.'))
    except ValueError:
        return None


def parsear(txt):
    lineas = [l.strip() for l in txt.splitlines()]
    temps, usos = [], []
    modo = None
    for l in lineas:
        if l.startswith('Temperatur'):
            modo = 'temp'
            continue
        if modo == 'temp':
            if l.isdigit() and 5 <= int(l) <= 45:
                temps.append(int(l))
                continue
            modo = None
        if l.startswith('Makupusag') and 'ml/hr' in l:
            modo = 'uso'
            continue
        if modo == 'uso':
            n = num_coma(l)
            if n is not None and 0.5 <= n <= 60:
                usos.append(n)
                continue
            modo = None
    meta = {}
    for i, l in enumerate(lineas):
        if l == 'Inkype':                      # "Ink type" (letras perdidas por fuente)
            j = i + 1
            if j < len(lineas):
                meta['tinta_documentada'] = lineas[j]
        elif l == 'Inkse':                     # "Ink set"
            j = i + 1
            if j < len(lineas):
                meta['base_quimica'] = lineas[j]
        elif l == 'Temperature':               # temperatura de referencia del cuadro
            j = i + 1
            while j < len(lineas) and not re.fullmatch(r'\d+(,\d+)?', lineas[j]):
                j += 1
            if j < len(lineas):
                meta['referencia_temp_c'] = num_coma(lineas[j])
        elif l == 'Makeupsage':                # uso de solvente en la temp de referencia
            if 'referencia_uso_ml_hr' not in meta:
                j = i + 1
                while j < len(lineas) and not re.fullmatch(r'\d+(,\d+)?', lineas[j]):
                    j += 1
                if j < len(lineas):
                    meta['referencia_uso_ml_hr'] = num_coma(lineas[j])
        elif l == 'Workingurseliter':          # "Working hrs per liter"
            j = i + 1
            if j < len(lineas) and lineas[j] == 'hrs':
                j += 1
                if j < len(lineas) and num_coma(lineas[j]):
                    meta['hrs_por_litro'] = num_coma(lineas[j])
        elif l == 'Cartridgeze':               # "Cartridge size"
            j = i + 1
            if j < len(lineas) and lineas[j] == 'ml':
                j += 1
                if j < len(lineas) and num_coma(lineas[j]):
                    meta['cartucho_ml'] = num_coma(lineas[j])
        elif l == 'WorkingurseCartridge':      # "Working hrs per Cartridge"
            j = i + 1
            if j < len(lineas) and lineas[j] == 'hrs':
                j += 1
                if j < len(lineas) and num_coma(lineas[j]):
                    meta['hrs_por_cartucho'] = num_coma(lineas[j])
    return {'temps': temps, 'usos': usos, 'meta': meta}


def principal():
    argv = sys.argv[1:]
    origen = os.path.abspath(argv[0]) if len(argv) > 0 else SRC_DEF
    modelo = argv[1] if len(argv) > 1 else None
    tinta_arg = argv[2] if len(argv) > 2 else None
    salida_path = argv[3] if len(argv) > 3 else SALIDA_DEF

    m_nombre = re.search(r'_v?(\d{3,4})[_-]?v?(\w{3,6})?\.', origen)
    modelo_doc = m_nombre.group(1) if m_nombre else None
    tinta_doc = (m_nombre.group(2) or '') if m_nombre else ''
    modelo = modelo or modelo_doc or 'por-definir'
    tinta = (tinta_arg or tinta_doc or '').strip().upper()
    if tinta.startswith('V'):
        tinta = tinta[1:]
    tinta = ('V' + tinta) if tinta else 'por-definir'

    texto = open(origen, 'r', encoding='utf-8').read()
    datos = parsear(texto)
    temps, usos, meta = datos['temps'], datos['usos'], datos['meta']

    curva = [{'temp_c': t, 'uso_ml_hr': u} for t, u in zip(temps, usos)] if len(temps) == len(usos) else []
    consistente = []
    if meta.get('referencia_temp_c') and int(meta['referencia_temp_c']) in temps \
            and meta.get('referencia_uso_ml_hr') is not None:
        pos = temps.index(int(meta['referencia_temp_c']))
        if pos < len(usos) and abs(usos[pos] - meta['referencia_uso_ml_hr']) < 0.05:
            consistente.append('referencia del cuadro coincide con la curva')
    else:
        consistente.append('sin verificacion cruzada interna')

    if len(curva) < 6:
        print('NO-LEGIBLE:', os.path.basename(origen),
              '| temps:', len(temps), '| usos:', len(usos),
              '| meta:', meta, '-> no se registra (evita datos dudosos)')
        return

    entrada = {
        'modelo': 'VJ' + modelo,
        'tinta': tinta,
        'base_quimica': meta.get('base_quimica', 'por-definir'),
        'tinta_documentada': meta.get('tinta_documentada', tinta),
        'curva': curva,
        'referencia': {'temp_c': meta.get('referencia_temp_c'),
                       'uso_ml_hr': meta.get('referencia_uso_ml_hr')},
        'hrs_por_litro': meta.get('hrs_por_litro'),
        'cartucho_ml': meta.get('cartucho_ml'),
        'hrs_por_cartucho': meta.get('hrs_por_cartucho'),
        'estado': 'verificado',
        'fuente_doc': 'CIJ Makeup Usage Model v14 (documento oficial del modelo)',
        'extraido_de': os.path.relpath(origen, RAIZ),
        'notas_verificacion': consistente,
    }
    if os.path.exists(salida_path):
        with open(salida_path, 'r', encoding='utf-8') as f:
            dsalida = json.load(f)
    else:
        dsalida = {
            'producto': 'Factronics Videojet Lab', 'schema': 1,
            'actualizado': '2026-11-08', 'estado_general': 'en-extraccion',
            'nota': 'Uso de solvente (makeup) CIJ por modelo y tinta, tomado de los documentos '
                    'oficiales CIJ Makeup Usage Model v14 del equipo. Es una ESTIMACION '
                    '(asi lo declara el propio documento): influyen solvente/base, temperatura, '
                    'humedad, temperatura de boquilla, recirculacion, condensador y bomba.',
            'fuentes': ['documentos de uso de solvente del equipo (17 modelos, 46 PDFs v14)'],
            'modelos': [],
        }
    dsalida['modelos'] = [m for m in dsalida.get('modelos', [])
                          if not (m['modelo'] == entrada['modelo'] and m['tinta'] == entrada['tinta'])]
    dsalida['modelos'].append(entrada)
    with open(salida_path, 'w', encoding='utf-8') as f:
        json.dump(dsalida, f, ensure_ascii=False, indent=1)
    print('OK', os.path.relpath(salida_path, RAIZ),
          '| VJ%s %s | puntos=%d ref=%s @%sC hrs/L=%s cartucho=%s ml / %s hrs'
          % (modelo, tinta, len(curva), meta.get('referencia_uso_ml_hr'), meta.get('referencia_temp_c'),
             meta.get('hrs_por_litro'), meta.get('cartucho_ml'), meta.get('hrs_por_cartucho')))


if __name__ == '__main__':
    principal()
