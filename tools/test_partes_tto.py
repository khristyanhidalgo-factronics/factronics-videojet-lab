# -*- coding: utf-8 -*-
"""Valida el cotejo de las 120 partes TTO contra las listas oficiales 6330/6530.

Comprueba:
  - estructura y unicidad de P/N;
  - que cada parte tenga evidencia oficial (snapshot en el repo);
  - que cada registro oficial citado exista exactamente en el snapshot;
  - que las 23 descripciones inglesas agregadas sean la descripcion oficial;
  - que no se dupliquen descripciones ni se pierda la evidencia original;
  - que el CSV de cotejo tenga las 120 filas.

Si los Excel oficiales estan disponibles en el PC del dueño, tambien se
relee la fuente y se compara contra el snapshot. En CI se valida el snapshot.

Uso: python tools/test_partes_tto.py   (exit 0 = OK)
"""
import csv
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import cotejar_partes_tto as C  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

PARTES = os.path.join(RAIZ, 'datos', 'partes_tto.json')
SNAPSHOT = os.path.join(RAIZ, 'datos', 'extraccion',
                        'tto_oficial_6330_6530.json')
CSV_SALIDA = os.path.join(RAIZ, 'datos', 'analisis', 'partes_tto_cotejo.csv')
ESTADOS = {'verificado', 'borrador', 'por-definir'}


