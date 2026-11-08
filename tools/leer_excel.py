"""Lector de archivos .xlsx sin dependencias (solo libreria estandar de Python).

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Uso:
  python tools/leer_excel.py ARCHIVO.xlsx [hoja1,hoja2] [SALIDA.json]
Sin SALIDA: imprime a stdout. Con SALIDA: guarda JSON UTF-8 y resumen corto.
Extrae celdas por hoja (hasta --max filas limitadas por seguridad de memoria).
"""
import sys
import zipfile
import json
import re
from xml.etree import ElementTree as ET

NS_M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
MAX_FILAS = 400

def cola_texto(elem):
    """Concatena todos los <t> bajo un elemento <si> o <is>."""
    return ''.join(t.text or '' for t in elem.iter('{%s}t' % NS_M))

def leer_xlsx(ruta, hojas=None, max_filas=MAX_FILAS):
    z = zipfile.ZipFile(ruta)
    # 1) cadenas compartidas
    compartidas = []
    try:
        ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in ss.findall('{%s}si' % NS_M):
            compartidas.append(cola_texto(si))
    except KeyError:
        pass
    # 2) hojas del libro y sus destinos
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    mapa_rels = {rel.get('Id'): rel.get('Target') for rel in rels}
    resultado = {}
    for hoja in wb.findall('{%s}sheets/{%s}sheet' % (NS_M, NS_M)):
        nombre = hoja.get('name')
        if hojas and nombre not in hojas:
            continue
        rid = hoja.get('{%s}id' % NS_R)
        destino = mapa_rels.get(rid, '')
        if destino.startswith('/'):
            destino = destino[1:]
        elif not destino.startswith('xl/'):
            destino = 'xl/' + destino
        try:
            datos = z.read(destino)
        except KeyError:
            continue
        sht = ET.fromstring(datos)
        filas = []
        for fila in sht.findall('{%s}sheetData/{%s}row' % (NS_M, NS_M)):
            celdas = {}
            for c in fila.findall('{%s}c' % NS_M):
                ref = c.get('r') or ''
                mcol = re.match(r'[A-Z]+', ref)
                col = mcol.group() if mcol else ref
                tipo = c.get('t')
                v = c.find('{%s}v' % NS_M)
                if v is not None:
                    valor = v.text or ''
                    if tipo == 's':
                        try:
                            valor = compartidas[int(valor)]
                        except (ValueError, IndexError):
                            valor = valor
                else:
                    en_linea = c.find('{%s}is' % NS_M)
                    valor = cola_texto(en_linea) if en_linea is not None else ''
                if valor != '':
                    celdas[col] = valor
            if celdas:
                filas.append({'fila': fila.get('r'), 'celdas': celdas})
            if len(filas) >= max_filas:
                break
        resultado[nombre] = {'filas': len(filas), 'cortado': len(filas) >= max_filas, 'contenido': filas}
    return resultado

def main():
    if len(sys.argv) < 2:
        print('Uso: python tools/leer_excel.py ARCHIVO.xlsx [hojas] [SALIDA.json]')
        sys.exit(1)
    ruta = sys.argv[1]
    hojas = None
    salida = None
    # Formas de llamada:
    #   leer_excel.py ARCHIVO.xmlx                 -> imprime a stdout
    #   leer_excel.py ARCHIVO.xlsx SALIDA.json     -> guarda en SALIDA (Archivo automatico .json)
    #   leer_excel.py ARCHIVO.xlsx hoja1,hoja2 SALIDA.json
    resto = sys.argv[2:]
    if resto and resto[-1].lower().endswith('.json'):
        salida = resto[-1]
        resto = resto[:-1]
    if resto:
        hojas = set(resto[0].split(','))
    datos = leer_xlsx(ruta, hojas=hojas)
    texto = json.dumps(datos, ensure_ascii=False, indent=1)
    if salida:
        with open(salida, 'w', encoding='utf-8') as f:
            f.write(texto)
        print('OK', salida, '| hojas:', list(datos.keys()), '| filas total:', sum(h['filas'] for h in datos.values()))
    else:
        print(texto)

if __name__ == '__main__':
    main()
