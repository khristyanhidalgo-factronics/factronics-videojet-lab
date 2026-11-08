"""Extractor de texto de PDFs cifrados (handler estandar RC4) con CMaps ToUnicode.

v2: ademas del descifrado RC4 (R4/V4/CFM-V2, contrasena de usuario vacia), aplica
los CMaps /ToUnicode de las fuentes para traducir GIDs (Type0/Identity-H, 2 bytes)
a texto Unicode real. Sin dependencias (hashlib, zlib, struct, re).

Flujo:
  1) localiza /Encrypt, deriva la clave (algoritmo 2) y descifra cada stream;
  2) infla FlateDecode;
  3) parsea los objetos /Type/Font: nombre de recurso -> obj -> /ToUnicode;
  4) parsea los CMaps ToUnicode (bfchar/bfrange);
  5) recorre cada content stream respetando '/Fn Tf' y decodifica Tj/TJ con el mapa.

Uso:
  python tools/leer_pdf_cifrado.py ORIGEN.pdf SALIDA.txt
"""
import hashlib
import os
import re
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PADDING = bytes.fromhex(
    '28BF4E5E4E758A4164004E56FFFA01082E2E00B6D0683E802F0CA9FE6453697A')

PATRON_OBJ = re.compile(rb'(?:^|[\r\n\s])(\d+)\s+(\d+)\s+obj\b', re.M)
PATRON_STREAM = re.compile(rb'stream\r?\n')


# ------------------------------------------------------------------ handler RC4
def leer_literal_bytes(b, pos):
    """String literal PDF '( ... )' -> bytes reales (respeta escapes y anidacion)."""
    if b[pos:pos + 1] != b'(':
        return b'', pos
    i = pos + 1
    nivel = 1
    salida = bytearray()
    while i < len(b) and nivel > 0:
        c = b[i:i + 1]
        if c == b'\\':
            n = b[i + 1:i + 2]
            mapa = {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'\b',
                    b'f': b'\f', b'(': b'(', b')': b')', b'\\': b'\\'}
            if n in mapa:
                salida += mapa[n]
                i += 2
                continue
            m = re.match(rb'([0-7]{1,3})', b[i + 1:i + 4])
            if m:
                salida.append(int(m.group(1), 8) & 0xFF)
                i += 1 + len(m.group(1))
                continue
            salida += n
            i += 2
            continue
        if c == b'(':
            nivel += 1
        elif c == b')':
            nivel -= 1
            if nivel == 0:
                i += 1
                break
        salida += c
        i += 1
    return bytes(salida), i


def rc4(clave, dato):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + clave[i % len(clave)]) & 0xFF
        s[i], s[j] = s[j], s[i]
    salida = bytearray(len(dato))
    i = j = 0
    for k, byte in enumerate(dato):
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]
        salida[k] = byte ^ s[(s[i] + s[j]) & 0xFF]
    return bytes(salida)


class Handler:
    def __init__(self, id0, O, U, P, R, V, nbytes):
        self.R, self.V, self.n = R, V, nbytes
        self.clave = self._clave(O, P, id0)

    def _clave(self, O, P, id0):
        h = hashlib.md5()
        h.update(PADDING)
        h.update(O)
        h.update(struct.pack('<i', P))
        h.update(id0)
        digest = h.digest()
        if self.R >= 3:
            for _ in range(50):
                digest = hashlib.md5(digest[:self.n]).digest()
        return digest[:self.n]

    def clave_objeto(self, num, gen):
        ext = struct.pack('<i', num)[:3] + struct.pack('<i', gen)[:2]
        return hashlib.md5(self.clave + ext).digest()[:min(self.n + 5, 16)]

    def descifrar(self, num, gen, dato):
        return rc4(self.clave_objeto(num, gen), dato)


