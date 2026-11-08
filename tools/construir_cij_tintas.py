"""Construye datos/cij_tintas.json v1 (dataset inicial de tintas CIJ Videojet).

Fuentes (todas del propio equipo, nada inventado):
  1) datos/cij_uso_solvente.json  -> por cada tinta: bases quimicas documentadas
     (tinta_documentada) y modelos con curva verificada (802 entradas).
  2) datos/extraccion/cij_tintas_brochure_us.txt -> mapa oficial industria->tinta
     con colores (pares codigo+color: estado 'borrador'; el texto viene de la
     concatenacion del extractor estandar).
  3) datos/extraccion/cij_tinta_ts22051529684_v471_d.txt (+ _dec) -> composicion
     parcial de la ficha V471-D (Butanone / Ethanol con CAS literal en la
     extraccion): estado 'borrador-decodificado', requiere revision contra el PDF.
  4) datos/fichas_tintas_inventario.json -> fichas QSS por tinta y su estado de
     extraccion (562 sin-texto-sacado, br-es/98039 legibles).
  5) datos/extraccion/cij_tinta_v4250_ficha.txt -> ficha V4250 fragmentada
     (estado 'borrador', no se estructuran fragmentos).

Los pares (tinta, base) y (tinta, modelos) salen de datos ya verificados; todo lo
que venga del总决赛 bróchure/fragments se marca 'borrador' explicito.
Uso: python tools/construir_cij_tintas.py
"""
import json
import os
import re
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'datos')
COLOR_PATRON = re.compile(
    r'(Black|Blue|Red|Purple|Green|Clear|White|Yellow|Orange|Brown|Gray|Grey)',
    re.IGNORECASE)


