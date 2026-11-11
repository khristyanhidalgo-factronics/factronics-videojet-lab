# -*- coding: utf-8 -*-
"""Aplica traducciones manuales revisadas sobre la memoria de contenido.

Google Translate acierta en la mayoria de las cadenas, pero algunos terminos
cortos de estado o nombres quimicos truncados se quedan sin traducir o se
transliteran mal. Estas correcciones son deliberadas y se conservan al volver
a ejecutar tools/traducir_contenido.py (el pipeline solo rellena lo que falta).

Uso:
  python tools/corregir_traducciones_manual.py
"""
import json
import os
import sys

from traducir_contenido import SALIDA, guardar, normalizar

# clave normalizada -> traducciones revisadas
OVERRIDES = {
    'por-definir': {
        'es': 'por definir', 'en': 'to be defined', 'pt': 'a definir',
        'it': 'da definire', 'zh': '待定',
    },
    'sin-datos-en-documento': {
        'es': 'sin datos en el documento', 'en': 'no data in the document',
        'pt': 'sem dados no documento', 'it': 'nessun dato nel documento',
        'zh': '文件中无数据',
    },
    'verificado': {
        'es': 'verificado', 'en': 'verified', 'pt': 'verificado',
        'it': 'verificato', 'zh': '已验证',
    },
    'borrador': {
        'es': 'borrador', 'en': 'draft', 'pt': 'rascunho',
        'it': 'bozza', 'zh': '草稿',
    },
    'borrador-decodificado': {
        'es': 'borrador decodificado', 'en': 'decoded draft',
        'pt': 'rascunho decodificado', 'it': 'bozza decodificata',
        'zh': '已解码草稿',
    },
    'sin-pn': {
        'es': 'sin P/N', 'en': 'no P/N', 'pt': 'sem P/N',
        'it': 'senza P/N', 'zh': '无 P/N',
    },
    'conflicto': {
        'es': 'conflicto', 'en': 'conflict', 'pt': 'conflito',
        'it': 'conflitto', 'zh': '冲突',
    },
    # Restos alemanes de listas de repuestos laser (Wasser = agua,
    # Wasserschl. = Wasserschlauch = manguera de agua, Khler = refrigerador).
    # Se conserva la cola numerica tal como esta impresa.
    'Wasser, de stilliert, 5L A ST 3,00018-01-07 02:56 3,000': {
        'es': 'Agua destilada, 5L A ST 3,00018-01-07 02:56 3,000',
        'en': 'Distilled water, 5L A ST 3,00018-01-07 02:56 3,000',
        'pt': 'Água destilada, 5L A ST 3,00018-01-07 02:56 3,000',
        'it': 'Acqua distillata, 5L A ST 3,00018-01-07 02:56 3,000',
        'zh': '蒸馏水，5L A ST 3,00018-01-07 02:56 3,000',
    },
    'Wasser/Was ser Khler (WWK) F ST 1,00018-01-07 02:56 1,000': {
        'es': 'Agua/enfriador de agua (WWK) F ST 1,00018-01-07 02:56 1,000',
        'en': 'Water/water cooler (WWK) F ST 1,00018-01-07 02:56 1,000',
        'pt': 'Água/resfriador de água (WWK) F ST 1,00018-01-07 02:56 1,000',
        'it': "Acqua/refrigeratore d'acqua (WWK) F ST 1,00018-01-07 02:56 1,000",
        'zh': '水/水冷却器 (WWK) F ST 1,00018-01-07 02:56 1,000',
    },
    'Wasserschl . PCM WWK<=>ext. E ST 1,00018-01-07 02:56 1,000': {
        'es': 'Manguera de agua PCM WWK<=>ext. E ST 1,00018-01-07 02:56 1,000',
        'en': 'Water hose PCM WWK<=>ext. E ST 1,00018-01-07 02:56 1,000',
        'pt': 'Mangueira de água PCM WWK<=>ext. E ST 1,00018-01-07 02:56 1,000',
        'it': "Tubo dell'acqua PCM WWK<=>ext. E ST 1,00018-01-07 02:56 1,000",
        'zh': '水管 PCM WWK<=>ext. E ST 1,00018-01-07 02:56 1,000',
    },
    'Wasserschl .PCM<=>LN Laserkopf D ST 1,00018-01-07 02:56 1,000': {
        'es': 'Manguera de agua PCM<=>cabezal láser LN D ST 1,00018-01-07 02:56 1,000',
        'en': 'Water hose PCM<=>LN laser head D ST 1,00018-01-07 02:56 1,000',
        'pt': 'Mangueira de água PCM<=>cabeça laser LN D ST 1,00018-01-07 02:56 1,000',
        'it': "Tubo dell'acqua PCM<=>testa laser LN D ST 1,00018-01-07 02:56 1,000",
        'zh': '水管 PCM<=>LN 激光头 D ST 1,00018-01-07 02:56 1,000',
    },
    # Nombre quimico truncado que Google dejo igual en es/pt/it.
    'Chromium, 1-[2-[5-(1,1-dimethylpropyl)': {
        'es': 'Cromo, 1-[2-[5-(1,1-dimetilpropil)',
        'en': 'Chromium, 1-[2-[5-(1,1-dimethylpropyl)',
        'pt': 'Cromo, 1-[2-[5-(1,1-dimetilpropil)',
        'it': 'Cromo, 1-[2-[5-(1,1-dimetilpropil)',
        'zh': '铬，1-[2-[5-(1,1-二甲基丙基)',
    },
}


def main():
    if not os.path.exists(SALIDA):
        print('No existe la memoria de traducciones.')
        return 1
    datos = json.load(open(SALIDA, encoding='utf-8'))
    entradas = datos.get('entradas', {})
    aplicadas = 0
    for texto, traducciones in OVERRIDES.items():
        clave = normalizar(texto)
        reg = entradas.setdefault(clave, {})
        reg.update(traducciones)
        reg['manual'] = True
        aplicadas += 1
    guardar(entradas)
    print('Correcciones manuales aplicadas: %d' % aplicadas)
    return 0


if __name__ == '__main__':
    sys.exit(main())