def leer_handler(b):
    m = re.search(rb'/Encrypt\s+(\d+)\s+(\d+)\s+R', b)
    if not m:
        return None
    num = int(m.group(1))
    om = re.search(rb'(?:^|[\r\n\s])%d\s+0\s+obj\b(.*?)endobj' % num, b, re.S)
    if not om:
        return None
    d = om.group(1)
    if b'/Filter/Standard' not in d.replace(b' ', b''):
        return None
    R = int((re.search(rb'/R\s+(\d+)', d) or [0, b'2'])[1])
    V = int((re.search(rb'/V\s+(\d+)', d) or [0, b'1'])[1])
    ml = re.search(rb'/Length\s+(\d+)', d)
    nbytes = int(ml.group(1)) // 8 if ml else 5
    mp = re.search(rb'/P\s+(-?\d+)', d)
    P = int(mp.group(1)) if mp else 0
    if b'/CF' in d:
        mcf = re.search(rb'/CFM\s*/(\w+)', d)
        if mcf and mcf.group(1) not in (b'V2', b''):
            return None  # AES no soportado en v2
    posO = d.find(b'(', d.find(b'/O'))
    posU = d.find(b'(', d.find(b'/U'))
    if posO < 0 or posU < 0:
        return None
    O, _ = leer_literal_bytes(d, posO)
    U, _ = leer_literal_bytes(d, posU)
    mtr = re.search(rb'/ID\s*\[\s*<([0-9A-Fa-f]+)>', b)
    if not mtr:
        return None
    id0 = bytes.fromhex(mtr.group(1).decode('ascii'))
    return Handler(id0, O, U, P, R, V, nbytes)


# ------------------------------------------------------------------ objetos/streams
def objetos_dict(b):
    """Devuelve {num: dict_bytes} para objetos top-level `N G obj ... endobj`."""
    salida = {}
    for m in PATRON_OBJ.finditer(b):
        num = int(m.group(1))
        fin = b.find(b'endobj', m.end())
        if fin < 0:
            continue
        cuerpo = b[m.end():fin]
        corte = cuerpo.find(b'stream')
        if corte >= 0:
            cuerpo = cuerpo[:corte]
        salida[num] = cuerpo
    return salida


def stream_de_objeto(b, num, handler):
    """Localiza el stream del objeto num, lo descifra y lo infla si aplica."""
    m = re.search(rb'(?:^|[\r\n\s])%d\s+0\s+obj\b(.*?)stream\r?\n' % num, b, re.S)
    if not m:
        return None, None
    dicc = m.group(1)
    inicio = m.end()
    fin = b.find(b'endstream', inicio)
    if fin < 0:
        return None, None
    crudo = b[inicio:fin]
    if handler:
        crudo = handler.descifrar(num, 0, crudo)
    if b'FlateDecode' in dicc:
        try:
            crudo = zlib.decompressobj().decompress(crudo)
        except zlib.error:
            return None, dicc
    return crudo, dicc


def objetos_objstm(b, dicts, handler):
    """Extrae los objetos empaquetados en los streams /Type/ObjStm (PDF 1.5+):
    cabecera de pares `num offset` + cuerpos concatenados a partir de /First."""
    extra = {}
    for num, d in list(dicts.items()):
        if b'/ObjStm' not in d:
            continue
        dato, dicc = stream_de_objeto(b, num, handler)
        if not dato:
            continue
        mn = re.search(rb'/N\s+(\d+)', d)
        mf = re.search(rb'/First\s+(\d+)', d)
        if not (mn and mf):
            continue
        n = int(mn.group(1))
        first = int(mf.group(1))
        pares = []
        for m in re.finditer(rb'(\d+)\s+(\d+)', dato[:first]):
            pares.append((int(m.group(1)), int(m.group(2))))
        for i, (objnum, off) in enumerate(pares[:n]):
            inicio = first + off
            fin = first + pares[i + 1][1] if i + 1 < len(pares) else len(dato)
            extra[objnum] = dato[inicio:fin]
    return extra


