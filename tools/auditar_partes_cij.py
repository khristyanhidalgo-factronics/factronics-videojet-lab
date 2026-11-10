# -*- coding: utf-8 -*-
"""Audita las partes CIJ contra el texto real de su bloque y su linea.

No modifica datos: genera evidencia para la revision visual.

Para cada aparicion de `datos/partes_cij.json` comprueba, en el bloque PDF
del que salio:
  - que el bloque y el objeto coincidan con el indice guardado;
  - que el P/N aparezca en una linea o celda del bloque;
  - que la descripcion aparezca en la ventana de lineas de esa fila
    (las descripciones pueden continuar en la linea siguiente);
  - que la cantidad de la ultima columna coincida, cuando es legible.

Para los items sin P/N comprueba que la descripcion exista en el bloque y
mide la mejor cobertura por ventana de lineas.

Salidas:
  datos/analisis/auditoria_partes_cij.csv
  datos/analisis/auditoria_partes_cij_resumen.json

Uso:
  python tools/auditar_partes_cij.py
"""
import csv
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import leer_pdf_cifrado as L
import estructurar_partes_cij as E

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'datos', 'analisis')
RADIO_Y = 32.0
UMBRAL_DESC = 0.8


def tokens(texto):
    return [t for t in re.findall(r'[a-z0-9]+', (texto or '').lower()) if len(t) >= 2]


def desc_base(desc):
    """Descripcion sin calificativos entre parentesis.

    Los calificativos (IP55, FG, Videojet 1220...) suelen venir de la
    cabecera de la tabla o de la seccion, no de la linea del P/N.
    """
    base = re.sub(r'\([^)]*\)', ' ', desc or '')
    return re.sub(r'\s+', ' ', base).strip() or (desc or '')


def cobertura(desc, texto):
    tt = tokens(desc)
    if not tt:
        return 0.0
    p = E.plano(texto).lower()
    return sum(1 for t in tt if t in p) / float(len(tt))


def lineas_de(runs):
    return E.agrupar_lineas(runs)


def texto_ventana(lineas, idx, radio=RADIO_Y):
    y0 = lineas[idx]['y']
    return ''.join(E.texto_de_linea(l) for l in lineas
                   if abs(l['y'] - y0) <= radio)


def contiene_pn(linea, pn):
    p = E.plano(pn)
    if p in E.plano(E.texto_de_linea(linea)):
        return True
    return any(p in E.plano(E.texto_de_celda(c))
               for c in E.dividir_celdas(linea))


def cantidad_de_linea(linea):
    """Cantidad de la ultima columna, solo si es legible sin ambiguedad."""
    celdas = E.dividir_celdas(linea)
    if celdas:
        ult = E.texto_de_celda(celdas[-1]).strip()
        if ult.isdigit():
            return ult
    # Sin separador de celda: corridas numericas al extremo derecho.
    qty = []
    for x, t, _ in reversed(linea['runs']):
        ts = t.strip()
        if ts.isdigit() and x > 460:
            qty.insert(0, ts)
        else:
            break
    return ''.join(qty) if qty else None


def fila_base(tipo, registro, parte=None):
    return {
        'tipo_registro': tipo,
        'pn': parte['pn'] if parte else '',
        'descripcion': (parte or registro).get('descripcion'),
        'estado': (parte or registro).get('estado'),
        'documento': registro['documento'],
        'bloque': registro.get('bloque'),
        'objeto': registro.get('objeto'),
        'item': registro.get('item'),
        'cantidad': registro.get('cantidad'),
        'pn_en_linea': '',
        'desc_cobertura': '',
        'desc_base_cobertura': '',
        'desc_bloque_cobertura': '',
        'desc_en_linea': '',
        'qty_en_linea': '',
        'alertas': '',
    }


def comprobar_bloque(fila, registro, bloques):
    idx = registro.get('bloque')
    obj = registro.get('objeto')
    if idx is None or idx >= len(bloques):
        fila['alertas'] = 'bloque_fuera_de_rango'
        return None
    num, runs, texto = bloques[idx]
    if obj is not None and num != obj:
        fila['alertas'] = 'bloque_objeto_distinto'
        return None
    # El objeto real del bloque queda como evidencia, aunque el JSON no lo
    # guarde para las partes con P/N.
    fila['objeto'] = num
    return runs, texto