def main():
    fallos = []

    def exigir(cond, mensaje):
        if not cond:
            fallos.append(mensaje)

    for ruta in (PARTES, SNAPSHOT, CSV_SALIDA):
        if not os.path.exists(ruta):
            print('FALLO: falta %s' % os.path.relpath(ruta, RAIZ))
            return 1
    with open(PARTES, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    with open(SNAPSHOT, 'r', encoding='utf-8') as f:
        snap = json.load(f)

    exigir(datos.get('schema', 0) >= 3, 'schema antiguo: %r' % datos.get('schema'))
    partes = datos.get('partes') or []
    exigir(len(partes) == 120, 'partes=%d (se esperaban 120)' % len(partes))
    exigir(datos.get('total_partes_unicas') == len(partes),
           'total_partes_unicas no coincide')
    exigir(datos.get('estado_general') == 'verificado',
           'estado_general=%r' % datos.get('estado_general'))

    resumen = datos.get('resumen') or {}
    exigir(resumen.get('partes') == len(partes), 'resumen.partes no coincide')
    exigir(resumen.get('verificadas') == len(partes),
           'resumen.verificadas=%r' % resumen.get('verificadas'))
    exigir(resumen.get('sin_oficial') == 0,
           'hay %r partes sin evidencia oficial' % resumen.get('sin_oficial'))
    exigir(resumen.get('revisar_descripcion') == 0,
           'hay %r descripciones por revisar' % resumen.get('revisar_descripcion'))
    exigir(resumen.get('ingles_agregado_desde_oficial') == 23,
           'ingles_agregado_desde_oficial=%r (se esperaban 23)'
           % resumen.get('ingles_agregado_desde_oficial'))
    exigir(resumen.get('con_descripcion_inglesa') == len(partes),
           'no todas las partes tienen descripcion inglesa')

    # Snapshot de evidencia oficial
    registros = snap.get('registros') or []
    exigir(snap.get('total_registros') == len(registros),
           'snapshot.total_registros no coincide')
    exigir(snap.get('total_pn') == len({r.get('pn') for r in registros}),
           'snapshot.total_pn no coincide')
    exigir(len(snap.get('archivos') or []) == 2,
           'el snapshot debe cubrir 6330 y 6530')
    indice_snap = {}
    for r in registros:
        clave = (r.get('archivo'), r.get('hoja'), str(r.get('fila')),
                 r.get('pn'), r.get('descripcion'))
        exigir(all(clave), 'registro oficial incompleto: %r' % (r,))
        exigir(clave not in indice_snap,
               'registro oficial duplicado: %r' % (clave,))
        indice_snap[clave] = r.get('descripcion')

    # Si los Excel estan disponibles, se relee la fuente y se compara.
    if os.path.isdir(C.BASE_POR_DEFECTO):
        try:
            vivos, _archivos = C.leer_oficial(C.BASE_POR_DEFECTO)
            claves_vivas = {
                (r['archivo'], r['hoja'], str(r['fila']), r['pn'],
                 r['descripcion']) for r in vivos}
            exigir(claves_vivas == set(indice_snap),
                   'el snapshot no coincide con los Excel oficiales actuales')
            print('Fuente oficial releida: %d registros' % len(vivos))
        except Exception as exc:  # noqa: BLE001 - se informa como fallo
            fallos.append('no se pudieron releer los Excel oficiales: %s' % exc)
    else:
        print('AVISO: Excel oficiales no disponibles; se valida el snapshot.')

    vistos = set()
    agregadas = 0
    for p in partes:
        pn = C.pn_limpio(p.get('parte'))
        exigir(bool(pn), 'parte sin P/N')
        exigir(C.PN_RE.match(pn), 'P/N con formato inesperado: %r' % pn)
        exigir(pn not in vistos, 'P/N duplicado: %r' % pn)
        vistos.add(pn)
        exigir(p.get('estado') in ESTADOS,
               '%s: estado no permitido: %r' % (pn, p.get('estado')))
        exigir(p.get('estado') == 'verificado',
               '%s: no quedo verificado' % pn)

        descripciones = p.get('descripciones') or []
        exigir(bool(descripciones), '%s: sin descripciones' % pn)
        claves_desc = []
        for d in descripciones:
            exigir(d.get('idioma'), '%s: descripcion sin idioma' % pn)
            exigir(d.get('fuente'), '%s: descripcion sin fuente' % pn)
            exigir((d.get('texto') or '').strip(),
                   '%s: descripcion vacia' % pn)
            claves_desc.append((d.get('idioma'), d.get('fuente'),
                                d.get('texto')))
        exigir(len(claves_desc) == len(set(claves_desc)),
               '%s: descripciones duplicadas' % pn)

        inglesas = [d for d in descripciones if d.get('idioma') == 'ingles']
        exigir(bool(inglesas), '%s: sin descripcion inglesa' % pn)

        cotejo = p.get('cotejo') or {}
        exigir(cotejo.get('oficial_encontrado') is True,
               '%s: cotejo sin evidencia oficial' % pn)
        regs = cotejo.get('registros_oficiales') or []
        exigir(bool(regs), '%s: cotejo sin registros oficiales' % pn)
        for r in regs:
            clave = (r.get('archivo'), r.get('hoja'), str(r.get('fila')),
                     r.get('pn'), r.get('descripcion'))
            exigir(clave in indice_snap,
                   '%s: registro oficial no esta en el snapshot: %r'
                   % (pn, clave))
            exigir(r.get('pn') == pn,
                   '%s: registro oficial de otro P/N' % pn)
        exigir(cotejo.get('coincide_descripcion_inglesa') is True,
               '%s: descripcion no marcada como coincidente' % pn)
        ratio = cotejo.get('ratio_similitud')
        exigir(isinstance(ratio, (int, float)) and ratio >= C.UMBRAL,
               '%s: ratio invalido %r' % (pn, ratio))
        exigir(bool((cotejo.get('descripcion_oficial_usada') or '').strip()),
               '%s: sin descripcion oficial usada' % pn)

        if cotejo.get('agrego_descripcion_inglesa'):
            agregadas += 1
            texto = cotejo.get('descripcion_oficial_usada')
            exigir(any(d.get('fuente', '').startswith('official-parts-list-')
                       and d.get('texto') == texto for d in inglesas),
                   '%s: no se encuentra la descripcion oficial agregada' % pn)
        else:
            exigir(any(d.get('texto') == cotejo.get('descripcion_inglesa_antes')
                       for d in inglesas),
                   '%s: no se conserva la descripcion inglesa original' % pn)

    exigir(agregadas == 23, 'descripciones agregadas=%d (se esperaban 23)'
           % agregadas)

    # CSV de revision
    with open(CSV_SALIDA, 'r', encoding='utf-8', newline='') as f:
        filas = list(csv.DictReader(f))
    exigir(len(filas) == len(partes),
           'CSV con %d filas (se esperaban %d)' % (len(filas), len(partes)))
    exigir({r.get('pn') for r in filas} == vistos,
           'el CSV no cubre los mismos P/N')
    for r in filas:
        exigir(r.get('estado') == 'verificado',
               'CSV: %s no verificado' % r.get('pn'))
        exigir(r.get('oficial_encontrado') == 'si',
               'CSV: %s sin evidencia oficial' % r.get('pn'))
        exigir(r.get('accion') in (
            'pn-y-descripcion-verificados',
            'pn-confirmado-descripcion-oficial-agregada'),
            'CSV: %s accion inesperada %r' % (r.get('pn'), r.get('accion')))

    if fallos:
        for f in fallos[:50]:
            print('FALLO:', f)
        print('%d fallo(s)' % len(fallos))
        return 1
    print('OK partes_tto: %d partes verificadas, %d descripciones inglesas '
          'agregadas, %d registros oficiales de evidencia'
          % (len(partes), agregadas, len(registros)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
