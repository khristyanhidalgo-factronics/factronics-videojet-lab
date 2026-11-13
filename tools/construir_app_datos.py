# -*- coding: utf-8 -*-
"""Genera el paquete de datos de la app web offline: docs/app/datos.js

Toma los datasets verificados/borrador del repo y los compacta para el navegador.
Claves cortas para reducir tamano; los datos NO se alteran (mismos valores y estados).

Uso: python tools/construir_app_datos.py
"""
import json
import os
import sys
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'datos')
SALIDA = os.path.join(RAIZ, 'docs', 'app', 'datos.js')


def cargar(nombre):
    with open(os.path.join(DATOS, nombre), 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    solvente = cargar('cij_uso_solvente.json')
    tintas = cargar('cij_tintas.json')
    partes_tto = cargar('partes_tto.json')
    partes_cij = cargar('partes_cij.json')
    partes_cij_ocr = {}
    ruta_ocr = os.path.join(DATOS, 'partes_cij_ocr.json')
    if os.path.exists(ruta_ocr):
        with open(ruta_ocr, 'r', encoding='utf-8') as f:
            partes_cij_ocr = json.load(f)
    velocidades = cargar('cij_velocidades.json')
    laser_partes = cargar('laser_partes.json')
    errores = cargar('codigos_error.json')
    ribbons = cargar('tto_ribbons.json')
    mant = cargar('mantenimiento.json')
    modelos_laser = cargar('laser_modelos.json')
    ruta_trad = os.path.join(DATOS, 'traducciones_contenido.json')
    traducciones = {}
    if os.path.exists(ruta_trad):
        traducciones = json.load(open(ruta_trad, encoding='utf-8')).get('entradas', {})

    paquete = {
        'meta': {
            'version': 'v0.2.0-alpha',
            'fecha': date.today().isoformat(),
            'producto': 'Factronics Videojet Lab',
            'aviso': ('Datos del propio equipo y de documentos oficiales Videojet. '
                      'Estados por dato: verificado / borrador / sin-datos-en-documento. '
                      'Revisar los borrador antes de usarlos como dato firme.'),
            'fuentes': {'solventes': 'CIJ Makeup Usage Model v14 (802/802)',
                        'tintas': 'fichas QSS descifradas + brochures + uso de solvente',
                        'ttO': 'Excel de curso + chart de ribbons 2.5.26',
                        'cij': ('6 IPL 1000VJ (1210/1510, 1220/1520, 1520E, 1610 DH, 1620E, 1650) '
                                '+ IPL 1550/1710 por OCR (borrador-decodificado)'),
                        'velocidades': 'CIJ Line Speed Calculator v9.7 (270 calculadores por OCR)',
                        'laser': 'manuales CO2/Fibra + SpareParts',
                        'errores': 'listas oficiales de error',
                        'mantenimiento': 'manuales y procedimientos'},
        },
        # calculadora CIJ: modelo/variante/tinta/base + curva
        'solventes': [{
            'm': e.get('modelo'),
            'v': e.get('variante') or '',
            't': e.get('tinta'),
            'b': e.get('base_quimica'),
            'c': [[p['temp_c'], p['uso_ml_hr']] for p in e.get('curva', [])],
            'r': e.get('referencia'),
            'hl': e.get('hrs_por_litro'),
            'cm': e.get('cartucho_ml'),
            'e': e.get('estado'),
        } for e in solvente.get('modelos', [])],
        # velocidades de linea CIJ por modelo/boquilla/fuente (calculadores v9.7)
        'velocidades': {
            'meta': {
                'fuente': velocidades.get('fuente'),
                'metodo': velocidades.get('metodo'),
                'fecha': velocidades.get('fecha'),
                'estado': velocidades.get('estado_general'),
                'calculadores': (velocidades.get('resumen') or {}).get('calculadores_leidos'),
                'entradas': len(velocidades.get('entradas', [])),
                'modelos': (velocidades.get('resumen') or {}).get('modelos'),
                'conflictos': (velocidades.get('resumen') or {}).get('conflictos'),
                'conflictos_boquilla': (velocidades.get('resumen') or {}).get('conflictos_boquilla'),
                'conflictos_modelo': (velocidades.get('resumen') or {}).get('conflictos_modelo'),
                'conflictos_fuente': (velocidades.get('resumen') or {}).get('conflictos_fuente'),
                'descartado': 'v9.7z.pdf (tabla resumen, no es calculador)',
                'nota': ('Velocidad nominal leida por OCR de los calculadores oficiales. '
                         'Queda como borrador-decodificado; los avisos de boquilla/modelo/fuente '
                         'se conservan y no se corrigen a mano.'),
            },
            'modelos': sorted({e.get('modelo') for e in velocidades.get('entradas', [])
                               if e.get('modelo')}),
            'boquillas': sorted({e.get('boquilla_um') for e in velocidades.get('entradas', [])
                                 if e.get('boquilla_um')}),
            'fuentes': sorted({e.get('fuente') for e in velocidades.get('entradas', [])
                               if e.get('fuente')}),
            'entradas': [{
                'm': e.get('modelo'),
                'mi': e.get('modelo_impreso') or '',
                'b': e.get('boquilla_um'),
                'f': e.get('fuente'),
                'v': e.get('velocidad_nominal_m_min'),
                'c': e.get('caracteres_por_segundo'),
                'col': e.get('columnas_por_segundo'),
                't': e.get('tipo_calculador'),
                'e': e.get('estado'),
                'a': '; '.join(os.path.basename(a) for a in (e.get('archivos') or [])),
                'cf': ''.join(k for k, campo in (
                    ('b', 'conflicto_boquilla'),
                    ('m', 'conflicto_modelo'),
                    ('f', 'conflicto_fuente')) if e.get(campo)),
            } for e in velocidades.get('entradas', [])],
        },
        # tintas CIJ con composicion y propiedades (por ficha)
        'tintas': {},
        # partes (TTO + LASER)
        'partes': [],
        # codigos de error
        'errores': [{
            'c': c['codigo'], 't': c['tecnologia'],
            'cl': c.get('clase'),
            'x': (c.get('descripcion_contexto') or ''),
        } for c in errores.get('codigos', [])],
        # ribbons TTO
        'ribbons': {
            'grados': [{
                'g': r.get('Videojet Grade'), 'pn': r.get('PN'),
                'col': r.get('Colors'), 'vel': r.get('Max Printing Speed (mm/s)'),
                'dur': r.get('Overall Durability (0-100%)'),
                'temp': r.get('Heat Resistance (°C)'),
                'tipo': r.get('Type'), 'film': r.get('Base Film'),
                'desc': (r.get('Description') or ''),
            } for r in ribbons.get('grados_ribbon', [])],
            'items': [[i['item_no'], i['descripcion']]
                      for i in ribbons.get('items_suministros_tto', [])],
        },
        'mant': {
            'docs': [{'a': d['archivo_txt'], 'tipo': d['tipo'], 'tec': d['tecnologia']}
                     for d in mant.get('documentos', [])],
            'tareas': [{'x': t['tarea'], 'iv': t.get('intervalo'),
                        'tec': t['tecnologia']} for t in mant.get('tareas', [])],
        },
        'modelosLaser': [m['modelo'] for m in modelos_laser.get('modelos', [])],
        # memoria de traduccion de contenido (clave = texto original normalizado)
        'tr': traducciones,
    }

    # tintas compactas
    for codigo, t in tintas.get('tintas', {}).items():
        fichas = []
        for f in t.get('fichas_qss', []):
            sds = f.get('sds') or {}
            comp = [{'n': c['componente'], 'cas': c['cas'],
                     'p': c.get('porcentaje'), 'e': c.get('estado')}
                    for c in sds.get('componentes', [])]
            props = sds.get('propiedades') or {}
            fichas.append({
                'a': f['archivo'],
                'v': sds.get('version'),
                'fd': sds.get('fecha_revision'),
                'comp': comp,
                'props': {k: props[k] for k in props},
            })
        paquete['tintas'][codigo] = {
            'b': t.get('bases_quimicas', []),
            'col': (t.get('color') or {}).get('valor'),
            'curvas': t.get('curvas_verificadas'),
            'fichas': fichas,
        }

    # partes TTO (estructura: parte + descripciones por idioma)
    for p in partes_tto.get('partes', []):
        numero = str(p.get('parte') or '').strip()
        if not numero:
            continue
        descripciones = p.get('descripciones') or []
        desc = ''
        # Texto canonico: ingles si existe (la app traduce al idioma activo);
        # si no, espanol y por ultimo portugues.
        for idioma in ('ingles', 'espanol', 'portugues'):
            for d in descripciones:
                if d.get('idioma') == idioma and d.get('texto'):
                    desc = d['texto']
                    break
            if desc:
                break
        if not desc and descripciones:
            desc = descripciones[0].get('texto', '')
        modelos = sorted({m for ms in (p.get('modelos_por_fuente') or {}).values()
                          for m in (ms or [])})
        paquete['partes'].append({'n': numero, 'd': str(desc), 't': 'TTO',
                                  'm': ', '.join(modelos),
                                  'e': p.get('estado') or 'borrador'})
    # partes CIJ (6 IPL + 1550/1710 OCR; se conserva el estado y los modelos)
    partes_cij_app = list(partes_cij.get('partes', []))
    por_pn = {str(p['pn']): p for p in partes_cij_app}
    ocr_nuevas = 0
    for p in partes_cij_ocr.get('partes', []):
        pn = str(p.get('pn') or '').strip()
        if not pn:
            continue
        modelos = p.get('modelos') or []
        if pn in por_pn:
            # El P/N ya existe en la base digital: se suma el modelo donde el
            # OCR lo volvio a leer y se conserva la evidencia. El estado no se
            # asciende por OCR.
            actual = por_pn[pn]
            actuales = actual.setdefault('modelos', [])
            for m in modelos:
                if m and m not in actuales:
                    actuales.append(m)
            if p.get('conflicto_descripciones'):
                # Conflicto real entre la base digital y el IPL OCR: la app
                # debe mostrarlo aunque el P/N ya existiera.
                actual['conflicto_descripciones'] = True
                actual['conflicto_ocr'] = {
                    'descripcion': p.get('descripcion') or '',
                    'descripciones': p.get('descripciones') or [],
                    'documentos': p.get('documentos') or [],
                }
                descs = actual.setdefault('descripciones', [])
                for d in p.get('descripciones') or []:
                    if d and d not in descs:
                        descs.append(d)
            continue
        nueva = {
            'pn': pn,
            'descripcion': p.get('descripcion') or '',
            'descripciones': p.get('descripciones') or [],
            'estado': p.get('estado') or 'borrador-decodificado',
            'conflicto_descripciones': bool(p.get('conflicto_descripciones')),
            'modelos': modelos,
            'origen': 'OCR',
        }
        partes_cij_app.append(nueva)
        por_pn[pn] = nueva
        ocr_nuevas += 1
    for p in partes_cij_app:
        paquete['partes'].append({
            'n': p['pn'],
            'd': (p.get('descripcion') or ''),
            't': 'CIJ',
            'm': ', '.join(p.get('modelos') or []),
            'e': p.get('estado'),
            'c': bool(p.get('conflicto_descripciones')),
        })
    # partes LASER
    for p in laser_partes.get('partes', []):
        paquete['partes'].append({'n': p['numero_parte'],
                                  'd': (p.get('descripcion') or ''),
                                  't': 'LASER'})

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, 'w', encoding='utf-8') as f:
        f.write('// Generado por tools/construir_app_datos.py - NO editar a mano.\n')
        f.write('window.DATOS = ')
        json.dump(paquete, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
    tam = os.path.getsize(SALIDA)
    print('OK %s (%.1f KB) | solventes=%d velocidades=%d tintas=%d partes=%d (CIJ=%d, +%d OCR) '
          'errores=%d ribbons=%d/%d mant=%d/%d modelos_laser=%d'
          % (os.path.relpath(SALIDA, RAIZ), tam / 1024.0,
             len(paquete['solventes']), len(paquete['velocidades']['entradas']),
             len(paquete['tintas']), len(paquete['partes']),
             len(partes_cij_app), ocr_nuevas, len(paquete['errores']),
             len(paquete['ribbons']['grados']), len(paquete['ribbons']['items']),
             len(paquete['mant']['docs']), len(paquete['mant']['tareas']),
             len(paquete['modelosLaser'])))


if __name__ == '__main__':
    main()
