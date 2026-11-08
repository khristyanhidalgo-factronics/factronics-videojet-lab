"""Lote: extrae y estructura TODOS los PDFs 'CIJ Makeup Usage Model' de una carpeta.

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Uso:
  python tools/lote_solvente.py CARPETA_USO_DE_SOLVENTE [SALIDA.json]
Recorre recursivamente los *.pdf cuyo nombre contiene 'makeup'; el modelo/variante/tinta
se derivan SIEMPRE del nombre (token 'v14' -> modelo -> 'vNNN' -> anotacion de base).
Extrae cada PDF con leer_pdf.py, escribe el .txt por documento en datos/extraccion/ y
acumula las curvas en datos/cij_uso_solvente.json (una por modelo+variante+tinta+base,
la base se toma del nombre del documento; sirve para distinguir pares como v461
ETHANOL_ISOPROP vs ETHYL_ACETATE).
Los PDFs que no se dejan leer (cifrados/escaneados) quedan 'NO' sin inventar nada.
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf import extraer                      # noqa: E402
import estructurar_solvente as es                 # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

RAIZ = es.RAIZ
DIR_TXT = os.path.join(RAIZ, 'datos', 'extraccion')


def limpiar(partes):
    texto = '\n\n'.join(partes)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto).strip()
    texto = texto.replace('\x00', '')
    texto = ''.join(ch if (ch.isprintable() or ch in '\n\t') else '' for ch in texto)
    return texto


def principal():
    argv = sys.argv[1:]
    if not argv:
        print('Uso: python tools/lote_solvente.py CARPETA_USO_DE_SOLVENTE [SALIDA.json]')
        sys.exit(1)
    carpeta = os.path.abspath(argv[0])
    salida_path = os.path.abspath(argv[1]) if len(argv) > 1 else es.SALIDA_DEF

    pdfs = sorted(os.path.join(root, f) for root, _, files in os.walk(carpeta) for f in files
                  if f.lower().endswith('.pdf') and 'makeup' in f.lower())
    print('PDFs makeup encontrados:', len(pdfs))
    # limpieza de extracciones antiguas (los nombres incluyen ahora la base del nombre)
    for f in sorted(os.listdir(DIR_TXT)):
        if f.startswith('cij_solvente_') and f.endswith('.txt'):
            os.remove(os.path.join(DIR_TXT, f))
    ok, no, omitidos = [], [], []
    for completo in pdfs:
        base = os.path.basename(completo)
        d_nombre = es.modelo_tinta_del_nombre(base)
        if not d_nombre:
            omitidos.append(base)
            print('OMITIDO (nombre sin modelo/tinta):', base)
            continue
        modelo, ink, variante, base_nombre = (d_nombre['modelo'], d_nombre['tinta'],
                                              d_nombre['variante'], d_nombre['base'])
        destino_txt = os.path.join(DIR_TXT, 'cij_solvente_%s%s_%s_%s.txt'
                                   % (modelo, (variante or '').lower(), ink.lower(), base_nombre))
        texto, nblok = '', 0
        try:
            partes = extraer(completo)
            texto = limpiar(partes)
            nblok = len(partes)
        except Exception as e:
            print('ERROR extraer:', base, '|', e)
        with open(destino_txt, 'w', encoding='utf-8') as f:
            f.write('# EXTRAIDO POR tools/leer_pdf.py (stdlib) - fuente: %s\n' % base)
            f.write('# bloque(s)=%d caracteres=%d\n\n' % (nblok, len(texto)))
            f.write(texto)
        estado, info = es.registrar(destino_txt, texto, salida_path, modelo, ink,
                                    variante, base_nombre, verbose=False)
        etiqueta = 'VJ%s%s %s %s' % (modelo, ('/' + variante) if variante else '', ink, base_nombre)
        if estado == 'OK':
            ok.append(etiqueta)
            print('OK %s | %s' % (destino_txt, etiqueta))
        else:
            no.append(etiqueta)
            print('NO %s | %s | %s' % (modelo, ink, info))

    por_modelo = Counter(e.split(' ')[0] for e in ok)
    print('-' * 60)
    print('RESUMEN: ok=%d  no-legibles=%d  omitidos=%d  entradas_dataset=%d'
          % (len(ok), len(no), len(omitidos), len(es.cargar_dataset(salida_path).get('modelos', []))))
    print('por_modelo:', dict(sorted(por_modelo.items())))
    if omitidos:
        print('omitidos:', ', '.join(omitidos))
    with open(os.path.join(DIR_TXT, '_lote_solvente_resumen.json'), 'w', encoding='utf-8') as f:
        json.dump({'ok': ok, 'no_legibles': no, 'omitidos': omitidos,
                   'por_modelo': dict(sorted(por_modelo.items())),
                   'total_encontrados': len(pdfs)}, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    principal()
