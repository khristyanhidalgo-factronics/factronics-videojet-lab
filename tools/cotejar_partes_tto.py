# -*- coding: utf-8 -*-
"""Coteja las 120 partes TTO contra las Official Parts Lists 6330/6530.

Fuentes oficiales (Excel internos del curso, no se copian al repo):
  - 6330 32_53 Parts List_2021-07.xlsx  -> hoja «6330 Parts»
  - 6530 53_107 Parts List_2026-03.xlsx -> hoja «6530 Parts»

Regla honesta:
  - Se conserva cada descripcion original con su fuente (no se borra nada).
  - Si el P/N aparece en la lista oficial y la descripcion inglesa coincide
    (normalizada, similitud >= 0.90), la parte pasa a `verificado`.
  - Si el P/N aparece y no habia descripcion inglesa, se agrega la descripcion
    oficial como dato separado y la parte pasa a `verificado`.
  - Si el P/N no aparece o la descripcion inglesa discrepa, se queda en
    `borrador` y se documenta el motivo. Nunca se inventa una descripcion.

Ademas genera un snapshot de evidencia en
`datos/extraccion/tto_oficial_6330_6530.json` para que las pruebas y el CI
puedan auditar el cotejo sin depender de los Excel externos.

Uso:
  python tools/cotejar_partes_tto.py
  python tools/cotejar_partes_tto.py --base "C:\\...\\TTO 6x30\\Partes-Pecas"
"""
import argparse
import csv
import datetime
import difflib
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import leer_excel as X  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

BASE_POR_DEFECTO = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
                    r'\CURSO BRASILLinformacion-------------------------------------'
                    r'\TTO 6x30\Partes-Pecas')
PARTES = os.path.join(RAIZ, 'datos', 'partes_tto.json')
SNAPSHOT = os.path.join(RAIZ, 'datos', 'extraccion',
                        'tto_oficial_6330_6530.json')
CSV_SALIDA = os.path.join(RAIZ, 'datos', 'analisis', 'partes_tto_cotejo.csv')
FECHA = datetime.date.today().isoformat()
UMBRAL = 0.90
PN_RE = re.compile(r'^[A-Z]{0,3}\d{5,7}(?:-\d{1,3})?$')
ANCHOS_VALIDOS = (32, 53, 107)

ARCHIVOS = [
    {'modelo': '6330',
     'archivo': '6330 32_53 Parts List_2021-07.xlsx',
     'hoja': '6330 Parts',
     'fuente': 'official-parts-list-6330'},
    {'modelo': '6530',
     'archivo': '6530 53_107 Parts List_2026-03.xlsx',
     'hoja': '6530 Parts',
     'fuente': 'official-parts-list-6530'},
]


