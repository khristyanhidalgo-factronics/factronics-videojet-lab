# -*- coding: utf-8 -*-
"""Estructura la seccion 9 (propiedades fisicoquimicas) de las SDS descifradas.

Entrada: datos/extraccion/cij_tinta_*_visual.txt (orden visual real)
Salida:  datos/sds_propiedades.json

Formato observado (SDS Videojet, plantilla SGA, texto visual):
    SECCIÓN 9: Propiedades físicas y químicas
    Apariencia
    Estado físico : Líquido.
    Color : Negro. [Obscuro]
    ...
    Punto de inflamación : -9 °C [ASTM D 56]
    Límites superior/inferior : Aproximado.: ≥ 0.8 % (Xilenos...).
    de inflamabilidad o Aproximado.: ≤ 19 % (Etanol).
    explosividad
Las etiquetas pueden venir partidas en varias lineas visuales (celda multilinea);
se normalizan por prefijo conocido y las lineas de continuacion se anexan al valor
solo cuando empiezan con un valor (Aproximado/No/≤/≥/número). Estado: borrador.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'sds_propiedades.json')

SEC9 = re.compile(r'SECCI[ÓO]N\s+9\s*[:\-]', re.I)
SEC10 = re.compile(r'SECCI[ÓO]N\s+10\s*[:\-]', re.I)
VERSION = re.compile(r'N[úu]mero de versi[óo]n\s*:?\s*\n?:?\s*([0-9]+(?:\.[0-9]+)?)')
FECHA = re.compile(r'Fecha de emisi[óo]n/\s*Fecha de\s*\n?\s*revisi[óo]n\s*:?\s*\n?:?\s*'
                   r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})')

# prefijo de etiqueta Normalizada -> clave canonica
ETIQUETAS = [
    ('estado fisico', 'estado_fisico'),
    ('color', 'color'),
    ('olor', 'olor'),
    ('umbral del olor', 'umbral_olor'),
    ('ph', 'ph'),
    ('punto de fusion', 'punto_fusion'),
    ('punto de ebullicion', 'punto_ebullicion'),
    ('punto de inflamacion', 'punto_inflamacion'),
    ('grado de evaporacion', 'grado_evaporacion'),
    ('inflamabilidad', 'inflamabilidad'),
    ('limites superior', 'limites_inflamabilidad'),
    ('presion de vapor', 'presion_vapor'),
    ('densidad de vapor', 'densidad_vapor'),
    ('densidad relativa', 'densidad_relativa'),
    ('solubilidad', 'solubilidad'),
    ('coeficiente de particion', 'log_pow'),
    ('temperatura de ignicion', 'temp_ignicion'),
    ('temperatura de descomposicion', 'temp_descomposicion'),
    ('viscosidad', 'viscosidad'),
    ('propiedades explosivas', 'propiedades_explosivas'),
    ('propiedades oxidantes', 'propiedades_oxidantes'),
    ('caracteristicas de las particulas', 'caracteristicas_particulas'),
    ('tamano mediano', 'tamano_particulas'),
    ('volatilidad', 'volatilidad'),
    ('cov volatilidad', 'cov_volatilidad'),
    ('apariencia', 'apariencia'),
]

INICIO_VALOR = re.compile(r'^(aproximado|no\s|≤|≥|<|>|\d)', re.I)


def sin_acentos(texto):
    tabla = str.maketrans('áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')
    return texto.translate(tabla).lower().strip()


def clave_de_etiqueta(etiqueta):
    e = sin_acentos(etiqueta).strip(' .:')
    for prefijo, clave in ETIQUETAS:
        if e.startswith(prefijo):
            return clave
    return None


def parsear_seccion9(texto):
    m9 = SEC9.search(texto)
    if not m9:
        return None
    resto = texto[m9.end():]
    m10 = SEC10.search(resto)
    if m10:
        resto = resto[:m10.start()]
    lineas = [l.strip() for l in resto.splitlines() if l.strip()]
    propiedades = {}
    ultima = None
    extra_limites = []
    for linea in lineas:
        if ' : ' in linea:
            etiqueta, valor = linea.split(' : ', 1)
            clave = clave_de_etiqueta(etiqueta)
            etiqueta_siguiente = clave_de_etiqueta(valor.split(' : ')[0]) \
                if ' : ' in valor else None
            if clave is None:
                # etiqueta no reconocida (p.ej. continuacion partida): si la linea
                # empieza con valor y hay etiqueta previa, se anexa como valor 2
                if ultima and INICIO_VALOR.match(linea):
                    propiedades.setdefault(ultima, []).append(linea)
                continue
            if etiqueta_siguiente is not None:
                # caso '... : Aproximado.: ≤ 0.8 %...' -> el valor real sigue
                valor = valor.split(' : ', 1)[-1]
            propiedades.setdefault(clave, []).append(valor.strip())
            ultima = clave
            continue
        # linea sin ' : '
        clave = clave_de_etiqueta(linea)
        if clave is not None:
            ultima = clave
            propiedades.setdefault(clave, [])
            continue
        if ultima and INICIO_VALOR.match(linea) and not linea.isupper():
            propiedades.setdefault(ultima, []).append(linea)
    # limpiar listas vacias y artefactos de celdas partidas
    def sanear(valores):
        limpios = []
        for v in valores:
            s = (v or '').strip()
            if not s:
                continue
            if re.fullmatch(r'\d+\)', s):          # resto '1)' de etiqueta partida
                continue
            if re.match(r'^\d\.\d\s', s):          # encabezado '9.2 Otra informacion'
                continue
            if s not in limpios:
                limpios.append(s)
        return limpios

    limpias = {}
    for clave, valores in propiedades.items():
        valores = sanear(valores)
        if valores:
            limpias[clave] = valores[0] if len(valores) == 1 else valores
    return limpias or None


def metadatos(texto):
    v = VERSION.search(texto)
    f = FECHA.search(texto)
    return {'version_sds': v.group(1) if v else None,
            'fecha_revision': f.group(1) if f else None}


def main():
    resultados = []
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not nombre.startswith('cij_tinta_') or not nombre.endswith('_visual.txt'):
            continue
        texto = open(os.path.join(EXTRACCION, nombre), 'r',
                     encoding='utf-8', errors='replace').read()
        slug = nombre[len('cij_tinta_'):-len('_visual.txt')]
        props = parsear_seccion9(texto)
        meta = metadatos(texto)
        resultados.append({
            'archivo_txt': nombre,
            'slug': slug,
            'codigo_tinta': slug.split('_')[0].replace('_', '-').upper(),
            'version_sds': meta['version_sds'],
            'fecha_revision': meta['fecha_revision'],
            'propiedades': props or {},
            'campos': len(props or {}),
            'estado': 'borrador' if props else 'sin-seccion-9',
            'fuente': 'ficha QSS cifrada descifrada + extraccion visual (v3)',
        })

    con = sum(1 for r in resultados if r['propiedades'])
    total_campos = sum(r['campos'] for r in resultados)
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump({
            'producto': 'Propiedades fisicoquimicas SDS (seccion 9)',
            'schema': 1,
            'estado_general': 'borrador (extraccion automatica de plantilla)',
            'nota': ('Seccion 9 de las SDS Videojet descifradas con extraccion visual. '
                     'Etiquetas normalizadas por prefijo; valores de celda multilinea '
                     'anexados solo si empiezan con valor. Sin datos inventados: los '
                     'campos no presentes quedan fuera.'),
            'total_fichas': len(resultados),
            'fichas_con_propiedades': con,
            'total_campos': total_campos,
            'fichas': resultados,
        }, f, ensure_ascii=False, indent=1)
    print('OK %s | fichas=%d con_propiedades=%d campos=%d'
          % (os.path.relpath(DESTINO, RAIZ), len(resultados), con, total_campos))
    for r in resultados:
        if r['slug'] == 'v471_d':
            try:
                print('V471-D:', json.dumps(r['propiedades'], ensure_ascii=False,
                                            indent=1)[:1200])
            except UnicodeEncodeError:
                print('V471-D: campos =', sorted(r['propiedades'].keys()))


if __name__ == '__main__':
    main()
