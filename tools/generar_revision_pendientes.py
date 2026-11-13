# -*- coding: utf-8 -*-
"""Genera los artefactos de revision de los pendientes documentales.

No corrige ni asciende datos: solo ordena la evidencia para que el dueno
pueda revisarla. Salidas en datos/analisis/:

  - partes_cij_ocr_revision.csv     193 P/N del OCR de los IPL 1550/1710.
  - partes_cij_ocr_apariciones.csv  277 apariciones con pagina/tabla/item.
  - conflictos_cij_ocr.md           los 5 P/N con descripciones incompatibles.
  - velocidades_cij_avisos.csv      filas con aviso de boquilla/modelo/fuente.
  - velocidades_cij_avisos.md       resumen de los 56 avisos.
  - PENDIENTES_REVISION.md          indice de todo lo que falta revisar.
  - revision_pendientes_resumen.json

Uso:
  python tools/generar_revision_pendientes.py
"""
import collections
import csv
import datetime
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
ANALISIS = os.path.join(DATOS, 'analisis')
OCR = os.path.join(DATOS, 'partes_cij_ocr.json')
CIJ = os.path.join(DATOS, 'partes_cij.json')
VELOCIDADES = os.path.join(DATOS, 'cij_velocidades.json')
VELOCIDADES_CSV = os.path.join(ANALISIS, 'velocidades_cij.csv')


def normalizar(texto):
    return re.sub(r'\s+', ' ', str(texto or '')).strip()


def unicos(valores):
    vistos = []
    for valor in valores:
        valor = normalizar(valor)
        if valor and valor not in vistos:
            vistos.append(valor)
    return vistos


def escribir_csv(ruta, campos, filas, delimitador=';'):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=delimitador)
        w.writerow(campos)
        w.writerows(filas)


def cargar_json(ruta):
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)


def pns_previos():
    datos = cargar_json(CIJ)
    return {p.get('pn') for p in datos.get('partes', []) if p.get('pn')}


def generar_partes_ocr(previos):
    datos = cargar_json(OCR)
    partes = datos.get('partes', [])
    filas = []
    apariciones = []
    conflictos = []
    for p in sorted(partes, key=lambda x: x.get('pn') or ''):
        pn = p.get('pn') or ''
        aps = p.get('apariciones') or []
        paginas = unicos(a.get('pagina') for a in aps)
        tablas = unicos(a.get('tabla') for a in aps)
        pns_ocr = unicos(a.get('pn_ocr') for a in aps)
        correcciones = unicos(
            c for a in aps for c in (a.get('correcciones_ocr') or []))
        fila = [
            pn,
            'si' if pn not in previos else 'no',
            normalizar(p.get('descripcion')),
            ' | '.join(p.get('descripciones') or []),
            'si' if p.get('conflicto_descripciones') else 'no',
            p.get('estado') or '',
            ' | '.join(p.get('modelos') or []),
            ' | '.join(p.get('documentos') or []),
            len(aps),
            ' | '.join(paginas),
            ' | '.join(tablas),
            ' | '.join(pns_ocr),
            ' | '.join(correcciones),
        ]
        filas.append(fila)
        if p.get('conflicto_descripciones'):
            conflictos.append(p)
        for a in aps:
            apariciones.append([
                pn,
                normalizar(a.get('descripcion')),
                normalizar(a.get('documento')),
                normalizar(a.get('modelo')),
                normalizar(a.get('pagina')),
                normalizar(a.get('tabla')),
                normalizar(a.get('item')),
                normalizar(a.get('cantidad')),
                normalizar(a.get('designador')),
                normalizar(a.get('grupo')),
                normalizar(a.get('conjunto')),
                normalizar(a.get('tipo')),
                normalizar(a.get('descripcion_ocr')),
                normalizar(a.get('pn_ocr')),
                ' | '.join(a.get('correcciones_ocr') or []),
                normalizar(a.get('metodo')),
            ])

    escribir_csv(
        os.path.join(ANALISIS, 'partes_cij_ocr_revision.csv'),
        ['pn', 'nuevo', 'descripcion', 'descripciones', 'conflicto', 'estado',
         'modelos', 'documentos', 'apariciones', 'paginas', 'tablas',
         'pn_ocr', 'correcciones_ocr'],
        filas)
    escribir_csv(
        os.path.join(ANALISIS, 'partes_cij_ocr_apariciones.csv'),
        ['pn', 'descripcion', 'documento', 'modelo', 'pagina', 'tabla', 'item',
         'cantidad', 'designador', 'grupo', 'conjunto', 'tipo',
         'descripcion_ocr', 'pn_ocr', 'correcciones_ocr', 'metodo'],
        apariciones)

    lineas = [
        '# Conflictos de descripcion en partes CIJ (OCR 1550/1710)',
        '',
        '> Evidencia leida de los IPL 1550 y 1710. No se elige una descripcion',
        '> por heuristica: las dos quedan registradas y el P/N sigue en estado',
        '> `borrador-decodificado` hasta la revision humana.',
        '',
        '| P/N | Descripcion principal | Descripciones detectadas | Modelos |',
        '|---|---|---|---|',
    ]
    for p in conflictos:
        lineas.append('| %s | %s | %s | %s |' % (
            p.get('pn'), normalizar(p.get('descripcion')),
            ' / '.join(p.get('descripciones') or []),
            ', '.join(p.get('modelos') or [])))
    lineas += ['', '## Evidencia por aparicion', '']
    for p in conflictos:
        lineas += ['### %s — %s' % (p.get('pn'),
                                    normalizar(p.get('descripcion'))),
                   '',
                   '| Documento | Pagina | Tabla | Item | Descripcion | P/N OCR | Correcciones |',
                   '|---|---|---|---|---|---|---|']
        for a in p.get('apariciones') or []:
            lineas.append('| %s | %s | %s | %s | %s | %s | %s |' % (
                normalizar(a.get('documento')), normalizar(a.get('pagina')),
                normalizar(a.get('tabla')), normalizar(a.get('item')),
                normalizar(a.get('descripcion')), normalizar(a.get('pn_ocr')),
                '; '.join(a.get('correcciones_ocr') or []) or '—'))
        lineas += ['', '**Lectura:** ambas descripciones son evidencia textual; '
                   'no se corrigen ni se fusionan sin confirmacion documental.',
                   '']
    ruta_conflictos = os.path.join(ANALISIS, 'conflictos_cij_ocr.md')
    with open(ruta_conflictos, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(lineas).rstrip() + '\n')

    resumen = datos.get('resumen') or {}
    return {
        'partes': len(partes),
        'registros': resumen.get('registros'),
        'apariciones': len(apariciones),
        'conflictos': len(conflictos),
        'nuevos': sum(1 for f in filas if f[1] == 'si'),
        'documentos': len(datos.get('documentos') or []),
        'paginas_ocr': resumen.get('paginas_ocr'),
        'items_sin_pn': len(datos.get('items_sin_pn') or []),
        'conflictos_pns': [p.get('pn') for p in conflictos],
    }


