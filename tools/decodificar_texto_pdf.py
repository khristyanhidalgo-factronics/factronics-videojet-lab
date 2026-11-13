# -*- coding: utf-8 -*-
"""Decodifica la capa de texto de PDFs con fuentes TrueType subseteadas.

Algunos PDFs generados por Ghostscript usan codigos propios (4..63) y una
tabla /Differences que apunta a nombres `gNN`. El `cmap` incrustado solo
mapea esos codigos a GIDs, no a Unicode. Para recuperar el texto se usa el
`cmap` de la fuente original del sistema (p. ej. Arial Narrow) y se traduce
GID -> Unicode.

No rasteriza ni hace OCR: lee el content stream y las fuentes incrustadas.

Uso:
  python tools/decodificar_texto_pdf.py --pdf ruta.pdf
  python tools/decodificar_texto_pdf.py --pdf ruta.pdf --salida texto.txt --json detalle.json
"""
import argparse
import json
import os
import re
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

FUENTES_SISTEMA = {
    'arialnarrow,bold': r'C:\Windows\Fonts\ARIALNB.TTF',
    'arialnarrow': r'C:\Windows\Fonts\ARIALN.TTF',
    'arial,bold': r'C:\Windows\Fonts\arialbd.ttf',
    'arial': r'C:\Windows\Fonts\arial.ttf',
}


def _objetos(b):
    """Devuelve {numero: cuerpo} de los objetos clasicos del PDF."""
    objs = {}
    for m in re.finditer(rb'(?m)^(\d+)\s+(\d+)\s+obj\b', b):
        num = int(m.group(1))
        fin = b.find(b'endobj', m.end())
        if fin >= 0:
            objs[num] = b[m.end():fin]
    return objs


def _referencia(body, clave):
    """Extrae el numero de objeto de una clave /Clave N 0 R."""
    m = re.search(rb'/' + re.escape(clave.encode('latin-1')) + rb'\s+(\d+)\s+0\s+R', body)
    return int(m.group(1)) if m else None


def _stream(objs, num):
    body = objs.get(num)
    if body is None:
        return None
    m = re.search(rb'stream\r?\n', body)
    if not m:
        return None
    raw = re.sub(rb'\r?\nendstream\s*$', b'', body[m.end():])
    if b'/FlateDecode' in body[:m.start()]:
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return raw
    return raw


def _tablas_sfnt(data):
    if len(data) < 12:
        return {}
    num = struct.unpack('>H', data[4:6])[0]
    tablas = {}
    for i in range(num):
        off = 12 + i * 16
        if off + 16 > len(data):
            break
        tag = data[off:off + 4].decode('latin-1')
        toff, tlen = struct.unpack('>II', data[off + 8:off + 16])
        tablas[tag] = (toff, tlen)
    return tablas


def _cmap_unicode(data):
    """Unicode -> GID usando la mejor subttabla cmap disponible."""
    tablas = _tablas_sfnt(data)
    if 'cmap' not in tablas:
        return {}
    off, ln = tablas['cmap']
    cm = data[off:off + ln]
    if len(cm) < 4:
        return {}
    n = struct.unpack('>H', cm[2:4])[0]
    subs = []
    for i in range(n):
        if 4 + i * 8 + 8 > len(cm):
            break
        pid, eid, so = struct.unpack('>HHI', cm[4 + i * 8:12 + i * 8])
        subs.append((pid, eid, so))
    orden = {(3, 1): 0, (3, 0): 1, (0, 3): 2, (0, 4): 3, (0, 6): 4, (1, 0): 5}
    subs.sort(key=lambda x: orden.get((x[0], x[1]), 9))
    u2g = {}
    for pid, eid, so in subs:
        if so + 2 > len(cm):
            continue
        fmt = struct.unpack('>H', cm[so:so + 2])[0]
        if fmt == 4:
            if so + 8 > len(cm):
                continue
            segx2 = struct.unpack('>H', cm[so + 6:so + 8])[0]
            seg = segx2 // 2
            endo = so + 14
            starto = endo + segx2 + 2
            deltao = starto + segx2
            rangeo = deltao + segx2
            for s in range(seg):
                try:
                    end = struct.unpack('>H', cm[endo + s * 2:endo + s * 2 + 2])[0]
                    start = struct.unpack('>H', cm[starto + s * 2:starto + s * 2 + 2])[0]
                    delta = struct.unpack('>h', cm[deltao + s * 2:deltao + s * 2 + 2])[0]
                    ro = struct.unpack('>H', cm[rangeo + s * 2:rangeo + s * 2 + 2])[0]
                except struct.error:
                    break
                for c in range(start, min(end, 0xFFFF) + 1):
                    if ro == 0:
                        g = (c + delta) & 0xFFFF
                    else:
                        gi = rangeo + s * 2 + ro + (c - start) * 2
                        if gi + 2 > len(cm):
                            continue
                        g = struct.unpack('>H', cm[gi:gi + 2])[0]
                        if g:
                            g = (g + delta) & 0xFFFF
                    if g:
                        u2g.setdefault(c, g)
        elif fmt == 6:
            if so + 10 > len(cm):
                continue
            first, count = struct.unpack('>HH', cm[so + 6:so + 10])
            for j in range(count):
                if so + 12 + j * 2 > len(cm):
                    break
                g = struct.unpack('>H', cm[so + 10 + j * 2:so + 12 + j * 2])[0]
                if g:
                    u2g.setdefault(first + j, g)
        elif fmt == 0:
            for c in range(256):
                if so + 6 + c >= len(cm):
                    break
                g = cm[so + 6 + c]
                if g:
                    u2g.setdefault(c, g)
    return u2g


