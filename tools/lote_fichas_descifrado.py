# -*- coding: utf-8 -*-
"""Lote: extrae texto de TODAS las fichas QSS usando tools/leer_pdf_cifrado.py.

- Recorre la carpeta 'ficha de tintas' (564 PDFs).
- Descifra (RC4 handler estandar) + aplica CMaps ToUnicode.
- Guarda datos/extraccion/cij_tinta_<slug>_descifrado.txt (UTF-8, con cabecera).
- Resumen acumulado en datos/extraccion/_lote_fichas_descifrado_resumen.json
  (archivo, chars, cifrado, estado: ok / cifrado-no-soportado / sin-texto / error).
- Los .txt viejos de 0 caracteres se conservan como evidencia del intento previo.
"""
import json
import os
import re
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf_cifrado import extraer  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
           r'\DOCUMENTOS VIDEOJET ETERNOSSSSSSSSSSSSSSSSSSSSS\ficha de tintas')
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
RESUMEN = os.path.join(EXTRACCION, '_lote_fichas_descifrado_resumen.json')
RENOMBRES = {
    'ts22051529684_information_for_v471_d': None,  # no aplica en esta carpeta
}


def slug_de(nombre_pdf):
    stem = re.sub(r'\.pdf$', '', nombre_pdf, flags=re.I)
    stem = re.sub(r'\.[a-z0-9]{6,}$', '', stem, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')


def limpiar(texto):
    texto = re.sub(r'[ \t]+', ' ', texto)
    return re.sub(r'\n{3,}', '\n\n', texto).strip()


def main():
    resultados = []
    hechos = 0
    for nombre in sorted(os.listdir(CARPETA)):
        if not nombre.lower().endswith('.pdf'):
            continue
        ruta = os.path.join(CARPETA, nombre)
        slug = slug_de(nombre)
        destino = os.path.join(EXTRACCION, 'cij_tinta_%s_descifrado.txt' % slug)
        registro = {'archivo': nombre, 'slug': slug, 'chars': 0,
                    'cifrado': None, 'estado': 'error'}
        try:
            partes, bloques, cifrado = extraer(ruta)
            texto = limpiar('\n\n'.join(partes))
            registro['cifrado'] = cifrado
            registro['bloques'] = bloques
            registro['chars'] = len(texto)
            if len(texto) >= 200:
                registro['estado'] = 'ok'
            elif len(texto) > 0:
                registro['estado'] = 'texto-escaso'
            else:
                registro['estado'] = 'sin-texto'
            with open(destino, 'w', encoding='utf-8') as f:
                f.write('# EXTRAIDO POR tools/leer_pdf_cifrado.py v2 (stdlib) - fuente: %s\n'
                        % nombre)
                f.write('# cifrado=%s bloques=%d caracteres=%d\n\n'
                        % (cifrado, bloques, len(texto)))
                f.write(texto)
        except RuntimeError as e:
            registro['estado'] = 'cifrado-no-soportado'
            registro['error'] = str(e)
        except Exception as e:
            registro['estado'] = 'error'
            registro['error'] = '%s: %s' % (type(e).__name__, e)
            traceback.print_exc()
        resultados.append(registro)
        hechos += 1
        if hechos % 50 == 0:
            print('... %d/564 procesados' % hechos)

    with open(RESUMEN, 'w', encoding='utf-8') as f:
        json.dump({
            'carpeta': CARPETA,
            'total': len(resultados),
            'herramienta': 'tools/leer_pdf_cifrado.py v2 + tools/lote_fichas_descifrado.py',
            'resultados': resultados,
        }, f, ensure_ascii=False, indent=1)

    cuentas = {}
    for r in resultados:
        cuentas[r['estado']] = cuentas.get(r['estado'], 0) + 1
    print('RESUMEN:', cuentas)
    ok = [r for r in resultados if r['estado'] == 'ok']
    if ok:
        ok.sort(key=lambda r: -r['chars'])
        print('mejores:', [(r['archivo'], r['chars']) for r in ok[:5]])
        print('chars totales extraidos:', sum(r['chars'] for r in ok))


if __name__ == '__main__':
    main()
