"""Extractor de texto de PDFs SIN dependencias (solo libreria estandar de Python).

Herramienta de Factronics Videojet Lab (Fase 1 - extraccion de fuentes).
Estrategia:
  1) Localiza los flujos `stream ... endstream` del PDF.
  2) Si son FlateDecode, los descomprime con zlib (stdlib).
  3) Camina los operadores de texto (Tj, TJ, ' y ") extrayendo los literales
     (decoded octal escapes) y las cadenas hexadecimales (<...> UTF-16BE typico
     de documentos generados con Word).
Limitaciones honestas: no desencripta, no OCR (PDFs escaneados no producen
texto), y fuentes CID con mapeos complejos pueden salir en hexadecimal.

Uso:
  python tools/leer_pdf.py ORIGEN.pdf SALIDA.txt
"""
import sys
import re
import zlib

def desescapar(literal: str) -> str:
    """Convierte un literal PDF (contenido entre parentesis ya quitados)."""
    fuera = []
    i = 0
    while i < len(literal):
        c = literal[i]
        if c == '\\' and i + 1 < len(literal):
            n = literal[i + 1]
            mapa = {'n': '\n', 'r': '\r', 't': '\t', '(': '(', ')': ')', '\\': '\\'}
            if n in mapa:
                fuera.append(mapa[n])
                i += 2
                continue
            m = re.match(r'\\([0-7]{1,3})', literal[i:])
            if m:
                try:
                    fuera.append(chr(int(m.group(1), 8)))
                    i += 1 + len(m.group(1))
                    continue
                except ValueError:
                    pass
            fuera.append(n)
            i += 2
            continue
        fuera.append(c)
        i += 1
    return ''.join(fuera)

def hex_a_texto(hexdata: str) -> str:
    txt = re.sub(r'\s+', '', hexdata)
    if len(txt) % 2 != 0:
        txt += '0'
    try:
        br = bytes.fromhex(txt)
    except ValueError:
        return ''
    # Heuristica Word: UTF-16BE (pares) o ASCII (bytes printable)
    try:
        cand16 = br.decode('utf-16-be')
        solo16 = sum(1 for ch in cand16 if ch.isprintable())
    except Exception:
        cand16, solo16 = '', 0
    cand8 = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in br)
    solo8 = sum(1 for ch in cand8 if ch.isprintable())
    if solo16 >= solo8 and any(ord(ch) > 255 or ch.isalpha() for ch in cand16):
        return cand16
    return cand8

def texto_de_flujo(seg: str) -> str:
    lineas = []
    pendientes = []
    token = re.compile(r'\((?:\\.|[^\s()\\])*\)|<[0-9A-Fa-f\s]+>|TJ\b|Tj\b|\'\b|"|\bBT\b|\bET\b|T\*')
    pila = []
    for m in token.finditer(seg):
        t = m.group(0)
        if t.startswith('('):
            pila.append(desescapar(t[1:-1]))
        elif t.startswith('<'):
            pila.append(hex_a_texto(t[1:-1]))
        elif t in ('Tj', 'TJ', "'", '"'):
            if pila:
                lineas.append(''.join(pila) if t == 'TJ' or t == "'" or t == '"' else (pila[-1] if pila else ''))
                pila = []
        elif t == 'T*' or t == 'ET':
            if pila:
                lineas.append(''.join(pila))
                pila = []
    return '\n'.join(lineas)

def extraer(ruta: str):
    data = open(ruta, 'rb').read()
    partes = []
    for m in re.finditer(rb'stream[\r\n]+(.*?)endstream', data, re.S):
        crudo = m.group(1)
        if b'FlateDecode' in data[max(0, m.start() - 400):m.start() + 40]:
            try:
                crudo = zlib.decompress(crudo)
            except Exception:
                try:
                    crudo = zlib.decompress(crudo.rstrip(b'\r\n'))
                except Exception:
                    continue
        else:
            continue  # streams sin filtro conocido (imagenes) no aportan texto
        seg = crudo.decode('latin-1', 'ignore')
        t = texto_de_flujo(seg)
        if t.strip():
            partes.append(t)
    return partes

def main():
    if len(sys.argv) < 3:
        print('Uso: python tools/leer_pdf.py ORIGEN.pdf SALIDA.txt')
        sys.exit(1)
    origen, salida = sys.argv[1], sys.argv[2]
    try:
        partes = extraer(origen)
    except Exception as e:
        print('ERROR', e)
        sys.exit(2)
    texto = '\n\n'.join(partes)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto).strip()
    meta = ';'.join(partes) .__len__()
    with open(salida, 'w', encoding='utf-8') as f:
        f.write(f'# EXTRAIDO POR tools/leer_pdf.py (stdlib) - fuente: {origen}\n')
        f.write(f'# bloques_de_texto={len(partes)} caracteres={len(texto)}\n\n')
        f.write(texto)
    print(f'OK {salida} bloques={len(partes)} caracteres={len(texto)}')

if __name__ == '__main__':
    main()