def _gid_a_unicode(ruta):
    """GID -> Unicode de una fuente del sistema, prefiriendo ASCII."""
    data = open(ruta, 'rb').read()
    u2g = _cmap_unicode(data)
    inv = {}

    def score(u):
        if 32 <= u < 127:
            return 0
        if 160 <= u < 256:
            return 1
        if u >= 0x2000:
            return 2
        return 3

    for u, g in u2g.items():
        if g not in inv or score(u) < score(inv[g]):
            inv[g] = u
    return inv


def _fuente_sistema(basefont):
    nombre = re.sub(r'^[A-Z]{6}\+', '', basefont or '').strip().lower()
    nombre = nombre.replace(' ', '')
    return FUENTES_SISTEMA.get(nombre)


def _encoding_diferencias(objs, num):
    body = objs.get(num)
    if body is None:
        return {}
    m = re.search(rb'/Differences\s*\[(.*?)\]', body, re.S)
    if not m:
        return {}
    tokens = re.findall(rb'/([A-Za-z0-9_.]+)|(\d+)', m.group(1))
    out = {}
    code = None
    for nombre, numero in tokens:
        if nombre:
            out[code] = nombre.decode('latin-1')
            code += 1
        else:
            code = int(numero)
    return out


def _decodificar_string(raw, emap, inv):
    s = bytearray()
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == 0x5c and i + 1 < len(raw):
            nxt = raw[i + 1]
            if nxt in b'nrtbf()\\':
                s.append({'n': 10, 'r': 13, 't': 9, 'b': 8, 'f': 12}.get(chr(nxt), nxt))
                i += 2
                continue
            if 48 <= nxt <= 55:
                octal = chr(nxt)
                i += 2
                for _ in range(2):
                    if i < len(raw) and 48 <= raw[i] <= 55:
                        octal += chr(raw[i])
                        i += 1
                    else:
                        break
                s.append(int(octal, 8))
                continue
            i += 1
            continue
        s.append(ch)
        i += 1
    out = []
    for ch in s:
        nombre = emap.get(ch)
        if nombre and re.fullmatch(r'g\d+', nombre):
            u = inv.get(int(nombre[1:]))
            if u is not None:
                out.append(chr(u))
                continue
        if 32 <= ch < 127:
            out.append(chr(ch))
        else:
            out.append('<%02x>' % ch)
    return ''.join(out)


def _decodificar_tj(arr, emap, inv):
    texto = []
    for m in re.finditer(rb'\((?:\\.|[^\\()])*\)|(-?\d+(?:\.\d+)?)', arr, re.S):
        tok = m.group(0)
        if tok.startswith(b'('):
            texto.append(_decodificar_string(tok[1:-1], emap, inv))
        else:
            try:
                v = float(tok)
                if v < -150:
                    texto.append(' ')
            except ValueError:
                pass
    return ''.join(texto)