# ------------------------------------------------------------------ ToUnicode
def parsear_cmap(texto):
    """Parsea un CMap ToUnicode -> {codigo_int: str_unicode}."""
    mapa = {}
    # bfchar
    for bloque in re.findall(r'beginbfchar(.*?)endbfchar', texto, re.S):
        for src, dst in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', bloque):
            try:
                codigo = int(src, 16)
                mapa[codigo] = bytes.fromhex(dst).decode('utf-16-be', errors='replace')
            except ValueError:
                continue
    # bfrange (destino unico y destino array)
    for bloque in re.findall(r'beginbfrange(.*?)endbfrange', texto, re.S):
        for m in re.finditer(
                r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*'
                r'(<[0-9A-Fa-f]+>|\[[^\]]*\])', bloque, re.S):
            lo = int(m.group(1), 16)
            hi = int(m.group(2), 16)
            dst = m.group(3)
            if dst.startswith('['):
                destinos = re.findall(r'<([0-9A-Fa-f]+)>', dst)
                for i, d in enumerate(destinos[:hi - lo + 1]):
                    mapa[lo + i] = bytes.fromhex(d).decode('utf-16-be',
                                                           errors='replace')
            else:
                base = bytes.fromhex(dst[1:-1]).decode('utf-16-be',
                                                       errors='replace')
                if not base:
                    continue
                for i in range(hi - lo + 1):
                    if len(base) >= 2:
                        mapa[lo + i] = base[:-1] + chr(ord(base[-1]) + i)
                    else:
                        mapa[lo + i] = chr(ord(base[0]) + i)
    return mapa


def fuentes_del_pdf(b, dicts, handler):
    """Devuelve {nombre_recurso: {'mapa': dict|None, 'bytes': 1|2}}."""
    # obj de fuente -> ToUnicode ref
    to_un_codigos = {}
    info_fuente = {}
    for num, d in dicts.items():
        if b'/Type/Font' not in d.replace(b' ', b''):
            continue
        mtu = re.search(rb'/ToUnicode\s+(\d+)\s+0\s+R', d)
        ancho = 2 if (b'/Type0' in d.replace(b' ', b'')
                      or b'Identity-H' in d) else 1
        info_fuente[num] = {'tu': int(mtu.group(1)) if mtu else None,
                            'bytes': ancho}

    # nombre de recurso (p.ej. /F1) -> objeto de fuente
    nombres = {}
    for d in dicts.values():
        i = d.find(b'/Font')
        if i < 0:
            continue
        trozo = d[i:i + 500]
        for m in re.finditer(rb'/([A-Za-z0-9]+)\s+(\d+)\s+0\s+R', trozo):
            nombre = m.group(1).decode('latin-1')
            obj = int(m.group(2))
            if obj in info_fuente:
                nombres.setdefault(nombre, obj)

    salida = {}
    for nombre, obj in nombres.items():
        info = info_fuente[obj]
        mapa = None
        if info['tu'] is not None:
            texto_cmap, _ = stream_de_objeto(b, info['tu'], handler)
            if texto_cmap:
                mapa = parsear_cmap(texto_cmap.decode('latin-1', errors='replace'))
        salida[nombre] = {'mapa': mapa, 'bytes': info['bytes']}
    return salida


# ------------------------------------------------------------------ texto
def decodificar_bytes(datos, fuente):
    """Decodifica bytes de un string PDF con el mapa de la fuente activa."""
    if fuente is None:
        return ''.join(chr(c) if 32 <= c < 127 else '' for c in datos)
    mapa = fuente.get('mapa')
    ancho = fuente.get('bytes', 1)
    if not mapa:
        if ancho == 2:
            return datos.decode('utf-16-be', errors='replace')
        return datos.decode('latin-1', errors='replace')
    salida = []
    if ancho == 2:
        for i in range(0, len(datos) - 1, 2):
            codigo = (datos[i] << 8) | datos[i + 1]
            salida.append(mapa.get(codigo, ''))
    else:
        for c in datos:
            salida.append(mapa.get(c, chr(c) if 32 <= c < 127 else ''))
    return ''.join(salida)


