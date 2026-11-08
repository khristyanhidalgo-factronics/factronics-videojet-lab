"""Reconstruye datos/cij_uso_solvente.json a partir de los .txt ya extraidos.

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Uso:
  python tools/reconstruir_dataset_solvente.py [SALIDA.json]
Recorre datos/extraccion/cij_solvente_*.txt; el modelo/variante/tinta/base se derivan
del PROPIO nombre del txt (patron cij_solvente_<modelo><variante>_<tinta>_<base>.txt,
generado por tools/lote_solvente.py). Sirve para reconstruir el dataset sin releer los
~800 PDFs cuando cambia la estructura (claves, campos) pero no las fuentes.
No inventa datos: el texto es el mismo extraido con leer_pdf.py en el ultimo lote.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estructurar_solvente as es                 # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

RAIZ = es.RAIZ
DIR_TXT = os.path.join(RAIZ, 'datos', 'extraccion')
PATRON = re.compile(r'cij_solvente_(\d{3,4})([a-z0-9]*)_([0-9a-z]+)_(.*?)\.txt$', re.I)


def principal():
    salida = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else es.SALIDA_DEF
    if os.path.exists(salida):
        os.remove(salida)
        print('dataset previo eliminado:', os.path.relpath(salida, RAIZ))
    n_ok = n_no = 0
    for f in sorted(os.listdir(DIR_TXT)):
        m = PATRON.fullmatch(f)
        if not m:
            continue
        modelo, variante, ink, base = m.groups()
        texto = open(os.path.join(DIR_TXT, f), 'r', encoding='utf-8').read()
        estado, _ = es.registrar(os.path.join(DIR_TXT, f), texto, salida,
                                 modelo, ink, variante.upper(), base, verbose=False)
        if estado == 'OK':
            n_ok += 1
        else:
            n_no += 1
            print('NO', f)
    total = len(es.cargar_dataset(salida).get('modelos', []))
    print('RESUMEN reconstruccion: procesados=%d  no-legibles=%d  entradas_dataset=%d'
          % (n_ok, n_no, total))


if __name__ == '__main__':
    principal()
