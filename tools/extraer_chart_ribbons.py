# -*- coding: utf-8 -*-
"""Extrae las hojas clave del chart de ribbons TTO a JSON (sin limite de 400)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'tools')
from leer_excel import leer_xlsx  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
          r'\CURSO BRASILLinformacion-------------------------------------\TTO 6x30'
          r'\Ribbons\Videojet Ribbon and Label Chart - 2.5.26.xlsx')
DESTINO = os.path.join(RAIZ, 'datos', 'extraccion', 'tto_ribbon_chart_hojas.json')
HOJAS = ['Ribbon Chart', 'TTO Ribbon', 'LPA Ribbon', 'Standard Lengths Widths',
         'Date and Lot Number Logic', 'Ribbon Brochure Chart', 'Label Printers']

datos = leer_xlsx(ORIGEN, hojas=set(HOJAS), max_filas=1000)
with open(DESTINO, 'w', encoding='utf-8') as f:
    json.dump(datos, f, ensure_ascii=False, indent=1)
for hoja, info in datos.items():
    print('%-28s filas=%-5d cortado=%s' % (hoja, info['filas'], info['cortado']))
print('OK', os.path.relpath(DESTINO, RAIZ))