TOKEN = re.compile(
    rb'/([A-Za-z0-9]+)\s+[\d.]+\s+Tf'          # seleccion de fuente
    rb'|\((?:\\.|[^()\\])*\)'                  # string literal (con espacios)
    rb'|<[0-9A-Fa-f\s]+>'                      # string hex
    rb'|TJ\b|Tj\b|\'|"'                        # operadores de texto
    rb'|T\*|\bET\b')


def texto_de_flujo_dec(dato, fuentes):
    lineas = []
    pila = []
    fuente = None
    for m in TOKEN.finditer(dato):
        t = m.group(0)
        if t.endswith(b'Tf'):
            nombre = m.group(1).decode('latin-1')
            fuente = fuentes.get(nombre)
            continue
        if t.startswith(b'('):
            datos, _ = leer_literal_bytes(t, 0)
            pila.append(decodificar_bytes(datos, fuente))
        elif t.startswith(b'<'):
            hexd = re.sub(rb'\s+', b'', t[1:-1])
            if len(hexd) % 2:
                hexd += b'0'
            try:
                datos = bytes.fromhex(hexd.decode('ascii'))
            except ValueError:
                datos = b''
            pila.append(decodificar_bytes(datos, fuente))
        elif t in (b'Tj', b'TJ', b"'", b'"'):
            if pila:
                lineas.append(''.join(pila))
                pila = []
        elif t in (b'T*', b'ET'):
            if pila:
                lineas.append(''.join(pila))
                pila = []
    return '\n'.join(lineas)


# ------------------------------------------------------------------ extraccion
def extraer(ruta):
    b = open(ruta, 'rb').read()
    handler = leer_handler(b)
    if handler is None and b'/Encrypt' in b:
        raise RuntimeError('PDF cifrado no soportado (AES u otro filtro)')
    dicts = objetos_dict(b)
    if handler:
        dicts.update(objetos_objstm(b, dicts, handler))
    fuentes = fuentes_del_pdf(b, dicts, handler) if handler else {}
    partes = []
    bloques = 0
    for m in PATRON_STREAM.finditer(b):
        cabecera = b[max(0, m.start() - 320):m.start()]
        om = None
        for cand in PATRON_OBJ.finditer(cabecera):
            om = cand
        if om is None:
            continue
        num = int(om.group(1))
        dicc = cabecera[om.end():]
        if b'/Image' in dicc or b'/ObjStm' in dicc or b'/FontFile' in dicc:
            continue
        if b'FlateDecode' not in dicc:
            continue
        inicio = m.end()
        fin = b.find(b'endstream', inicio)
        if fin < 0:
            continue
        crudo = b[inicio:fin]
        if handler:
            crudo = handler.descifrar(num, 0, crudo)
        try:
            dato = zlib.decompressobj().decompress(crudo)
        except zlib.error:
            continue
        if b'BT' not in dato:
            continue
        bloques += 1
        t = texto_de_flujo_dec(dato, fuentes)
        if t.strip():
            partes.append(t)
    return partes, bloques, handler is not None


# ---------------------------------------------------- extraccion POSICIONAL (v3)
TOKENS_POS = re.compile(
    rb'\((?:\\.|[^()\\])*\)'      # string literal
    rb'|<[0-9A-Fa-f\s]*>'         # string hex
    rb'|/[^\s/<>\[\](){}]+'       # nombre
    rb'|[-+]?[0-9]*\.?[0-9]+'     # numero
    rb'|\[|\]'                    # delimitadores de array
    rb"|[A-Za-z*'\"]+"            # operador
)