def generar_velocidades():
    datos = cargar_json(VELOCIDADES)
    resumen = datos.get('resumen') or {}
    with open(VELOCIDADES_CSV, encoding='utf-8-sig', newline='') as f:
        lector = csv.DictReader(f)
        campos = lector.fieldnames or []
        filas = list(lector)
    avisos = []
    for fila in filas:
        tipos = [t for t, campo in (
            ('boquilla', 'conflicto_boquilla'),
            ('modelo', 'conflicto_modelo'),
            ('fuente', 'conflicto_fuente')) if fila.get(campo) == 'si']
        if tipos:
            fila = dict(fila)
            fila['tipos_aviso'] = ';'.join(tipos)
            avisos.append(fila)
    escribir_csv(
        os.path.join(ANALISIS, 'velocidades_cij_avisos.csv'),
        campos + ['tipos_aviso'],
        [[a.get(c, '') for c in campos] + [a['tipos_aviso']] for a in avisos],
        delimitador=',')

    conteo = collections.Counter()
    for fila in avisos:
        for tipo in fila['tipos_aviso'].split(';'):
            conteo[tipo] += 1
    notas = datos.get('conflictos_documentados') or []
    lineas = [
        '# Avisos de velocidades CIJ',
        '',
        '> Los valores se conservan tal como los imprime el PDF oficial. Los',
        '> avisos senalan nombres de archivo o de carpeta que no coinciden con',
        '> lo impreso; no se corrige el dato ni se reconstruye la tabla.',
        '',
        '## Conteo',
        '',
        '| Tipo | Avisos |',
        '|---|---|',
        '| Boquilla | %d |' % conteo.get('boquilla', 0),
        '| Modelo | %d |' % conteo.get('modelo', 0),
        '| Fuente | %d |' % conteo.get('fuente', 0),
        '| **Total** | **%d** |' % sum(conteo.values()),
        '',
        'Entradas con al menos un aviso: **%d** de %d.' % (
            len(avisos), len(filas)),
        '',
        '## Notas documentadas',
        '',
    ]
    for nota in notas:
        lineas.append('- **%s** (%s): %s' % (
            nota.get('tipo'), nota.get('modelo'), nota.get('detalle')))
    lineas += [
        '',
        '## Criterio de revision',
        '',
        '- El valor impreso en el PDF y la carpeta oficial mandan.',
        '- El nombre de archivo desactualizado se conserva como evidencia, no',
        '  como correccion.',
        '- Cualquier cambio de valor exige volver al PDF y dejar la huella OCR.',
        '',
        'Detalle fila por fila: `velocidades_cij_avisos.csv`.',
    ]
    with open(os.path.join(ANALISIS, 'velocidades_cij_avisos.md'), 'w',
              encoding='utf-8', newline='') as f:
        f.write('\n'.join(lineas).rstrip() + '\n')

    return {
        'entradas': len(filas),
        'con_aviso': len(avisos),
        'avisos_boquilla': conteo.get('boquilla', 0),
        'avisos_modelo': conteo.get('modelo', 0),
        'avisos_fuente': conteo.get('fuente', 0),
        'total_avisos': sum(conteo.values()),
        'resumen': resumen,
    }


