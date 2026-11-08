"""Lote: extrae los PDFs 'Illustrated Parts List' (IPL) de la familia Videojet 1000VJ.

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Uso:
  python tools/lote_ipl.py CARPETA_IPL
Extrae cada PDF con leer_pdf.py, limpia el texto (sin bytes NUL ni no imprimibles,
respeta \n y \t) y lo guarda en datos/extraccion/cij_ipl_<slug>.txt, donde <slug> sale
del nombre del archivo (sin las palabras 'illustrated', 'parts', 'list', 'ipl').
Emite el resumen datos/extraccion/_lote_ipl_resumen.json (bloques, caracteres, lineas)
para evaluar ANTES de estructurar si las tablas de partes son texto legible.
No inventa datos: si un PDF no entrega texto, queda con 0 caracteres en el resumen.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leer_pdf import extraer                      # noqa: E402
from lote_solvente import limpiar                 # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_TXT = os.path.join(RAIZ, 'datos', 'extraccion')
PALABRAS_QUITAR = {'illustrated', 'parts', 'list', 'ipl', 'eng', 'english'}


def slug_de(nombre_archivo):
    stem = re.sub(r'\.pdf$', '', os.path.basename(nombre_archivo), flags=re.I)
    toks = [t for t in re.split(r'[^a-zA-Z0-9]+', stem) if t]
    toks = [t.lower() for t in toks if t.lower() not in PALABRAS_QUITAR]
    return '_'.join(toks)


def principal():
    carpeta = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None
    if not carpeta or not os.path.isdir(carpeta):
        print('Uso: python tools/lote_ipl.py CARPETA_IPL')
        sys.exit(1)
    pdfs = sorted(os.path.join(root, f) for root, _, files in os.walk(carpeta)
                  for f in files if f.lower().endswith('.pdf'))
    print('PDFs IPL encontrados:', len(pdfs))
    resumen = []
    for completo in pdfs:
        base = os.path.basename(completo)
        slug = slug_de(base)
        destino_txt = os.path.join(DIR_TXT, 'cij_ipl_%s.txt' % slug)
        texto, nblok = '', 0
        try:
            partes = extraer(completo)
            nblok = len(partes)
            texto = limpiar(partes)
        except Exception as e:
            print('ERROR extraer:', base, '|', e)
        with open(destino_txt, 'w', encoding='utf-8') as f:
            f.write('# EXTRAIDO POR tools/leer_pdf.py (stdlib) - fuente: %s\n' % base)
            f.write('# bloque(s)=%d caracteres=%d\n\n' % (nblok, len(texto)))
            f.write(texto)
        lineas = len(texto.splitlines())
        resumen.append({'archivo': base, 'txt': os.path.basename(destino_txt),
                        'bloques': nblok, 'caracteres': len(texto), 'lineas': lineas})
        print('OK cij_ipl_%s.txt | bloques=%d caracteres=%d lineas=%d' % (slug, nblok, len(texto), lineas))
    with open(os.path.join(DIR_TXT, '_lote_ipl_resumen.json'), 'w', encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1)
    print('resumen -> datos/extraccion/_lote_ipl_resumen.json')


if __name__ == '__main__':
    principal()
