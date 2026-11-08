# -*- coding: utf-8 -*-
"""Estructura el chart oficial de ribbons TTO (XLSX 'Videojet Ribbon and Label Chart').

Fuente: 'Videojet Ribbon and Label Chart - 2.5.26.xlsx' (curso TTO 6x30, carpeta Ribbons).
Hojas usadas: 'Ribbon Chart' (grados), 'TTO Ribbon' (items), 'Standard Lengths Widths'
(matriz impresora x grado), 'Date and Lot Number Logic'.
Salida: datos/tto_ribbons.json. Extraccion DIRECTA de celdas (sin interpretacion).
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, 'datos', 'extraccion', 'tto_ribbon_chart_hojas.json')
DESTINO = os.path.join(RAIZ, 'datos', 'tto_ribbons.json')


def cargar():
    with open(ORIGEN, 'r', encoding='utf-8') as f:
        return json.load(f)


def valor_celda(v):
    """Convierte numeros simples a float/int; deja texto tal cual."""
    s = str(v).strip()
    if not s:
        return ''
    if re.fullmatch(r'-?\d+', s):
        try:
            return int(s)
        except ValueError:
            return s
    if re.fullmatch(r'-?\d+[.,]\d+', s):
        try:
            return float(s.replace(',', '.'))
        except ValueError:
            return s
    return s


def primera_linea(texto):
    return str(texto).splitlines()[0].strip()


def grados_de_ribbon(hoja):
    filas = hoja['contenido']
    cab = filas[0]['celdas']
    encabezados = {col: primera_linea(txt) for col, txt in cab.items()}
    # solo columnas A..N (datos Videojet; competencia queda fuera en v1)
    columnas = [c for c in cab if len(c) == 1 and c <= 'N']
    grados = []
    for fila in filas[1:]:
        celdas = fila['celdas']
        registro = {}
        for col in columnas:
            if col in celdas and str(celdas[col]).strip():
                registro[encabezados.get(col, col)] = valor_celda(celdas[col])
        if registro.get('PN') or registro.get('Videojet Grade'):
            grados.append(registro)
    return grados, encabezados


def items_tto(hoja):
    filas = hoja['contenido']
    items = []
    excluir = {'PFV Group', 'Pricing Family', 'Item No'}
    for fila in filas:
        celdas = fila['celdas']
        a = str(celdas.get('A', '')).strip()
        b = str(celdas.get('B', '')).strip()
        if a and b and a not in excluir:
            items.append({'item_no': a, 'descripcion': b})
    return items


def matriz_longitudes(hoja):
    filas = hoja['contenido']
    # etiquetas de grado en la fila 1 (columnas E..Q)
    etiquetas = {}
    for fila in filas:
        if fila['fila'] == '1':
            for col, txt in fila['celdas'].items():
                etiquetas[col] = primera_linea(txt)
    bloques = {'estandar': [], 'no_estandar': []}
    for fila in filas:
        celdas = fila['celdas']
        a = str(celdas.get('A', '')).strip()
        tech = str(celdas.get('B', '')).strip()
        if not a and not tech:
            continue
        registro = {
            'impresora': a,
            'tecnologia': tech,
            'anchos_mm': str(celdas.get('C', '')).strip(),
            'diametro_mm': str(celdas.get('D', '')).strip(),
            'longitudes_por_grado': {},
        }
        for col in 'EFGHIJKLMNOPQ':
            if col in celdas and etiquetas.get(col):
                registro['longitudes_por_grado'][etiquetas[col]] = valor_celda(celdas[col])
        if registro['impresora'] and a and a[0].isdigit() or a in ('DATAFLEX', '9550'):
            bloque = 'estandar' if fila['fila'] in ('3', '4', '5', '6') else 'no_estandar'
            bloques[bloque].append(registro)
        elif a == 'DATAFLEX' and fila['fila'] in ('13', '14'):
            bloques['no_estandar'].append(registro)
        elif a == 'DATAFLEX' and fila['fila'] in ('5', '6'):
            bloques['estandar'].append(registro)
    return bloques


def logica_lote(hoja):
    lineas = []
    for fila in hoja['contenido']:
        for col, txt in fila['celdas'].items():
            s = str(txt).strip()
            if s:
                lineas.append({'celda': '%s%s' % (col, fila['fila']), 'texto': s})
    return lineas


def main():
    d = cargar()
    grados, encabezados = grados_de_ribbon(d['Ribbon Chart'])
    items = items_tto(d['TTO Ribbon'])
    longitudes = matriz_longitudes(d['Standard Lengths Widths'])
    lote = logica_lote(d['Date and Lot Number Logic'])

    datos = {
        'producto': 'Ribbons TTO Videojet - chart oficial 2.5.26',
        'schema': 1,
        'estado_general': 'verificado (extraccion directa de celdas del XLSX oficial)',
        'fuente': {
            'archivo': 'Videojet Ribbon and Label Chart - 2.5.26.xlsx',
            'carpeta_equipo': 'CURSO BRASIL / TTO 6x30 / Ribbons',
            'hojas_usadas': ['Ribbon Chart', 'TTO Ribbon',
                             'Standard Lengths Widths', 'Date and Lot Number Logic'],
            'extraido_de': 'datos/extraccion/tto_ribbon_chart_hojas.json',
        },
        'resumen': {
            'grados_ribbon': len(grados),
            'items_suministros': len(items),
            'filas_longitudes_estandar': len(longitudes['estandar']),
            'filas_longitudes_no_estandar': len(longitudes['no_estandar']),
            'lineas_logica_lote': len(lote),
        },
        'grados_ribbon': grados,
        'items_suministros_tto': items,
        'longitudes_anchos': longitudes,
        'logica_lote': lote,
        'nota': ('Los grados traen PN, descripcion, aplicaciones, sustratos, colores, '
                 'velocidad max (mm/s), negrura Macbeth, durabilidad (0-100%), resistencia '
                 'termica, tipo y film base. Los items son la lista de suministros TTO '
                 '(item_no + descripcion). Longitudes/anchos por impresora y grado. '
                 'Columnas de competencia (O-AE) no incluidas en v1.'),
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | grados=%d items=%d long_std=%d long_nostd=%d lote=%d'
          % (os.path.relpath(DESTINO, RAIZ), len(grados), len(items),
             len(longitudes['estandar']), len(longitudes['no_estandar']), len(lote)))


if __name__ == '__main__':
    main()