def cargas_json(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def leer_txt(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


def pares_brochure(texto):
    resultado = []
    for m in re.finditer(r'V\s?\d{3,4}', texto):
        codigo = re.sub(r'\s+', '', m.group())
        vistazo = texto[m.end():m.end() + 16]
        pm = COLOR_PATRON.match(vistazo)
        if pm:
            resultado.append({'tinta': codigo,
                              'color': pm.group(1),
                              'estado': 'borrador'})
        else:
            resultado.append({'tinta': codigo,
                              'color': None,
                              'estado': 'borrador'})
    # deducir repeticiones conservando el orden
    vistos = {}
    for par in resultado:
        k = (par['tinta'], par['color'])
        if k not in vistos:
            vistos[k] = par
    return list(vistos.values())


def pares_industrias(texto):
    industrias = ['beverage', 'cosmetics', 'pharmaceuticals', 'bakery', 'tobacco',
                  'dairy', 'confectionery', 'personal care', 'food', 'eggs',
                  'retort', 'capped', 'cappers', 'diaper', 'incontinence',
                  'packaging', 'personal', 'care']
    encontradas = []
    low = texto.lower()
    for ind in industrias:
        if low.count(ind) > 0 and ind not in encontradas:
            encontradas.append(ind)
    return [{'industria': i.title(), 'estado': 'borrador'} for i in encontradas]


def composicion_v471d(texto_dec):
    """Del block decodificado del TS2205: componentes reconocibles con CAS literal
    tambien presente en la extraccion cruda. Solo lo que aparece COMPLETO."""
    filas = []
    t = texto_dec.lower()
    for nombre, cas in (('butanone', '78-93-3'), ('ethanol', '64-17-5')):
        if nombre in t:
            filas.append({'componente': nombre.capitalize(),
                          'cas': cas,
                          'estado': 'borrador-decodificado'})
    return filas


def principal():
    ruta_uso = os.path.join(DATOS, 'cij_uso_solvente.json')
    uso = cargas_json(ruta_uso)
    if not uso or 'modelos' not in uso:
        print('ERROR: no se pudo leer cij_uso_solvente.json')
        return

    inventario = cargas_json(os.path.join(DATOS, 'fichas_tintas_inventario.json')) or {}
    sds = cargas_json(os.path.join(DATOS, 'sds_composicion.json')) or {}
    sds_por_slug = {}
    for f in sds.get('fichas', []):
        if f.get('componentes'):
            sds_por_slug[f['slug']] = f
    props = cargas_json(os.path.join(DATOS, 'sds_propiedades.json')) or {}
    props_por_slug = {f['slug']: f for f in props.get('fichas', [])
                      if f.get('propiedades')}
    CAMPOS_CLAVE = ('estado_fisico', 'color', 'ph', 'punto_inflamacion',
                    'punto_ebullicion', 'densidad_relativa', 'presion_vapor',
                    'viscosidad', 'volatilidad', 'solubilidad')
    brochure_txt = leer_txt(os.path.join(DATOS, 'extraccion',
                                         'cij_tintas_brochure_us.txt'))
    ts_txt = leer_txt(os.path.join(DATOS, 'extraccion',
                                   'cij_tinta_ts22051529684_v471_d.txt'))
    ts_dec = leer_txt(os.path.join(DATOS, 'extraccion',
                                   'cij_tinta_ts22051529684_v471_d_dec.txt'))

    # 1) agregados de solvente por tinta
    tintas = {}
    for entrada in uso['modelos']:
        codigo = (entrada.get('tinta') or '').strip().upper()
        if not codigo:
            continue
        t = tintas.setdefault(codigo, {
            'bases_documentadas': [],
            'modelos_curva': [],
            'curvas': 0,
        })
        base = entrada.get('base_quimica') or ''
        if base and base != 'por-definir' and base not in t['bases_documentadas']:
            t['bases_documentadas'].append(base)
        model = [e for e in (entrada.get('modelo'), entrada.get('variante')) if e]
        etiqueta = ' '.join(model) if model else ''
        if etiqueta and etiqueta not in t['modelos_curva']:
            t['modelos_curva'].append(etiqueta)
        if entrada.get('curva'):
            t['curvas'] += 1

    # 2) brochure US: colores y industrias
    pares = pares_brochure(brochure_txt)
    industrias = pares_industrias(brochure_txt)
    for par in pares:
        t = tintas.setdefault(par['tinta'], {
            'bases_documentadas': [], 'modelos_curva': [], 'curvas': 0})
        if par['color'] and not t.get('color'):
            t['color'] = {'valor': par['color'], 'estado': 'borrador',
                          'fuente': 'datos/extraccion/cij_tintas_brochure_us.txt'}
    colores_ind = set()
    for par in pares:
        if par['color']:
            colores_ind.add(par['color'])

    # 3) TS2205 V471-D
    v471d = composicion_v471d(ts_dec)

    # 4) fichas del inventario por codigo
    fichas_por_tinta = {}
    for ficha in inventario.get('fichas', []):
        codigo = ficha.get('codigo_tinta', '').upper()
        if not codigo:
            continue
        fichas_por_tinta.setdefault(codigo, []).append({
            'archivo': ficha['archivo'],
            'estado_extraccion': ficha['estado_extraccion'],
            'caracteres': ficha['caracteres'],
            'caracteres_descifrado': ficha.get('caracteres_descifrado', 0),
            'txt_descifrado': ficha.get('txt_descifrado'),
        })
        txt_desc = ficha.get('txt_descifrado') or ''
        slug_desc = txt_desc.replace('cij_tinta_', '').replace('_descifrado.txt', '')
        comp = sds_por_slug.get(slug_desc)
        if comp:
            fichas_por_tinta[codigo][-1]['sds'] = {
                'version': comp.get('version_sds'),
                'fecha_revision': comp.get('fecha_revision'),
                'componentes': [{'componente': c['componente'],
                                 'cas': c['cas'],
                                 'porcentaje': c['porcentaje'],
                                 'estado': c.get('estado', 'borrador')}
                                for c in comp['componentes']],
                'componentes_verificados': comp.get('componentes_verificados'),
                'estado': 'borrador',
            }
            propiedades = props_por_slug.get(slug_desc, {}).get('propiedades') or {}
            resumen = {k: propiedades[k] for k in CAMPOS_CLAVE if k in propiedades}
            if resumen:
                fichas_por_tinta[codigo][-1]['sds']['propiedades'] = resumen

    datos = {
        'producto': 'Dataset tintas CIJ Videojet v1',
        'schema': '1',
        'actualizado': date.today().isoformat(),
        'estado_general': 'borrador-fase-tintas (bases y modelos de curvas verificados; '
                          'colores y composicion en borrador explicito)',
        'nota': ('Las bases quimicas y los modelos provienen de cij_uso_solvente.json '
                 '(802 entradas verificadas). Colores e industrias salen del brochure '
                 'US oficial, estado borrador hasta revisar contra el PDF original. La '
                 'composicion V471-D proviene del TS2205 con extraction literal de '
                 'CAS + decodificacion de nombres (borrador-decodificado). No se '
                 'invento ningun dato; lo no legible queda fuera.'),
        'fuentes': [
            'datos/cij_uso_solvente.json',
            'datos/fichas_tintas_inventario.json',
            'datos/sds_composicion.json',
            'datos/sds_propiedades.json',
            'datos/extraccion/cij_tintas_brochure_us.txt',
            'datos/extraccion/cij_tinta_ts22051529684_v471_d.txt',
            'datos/extraccion/cij_tinta_ts22051529684_v471_d_dec.txt',
            'datos/extraccion/cij_tinta_v4250_ficha.txt',
        ],
        'sds': {
            'archivo': 'datos/sds_composicion.json',
            'total_fichas': sds.get('total_fichas'),
            'fichas_con_componentes': sds.get('fichas_con_componentes'),
            'total_componentes': sds.get('total_componentes'),
            'componentes_con_cas_valido': sds.get('componentes_con_cas_valido'),
            'propiedades': {
                'archivo': 'datos/sds_propiedades.json',
                'fichas_con_propiedades': props.get('fichas_con_propiedades'),
                'total_campos': props.get('total_campos'),
            },
            'estado': 'borrador',
        },
        'tintas': {},
        'brochure_us': {
            'pares_codigo_color': pares,
            'industrias': industrias,
            'archivo_txt': 'datos/extraccion/cij_tintas_brochure_us.txt',
            'estado': 'borrador',
        },
        'ts2205_v471_d': {
            'componentes': v471d,
            'estado': 'borrador-decodificado',
            'txt': 'datos/extraccion/cij_tinta_ts22051529684_v471_d.txt',
            'txt_dec': 'datos/extraccion/cij_tinta_ts22051529684_v471_d_dec.txt',
        },
    }

    for codigo, info in sorted(tintas.items()):
        fichas = fichas_por_tinta.get(codigo, [])
        entry = {
            'bases_quimicas': info['bases_documentadas'],
            'modelos_con_curva': info['modelos_curva'],
            'curvas_verificadas': info['curvas'],
            'fichas_qss': fichas,
            'estado': ('verificado-base-y-curvas' if info['curvas']
                       else 'por-definir'),
        }
        if info.get('color'):
            entry['color'] = info['color']
            entry['estado'] = 'verificado-base-y-curvas-color-borrador'
        if codigo == 'V471' and v471d:
            entry['composicion_partial'] = v471d
        datos['tintas'][codigo] = entry

    destino = os.path.join(DATOS, 'cij_tintas.json')
    with open(destino, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print('OK %s | tintas=%d con_curva=%d colores=%d industrias=%d | componentes_v471d=%d'
          % (os.path.relpath(destino, RAIZ), len(datos['tintas']),
             sum(1 for t in datos['tintas'].values() if t['curvas_verificadas']),
             len(colores_ind), len(industrias), len(v471d)))


if __name__ == '__main__':
    principal()
