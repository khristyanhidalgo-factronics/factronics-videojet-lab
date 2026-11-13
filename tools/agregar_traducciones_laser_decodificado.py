# -*- coding: utf-8 -*-
"""Agrega las traducciones de las dos descripciones laser decodificadas.

MedidoresPortenciaCO2.pdf tenia una capa de texto con codificacion propia.
Al decodificarla aparecieron las descripciones exactas de AL-67438 y AL-66517.
Se traducen a mano a es/pt/it/zh; en conserva el texto original.

Uso:
  python tools/agregar_traducciones_laser_decodificado.py
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
    'this is the power wizard that is the small hand held device limited to 10s measuring': {
        'es': 'este es el Power Wizard, el pequeño dispositivo portátil limitado a 10 s de medición',
        'en': 'this is the power wizard that is the small hand held device limited to 10s measuring',
        'pt': 'este é o Power Wizard, o pequeno dispositivo portátil limitado a 10 s de medição',
        'it': 'questo è il Power Wizard, il piccolo dispositivo portatile limitato a 10 s di misurazione',
        'zh': '这是 Power Wizard 小型手持设备，测量时间限制为 10 秒',
    },
    'this is the professional power meter that our laser engineers would use for long tests': {
        'es': 'este es el medidor de potencia profesional que nuestros ingenieros láser usarían para pruebas prolongadas',
        'en': 'this is the professional power meter that our laser engineers would use for long tests',
        'pt': 'este é o medidor de potência profissional que nossos engenheiros de laser usariam para testes longos',
        'it': 'questo è il misuratore di potenza professionale che i nostri tecnici laser userebbero per test prolungati',
        'zh': '这是我们的激光工程师用于长时间测试的专业功率计',
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
    print('OK: %d descripciones laser traducidas en es/en/pt/it/zh' % agregadas)


if __name__ == '__main__':
    main()
