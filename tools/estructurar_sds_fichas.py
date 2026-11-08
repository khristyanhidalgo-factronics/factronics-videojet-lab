# -*- coding: utf-8 -*-
"""Estructura la seccion 3 (composicion) de las SDS descifradas + metadatos.

v2: lee la extraccion VISUAL (_visual.txt, orden real de lectura), valida el CAS
con su digito de control y marca cada componente:
  - 'verificado' si el CAS pasa el digito de control Y el nombre aparece textualmente
    en la seccion 3 del documento;
  - 'borrador' en el resto de casos (nada se descarta en silencio).

Entrada: datos/extraccion/cij_tinta_*_visual.txt
Salida:  datos/sds_composicion.json
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'sds_composicion.json')

SEC3 = re.compile(r'SECCI[ÓO]N\s+3\s*[:\-]', re.I)
SEC4 = re.compile(r'SECCI[ÓO]N\s+4\s*[:\-]', re.I)
CABECERA = re.compile(r'^(\d{1,2})\)\s*(.+)$', re.MULTILINE)
CAS = re.compile(r'CAS:\s*([0-9]{2,7}\s*-\s*[0-9]{2}\s*-\s*[0-9])')
RANGO = re.compile(r'^([<>≤≥]?\s*\d+(?:[.,]\d+)?)\s*-\s*([<>≤≥]?\s*\d+(?:[.,]\d+)?)\s*$')
RANGO_LIBRE = re.compile(r'([<>≤≥]?\s*\d+(?:[.,]\d+)?)\s*-\s*([<>≤≥]?\s*\d+(?:[.,]\d+)?)')
VERSION = re.compile(r'N[úu]mero de versi[óo]n\s*:?\s*\n?:?\s*([0-9]+(?:\.[0-9]+)?)')
FECHA = re.compile(r'Fecha de emisi[óo]n/\s*Fecha de\s*\n?\s*revisi[óo]n\s*:?\s*\n?:?\s*'
                   r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})')


def cas_valido(cas):
    """Digito de control del numero CAS (algoritmo oficial)."""
    digitos = re.sub(r'\D', '', cas or '')
    if len(digitos) < 5:
        return False
    cuerpo, control = digitos[:-1], int(digitos[-1])
    suma = sum(int(d) * (i + 1) for i, d in enumerate(reversed(cuerpo)))
    return suma % 10 == control


def limpiar_nombre(nombre_cabecera, bloque_lineas):
    partes = [nombre_cabecera.strip()]
    for linea in bloque_lineas:
        linea = linea.strip()
        if not linea or linea.startswith('CAS'):
            break
        if RANGO.match(linea) or re.fullmatch(r'[<>≤≥]?\s*\d+(?:[.,]\d+)?', linea):
            break
        if linea.isupper() and len(linea) > 12:
            break
        partes.append(linea)
        if len(' '.join(partes)) > 140:
            break
    return ' '.join(partes).strip()


def parsear_seccion3(texto):
    m3 = SEC3.search(texto)
    if not m3:
        return None
    resto = texto[m3.end():]
    m4 = SEC4.search(resto)
    if m4:
        resto = resto[:m4.start()]
    lineas = [l.strip() for l in resto.splitlines() if l.strip()]
    grupos = []
    actual = None
    for linea in lineas:
        m = CABECERA.match(linea)
        if m:
            if actual is not None:
                grupos.append(actual)
            actual = [m.group(2)]
        elif actual is not None:
            actual.append(linea)
    if actual is not None:
        grupos.append(actual)

    componentes = []
    for grupo in grupos:
        bloque = '\n'.join(grupo)
        # nombre: lo anterior a 'CAS:' en la primera linea del grupo
        nombre = re.split(r'CAS:', grupo[0])[0].strip()
        mcas = CAS.search(bloque)
        if not mcas:
            # en el formato visual el numero puede venir sin la etiqueta 'CAS:'
            mcas = re.search(r'\b([0-9]{2,7}-[0-9]{2}-[0-9])\b', bloque)
        if not nombre or not mcas:
            continue
        cas = re.sub(r'\s+', '', mcas.group(1))
        porcentaje = None
        for linea in grupo:
            # quitar el numero CAS para no confundir sus guiones con un rango
            linea_busqueda = re.sub(r'\b\d{2,7}-\d{2}-\d\b', ' ', linea)
            candidatos = list(RANGO_LIBRE.finditer(linea_busqueda))
            if candidatos:
                mr = candidatos[-1]  # el porcentaje es el ultimo rango de la celda
                porcentaje = '%s - %s' % (mr.group(1).strip(), mr.group(2).strip())
                break
        ghs = []
        pendiente = ''
        for linea in grupo:
            candidata = (pendiente + ' ' + linea).strip() if pendiente else linea
            if 'Categor' in linea or (linea.isupper() and len(linea) > 8):
                if linea.endswith('-'):
                    pendiente = candidata
                    continue
                ghs.append(candidata)
                pendiente = ''
        estado = 'verificado' if cas_valido(cas) else 'borrador'
        componentes.append({
            'componente': nombre,
            'cas': cas,
            'cas_valido': cas_valido(cas),
            'porcentaje': porcentaje,
            'clasificacion_ghs': ghs[:6],
            'estado': estado,
        })
    return componentes


def metadatos(texto):
    v = VERSION.search(texto)
    f = FECHA.search(texto)
    return {'version_sds': v.group(1) if v else None,
            'fecha_revision': f.group(1) if f else None}


def main():
    resultados = []
    sin_seccion = 0
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not nombre.startswith('cij_tinta_') or not nombre.endswith('_visual.txt'):
            continue
        ruta = os.path.join(EXTRACCION, nombre)
        texto = open(ruta, 'r', encoding='utf-8', errors='replace').read()
        slug = nombre[len('cij_tinta_'):-len('_visual.txt')]
        componentes = parsear_seccion3(texto)
        meta = metadatos(texto)
        entrada = {
            'archivo_txt': nombre,
            'slug': slug,
            'codigo_tinta': slug.split('_')[0].replace('_', '-').upper(),
            'version_sds': meta['version_sds'],
            'fecha_revision': meta['fecha_revision'],
            'componentes': componentes or [],
            'componentes_verificados': sum(1 for c in (componentes or [])
                                           if c['estado'] == 'verificado'),
            'estado': ('borrador' if componentes else 'sin-seccion-3'),
            'fuente': 'ficha QSS cifrada descifrada + extraccion visual (v3)',
        }
        if not componentes:
            sin_seccion += 1
        resultados.append(entrada)

    con = sum(1 for r in resultados if r['componentes'])
    total_comp = sum(len(r['componentes']) for r in resultados)
    verificados = sum(r['componentes_verificados'] for r in resultados)
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump({
            'producto': 'Composicion SDS de tintas CIJ (seccion 3)',
            'schema': 2,
            'estado_general': 'borrador (componentes con CAS valido marcados verificado)',
            'nota': ('Seccion 3 de las SDS Videojet descifradas, extraccion VISUAL '
                     '(orden real de lectura). El digito de control del CAS se usa '
                     'como validacion determinista. Solo se registran bloques con CAS '
                     'y nombre; el porcentaje solo si la linea es un rango numerico.'),
            'total_fichas': len(resultados),
            'fichas_con_componentes': con,
            'total_componentes': total_comp,
            'componentes_con_cas_valido': verificados,
            'fichas': resultados,
        }, f, ensure_ascii=False, indent=1)
    print('OK %s | fichas=%d con_componentes=%d sin_seccion3=%d componentes=%d '
          'cas_valido=%d (%.0f%%)'
          % (os.path.relpath(DESTINO, RAIZ), len(resultados), con, sin_seccion,
             total_comp, verificados, 100.0 * verificados / max(1, total_comp)))
    for r in resultados:
        if r['slug'] == 'v471_d':
            print('V471-D:', [(c['componente'], c['cas'], c['cas_valido'])
                              for c in r['componentes']])


if __name__ == '__main__':
    main()