def decodificar_pdf(ruta):
    """Devuelve {texto, lineas, fuentes, pns, metodo, error}."""
    b = open(ruta, 'rb').read()
    objs = _objetos(b)
    pagina = None
    for num, body in objs.items():
        if re.search(rb'/Type\s*/Page\b', body):
            pagina = num
            break
    if pagina is None:
        return {'texto': '', 'lineas': [], 'fuentes': {}, 'pns': [],
                'metodo': 'sin-pagina', 'error': 'no se encontro /Type /Page'}

    page = objs[pagina]
    contenido = _referencia(page, 'Contents')
    if contenido is None:
        return {'texto': '', 'lineas': [], 'fuentes': {}, 'pns': [],
                'metodo': 'sin-contenido', 'error': 'la pagina no tiene /Contents'}

    recursos = _referencia(page, 'Resources')
    font_dict = {}
    if recursos and recursos in objs:
        recursos_body = objs[recursos]
    else:
        m = re.search(rb'/Resources\s*<<(.*?)>>', page, re.S)
        recursos_body = m.group(1) if m else b''
    font_ref = _referencia(recursos_body, 'Font')
    if font_ref and font_ref in objs:
        font_body = objs[font_ref]
    else:
        mfont = re.search(rb'/Font\s*<<(.*?)>>', recursos_body, re.S)
        font_body = mfont.group(1) if mfont else b''
    for m in re.finditer(rb'/([A-Za-z0-9]+)\s+(\d+)\s+0\s+R', font_body):
        font_dict[m.group(1).decode('latin-1')] = int(m.group(2))

    fuentes = {}
    for nombre, num in font_dict.items():
        fbody = objs.get(num, b'')
        mb = re.search(rb'/BaseFont\s*/([^\s/<>\[\]]+)', fbody)
        basefont = mb.group(1).decode('latin-1') if mb else ''
        descriptor = _referencia(fbody, 'FontDescriptor')
        fontfile = _referencia(objs.get(descriptor, b''), 'FontFile2') if descriptor else None
        encoding = _referencia(fbody, 'Encoding')
        emap = _encoding_diferencias(objs, encoding) if encoding else {}
        ruta_fuente = _fuente_sistema(basefont)
        inv = _gid_a_unicode(ruta_fuente) if ruta_fuente and os.path.exists(ruta_fuente) else {}
        fuentes[nombre] = {
            'objeto': num, 'basefont': basefont, 'fontfile': fontfile,
            'encoding': encoding, 'sistema': ruta_fuente,
            'gids': len(inv), 'diferencias': len(emap),
        }

    d = _stream(objs, contenido)
    if d is None:
        return {'texto': '', 'lineas': [], 'fuentes': fuentes, 'pns': [],
                'metodo': 'sin-stream', 'error': 'no se pudo leer /Contents'}

    lineas = []
    for bloque in re.findall(rb'BT(.*?)ET', d, re.S):
        actual = None
        partes = []
        for m in re.finditer(
                rb'/([A-Za-z0-9]+)\s+[\d.]+\s+Tf|\[(.*?)\]\s*TJ|\((.*?)\)\s*Tj',
                bloque, re.S):
            if m.group(1):
                actual = m.group(1).decode('latin-1')
                continue
            info = fuentes.get(actual)
            if not info:
                continue
            emap = _encoding_diferencias(objs, info['encoding']) if info['encoding'] else {}
            inv = _gid_a_unicode(info['sistema']) if info['sistema'] and os.path.exists(info['sistema']) else {}
            if m.group(2) is not None:
                partes.append(_decodificar_tj(m.group(2), emap, inv))
            elif m.group(3) is not None:
                partes.append(_decodificar_string(m.group(3), emap, inv))
        texto = re.sub(r'\s+', ' ', ' '.join(partes)).strip()
        if texto:
            lineas.append({'fuente': actual, 'texto': texto})

    texto = '\n'.join(l['texto'] for l in lineas)
    pns = sorted(set(re.findall(r'\b[A-Z]{1,3}-\d{4,6}\b', texto)))
    metodo = 'texto-decodificado-cmap' if texto else 'sin-texto-decodificado'
    return {'texto': texto, 'lineas': lineas, 'fuentes': fuentes, 'pns': pns,
            'metodo': metodo, 'error': None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--salida', default='')
    ap.add_argument('--json', default='')
    args = ap.parse_args()
    d = decodificar_pdf(args.pdf)
    print('metodo:', d['metodo'])
    print('lineas:', len(d['lineas']), 'chars:', len(d['texto']), 'pns:', d['pns'])
    for f, info in d['fuentes'].items():
        print('fuente', f, info)
    print('--- texto ---')
    print(d['texto'])
    if args.salida:
        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        with open(args.salida, 'w', encoding='utf-8') as f:
            f.write('# Texto decodificado del PDF: %s\n' % args.pdf)
            f.write('# metodo=%s lineas=%d caracteres=%d pns=%s\n\n'
                    % (d['metodo'], len(d['lineas']), len(d['texto']), ','.join(d['pns'])))
            f.write(d['texto'] + '\n')
        print('guardado:', args.salida)
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print('guardado:', args.json)
    return 0 if d['texto'] else 1


if __name__ == '__main__':
    sys.exit(main())
