# -*- coding: utf-8 -*-
"""Cataloga los modelos LASER documentados (evidencia: nombres de archivo + textos).

Salida: datos/laser_modelos.json
- CO2 y fibra Videojet (evidencia en manuales/entrenamiento).
- ALLPRINT (terceros) se registra aparte como referencia, no como modelo Videojet.
"""
import json
import os
import re
import sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
LASER = (r'C:\Users\Sr_Hidalgo\Documents\Documentos Videojet'
         r'\CARPETA A MEJORAR\hacer notebookllm\documentacion laser')
DESTINO = os.path.join(RAIZ, 'datos', 'laser_modelos.json')

CO2 = {'3020', '3120', '3220', '3320', '3350', '3420', '3520'}
FIBRA = {'7010', '7020', '7030', '7110', '7120', '7130', '7210', '7220',
         '7230', '7310', '7320', '7330', '7340', '7440', '7510', '7610',
         '7810', '7920'}


def main():
    evidencia = defaultdict(lambda: {'archivos': [], 'menciones_texto': 0})
    # 1) nombres de archivo de las subcarpetas
    for raiz, _, archivos in os.walk(LASER):
        for nombre in archivos:
            for m in re.finditer(r'\b(3\d{3}|7\d{3})\b', nombre):
                modelo = m.group(1)
                if modelo in CO2 or modelo in FIBRA:
                    rel = os.path.relpath(os.path.join(raiz, nombre), LASER)
                    if len(evidencia[modelo]['archivos']) < 6:
                        evidencia[modelo]['archivos'].append(rel)
    # 2) menciones en los textos extraidos
    for nombre in os.listdir(EXTRACCION):
        if not (nombre.startswith('laser_') and nombre.endswith('_visual.txt')):
            continue
        t = open(os.path.join(EXTRACCION, nombre), encoding='utf-8',
                 errors='replace').read()
        for modelo in list(CO2) + list(FIBRA):
            if re.search(r'\b%s\b' % modelo, t):
                evidencia[modelo]['menciones_texto'] += 1

    modelos = []
    for modelo in sorted(set(evidencia), key=lambda m: (m not in CO2, m)):
        fam = 'CO2' if modelo in CO2 else 'fibra'
        e = evidencia[modelo]
        modelos.append({
            'modelo': modelo,
            'familia': fam,
            'archivos_evidencia': e['archivos'],
            'menciones_en_textos': e['menciones_texto'],
            'estado': 'documentado' if e['archivos'] else 'mencionado-en-textos',
        })

    datos = {
        'producto': 'Modelos LASER Videojet documentados en la carpeta del equipo',
        'schema': 1,
        'fuente': 'documentacion laser (manuales, entrenamiento, drawings) + textos extraidos',
        'nota': ('Modelos detectados por evidencia directa (nombres de archivo de manuales/'
                 'entrenamiento y menciones en textos). ALLPRINT (DN-A/LN-A) es marca de '
                 'terceros presente en la carpeta: se registra aparte como referencia, no '
                 'como modelo Videojet. Los modelos sin archivo de evidencia quedan como '
                 'mencionados-en-textos.'),
        'modelos': modelos,
        'resumen': {
            'total_modelos': len(modelos),
            'co2': sorted(m['modelo'] for m in modelos if m['familia'] == 'CO2'),
            'fibra': sorted(m['modelo'] for m in modelos if m['familia'] == 'fibra'),
        },
        'terceros_referencia': {
            'ALLPRINT': {'familias': ['DN-A', 'LN-A'],
                         'nota': 'marca de terceros; manuales y accesorios en la carpeta'},
            'sensores_seguridad': ['AES 1235', 'AES 1236', 'BNS 33', 'BNS 36'],
        },
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | modelos=%d | CO2=%s | fibra=%s'
          % (os.path.relpath(DESTINO, RAIZ), len(modelos),
             datos['resumen']['co2'], datos['resumen']['fibra']))


if __name__ == '__main__':
    main()
