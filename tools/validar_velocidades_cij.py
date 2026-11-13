# -*- coding: utf-8 -*-
"""Valida el consolidado de velocidades CIJ contra los charts oficiales.

Comprueba:
  - conteos del resumen (270 calculadores, 1 descartado, 266 entradas, 12 modelos);
  - que `v9.7z.pdf` quede descartado y no aparezca como calculador;
  - que todas las entradas sean `borrador-decodificado` y conserven evidencia;
  - que no haya conflictos de valores (c/s y columnas/s son complementarios);
  - los casos UHS 50 um aunque el nombre diga `_60_`, y los HR 40 um;
  - el calculador experto `1620-50 UHS|50|4x5 single` (3333 c/s, 16667 col/s);
  - las anclas de los charts 1280/1580/1880 en fpm convertidas a m/min
    (tolerancia +-1.2 m/min por redondeo).

Uso:
  python tools/validar_velocidades_cij.py
  python tools/validar_velocidades_cij.py --json datos/cij_velocidades.json
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'datos')
SALIDA = os.path.join(DATOS, 'cij_velocidades.json')
CACHE = os.path.join(DATOS, 'extraccion', 'velocidades_cij_ocr')

ANCLAS = {
    '1280': {
        'modelos': ['1240-1280'],
        'chart': 'line_speed_chart_1280',
        'fpm': [533, 305, 256, 95, 56],
    },
    '1580': {
        # El chart 1580 cubre las dos variantes: 1580+ y 1580 C.
        'modelos': ['1580+', '1580 C'],
        'chart': 'line_speed_chart_1580',
        'fpm': [914, 800, 533, 305, 256, 95, 56],
    },
    '1880': {
        'modelos': ['1880+'],
        'chart': 'line_speed_chart_1880',
        'fpm': [1097, 914, 800, 533, 305, 256, 96, 56],
    },
}
CHART_COMBINADO = 'line_speed_chart_1280_1580_1880'
TOLERANCIA_M_MIN = 1.2


def cargar(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)


def valores_chart(nombre):
    """Valores enteros utiles del OCR de un chart (fpm)."""
    ruta = os.path.join(CACHE, nombre + '.json')
    if not os.path.exists(ruta):
        raise FileNotFoundError('falta el OCR del chart: %s' % ruta)
    datos = cargar(ruta)
    valores = set()
    for pagina in datos.get('paginas', []):
        for linea in pagina.get('lineas', []):
            texto = (linea.get('texto') or '').strip().replace(',', '')
            if re.fullmatch(r'\d{2,4}', texto):
                valor = int(texto)
                if 50 <= valor <= 2000:
                    valores.add(valor)
    return valores


def fpm_a_m_min(fpm):
    return fpm / 3.280839895013123


def validar(ruta=SALIDA):
    errores = []
    avisos = []
    datos = cargar(ruta)
    entradas = datos.get('entradas', [])
    resumen = datos.get('resumen', {})

    def fallo(mensaje):
        errores.append(mensaje)

    def aviso(mensaje):
        avisos.append(mensaje)

    # --- conteos del resumen ---
    esperado = {
        'calculadores_leidos': 270,
        'pdfs_leidos': 271,
        'calculadores_objetivo': 270,
        'descartados': 1,
        'entradas': 266,
        'duplicados': 4,
        'modelos': 12,
        'conflictos': 0,
        'conflictos_boquilla': 22,
        'conflictos_modelo': 31,
        'conflictos_fuente': 3,
        'sin_datos': 0,
        'sin_cps': 0,
        'expertos': 1,
        'errores': 0,
    }
    for clave, valor in esperado.items():
        if resumen.get(clave) != valor:
            fallo('resumen.%s = %r; se esperaba %r'
                  % (clave, resumen.get(clave), valor))
    if len(entradas) != 266:
        fallo('entradas = %d; se esperaban 266' % len(entradas))
    if len(datos.get('errores', [])) != 0:
        fallo('hay %d errores en el consolidado' % len(datos['errores']))

    # --- descarte de la tabla resumen ---
    descartados = datos.get('descartados', [])
    if len(descartados) != 1:
        fallo('descartados = %d; se esperaba 1' % len(descartados))
    elif 'v9.7z.pdf' not in descartados[0].get('archivo', ''):
        fallo('el descartado no es v9.7z.pdf: %r' % descartados[0])
    for entrada in entradas:
        for archivo in entrada.get('archivos', []):
            if 'v9.7z' in archivo.lower():
                fallo('v9.7z.pdf aparece como calculador: %s' % archivo)

    # --- integridad de cada entrada ---
    claves = set()
    por_modelo = {}
    duplicados = 0
    for entrada in entradas:
        clave = entrada.get('clave')
        if not clave:
            fallo('entrada sin clave: %r' % entrada)
            continue
        if clave in claves:
            fallo('clave repetida: %s' % clave)
        claves.add(clave)
        if entrada.get('estado') != 'borrador-decodificado':
            fallo('%s: estado %r' % (clave, entrada.get('estado')))
        if entrada.get('velocidad_nominal_m_min') is None:
            fallo('%s: sin velocidad nominal' % clave)
        if (entrada.get('caracteres_por_segundo') is None
                and entrada.get('columnas_por_segundo') is None):
            fallo('%s: sin c/s ni columnas/s' % clave)
        if not entrada.get('archivos'):
            fallo('%s: sin archivos de origen' % clave)
        if not entrada.get('evidencias_ocr'):
            fallo('%s: sin evidencia OCR' % clave)
        if entrada.get('conflicto'):
            fallo('%s: marcada como conflicto de valores' % clave)
        if len(entrada.get('archivos', [])) > 1:
            duplicados += 1
        por_modelo.setdefault(entrada.get('modelo'), []).append(entrada)

    if duplicados != 4:
        fallo('entradas con mas de un archivo = %d; se esperaban 4' % duplicados)
    if len(por_modelo) != 12:
        fallo('modelos distintos = %d; se esperaban 12' % len(por_modelo))

    # --- UHS 50 um y HR 40 um ---
    uhs_1880 = [e for e in por_modelo.get('1880 UHS', [])
                if e.get('boquilla_um') == 50]
    uhs_1620 = [e for e in por_modelo.get('1620-50 UHS', [])
                if e.get('boquilla_um') == 50]
    if len(uhs_1880) != 19:
        fallo('1880 UHS con boquilla 50 = %d; se esperaban 19' % len(uhs_1880))
    if len(uhs_1620) != 18:
        fallo('1620-50 UHS con boquilla 50 = %d; se esperaban 18' % len(uhs_1620))
    if not any('_60_' in a for e in uhs_1880 for a in e.get('archivos', [])):
        fallo('1880 UHS 50: no se conserva ningun nombre _60_ como evidencia')
    if not any('_60_' in a for e in uhs_1620 for a in e.get('archivos', [])):
        fallo('1620-50 UHS 50: no se conserva ningun nombre _60_ como evidencia')
    for modelo in ('1880 HR', '1620-50 HR'):
        malas = [e for e in por_modelo.get(modelo, [])
                 if e.get('boquilla_um') != 40]
        if malas:
            fallo('%s: %d entradas no tienen boquilla 40'
                  % (modelo, len(malas)))

    # --- calculador experto ---
    expertos = [e for e in entradas if e.get('tipo_calculador') == 'experto']
    if len(expertos) != 1:
        fallo('calculadores expertos = %d; se esperaba 1' % len(expertos))
    else:
        e = expertos[0]
        if e.get('clave') != '1620-50 UHS|50|4x5_single':
            fallo('experto inesperado: %s' % e.get('clave'))
        if e.get('caracteres_por_segundo') != 3333:
            fallo('experto: c/s = %r; se esperaba 3333'
                  % e.get('caracteres_por_segundo'))
        if e.get('columnas_por_segundo') != 16667:
            fallo('experto: columnas/s = %r; se esperaba 16667'
                  % e.get('columnas_por_segundo'))
        if e.get('velocidad_nominal_m_min') != 508:
            fallo('experto: velocidad = %r; se esperaba 508'
                  % e.get('velocidad_nominal_m_min'))

    # --- anclas contra los charts ---
    charts = {}
    for familia, cfg in ANCLAS.items():
        nombre = cfg['chart']
        if nombre not in charts:
            charts[nombre] = valores_chart(nombre)
        valores = charts[nombre]
        velocidades = []
        for modelo in cfg['modelos']:
            velocidades.extend(
                e.get('velocidad_nominal_m_min')
                for e in por_modelo.get(modelo, [])
                if e.get('velocidad_nominal_m_min') is not None)
        if not velocidades:
            fallo('%s: no hay velocidades para validar' % familia)
            continue
        for fpm in cfg['fpm']:
            if fpm not in valores:
                fallo('%s: el chart %s no contiene %d fpm'
                      % (familia, nombre, fpm))
                continue
            objetivo = fpm_a_m_min(fpm)
            cercana = min(velocidades, key=lambda v: abs(v - objetivo))
            if abs(cercana - objetivo) > TOLERANCIA_M_MIN:
                fallo('%s: %d fpm (~%.1f m/min) no coincide con ninguna '
                      'velocidad (la mas cercana es %.0f m/min)'
                      % (familia, fpm, objetivo, cercana))

    # El chart combinado solo contiene la tabla 1580 aunque su nombre mencione
    # 1280/1580/1880; se valida contra las anclas 1580 y se avisa del nombre.
    combinado = valores_chart(CHART_COMBINADO)
    faltan = sorted(set(ANCLAS['1580']['fpm']) - combinado)
    if faltan:
        fallo('chart combinado sin las anclas 1580: %s' % faltan)
    union_charts = set()
    for nombre in charts:
        union_charts |= charts[nombre]
    sobrantes = sorted(combinado - union_charts)
    if sobrantes:
        aviso('chart combinado con valores que no estan en los charts '
              'individuales: %s' % sobrantes)
    if 1097 not in combinado or 96 not in combinado:
        aviso('el archivo 1280_1580_1880 Line speed chart.pdf solo contiene '
              'la tabla 1580; no se usa para validar 1280/1880')

    # --- notas documentadas ---
    notas = datos.get('conflictos_documentados', [])
    tipos = {n.get('tipo') for n in notas}
    if tipos != {'boquilla', 'modelo', 'fuente'}:
        fallo('conflictos_documentados no cubre boquilla/modelo/fuente: %s'
              % sorted(tipos))
    if len(notas) != 5:
        aviso('conflictos_documentados = %d; se esperaban 5' % len(notas))

    return errores, avisos, datos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', default=SALIDA)
    args = ap.parse_args()
    errores, avisos, datos = validar(args.json)
    resumen = datos.get('resumen', {})
    print('Validacion de velocidades CIJ')
    print('  calculadores=%s pdfs=%s entradas=%s modelos=%s'
          % (resumen.get('calculadores_leidos'), resumen.get('pdfs_leidos'),
             len(datos.get('entradas', [])), resumen.get('modelos')))
    print('  conflictos valores=%s boquilla=%s modelo=%s fuente=%s'
          % (resumen.get('conflictos'), resumen.get('conflictos_boquilla'),
             resumen.get('conflictos_modelo'), resumen.get('conflictos_fuente')))
    for aviso in avisos:
        print('  AVISO: %s' % aviso)
    if errores:
        print('  FALLOS: %d' % len(errores))
        for error in errores:
            print('   - %s' % error)
        return 1
    print('  OK: charts 1280/1580/1880 y casos UHS/HR validados')
    return 0


if __name__ == '__main__':
    sys.exit(main())
