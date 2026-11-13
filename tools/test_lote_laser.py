# -*- coding: utf-8 -*-
"""Prueba el cierre del lote laser (14 PDFs que no tenian texto).

No ejecuta OCR: valida el resumen y los archivos de texto/evidencia que quedaron
en el repo, para que el CI detecte si se pierde la clasificacion.

Uso:
  python tools/test_lote_laser.py
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUMEN = os.path.join(RAIZ, 'datos', 'extraccion', '_lote_laser_resumen.json')

RECUPERABLES = {
    r'manuales fibra\Nueva carpeta\18030-Working Distance 7230, 7330, 7320, 7220 (Eng).pdf': 'ok',
    r'manuales fibra\Nueva carpeta\18032-Marking Fields and Working Distances 7340, 7440 (Eng).pdf': 'ok',
    r'manuales fibra\Nueva carpeta\18035-Locating Fault Messages in Laser Unit Interfaces (Eng).pdf': 'ok',
    r'manuales fibra\Nueva carpeta\18037-Laser User Interface Devices and Software (Eng).pdf': 'ok',
    r'accesorios laser\Extraction Accesories.pdf': 'ok-rotado',
    r'accesorios laser\k30 wiring diagram.pdf': 'ok-rotado',
}
SIN_TEXTO = [
    r'accesorios laser\07130.PDF',
    r'accesorios laser\AL-SP71082_Drehgebereinheit.pdf',
    r'drawings co2\OG5052 3d drawing.pdf',
    r'drawings co2\Soporte Laser Fiber.pdf',
    r'drawings co2\Soporte laser CO2.pdf',
    r'drawings co2\prueba.pdf',
    r'drawings co2\pruebaaaaaaaaaaaaaaaaaaaaaaaaa.pdf',
]
DANADO = r'accesorios laser\MedidoresPortenciaCO2.pdf'


def main():
    fallos = []
    with open(RESUMEN, encoding='utf-8') as f:
        datos = json.load(f)
    resultados = {r.get('archivo'): r for r in datos.get('resultados', [])}
    if len(resultados) != 1253:
        fallos.append('el resumen laser tiene %d resultados; se esperaban 1253'
                      % len(resultados))

    for archivo, estado in RECUPERABLES.items():
        r = resultados.get(archivo)
        if not r:
            fallos.append('falta en el resumen: %s' % archivo)
            continue
        if r.get('estado_ocr') != estado:
            fallos.append('%s: estado_ocr %r (se esperaba %r)'
                          % (archivo, r.get('estado_ocr'), estado))
        if (r.get('ocr_chars') or 0) < 200:
            fallos.append('%s: solo %s caracteres OCR'
                          % (archivo, r.get('ocr_chars')))
        txt = r.get('txt_ocr')
        if not txt or not os.path.exists(os.path.join(RAIZ, txt)):
            fallos.append('%s: falta el TXT OCR' % archivo)
        elif os.path.getsize(os.path.join(RAIZ, txt)) < 200:
            fallos.append('%s: TXT OCR demasiado pequeno' % archivo)
        if estado == 'ok-rotado' and not r.get('ocr_rotacion'):
            fallos.append('%s: no registra la rotacion' % archivo)

    for archivo in SIN_TEXTO:
        r = resultados.get(archivo)
        if not r:
            fallos.append('falta en el resumen: %s' % archivo)
            continue
        if r.get('estado_ocr') != 'sin-texto-por-diseno':
            fallos.append('%s: estado_ocr %r (se esperaba sin-texto-por-diseno)'
                          % (archivo, r.get('estado_ocr')))
        if r.get('ocr_chars'):
            fallos.append('%s: tiene texto y no deberia' % archivo)

    r = resultados.get(DANADO)
    if not r:
        fallos.append('falta en el resumen: %s' % DANADO)
    else:
        if r.get('estado_ocr') != 'ok-decodificado':
            fallos.append('%s: estado_ocr %r (se esperaba ok-decodificado)'
                          % (DANADO, r.get('estado_ocr')))
        if (r.get('ocr_chars') or 0) < 200:
            fallos.append('%s: solo %s caracteres decodificados'
                          % (DANADO, r.get('ocr_chars')))
        txt = r.get('txt_ocr')
        if not txt or not os.path.exists(os.path.join(RAIZ, txt)):
            fallos.append('%s: falta el TXT decodificado' % DANADO)
        else:
            contenido = open(os.path.join(RAIZ, txt), encoding='utf-8').read()
            for esperado in ('Laser Power Measurement', 'AL-67438', 'AL-66517',
                             'professional power meter', 'power wizard'):
                if esperado not in contenido:
                    fallos.append('%s: el TXT no contiene %r'
                                  % (DANADO, esperado))
        dec = r.get('texto_decodificado') or {}
        if sorted(dec.get('pns') or []) != ['AL-66517', 'AL-67438']:
            fallos.append('%s: P/N decodificados %r' % (DANADO, dec.get('pns')))
        if dec.get('metodo') != 'texto-decodificado-cmap':
            fallos.append('%s: metodo %r' % (DANADO, dec.get('metodo')))
        imagenes = r.get('imagenes_extraidas') or []
        if not imagenes:
            fallos.append('%s: no registra imagenes extraidas' % DANADO)
        else:
            ruta = os.path.join(RAIZ, imagenes[0]['archivo'])
            if not os.path.exists(ruta):
                fallos.append('%s: falta la imagen %s' % (DANADO, ruta))
            elif os.path.getsize(ruta) < 10000:
                fallos.append('%s: imagen demasiado pequena' % DANADO)
        visual = r.get('lectura_visual') or {}
        if not visual.get('descartada_por_texto_decodificado'):
            fallos.append('%s: la lectura visual no marca que fue descartada'
                          % DANADO)
        if 'dato tecnico firme' not in (visual.get('nota') or '').lower():
            fallos.append('%s: falta la salvedad de dato no firme' % DANADO)

    cierre = datos.get('cierre_lote_laser') or {}
    if cierre.get('casos_revisados') != 14:
        fallos.append('cierre: casos_revisados %r' % cierre.get('casos_revisados'))
    if cierre.get('recuperados_con_texto') != 7:
        fallos.append('cierre: recuperados_con_texto %r'
                      % cierre.get('recuperados_con_texto'))
    if cierre.get('chars_recuperados') != 16148:
        fallos.append('cierre: chars_recuperados %r (se esperaban 16148)'
                      % cierre.get('chars_recuperados'))
    if cierre.get('sin_texto_por_diseno') != 7:
        fallos.append('cierre: sin_texto_por_diseno %r'
                      % cierre.get('sin_texto_por_diseno'))
    if cierre.get('danado_rasterizado') != 0:
        fallos.append('cierre: danado_rasterizado %r'
                      % cierre.get('danado_rasterizado'))
    if cierre.get('decodificado_por_cmap') != 1:
        fallos.append('cierre: decodificado_por_cmap %r'
                      % cierre.get('decodificado_por_cmap'))

    conteo = datos.get('conteo_ocr') or {}
    if conteo.get('ok-decodificado') != 1:
        fallos.append('conteo_ocr: ok-decodificado %r'
                      % conteo.get('ok-decodificado'))
    if conteo.get('imagen-extraida'):
        fallos.append('conteo_ocr: queda imagen-extraida')
    if sum(conteo.values()) != 1253:
        fallos.append('conteo_ocr suma %r (se esperaban 1253)'
                      % sum(conteo.values()))

    pendientes = [r for r in resultados.values()
                  if r.get('estado_ocr') in ('sin-resultado', 'error')]
    if pendientes:
        fallos.append('quedan %d casos sin clasificar (sin-resultado/error)'
                      % len(pendientes))
        for r in pendientes[:5]:
            fallos.append('  - %s' % r.get('archivo'))

    if fallos:
        print('FALLOS (%d):' % len(fallos))
        for f in fallos:
            print('  -', f)
        return 1
    print('Lote laser OK: 7 recuperados (6 OCR + 1 texto decodificado), '
          '7 sin texto por diseno, imagen 029/581 conservada como secundaria')
    return 0


if __name__ == '__main__':
    sys.exit(main())
