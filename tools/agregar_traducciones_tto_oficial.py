# -*- coding: utf-8 -*-
"""Agrega las traducciones de las 23 descripciones TTO oficiales 6530.

El cotejo TTO agrego 23 descripciones en ingles que no existian en la memoria
de traduccion. Se traducen a mano (es/pt/it/zh) conservando la designacion
tecnica 107mm_TT(iii), los modelos y las siglas (PCB, PCBA, LH, RH).

Uso:
  python tools/agregar_traducciones_tto_oficial.py
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORIA = os.path.join(RAIZ, 'datos', 'traducciones_contenido.json')

TRADUCCIONES = {
    '107mm_TT(iii) Cassette Shaft (pair)': {
        'es': 'Eje del casete 107mm_TT(iii) (par)',
        'en': '107mm_TT(iii) Cassette Shaft (pair)',
        'pt': 'Eixo do cassete 107mm_TT(iii) (par)',
        'it': 'Albero della cassetta 107mm_TT(iii) (coppia)',
        'zh': '107mm_TT(iii) 盒轴（一对）',
    },
    'Spare 107mm_TT(iii) Belt (Pair)': {
        'es': 'Correa 107mm_TT(iii) (par)',
        'en': 'Spare 107mm_TT(iii) Belt (Pair)',
        'pt': 'Correia 107mm_TT(iii) (par)',
        'it': 'Cinghia 107mm_TT(iii) (coppia)',
        'zh': '107mm_TT(iii) 皮带（一对）',
    },
    'Spare 107mm_TT(iii) Carriage Motor (bigger motor - same encoder)': {
        'es': 'Motor del carro 107mm_TT(iii) (motor más grande, mismo codificador)',
        'en': 'Spare 107mm_TT(iii) Carriage Motor (bigger motor - same encoder)',
        'pt': 'Motor do carro 107mm_TT(iii) (motor maior, mesmo encoder)',
        'it': 'Motore del carrello 107mm_TT(iii) (motore più grande, stesso encoder)',
        'zh': '107mm_TT(iii) 滑架电机（较大电机，同一编码器）',
    },
    'Spare 107mm_TT(iii) Cassette Middle Guide Pin': {
        'es': 'Pasador guía central del casete 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Cassette Middle Guide Pin',
        'pt': 'Pino guia central do cassete 107mm_TT(iii)',
        'it': 'Perno guida centrale della cassetta 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 盒中部导销',
    },
    'Spare 107mm_TT(iii) Idler Pulley Assy': {
        'es': 'Conjunto de polea tensora 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Idler Pulley Assy',
        'pt': 'Conjunto de polia tensora 107mm_TT(iii)',
        'it': 'Gruppo puleggia folle 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 惰轮组件',
    },
    'Spare 107mm_TT(iii) Linear Slide': {
        'es': 'Guía lineal 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Linear Slide',
        'pt': 'Guia linear 107mm_TT(iii)',
        'it': 'Guida lineare 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 直线导轨',
    },
    'Spare 107mm_TT(iii) Mandrel Body Assembly': {
        'es': 'Conjunto del cuerpo del mandril 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Mandrel Body Assembly',
        'pt': 'Conjunto do corpo do mandril 107mm_TT(iii)',
        'it': 'Gruppo corpo mandrino 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 芯轴主体组件',
    },
    'Spare 107mm_TT(iii) Peel Arm Assembly - LH': {
        'es': 'Conjunto del brazo de despegue 107mm_TT(iii), izquierdo',
        'en': 'Spare 107mm_TT(iii) Peel Arm Assembly - LH',
        'pt': 'Conjunto do braço de descolamento 107mm_TT(iii), esquerdo',
        'it': 'Gruppo braccio di distacco 107mm_TT(iii), sinistro',
        'zh': '107mm_TT(iii) 剥离臂组件 - 左',
    },
    'Spare 107mm_TT(iii) Peel Arm Assembly - RH': {
        'es': 'Conjunto del brazo de despegue 107mm_TT(iii), derecho',
        'en': 'Spare 107mm_TT(iii) Peel Arm Assembly - RH',
        'pt': 'Conjunto do braço de descolamento 107mm_TT(iii), direito',
        'it': 'Gruppo braccio di distacco 107mm_TT(iii), destro',
        'zh': '107mm_TT(iii) 剥离臂组件 - 右',
    },
    'Spare 107mm_TT(iii) Power Supply': {
        'es': 'Fuente de alimentación 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Power Supply',
        'pt': 'Fonte de alimentação 107mm_TT(iii)',
        'it': 'Alimentatore 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 电源',
    },
    'Spare 107mm_TT(iii) Printhead': {
        'es': 'Cabezal de impresión 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Printhead',
        'pt': 'Cabeça de impressão 107mm_TT(iii)',
        'it': 'Testina di stampa 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 打印头',
    },
    'Spare 107mm_TT(iii) Printhead Motor (smaller motor - same encoder)': {
        'es': 'Motor del cabezal de impresión 107mm_TT(iii) (motor más pequeño, mismo codificador)',
        'en': 'Spare 107mm_TT(iii) Printhead Motor (smaller motor - same encoder)',
        'pt': 'Motor da cabeça de impressão 107mm_TT(iii) (motor menor, mesmo encoder)',
        'it': 'Motore della testina di stampa 107mm_TT(iii) (motore più piccolo, stesso encoder)',
        'zh': '107mm_TT(iii) 打印头电机（较小电机，同一编码器）',
    },
    'Spare 107mm_TT(iii) Printhead Mount': {
        'es': 'Soporte del cabezal de impresión 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Printhead Mount',
        'pt': 'Suporte da cabeça de impressão 107mm_TT(iii)',
        'it': 'Supporto della testina di stampa 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 打印头支架',
    },
    'Spare 107mm_TT(iii) Printhead PCB - LH': {
        'es': 'PCB del cabezal de impresión 107mm_TT(iii), izquierdo',
        'en': 'Spare 107mm_TT(iii) Printhead PCB - LH',
        'pt': 'PCB da cabeça de impressão 107mm_TT(iii), esquerdo',
        'it': 'PCB della testina di stampa 107mm_TT(iii), sinistro',
        'zh': '107mm_TT(iii) 打印头 PCB - 左',
    },
    'Spare 107mm_TT(iii) Printhead PCB - RH': {
        'es': 'PCB del cabezal de impresión 107mm_TT(iii), derecho',
        'en': 'Spare 107mm_TT(iii) Printhead PCB - RH',
        'pt': 'PCB da cabeça de impressão 107mm_TT(iii), direito',
        'it': 'PCB della testina di stampa 107mm_TT(iii), destro',
        'zh': '107mm_TT(iii) 打印头 PCB - 右',
    },
    'Spare 107mm_TT(iii) Printhead Pivot Assy - LH': {
        'es': 'Conjunto de pivote del cabezal de impresión 107mm_TT(iii), izquierdo',
        'en': 'Spare 107mm_TT(iii) Printhead Pivot Assy - LH',
        'pt': 'Conjunto de pivô da cabeça de impressão 107mm_TT(iii), esquerdo',
        'it': 'Gruppo perno della testina di stampa 107mm_TT(iii), sinistro',
        'zh': '107mm_TT(iii) 打印头枢轴组件 - 左',
    },
    'Spare 107mm_TT(iii) Printhead Pivot Assy - RH': {
        'es': 'Conjunto de pivote del cabezal de impresión 107mm_TT(iii), derecho',
        'en': 'Spare 107mm_TT(iii) Printhead Pivot Assy - RH',
        'pt': 'Conjunto de pivô da cabeça de impressão 107mm_TT(iii), direito',
        'it': 'Gruppo perno della testina di stampa 107mm_TT(iii), destro',
        'zh': '107mm_TT(iii) 打印头枢轴组件 - 右',
    },
    'Spare 107mm_TT(iii) Ribbon Motor': {
        'es': 'Motor de la cinta 107mm_TT(iii)',
        'en': 'Spare 107mm_TT(iii) Ribbon Motor',
        'pt': 'Motor da fita 107mm_TT(iii)',
        'it': 'Motore del nastro 107mm_TT(iii)',
        'zh': '107mm_TT(iii) 色带电机',
    },
    'Spare 6530 107mm Printer PCBA (Main Printer PCB)': {
        'es': 'PCBA de impresora 6530 de 107 mm (PCB principal de la impresora)',
        'en': 'Spare 6530 107mm Printer PCBA (Main Printer PCB)',
        'pt': 'PCBA da impressora 6530 de 107 mm (PCB principal da impressora)',
        'it': 'PCBA della stampante 6530 da 107 mm (PCB principale della stampante)',
        'zh': '6530 107mm 打印机 PCBA（主打印机 PCB）',
    },
    'Spare 6530 53mm Printer PCBA (Main Printer PCB)': {
        'es': 'PCBA de impresora 6530 de 53 mm (PCB principal de la impresora)',
        'en': 'Spare 6530 53mm Printer PCBA (Main Printer PCB)',
        'pt': 'PCBA da impressora 6530 de 53 mm (PCB principal da impressora)',
        'it': 'PCBA della stampante 6530 da 53 mm (PCB principale della stampante)',
        'zh': '6530 53mm 打印机 PCBA（主打印机 PCB）',
    },
    'Spare 6530 Memory Card (Micro SD Card)': {
        'es': 'Tarjeta de memoria 6530 (tarjeta Micro SD)',
        'en': 'Spare 6530 Memory Card (Micro SD Card)',
        'pt': 'Cartão de memória 6530 (cartão Micro SD)',
        'it': 'Scheda di memoria 6530 (scheda Micro SD)',
        'zh': '6530 存储卡（Micro SD 卡）',
    },
    'Spare VJ6530 107mm_TT(iii) Cassette': {
        'es': 'Casete VJ6530 107mm_TT(iii)',
        'en': 'Spare VJ6530 107mm_TT(iii) Cassette',
        'pt': 'Cassete VJ6530 107mm_TT(iii)',
        'it': 'Cassetta VJ6530 107mm_TT(iii)',
        'zh': 'VJ6530 107mm_TT(iii) 盒',
    },
    'Spare VJ6530 53mm Cassette': {
        'es': 'Casete VJ6530 de 53 mm',
        'en': 'Spare VJ6530 53mm Cassette',
        'pt': 'Cassete VJ6530 de 53 mm',
        'it': 'Cassetta VJ6530 da 53 mm',
        'zh': 'VJ6530 53mm 盒',
    },
}


def main():
    with open(MEMORIA, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    entradas = datos.setdefault('entradas', {})
    agregadas = 0
    for texto, traducciones in TRADUCCIONES.items():
        registro = entradas.get(texto) or {}
        for idioma, valor in traducciones.items():
            registro[idioma] = valor
        registro['fuente'] = 'en'
        registro['fuente_detectada'] = 'en'
        registro['manual'] = True
        entradas[texto] = registro
        agregadas += 1
    datos['entradas'] = {k: entradas[k] for k in sorted(entradas)}
    datos['actualizado'] = '2026-11-13'
    temporal = MEMORIA + '.tmp'
    with open(temporal, 'w', encoding='utf-8', newline='') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(temporal, MEMORIA)
    print('OK: %d descripciones TTO traducidas en es/en/pt/it/zh' % agregadas)


if __name__ == '__main__':
    main()