def runs_de_flujo(dato, fuentes):
    """Corridas de texto con coordenadas VISUALES: [(y, x, texto)]. Implementa el
    modelo basico de matrices de texto (Tm/Td/TD/T*/TL/Tj/TJ/'/") y la matriz
    grafica (q/Q/cm) para que el orden sea el visual real de la pagina."""
    pila = []
    en_array = None
    runs = []
    fuente = None
    tamano = 10.0
    tm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]   # a b c d e f
    lm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    leading = 0.0
    ctm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    pila_ctm = []

    def multiplicar(m1, m2):
        a1, b1, c1, d1, e1, f1 = m1
        a2, b2, c2, d2, e2, f2 = m2
        return [a1 * a2 + b1 * c2, a1 * b2 + b1 * d2,
                c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
                e1 * a2 + f1 * c2 + e2, e1 * b2 + f1 * d2 + f2]

    def emitir(txt):
        if not txt or not txt.strip():
            return
        x = lm[4] + tm[4]
        y = lm[5] + tm[5]
        X = ctm[0] * x + ctm[2] * y + ctm[4]
        Y = ctm[1] * x + ctm[3] * y + ctm[5]
        runs.append((round(Y, 1), round(X, 1), txt))
        # avance aproximado de la linea (sin metricas de fuente): ancho medio 0.45em
        lm[4] += len(txt) * tamano * 0.45

    for m in TOKENS_POS.finditer(dato):
        t = m.group(0)
        if t == b'[':
            en_array = []
            continue
        if t == b']':
            pila.append(('array', en_array or []))
            en_array = None
            continue
        if t.startswith(b'(') or t.startswith(b'<'):
            if t.startswith(b'('):
                datos, _ = leer_literal_bytes(t, 0)
            else:
                hexd = re.sub(rb'\s+', b'', t[1:-1])
                if len(hexd) % 2:
                    hexd += b'0'
                try:
                    datos = bytes.fromhex(hexd.decode('ascii'))
                except ValueError:
                    datos = b''
            texto = decodificar_bytes(datos, fuente)
            if en_array is not None:
                en_array.append(texto)
            else:
                pila.append(texto)
            continue
        if t.startswith(b'/'):
            pila.append(('nombre', t[1:].decode('latin-1')))
            continue
        if re.fullmatch(rb'[-+]?[0-9]*\.?[0-9]+', t):
            valor = float(t)
            if en_array is not None:
                en_array.append(valor)
            else:
                pila.append(valor)
            continue

        op = t.decode('latin-1')
        numeros = [x for x in pila if isinstance(x, float)]
        textos = [x for x in pila if isinstance(x, str)]
        nombres = [x for x in pila if isinstance(x, tuple)]
        arrays = [x[1] for x in pila if isinstance(x, tuple) and x[0] == 'array']

        if op == 'q':
            pila_ctm.append(list(ctm))
        elif op == 'Q':
            if pila_ctm:
                ctm = pila_ctm.pop()
        elif op == 'cm' and len(numeros) >= 6:
            ctm = multiplicar(ctm, list(numeros[-6:]))
        elif op == 'Tf':
            tamano = numeros[-1] if numeros else 10.0
            fuente = fuentes.get(nombres[-1][1]) if nombres else fuente
        elif op == 'Tm' and len(numeros) >= 6:
            tm = list(numeros[-6:])
            lm = list(numeros[-6:])
        elif op in ('Td', 'TD') and len(numeros) >= 2:
            tx, ty = numeros[-2], numeros[-1]
            lm[4] += tx
            lm[5] += ty
            if op == 'TD':
                leading = -ty
        elif op == 'T*':
            lm[5] -= leading if leading else tamano * 1.2
        elif op == 'TL' and numeros:
            leading = numeros[-1]
        elif op == 'Tj' and textos:
            emitir(textos[-1])
        elif op == 'TJ' and arrays:
            # un TJ es UNA corrida de texto: sus strings se concatenan sin espacios
            # (los numeros intermedios son ajustes de kerning, no separadores)
            texto = ''.join(e for e in arrays[-1] if isinstance(e, str))
            emitir(texto)
        elif op == "'" and textos:
            lm[5] -= leading if leading else tamano * 1.2
            emitir(textos[-1])
        elif op == '"' and textos:
            lm[5] -= leading if leading else tamano * 1.2
            emitir(textos[-1])
        pila = []
    return runs


