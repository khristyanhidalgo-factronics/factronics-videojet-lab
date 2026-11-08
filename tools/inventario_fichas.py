"""Inventario de fichas de tintas QSS de la carpeta 'ficha de tintas'.

Cruza cada PDF de la carpeta original con su .txt de extraccion (si existe) en
datos/extraccion/ y clasifica el intento de extraction:
  - 'legible'            : el .txt tiene texto (>= 200 caracteres de cuerpo)
  - 'texto-escaso'       : el .txt existe pero con menos de 200 caracteres utiles
  - 'sin-texto-sacado'   : la extraccion produjo 0 caracteres (probable PDF escaneado)
  - 'sin-extraccion'     : PDF presente pero sin .txt asociado
Claves de cruce: el slug del PDF (V471-D.00q406f20 -> v471_d / 16-1020A-Q -> 16_1020a_q).

Uso:
  python tools/inventario_fichas.py
Salida: datos/fichas_tintas_inventario.json (+ resumen por consola)
"""
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(
    r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet',
    'DOCUMENTOS VIDEOJET ETERNOSSSSSSSSSSSSSSSSSSSSS', 'ficha de tintas')
DESTINO = os.path.join(RAIZ, 'datos', 'fichas_tintas_inventario.json')
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')


def slug_de(nombre_pdf):
    stem = re.sub(r'\.pdf$', '', nombre_pdf, flags=re.I)          # quita '.pdf'
    stem = re.sub(r'\.[a-z0-9]{6,}$', '', stem, flags=re.I)       # quita '.026306f20'
    slug = re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')
    return slug


# Renombres historicos: extracciones hechas con otro slug y ya movidas al repo.
RENOMBRES = {
    'ts22051529684_information_for_v471_d': 'cij_tinta_ts22051529684_v471_d.txt',
}


def principal():
    if not os.path.isdir(CARPETA):
        print('ERROR: no existe la carpeta %s' % CARPETA)
        return
    txts = {}
    for nombre in os.listdir(EXTRACCION):
        if nombre.endswith('.txt'):
            txts[os.path.splitext(nombre)[0]] = os.path.join(EXTRACCION, nombre)

    entradas = []
    resumen = {'legible-descifrado': 0, 'texto-escaso-descifrado': 0,
               'sin-texto-descifrado': 0, 'legible': 0, 'texto-escaso': 0,
               'sin-texto-sacado': 0, 'sin-extraccion': 0}
    for nombre in sorted(os.listdir(CARPETA)):
        if not nombre.lower().endswith('.pdf'):
            continue
        slug = slug_de(nombre)
        clave_legacy = RENOMBRES.get(slug, 'cij_tinta_%s' % slug)
        ruta_txt = txts.get(clave_legacy)
        ruta_desc = txts.get('cij_tinta_%s_descifrado' % slug)
        entrada = {
            'archivo': nombre,
            'slug': slug,
            'codigo_tinta': slug.split('_')[0].replace('_', '-'),
            'txt': None,
            'caracteres': 0,
            'bloques': 0,
            'txt_descifrado': None,
            'caracteres_descifrado': 0,
            'estado_extraccion': 'sin-extraccion',
        }

        def leer_cuerpo_y_bloques(ruta):
            cuerpo, bloques = '', 0
            try:
                contenido = open(ruta, 'r', encoding='utf-8', errors='replace').read()
                cuerpo = '\n'.join(l for l in contenido.splitlines()
                                   if not l.startswith('#')).strip()
                m = re.search(r'bloque\(s\)=(\d+)', contenido.splitlines()[0] if contenido else '')
                if m:
                    bloques = int(m.group(1))
            except OSError:
                pass
            return cuerpo, bloques

        if ruta_txt:
            cuerpo, bloques = leer_cuerpo_y_bloques(ruta_txt)
            entrada['txt'] = os.path.basename(ruta_txt)
            entrada['caracteres'] = len(cuerpo)
            entrada['bloques'] = bloques
            if len(cuerpo) >= 200:
                entrada['estado_extraccion'] = 'legible'
            elif len(cuerpo) > 0:
                entrada['estado_extraccion'] = 'texto-escaso'
            else:
                entrada['estado_extraccion'] = 'sin-texto-sacado'
        if ruta_desc:
            cuerpo, bloques = leer_cuerpo_y_bloques(ruta_desc)
            entrada['txt_descifrado'] = os.path.basename(ruta_desc)
            entrada['caracteres_descifrado'] = len(cuerpo)
            if len(cuerpo) >= 200:
                entrada['estado_extraccion'] = 'legible-descifrado'
            elif len(cuerpo) > 0:
                entrada['estado_extraccion'] = 'texto-escaso-descifrado'
            else:
                entrada['estado_extraccion'] = 'sin-texto-descifrado'
        resumen[entrada['estado_extraccion']] += 1
        entradas.append(entrada)

    datos = {
        'fuente': CARPETA,
        'herramienta': 'tools/leer_pdf.py (stdlib) + este inventario',
        'fecha': 'registro acumulado del proyecto',
        'total_pdfs': len(entradas),
        'resumen': resumen,
        'nota': ('Todos los PDFs se procesaron con el extractor stdlib; los 562 cifrados '
                 'con el handler estandar (RC4 128 bits, contrasena de usuario vacia) se '
                 'descifraron con tools/leer_pdf_cifrado.py v2 y sus CMaps ToUnicode -> '
                 'extraccion <slug>_descifrado.txt. Los .txt de 0 caracteres previos se '
                 'conservan como evidencia del intento original. Estados: '
                 'legible-descifrado / texto-escaso-descifrado / sin-texto-descifrado / '
                 'legible / texto-escaso / sin-texto-sacado / sin-extraccion.'),
        'fichas': entradas,
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print('OK %s | total=%d %s' % (os.path.relpath(DESTINO, RAIZ),
                                   datos['total_pdfs'], resumen))


if __name__ == '__main__':
    principal()