def generar_indice(ocr, vel):
    hoy = datetime.date.today().isoformat()
    lineas = [
        '# Pendientes de revision documental',
        '',
        '> Generado por `tools/generar_revision_pendientes.py` el %s.' % hoy,
        '> Esta carpeta es evidencia de revision: no modifica los datasets ni',
        '> asciende estados. Los datos siguen en `borrador-decodificado` hasta',
        '> que el dueno confirme contra el documento original.',
        '',
        '## Tablero',
        '',
        '| Pendiente | Cantidad | Estado | Artefacto |',
        '|---|---|---|---|',
        '| P/N del OCR 1550/1710 | %d | `borrador-decodificado` | `partes_cij_ocr_revision.csv` |' % ocr['partes'],
        '| Registros OCR con P/N | %d | %d apariciones unicas | `partes_cij_ocr_apariciones.csv` |' % (ocr['registros'], ocr['apariciones']),
        '| Conflictos de descripcion | %d | requiere revision humana | `conflictos_cij_ocr.md` |' % ocr['conflictos'],
        '| Avisos de velocidades | %d | valor impreso conservado | `velocidades_cij_avisos.csv` |' % vel['total_avisos'],
        '| Items sin P/N | %d | `sin-pn` | `items_sin_pn.csv` |' % ocr['items_sin_pn'],
        '| Partes TTO | 120 | `verificado` | `partes_tto_cotejo.csv` |',
        '',
        '## Conflictos que requieren confirmacion',
        '',
        'P/N con dos descripciones incompatibles en el OCR: **%s**.'
        % ', '.join(ocr.get('conflictos_pns') or []),
        '',
        'Ver `conflictos_cij_ocr.md` para la pagina, tabla e item de cada',
        'aparicion. No se elige una descripcion automaticamente.',
        '',
        '## Como revisar',
        '',
        '1. Abrir `partes_cij_ocr_revision.csv` y filtrar `conflicto = si` o',
        '   `nuevo = si` para priorizar.',
        '2. Para cada P/N dudoso, abrir la pagina indicada en',
        '   `partes_cij_ocr_apariciones.csv` y comparar la descripcion impresa',
        '   con `descripcion` y `descripcion_ocr`.',
        '3. No reconstruir P/N a mano. Si el OCR no alcanza, dejar el estado',
        '   actual y anotar la duda.',
        '4. Para velocidades, revisar `velocidades_cij_avisos.md`: el valor',
        '   impreso ya prevalece sobre el nombre de archivo.',
        '',
        '## Criterios',
        '',
        '- `verificado`: P/N confirmado y descripcion oficial coincidente.',
        '- `borrador-decodificado`: lectura OCR/decodificada pendiente de',
        '  confirmacion humana.',
        '- `sin-pn`: hardware sin numero impreso; no se inventa.',
        '- La traduccion es un dato separado; el texto original se conserva.',
        '',
        '## Resumen legible por maquina',
        '',
        '`revision_pendientes_resumen.json`.',
    ]
    with open(os.path.join(ANALISIS, 'PENDIENTES_REVISION.md'), 'w',
              encoding='utf-8', newline='') as f:
        f.write('\n'.join(lineas).rstrip() + '\n')

    resumen = {
        'generado': hoy,
        'fuente': 'datos/partes_cij_ocr.json + datos/cij_velocidades.json',
        'partes_cij_ocr': ocr,
        'velocidades_cij': {k: v for k, v in vel.items() if k != 'resumen'},
        'archivos': [
            'partes_cij_ocr_revision.csv',
            'partes_cij_ocr_apariciones.csv',
            'conflictos_cij_ocr.md',
            'velocidades_cij_avisos.csv',
            'velocidades_cij_avisos.md',
            'PENDIENTES_REVISION.md',
        ],
    }
    with open(os.path.join(ANALISIS, 'revision_pendientes_resumen.json'), 'w',
              encoding='utf-8', newline='') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1)
        f.write('\n')
    return resumen


def main():
    previos = pns_previos()
    ocr = generar_partes_ocr(previos)
    vel = generar_velocidades()
    generar_indice(ocr, vel)
    print('OK | P/N OCR=%d (nuevos=%d) | apariciones=%d | conflictos=%d'
          % (ocr['partes'], ocr['nuevos'], ocr['apariciones'],
             ocr['conflictos']))
    print('   | velocidades con aviso=%d de %d | avisos=%d (boquilla=%d, '
          'modelo=%d, fuente=%d)'
          % (vel['con_aviso'], vel['entradas'], vel['total_avisos'],
             vel['avisos_boquilla'], vel['avisos_modelo'],
             vel['avisos_fuente']))
    print('   -> datos/analisis/PENDIENTES_REVISION.md')


if __name__ == '__main__':
    main()