def lineas_de_runs(runs, tolerancia_y=1.5):
    """Agrupa corridas por linea visual (y) y ordena por x dentro de cada linea."""
    if not runs:
        return ''
    ordenados = sorted(runs, key=lambda r: (-r[0], r[1]))
    lineas = []
    actual = None
    for y, x, txt in ordenados:
        if actual is None or abs(y - actual[0]) > tolerancia_y:
            actual = [y, [(x, txt)]]
            lineas.append(actual)
        else:
            actual[1].append((x, txt))
    salida = []
    for _, celdas in lineas:
        celdas.sort(key=lambda c: c[0])
        partes = []
        fin_anterior = None
        for x, txt in celdas:
            if fin_anterior is not None and x - fin_anterior > 2.5:
                partes.append(' ')
            partes.append(txt)
            fin_anterior = x + max(1.0, len(txt) * 2.6)
        salida.append(''.join(partes).rstrip())
    return '\n'.join(salida)


def extraer_visual(ruta):
    """Como extraer() pero ordena el texto por posicion (lectura visual real)."""
    b = open(ruta, 'rb').read()
    handler = leer_handler(b)
    if handler is None and b'/Encrypt' in b:
        raise RuntimeError('PDF cifrado no soportado (AES u otro filtro)')
    dicts = objetos_dict(b)
    if handler:
        dicts.update(objetos_objstm(b, dicts, handler))
    fuentes = fuentes_del_pdf(b, dicts, handler) if handler else {}
    partes = []
    bloques = 0
    for m in PATRON_STREAM.finditer(b):
        cabecera = b[max(0, m.start() - 320):m.start()]
        om = None
        for cand in PATRON_OBJ.finditer(cabecera):
            om = cand
        if om is None:
            continue
        num = int(om.group(1))
        dicc = cabecera[om.end():]
        if b'/Image' in dicc or b'/ObjStm' in dicc or b'/FontFile' in dicc:
            continue
        if b'FlateDecode' not in dicc:
            continue
        inicio = m.end()
        fin = b.find(b'endstream', inicio)
        if fin < 0:
            continue
        crudo = b[inicio:fin]
        if handler:
            crudo = handler.descifrar(num, 0, crudo)
        try:
            dato = zlib.decompressobj().decompress(crudo)
        except zlib.error:
            continue
        if b'BT' not in dato:
            continue
        bloques += 1
        runs = runs_de_flujo(dato, fuentes)
        t = lineas_de_runs(runs)
        if t.strip():
            partes.append(t)
    return partes, bloques, handler is not None


def main():
    if len(sys.argv) < 3:
        print('Uso: python tools/leer_pdf_cifrado.py ORIGEN.pdf SALIDA.txt [--visual]')
        sys.exit(1)
    origen, salida = sys.argv[1], sys.argv[2]
    visual = '--visual' in sys.argv[3:]
    if visual:
        partes, bloques, cifrado = extraer_visual(origen)
    else:
        partes, bloques, cifrado = extraer(origen)
    texto = '\n\n'.join(partes)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto).strip()
    with open(salida, 'w', encoding='utf-8') as f:
        f.write('# EXTRAIDO POR tools/leer_pdf_cifrado.py v3 (stdlib) - fuente: %s\n'
                % os.path.basename(origen))
        f.write('# cifrado=%s flate_texto=%d orden=%s caracteres=%d\n\n'
                % (cifrado, bloques, 'visual' if visual else 'stream', len(texto)))
        f.write(texto)
    print('OK %s bloques=%d chars=%d cifrado=%s orden=%s'
          % (salida, bloques, len(texto), cifrado, 'visual' if visual else 'stream'))


if __name__ == '__main__':
    main()
