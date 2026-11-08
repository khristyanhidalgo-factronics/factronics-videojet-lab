"""Decodificador calibrado de fuentes subset de Videojet (v2, sin dependencias).

Fenomeno verificado en los documentos del equipo: los PDFs usan fuentes subset sin
ToUnicode y el extractor entrega el codigo del glifo en lugar del caracter real.
Prueba de oro del equipo (comprobada a mano contra el PDF):
  '9 L G H R M H W 7 H F K Q R O R J L H V'  ->  (+29) 'Videojet Technologies'
  '  QWHUQDWLRQDO 3URGXFWV'                  ->  (+29) ' International Products'
  ', O O X V W U D W H G 3 D U W V'          ->  (+29) 'Illustrated Parts'
y en el TS2205 V471-D: 'o L W W H O % R X O H Y D U G : R R G ' D O H' -> 'Mittel
Boulevard Wood Dale IL' (sede de Videojet).

Hallazgo v2: un mismo documento puede MEZCLAR varias fuentes (una ya correcta, una
desplazada +29, otra irreparable), asi que el offset real no es unico por documento:
se decide POR BLOQUE (ventana de texto) entre todos los offsets -40..+40, incluido el
0 (dejar sin cambiar). Cada bloque apenas se decodifica si el lexic de control gana
con margen; si no, se conserva el texto original tal cual. No se reconstruye nada: el
lexicon solo sirve para CALIBRAR el offset, y los bloques sin evidencia quedan crudos.

Uso:
  python tools/decodificar_cipher_offset.py ENTRADA.txt [SALIDA_dec.txt]
Salida: <nombre>_dec.txt con encabezado de evidencia por bloque + texto.
"""
import os
import re
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# LEXICO DE CONTROL: terminos estandar de documentos Videojet/SDS/IPL + ingles basico.
# Sirve SOLO para elegir el offset (calibracion), no para reconstruir texto.
LEXICO = [
    'illustrated parts list', 'videojet technologies', 'technologies inc',
    'information for', 'intended', 'application', 'cartridge', 'returnable',
    'component', 'weight', 'physical', 'description', 'composition',
    'butanone', 'ethanol', 'methanol', 'isopropanol', 'acetate', 'ketone',
    'solvent', 'makeup', 'cleaners', 'reactivity', 'stability',
    'disposal', 'storage', 'handling', 'precautionary', 'hazard', 'section',
    'emergency', 'contain', 'symptoms', 'effects', 'first aid',
    'the', 'and', 'for', 'with', 'from', 'ink', 'data sheet',
    'loose parts', 'quantity', 'assembly', 'subassembly', 'alphabet',
    'symbols', 'figure', 'note', 'manual', 'rev', 'printer', 'printhead',
    'international products', 'aquatic', 'acute', 'chronic', 'category',
    'illinois', 'boulevard', 'media', 'page', 'sample', 'general',
]

# Decisiones de calidad
VENTANA = 110          # tamano del bloque de decision
UMBRAL_DECODIFICAR = 20  # puntos de evidencia minimos para aceptar el offset de un bloque

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def solo_letras(texto):
    return ''.join(ch for ch in texto if ch.isalpha())


def puntuar_bloque(texto_decodificado, texto_original):
    """Puntos de evidencia de un bloque: suma de (aciertos_nuevos * len) del lexicon
    sobre el texto lower, comparado con el mismo conteo del bloque sin decodificar."""
    t = texto_decodificado.lower()
    o = texto_original.lower()
    ganancia = 0
    for w in LEXICO:
        hd = t.count(w)
        ho = o.count(w)
        if hd > ho:
            ganancia += (hd - ho) * len(w)
    # variante solo-letras: atrapa textos donde cada palabra esta separada
    td = solo_letras(t)
    to = solo_letras(o)
    for w in LEXICO:
        if len(w) < 5:
            continue  # en solo-letras las palabras cortas traen demasiados falsos
            # positivos
        wl = ''.join(ch for ch in w if ch.isalpha())
        hd = td.count(wl)
        ho = to.count(wl)
        if hd > ho:
            ganancia += (hd - ho) * len(w)
    return ganancia


def desplazar(texto, offset):
    """Aplica el offset conservando espacios/saltos y dejando crudo lo no imprimible."""
    out = []
    for ch in texto:
        if not ch.isprintable() and ch != ' ':
            continue
        if ch in ' \n\t\r':
            out.append(ch)
            continue
        codigo = ord(ch) + offset
        if 0 <= codigo <= 0x10FFFF:
            nuevo = chr(codigo)
        else:
            nuevo = ch
        out.append(nuevo if nuevo.isprintable() else ch)
    return ''.join(out)


def elegir_offset_bloque(bloque):
    """Devuelve (offset_elegido, texto, ganancia) para un bloque. El offset 0 es un
    candidato valido (bloque correcto desde el origen)."""
    mejor = (0, bloque, 0)
    for offset in range(-40, 41):
        dec = desplazar(bloque, offset)
        g = puntuar_bloque(dec, bloque)
        if g > mejor[2]:
            mejor = (offset, dec, g)
    return mejor


def decodificar_cuerpo(cuerpo):
    """Decide offset por bloque, sin solapar ventanas."""
    salida = []
    offsets = Counter()
    bloques_totales = 0
    bloques_decodificados = 0
    for i in range(0, len(cuerpo), VENTANA):
        bloque = cuerpo[i:i + VENTANA]
        if not solo_letras(bloque):
            salida.append(bloque)
            continue
        bloques_totales += 1
        offset, texto, ganancia = elegir_offset_bloque(bloque)
        if offset != 0 and ganancia >= UMBRAL_DECODIFICAR:
            salida.append(texto)
            offsets[offset] += 1
            bloques_decodificados += 1
        else:
            salida.append(bloque)
            offsets[0] += 1
    return ''.join(salida), offsets, bloques_totales, bloques_decodificados


def principal():
    argv = sys.argv[1:]
    if not argv:
        print('Uso: python tools/decodificar_cipher_offset.py ENTRADA.txt [SALIDA_dec.txt]')
        sys.exit(1)
    origen = os.path.abspath(argv[0])
    texto = open(origen, 'r', encoding='utf-8', errors='replace').read()
    lineas = texto.splitlines()
    cabecera = '\n'.join(l for l in lineas if l.startswith('#'))
    cuerpo = '\n'.join(l for l in lineas if not l.startswith('#')).strip('\n')

    dec, offsets, totales, decodificados = decodificar_cuerpo(cuerpo)
    top = ', '.join('%+d:%d' % (o, n) for o, n in offsets.most_common(3))
    partes = []
    for offset, n in offsets.most_common(3):
        partes.append('%s por %d bloque(s)' % ('sin cambio' if offset == 0 else 'offset=%+d' % offset, n))
    decision = ('bloques=%d decodificados=%d | %s'
                % (totales, decodificados, ' | '.join(partes)))
    if decodificados == 0:
        decision += ' -> SIN desplazamiento suficiente (se conserva texto original)'
    else:
        decision += ' -> DECODIFICADO EXPERIMENTAL (borrador-decodificado; revisar contra el PDF original)'

    salida = os.path.abspath(argv[1]) if len(argv) > 1 else \
        os.path.splitext(origen)[0] + '_dec.txt'
    with open(salida, 'w', encoding='utf-8') as f:
        f.write('# DECODIFICADO POR tools/decodificar_cipher_offset.py (v2) - fuente: %s\n'
                % os.path.basename(origen))
        f.write('# %s\n\n' % decision)
        f.write(dec)
    print('%-52s | %s' % (os.path.basename(origen), decision))


if __name__ == '__main__':
    principal()