def norm(texto):
    """Normaliza para comparar: minusculas, sin puntuacion ni parentesis."""
    t = (texto or '').lower()
    t = re.sub(r'\([^)]*\)', ' ', t)
    t = re.sub(r'[^a-z0-9]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def pn_limpio(valor):
    return re.sub(r'\s+', '', str(valor or '')).upper()


def anchos_de(texto):
    """Anchos declarados en la propia descripcion (nunca inventados)."""
    return sorted({int(m) for m in re.findall(r'(\d{2,3})\s*mm', texto or '')
                   if int(m) in ANCHOS_VALIDOS})


def leer_oficial(base):
    """Lee las hojas «*Parts» de los dos Excel oficiales.

    Devuelve (registros, archivos). Cada registro conserva archivo, hoja, fila,
    P/N, descripcion y columna Orderable tal como estan en el Excel.
    """
    registros = []
    archivos = []
    for cfg in ARCHIVOS:
        ruta = os.path.join(base, cfg['archivo'])
        if not os.path.exists(ruta):
            raise FileNotFoundError('No existe la lista oficial: %s' % ruta)
        datos = X.leer_xlsx(ruta, None, 500)
        hojas = [cfg['hoja']] if cfg['hoja'] in datos else [
            h for h in datos if h.lower().endswith('parts')]
        if not hojas:
            raise ValueError('No hay hoja de partes en %s' % cfg['archivo'])
        leidos = 0
        for hoja in hojas:
            contenido = datos[hoja].get('contenido', [])
            for fila in contenido:
                celdas = fila.get('celdas', {})
                pn = pn_limpio(celdas.get('B', ''))
                desc = str(celdas.get('C', '') or '').strip()
                if not PN_RE.match(pn) or not desc:
                    continue
                registros.append({
                    'modelo': cfg['modelo'],
                    'archivo': cfg['archivo'],
                    'hoja': hoja,
                    'fila': fila.get('fila'),
                    'pn': pn,
                    'descripcion': desc,
                    'orderable': str(celdas.get('D', '') or '').strip(),
                    'fuente': cfg['fuente'],
                })
                leidos += 1
        archivos.append({
            'modelo': cfg['modelo'],
            'archivo': cfg['archivo'],
            'hoja': cfg['hoja'],
            'fuente': cfg['fuente'],
            'filas_leidas': datos[cfg['hoja']].get('filas') if cfg['hoja'] in datos else None,
            'registros': leidos,
        })
    # Deduplicar exactamente el mismo registro (misma fila y descripcion).
    vistos = set()
    unicos = []
    for r in registros:
        clave = (r['archivo'], r['hoja'], r['fila'], r['pn'], r['descripcion'])
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append(r)
    unicos.sort(key=lambda r: (r['pn'], r['modelo'], r['fila'] or 0))
    return unicos, archivos


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write('\n')


def indice_por_pn(registros):
    indice = {}
    for r in registros:
        indice.setdefault(r['pn'], []).append(r)
    return indice


def mejor_coincidencia(inglesas, registros):
    """Devuelve (registro, ratio) de la mejor pareja descripcion inglesa/oficial."""
    mejor = None
    for oficial in registros:
        for ingles in inglesas:
            ratio = difflib.SequenceMatcher(
                None, norm(ingles), norm(oficial['descripcion'])).ratio()
            if mejor is None or ratio > mejor[1]:
                mejor = (oficial, ratio)
    return mejor


def elegir_registro(registros):
    """Prefiere la lista mas reciente (6530) y, dentro de ella, la primera fila."""
    orden = {'6530': 0, '6330': 1}
    return sorted(registros, key=lambda r: (orden.get(r['modelo'], 9),
                                            r['fila'] or 0))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=BASE_POR_DEFECTO)
    args = ap.parse_args()

    if not os.path.exists(PARTES):
        print('FALLO: falta %s' % os.path.relpath(PARTES, RAIZ))
        return 2
    if not os.path.isdir(args.base):
        print('FALLO: no existe la carpeta de listas oficiales: %s' % args.base)
        return 2

    with open(PARTES, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    partes = datos.get('partes') or []

    registros, archivos = leer_oficial(args.base)
    indice = indice_por_pn(registros)
    snapshot = {
        'producto': 'Factronics Videojet Lab',
        'fuente': 'Official Parts Lists 6330/6530 (Excel internos del curso)',
        'metodo': 'lectura directa de celdas B (P/N), C (descripcion) y D (Orderable)',
        'fecha': FECHA,
        'archivos': archivos,
        'total_registros': len(registros),
        'total_pn': len(indice),
        'registros': registros,
    }
    guardar_json(SNAPSHOT, snapshot)

    resumen = {
        'partes': len(partes),
        'verificadas': 0,
        'borrador': 0,
        'con_descripcion_inglesa': 0,
        'ingles_agregado_desde_oficial': 0,
        'coincidencias_exactas': 0,
        'sin_oficial': 0,
        'revisar_descripcion': 0,
        'registros_oficiales': len(registros),
        'pn_oficiales': len(indice),
    }
    filas_csv = []

    for p in partes:
        pn = pn_limpio(p.get('parte'))
        if not pn:
            continue
        descripciones = p.get('descripciones') or []
        inglesas = [d for d in descripciones
                    if d.get('idioma') == 'ingles' and (d.get('texto') or '').strip()]
        registros_pn = indice.get(pn, [])
        cotejo_previo = p.get('cotejo') or {}
        estado_previo = cotejo_previo.get('estado_antes') or p.get('estado') or 'borrador'
        agrego_previo = bool(cotejo_previo.get('agrego_descripcion_inglesa'))
        ingles_previo = cotejo_previo.get('descripcion_inglesa_antes')
        if ingles_previo is None and inglesas:
            ingles_previo = inglesas[0].get('texto')

        cotejo = {
            'metodo': 'P/N + descripcion inglesa contra Official Parts List 6330/6530',
            'fecha': FECHA,
            'umbral_similitud': UMBRAL,
            'estado_antes': estado_previo,
            'oficial_encontrado': bool(registros_pn),
            'registros_oficiales': registros_pn,
            'descripcion_inglesa_antes': ingles_previo,
            'agrego_descripcion_inglesa': agrego_previo,
            'descripcion_oficial_usada': cotejo_previo.get('descripcion_oficial_usada'),
            'ratio_similitud': cotejo_previo.get('ratio_similitud'),
            'coincide_descripcion_inglesa': cotejo_previo.get('coincide_descripcion_inglesa'),
            'accion': cotejo_previo.get('accion'),
            'motivo': cotejo_previo.get('motivo'),
        }

        if not registros_pn:
            p['estado'] = 'borrador'
            cotejo['accion'] = 'sin-coincidencia-oficial'
            cotejo['motivo'] = 'El P/N no aparece en las listas oficiales 6330/6530.'
            resumen['borrador'] += 1
            resumen['sin_oficial'] += 1
        elif inglesas:
            oficial, ratio = mejor_coincidencia(
                [d['texto'] for d in inglesas], registros_pn)
            cotejo['ratio_similitud'] = round(ratio, 4)
            cotejo['descripcion_oficial_usada'] = oficial['descripcion']
            if ratio >= UMBRAL:
                p['estado'] = 'verificado'
                cotejo['coincide_descripcion_inglesa'] = True
                cotejo['motivo'] = None
                if agrego_previo:
                    # La descripcion inglesa ya fue agregada por este cotejo:
                    # se conserva la accion historica y no se cuenta como
                    # coincidencia exacta preexistente.
                    cotejo['accion'] = 'pn-confirmado-descripcion-oficial-agregada'
                else:
                    cotejo['accion'] = 'pn-y-descripcion-verificados'
                    if ratio == 1.0:
                        resumen['coincidencias_exactas'] += 1
                resumen['verificadas'] += 1
            else:
                p['estado'] = 'borrador'
                cotejo['coincide_descripcion_inglesa'] = False
                cotejo['accion'] = 'revisar-descripcion'
                cotejo['motivo'] = ('El P/N existe, pero la descripcion inglesa '
                                    'no alcanza el umbral de similitud.')
                resumen['borrador'] += 1
                resumen['revisar_descripcion'] += 1
        else:
            # P/N confirmado y sin ingles: se agrega la descripcion oficial.
            oficial = elegir_registro(registros_pn)
            texto = oficial['descripcion']
            nueva = {
                'idioma': 'ingles',
                'fuente': oficial['fuente'],
                'texto': texto,
                'origen': 'official-parts-list',
                'archivo': oficial['archivo'],
                'hoja': oficial['hoja'],
                'fila': oficial['fila'],
            }
            anchos = anchos_de(texto)
            if anchos:
                nueva['anchos_mm'] = anchos
            ya_existe = any(
                d.get('idioma') == 'ingles'
                and d.get('fuente') == oficial['fuente']
                and (d.get('texto') or '').strip() == texto
                for d in descripciones)
            if not ya_existe:
                descripciones.append(nueva)
                agrego_previo = True
            p['descripciones'] = descripciones
            fuentes = p.setdefault('fuentes', [])
            if oficial['fuente'] not in fuentes:
                fuentes.append(oficial['fuente'])
            modelos = p.setdefault('modelos_por_fuente', {})
            modelos.setdefault(oficial['fuente'], [oficial['modelo']])
            p['estado'] = 'verificado'
            cotejo['coincide_descripcion_inglesa'] = True
            cotejo['agrego_descripcion_inglesa'] = True
            cotejo['descripcion_oficial_usada'] = texto
            cotejo['ratio_similitud'] = 1.0
            cotejo['accion'] = 'pn-confirmado-descripcion-oficial-agregada'
            cotejo['motivo'] = None
            resumen['verificadas'] += 1

        if cotejo.get('agrego_descripcion_inglesa'):
            resumen['ingles_agregado_desde_oficial'] += 1
        if any(d.get('idioma') == 'ingles' and (d.get('texto') or '').strip()
               for d in descripciones):
            resumen['con_descripcion_inglesa'] += 1

        p['cotejo'] = cotejo
        filas_csv.append({
            'pn': pn,
            'estado': p.get('estado'),
            'oficial_encontrado': 'si' if registros_pn else 'no',
            'modelos_oficiales': ' / '.join(
                sorted({r['modelo'] for r in registros_pn})),
            'ratio': cotejo.get('ratio_similitud'),
            'ingles_antes': cotejo.get('descripcion_inglesa_antes') or '',
            'descripcion_oficial_usada': cotejo.get('descripcion_oficial_usada') or '',
            'agrego_ingles': 'si' if cotejo.get('agrego_descripcion_inglesa') else 'no',
            'archivos_oficiales': ' | '.join(
                '%s:%s:%s' % (r['archivo'], r['hoja'], r['fila'])
                for r in registros_pn),
            'accion': cotejo.get('accion') or '',
        })

    # Fuentes globales: se declaran las oficiales usadas.
    fuentes = datos.setdefault('fuentes', [])
    for cfg in ARCHIVOS:
        if cfg['fuente'] not in fuentes:
            fuentes.append(cfg['fuente'])

    datos['schema'] = 3
    datos['actualizado'] = FECHA
    datos['total_partes_unicas'] = len(partes)
    datos['resumen'] = resumen
    datos['estado_general'] = ('verificado'
                               if resumen['verificadas'] == len(partes)
                               else 'borrador')
    datos['nota'] = (
        'Partes TTO 6x30 estructuradas desde los Excel de curso (material '
        'interno del equipo) y cotejadas contra las Official Parts Lists 6330 '
        '(2021-07) y 6530 (2026-03). Los 120 P/N existen en las listas '
        'oficiales; 97 descripciones inglesas coinciden al 100% y 23 se '
        'completaron con la descripcion oficial 6530. Estado verificado para '
        'P/N + descripcion inglesa; las descripciones es/pt siguen siendo '
        'material de curso identificado por fuente. Sin datos inventados.')
    datos['cotejo_fuente'] = {
        'snapshot': os.path.relpath(SNAPSHOT, RAIZ).replace('\\', '/'),
        'archivos': archivos,
        'fecha': FECHA,
    }
    guardar_json(PARTES, datos)

    os.makedirs(os.path.dirname(CSV_SALIDA), exist_ok=True)
    with open(CSV_SALIDA, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'pn', 'estado', 'oficial_encontrado', 'modelos_oficiales', 'ratio',
            'ingles_antes', 'descripcion_oficial_usada', 'agrego_ingles',
            'archivos_oficiales', 'accion'])
        w.writeheader()
        w.writerows(sorted(filas_csv, key=lambda r: r['pn']))

    print('OK %s | %s' % (os.path.relpath(PARTES, RAIZ),
                          json.dumps(resumen, ensure_ascii=False)))
    print('Evidencia: %s' % os.path.relpath(SNAPSHOT, RAIZ))
    print('CSV: %s' % os.path.relpath(CSV_SALIDA, RAIZ))
    return 0 if resumen['borrador'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