def auditar_parte(parte, aparicion, bloques):
    fila = fila_base('parte', aparicion, parte)
    comprobado = comprobar_bloque(fila, aparicion, bloques)
    if comprobado is None:
        return fila
    runs, texto = comprobado
    lineas = lineas_de(runs)

    candidatos = [i for i, l in enumerate(lineas)
                  if contiene_pn(l, parte['pn'])]
    if not candidatos:
        fila['pn_en_linea'] = 'no'
        fila['alertas'] = 'pn_no_en_linea'
        return fila
    fila['pn_en_linea'] = 'si'

    # La mencion del P/N puede estar en otra fila (p. ej. "use with..."):
    # se elige la linea cuya ventana explica mejor la descripcion base.
    base = desc_base(parte.get('descripcion'))
    idx = max(candidatos,
              key=lambda i: (cobertura(base, texto_ventana(lineas, i)), -i))
    ventana = texto_ventana(lineas, idx)
    cob = cobertura(parte.get('descripcion'), ventana)
    cob_base = cobertura(base, ventana)
    fila['desc_cobertura'] = '%.2f' % cob
    fila['desc_base_cobertura'] = '%.2f' % cob_base
    fila['desc_bloque_cobertura'] = '%.2f' % cobertura(base, texto)
    fila['desc_en_linea'] = 'si' if cob_base >= UMBRAL_DESC else 'no'
    qty = cantidad_de_linea(lineas[idx])
    fila['qty_en_linea'] = qty or 'n/d'

    alertas = []
    if cob_base < UMBRAL_DESC:
        alertas.append('desc_no_en_linea')
    if qty and aparicion.get('cantidad') and qty != str(aparicion['cantidad']):
        alertas.append('qty_distinta')
    fila['alertas'] = ';'.join(alertas)
    return fila


def indice_ancla(lineas, item, base):
    """Linea de la fila: empieza por el item (o designador) y la describe.

    El item va pegado a la descripcion ('350 Way Ribbon Cables'), por lo que
    no basta con exigir que el siguiente caracter no sea digito: hay
    descripciones que empiezan por numero. Se prefiere la linea cuya ventana
    explica la descripcion base.
    """
    pref = E.plano(str(item or ''))
    if not pref:
        return None
    exactos, amplios = [], []
    for i, linea in enumerate(lineas):
        p = E.plano(E.texto_de_linea(linea))
        if not p.startswith(pref):
            continue
        amplios.append(i)
        if len(p) == len(pref) or not p[len(pref)].isdigit():
            exactos.append(i)

    def mejor(candidatos):
        if not candidatos:
            return None
        i = max(candidatos,
                key=lambda j: (cobertura(base, texto_ventana(lineas, j)), -j))
        if cobertura(base, texto_ventana(lineas, i)) >= UMBRAL_DESC:
            return i
        return None

    elegido = mejor(exactos) or mejor(amplios)
    if elegido is not None:
        return elegido
    if exactos:
        return exactos[0]
    return amplios[0] if amplios else None


def auditar_sin_pn(item, bloques):
    fila = fila_base('sin-pn', item)
    comprobado = comprobar_bloque(fila, item, bloques)
    if comprobado is None:
        return fila
    runs, texto = comprobado
    lineas = lineas_de(runs)

    base = desc_base(item.get('descripcion'))
    cob_bloque = cobertura(base, texto)
    fila['desc_cobertura'] = '%.2f' % cobertura(item.get('descripcion'), texto)
    fila['desc_bloque_cobertura'] = '%.2f' % cob_bloque
    if not lineas:
        fila['alertas'] = 'desc_no_en_bloque'
        return fila

    # La fila se ancla por su item; si no hay item, por su designador.
    idx = indice_ancla(lineas, item.get('item'), base)
    anclada = idx is not None
    if idx is None and item.get('designador'):
        idx = indice_ancla(lineas, item.get('designador'), base)
        anclada = idx is not None
    if idx is None:
        idx = max(range(len(lineas)),
                  key=lambda i: cobertura(base, texto_ventana(lineas, i)))

    cob = cobertura(base, texto_ventana(lineas, idx))
    fila['desc_base_cobertura'] = '%.2f' % cob
    fila['desc_en_linea'] = 'si' if cob >= UMBRAL_DESC else 'no'
    # La cantidad solo se compara si la linea ancla es la fila real.
    qty = None
    if anclada or cob >= UMBRAL_DESC:
        qty = cantidad_de_linea(lineas[idx])
    fila['qty_en_linea'] = qty or 'n/d'

    alertas = []
    if cob_bloque < UMBRAL_DESC:
        alertas.append('desc_no_en_bloque')
    if qty and item.get('cantidad') and qty != str(item['cantidad']):
        alertas.append('qty_distinta')
    fila['alertas'] = ';'.join(alertas)
    return fila


