"""Estructura el uso de solvente (makeup) CIJ desde un PDF extraido con leer_pdf.py.

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Los documentos oficiales 'CIJ Makeup Usage Model' entregan una curva de uso de solvente
vs temperatura para cada combinacion MODELO + VARIANTE + TINTA. Este script la convierte en JSON.

Uso directo (todo opcional; por defecto procesa el VJ1210 V401 ya extraido):
  python tools/estructurar_solvente.py
  python tools/estructurar_solvente.py datos/extraccion/algo.txt 1210 v401
  python tools/estructurar_solvente.py datos/extraccion/algo.txt 1210 v401 salida.json

Lotes: tools/lote_solvente.py usa registrar()/construir_entrada()/cargar_dataset().

Tolerancias documentadas (los PDFs usan fuentes subset con letras perdidas):
  - etiqueta de curva: 'Makupusaginml/hr' | 'Makl/hr' | variantes -> detectada por
    ('mak'|'usage' in minusculas) y 'hr';
  - tinta: 'Inkype' | 'InkType'; base: 'Inkse' | 'InkBase';
  - 'Workingurseliter' | 'WorkingHourperliter'; 'Cartridgeze'|'CartridgeSize';
    'WorkingurseCartridge'|'WorkingHourperCartridge'.

Reglas de honestidad:
  - el MODELO y la TINTA se toman del NOMBRE del archivo origen (dato garantizado);
  - se acepta solo lo parseado con exito; si el archivo esta cifrado/garbled se registra
    'no-legible' — no se reconstruye a mano;
  - si el propio documento muestra '#N/D' (sin datos, hoja exportada a PDF) la entrada se
    acepta con curva vacia y estado 'sin-datos-en-documento' — dato honesto, no inventado;
  - la salida se acumula en datos/cij_uso_solvente.json (una entrada por
    modelo+variante+tinta+base_del_nombre).
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
SRC_DEF = os.path.join(RAIZ, 'datos', 'extraccion', 'cij_solvente_1210_401.txt')


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
        ll = l.lower()
        if ll.startswith('temperatur'):      # 'Temperature in °C' / 'TemperaturC'
            modo = 'temp'
            continue
        if modo == 'temp':
            if l.isdigit() and 5 <= int(l) <= 45:
                temps.append(int(l))
                continue
            modo = None
        if modo != 'uso' and ('mak' in ll or 'usage' in ll) and 'hr' in ll:
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
        ll = l.lower()
        if ll.startswith('inkb'):            # 'InkBase' / 'Inkse' variante
            j = i + 1
            if j < len(lineas):
                meta['base_quimica'] = lineas[j]
        elif ll.startswith('ink'):           # 'InkType' / 'Inkype'
            j = i + 1
            if j < len(lineas):
                meta['tinta_documentada'] = lineas[j]
        elif l == 'Temperature':             # cuadro de referencia: temp y su uso
            j = i + 1
            vref = None
            while j < len(lineas):
                if re.fullmatch(r'\d+(,\d+)?', lineas[j]):
                    vref = num_coma(lineas[j])
                    break
                j += 1
            if vref is not None:
                meta['referencia_temp_c'] = vref
                k, pasos, visto_unidad = j + 1, 0, False
                while k < len(lineas) and pasos < 8:
                    s = lineas[k]
                    if s == 'ml/hr':
                        visto_unidad = True
                    elif visto_unidad and re.fullmatch(r'\d+(,\d+)?', s):
                        meta['referencia_uso_ml_hr'] = num_coma(s)
                        break
                    k += 1
                    pasos += 1
        elif 'hour' in ll or ll.startswith('working'):
            if 'cartridg' in ll:
                j = i + 1
                if j + 1 < len(lineas) and lineas[j] in ('hrs', 'hr', 'hours'):
                    meta['hrs_por_cartucho'] = num_coma(lineas[j + 1])
            elif 'liter' in ll or 'litre' in ll:
                j = i + 1
                if j + 1 < len(lineas) and lineas[j] in ('hrs', 'hr', 'hours'):
                    meta['hrs_por_litro'] = num_coma(lineas[j + 1])
        elif 'cartridg' in ll:               # 'Cartridgeze' | 'CartridgeSize' + ml
            j = i + 1
            if j + 1 < len(lineas) and lineas[j].startswith('ml'):
                meta['cartucho_ml'] = num_coma(lineas[j + 1])
    return {'temps': temps, 'usos': usos, 'meta': meta}


def modelo_tinta_del_nombre(nombre_archivo):
    """Deriva (modelo, variante, tinta, base) del nombre del documento (dato garantizado).
    Formatos soportados (tras el token 'v14'):
      _1210_v401.pdf | _1510_v401_MEK.pdf | _1610DH_v401_MEK.pdf |
      _1880UHS_v4201_MEK.pdf | _1580_C_v4225_MEK.pdf | _1210_v461_ETHYL ACETATE.pdf |
      _1240_v4210A_MEK.pdf | _1710_v483AB_MEK.pdf   (tinta con sufijo de letras)
    """
    stem = re.sub(r'\.pdf$', '', os.path.basename(nombre_archivo), flags=re.I)
    toks = [t for t in re.split(r'[_\- ]+', stem) if t]
    iv = next((i for i, t in enumerate(toks) if re.fullmatch(r'v\d+[A-Z]{0,2}', t, re.I)), None)
    if iv is None:
        return None
    resto = toks[iv + 1:]
    ink_i = next((i for i, t in enumerate(resto) if re.fullmatch(r'v\d+[A-Z]{0,2}', t, re.I)), None)
    if ink_i is None or ink_i == 0:
        return None
    crudo = ''.join(resto[:ink_i]).upper()
    m = re.match(r'(\d{3,4})(.*)', crudo)
    if not m:
        return None
    base = re.sub(r'[^A-Z0-9]+', '_', '-'.join(resto[ink_i + 1:]), flags=re.I).lower().strip('_')
    return {'modelo': m.group(1), 'variante': (m.group(2) or ''),
            'tinta': resto[ink_i][1:], 'base': base}


def construir_entrada(origen, texto, modelo=None, tinta_arg=None, variante=None, base=None):
    """Texto de UN pdf de makeup -> entrada del dataset. Devuelve (entrada, motivo)."""
    if modelo is None or tinta_arg is None:
        m_nombre = re.search(r'_v?(\d{3,4})[_-]v?(\w+)\.', os.path.basename(origen))
        if m_nombre:
            modelo = modelo or m_nombre.group(1)
            tinta_arg = tinta_arg or m_nombre.group(2)
        else:
            d_nombre = modelo_tinta_del_nombre(origen)
            if d_nombre:
                modelo = modelo or d_nombre['modelo']
                tinta_arg = tinta_arg or d_nombre['tinta']
                variante = variante or d_nombre['variante']
                base = base or d_nombre['base']
    if not modelo or not tinta_arg:
        return None, 'nombre-sin-modelo-tinta: ' + os.path.basename(origen)
    tinta = tinta_arg.strip().upper()
    if tinta.startswith('V') and tinta != 'V401':   # 'v401' -> '401'
        tinta_manual = re.sub(r'^V(?=\d)', '', tinta)
    else:
        tinta_manual = tinta
    if re.fullmatch(r'\d+\w*', tinta_manual):
        tinta = 'V' + tinta_manual
    else:
        tinta = tinta_manual if tinta_manual else 'por-definir'

    datos = parsear(texto)
    temps, usos, meta = datos['temps'], datos['usos'], datos['meta']
    curva = [{'temp_c': t, 'uso_ml_hr': u} for t, u in zip(temps, usos)] if len(temps) == len(usos) else []

    consistente = ['sin verificacion cruzada interna']
    notas_extra = []
    estado = 'verificado'
    if len(curva) < 6:
        if '#N/D' in texto or '#N/A' in texto:
            # El propio documento (hoja exportada a PDF) declara SIN DATOS para esa tinta.
            estado = 'sin-datos-en-documento'
            notas_extra = ['la curva del documento muestra #N/D (sin datos) para esta combinacion']
            curva = []
        else:
            return None, ('no-legible: temps=%d usos=%d meta=%s' % (len(temps), len(usos), meta or '{}'))
    if meta.get('referencia_temp_c') and int(meta['referencia_temp_c']) in temps \
            and meta.get('referencia_uso_ml_hr') is not None:
        pos = temps.index(int(meta['referencia_temp_c']))
        if pos < len(usos) and abs(usos[pos] - meta['referencia_uso_ml_hr']) < 0.05:
            consistente = ['referencia del cuadro coincide con la curva']

    entrada = {
        'modelo': 'VJ' + modelo,
        'variante': variante or '',
        'base_del_nombre': (base or '').lower(),
        'tinta': tinta,
        'base_quimica': meta.get('base_quimica', 'por-definir'),
        'tinta_documentada': meta.get('tinta_documentada', tinta),
        'curva': curva,
        'referencia': {'temp_c': meta.get('referencia_temp_c'),
                       'uso_ml_hr': meta.get('referencia_uso_ml_hr')},
        'hrs_por_litro': meta.get('hrs_por_litro'),
        'cartucho_ml': meta.get('cartucho_ml'),
        'hrs_por_cartucho': meta.get('hrs_por_cartucho'),
        'estado': estado,
        'fuente_doc': 'CIJ Makeup Usage Model v14 (documento oficial del modelo)',
        'extraido_de': os.path.relpath(origen, RAIZ) if os.path.isabs(origen) else origen,
        'notas_verificacion': consistente + notas_extra,
    }
    return entrada, None


def cargar_dataset(salida_path):
    if os.path.exists(salida_path):
        with open(salida_path, 'r', encoding='utf-8') as f:
            ds = json.load(f)
    else:
        ds = {
            'producto': 'Factronics Videojet Lab', 'schema': 2,
            'actualizado': '2026-11-08', 'estado_general': 'en-extraccion',
            'nota': 'Uso de solvente (makeup) CIJ por modelo, variante y tinta, tomado de los '
                    'documentos oficiales CIJ Makeup Usage Model v14 del equipo. Es una ESTIMACION '
                    '(asi lo declara el propio documento): influyen solvente/base, temperatura, '
                    'humedad, temperatura de boquilla, recirculacion, condensador y bomba. '
                    'Tinta documentada = la que el propio PDF declara; modelo/variante/tinta del nombre.',
            'fuentes': ['documentos de uso de solvente del equipo (~802 PDFs v14 en 23 carpetas)'],
            'modelos': [],
        }
    for m in ds.get('modelos', []):
        m.setdefault('variante', '')
        m.setdefault('base_del_nombre', '')
        m.setdefault('tinta_documentada', m.get('tinta', ''))
    return ds


def guardar_dataset(d, salida_path):
    with open(salida_path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def registrar(origen, texto, salida_path=SALIDA_DEF, modelo=None, tinta=None,
              variante=None, base=None, verbose=True):
    entrada, motivo = construir_entrada(origen, texto, modelo, tinta, variante, base)
    if entrada is None:
        if verbose:
            print('NO', os.path.basename(origen), '|', motivo)
        return 'NO', motivo
    ds = cargar_dataset(salida_path)
    dm = ds['modelos']
    dm = [m for m in dm if not (m['modelo'] == entrada['modelo']
                                and m.get('variante', '') == entrada.get('variante', '')
                                and m.get('base_del_nombre', '') == entrada.get('base_del_nombre', '')
                                and m['tinta'] == entrada['tinta'])]
    dm.append(entrada)
    ds['modelos'] = dm
    guardar_dataset(ds, salida_path)
    resumen = ('OK | %s%s %s (%s) | puntos=%d ref=%s @%sC hrs/L=%s cartucho=%s ml / %s hrs'
               % (entrada['modelo'], ('/' + entrada['variante']) if entrada['variante'] else '',
                  entrada['tinta'], entrada['base_quimica'], len(entrada['curva']),
                  entrada['referencia'].get('uso_ml_hr'), entrada['referencia'].get('temp_c'),
                  entrada['hrs_por_litro'], entrada['cartucho_ml'], entrada['hrs_por_cartucho']))
    if verbose:
        print(resumen)
    return 'OK', resumen


def principal():
    argv = sys.argv[1:]
    origen = os.path.abspath(argv[0]) if len(argv) > 0 else SRC_DEF
    modelo = argv[1] if len(argv) > 1 else None
    tinta_arg = argv[2] if len(argv) > 2 else None
    salida_path = os.path.abspath(argv[3]) if len(argv) > 3 else SALIDA_DEF
    texto = open(origen, 'r', encoding='utf-8').read()
    estado, info = registrar(origen, texto, salida_path, modelo, tinta_arg)
    if estado == 'OK':
        print('acumulador:', os.path.relpath(salida_path, RAIZ),
              '| entradas:', len(cargar_dataset(salida_path).get('modelos', [])))


if __name__ == '__main__':
    principal()