def main():
    with open(os.path.join(RAIZ, 'datos', 'partes_cij.json'), encoding='utf-8') as f:
        datos = json.load(f)

    por_doc = {}
    for parte in datos['partes']:
        for ap in parte.get('apariciones', []):
            por_doc.setdefault(ap['documento'], []).append((parte, ap))
    for item in datos['items_sin_pn']:
        por_doc.setdefault(item['documento'], []).append((None, item))

    filas = []
    for doc in sorted(por_doc):
        print('Extrayendo %s ...' % doc, flush=True)
        bloques, _ = L.extraer_runs_visual(os.path.join(E.CARPETA, doc))
        print('  bloques=%d' % len(bloques), flush=True)
        for parte, registro in por_doc[doc]:
            if parte is None:
                filas.append(auditar_sin_pn(registro, bloques))
            else:
                filas.append(auditar_parte(parte, registro, bloques))

    os.makedirs(SALIDA, exist_ok=True)
    ruta_csv = os.path.join(SALIDA, 'auditoria_partes_cij.csv')
    campos = ['tipo_registro', 'pn', 'descripcion', 'estado', 'documento',
              'bloque', 'objeto', 'item', 'cantidad', 'pn_en_linea',
              'desc_cobertura', 'desc_base_cobertura', 'desc_bloque_cobertura',
              'desc_en_linea', 'qty_en_linea', 'alertas']
    with open(ruta_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=';')
        w.writeheader()
        w.writerows(filas)

    def cuenta(tipo, alerta):
        return sum(1 for x in filas
                   if x['tipo_registro'] == tipo and alerta in x['alertas'])

    partes = [x for x in filas if x['tipo_registro'] == 'parte']
    sinpn = [x for x in filas if x['tipo_registro'] == 'sin-pn']
    resumen = {
        'generado': date.today().isoformat(),
        'fuente': 'datos/partes_cij.json',
        'estado': 'borrador',
        'nota': ('Auditoria automatica de evidencia: comprueba que cada P/N y '
                 'descripcion existan en la linea/ventana del PDF de origen. No '
                 'corrige ni reconstruye datos; las alertas son candidatas a '
                 'revision visual.'),
        'apariciones_partes': len(partes),
        'items_sin_pn': len(sinpn),
        'alertas': {
            'partes': {
                'bloque_fuera_de_rango': cuenta('parte', 'bloque_fuera_de_rango'),
                'bloque_objeto_distinto': cuenta('parte', 'bloque_objeto_distinto'),
                'pn_no_en_linea': cuenta('parte', 'pn_no_en_linea'),
                'desc_no_en_linea': cuenta('parte', 'desc_no_en_linea'),
                'qty_distinta': cuenta('parte', 'qty_distinta'),
            },
            'sin_pn': {
                'bloque_fuera_de_rango': cuenta('sin-pn', 'bloque_fuera_de_rango'),
                'bloque_objeto_distinto': cuenta('sin-pn', 'bloque_objeto_distinto'),
                'desc_no_en_bloque': cuenta('sin-pn', 'desc_no_en_bloque'),
                'qty_distinta': cuenta('sin-pn', 'qty_distinta'),
            },
        },
        'partes_con_desc_en_ventana': sum(
            1 for x in partes if x['desc_en_linea'] == 'si'),
        'partes_con_desc_en_bloque': sum(
            1 for x in partes if x['desc_bloque_cobertura']
            and float(x['desc_bloque_cobertura']) >= UMBRAL_DESC),
        'sin_pn_con_desc_en_ventana': sum(
            1 for x in sinpn if x['desc_en_linea'] == 'si'),
        'sin_pn_con_desc_en_bloque': sum(
            1 for x in sinpn if x['desc_bloque_cobertura']
            and float(x['desc_bloque_cobertura']) >= UMBRAL_DESC),
        'pn_con_alertas': sorted({x['pn'] for x in partes if x['alertas']}),
        'archivo_csv': 'datos/analisis/auditoria_partes_cij.csv',
    }
    ruta_json = os.path.join(SALIDA, 'auditoria_partes_cij_resumen.json')
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1)
        f.write('\n')

    print('OK %s' % ruta_csv)
    print('OK %s' % ruta_json)
    print(json.dumps(resumen['alertas'], ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
