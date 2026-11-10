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
    laser_partes = cargar('laser_partes.json')
    errores = cargar('codigos_error.json')
    ribbons = cargar('tto_ribbons.json')
    mant = cargar('mantenimiento.json')
    modelos_laser = cargar('laser_modelos.json')

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
                        'cij': '6 IPL 1000VJ (1210/1510, 1220/1520, 1520E, 1610 DH, 1620E, 1650)',
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
        # tintas CIJ con composicion y propiedades (por ficha)
        'tintas': {},
        # partes (TTO + LASER)
        'partes': [],
        # codigos de error
        'errores': [{
            'c': c['codigo'], 't': c['tecnologia'],
            'cl': c.get('clase'),
            'x': (c.get('descripcion_contexto') or '')[:160],
        } for c in errores.get('codigos', [])],
        # ribbons TTO
        'ribbons': {
            'grados': [{
                'g': r.get('Videojet Grade'), 'pn': r.get('PN'),
                'col': r.get('Colors'), 'vel': r.get('Max Printing Speed (mm/s)'),
                'dur': r.get('Overall Durability (0-100%)'),
                'temp': r.get('Heat Resistance (°C)'),
                'tipo': r.get('Type'), 'film': r.get('Base Film'),
                'desc': (r.get('Description') or '')[:180],
            } for r in ribbons.get('grados_ribbon', [])],
            'items': [[i['item_no'], i['descripcion']]
                      for i in ribbons.get('items_suministros_tto', [])],
        },
        'mant': {
            'docs': [{'a': d['archivo_txt'], 'tipo': d['tipo'], 'tec': d['tecnologia']}
                     for d in mant.get('documentos', [])],
            'tareas': [{'x': t['tarea'][:180], 'iv': t.get('intervalo'),
                        'tec': t['tecnologia']} for t in mant.get('tareas', [])],
        },
        'modelosLaser': [m['modelo'] for m in modelos_laser.get('modelos', [])],
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
        for idioma in ('espanol', 'ingles', 'portugues'):
            for d in descripciones:
                if d.get('idioma') == idioma and d.get('texto'):
                    desc = d['texto']
                    break
            if desc:
                break
        if not desc and descripciones:
            desc = descripciones[0].get('texto', '')
        paquete['partes'].append({'n': numero, 'd': str(desc)[:220], 't': 'TTO'})
    # partes CIJ (6 IPL; se conserva el estado y los modelos)
    for p in partes_cij.get('partes', []):
        paquete['partes'].append({
            'n': p['pn'],
            'd': (p.get('descripcion') or '')[:220],
            't': 'CIJ',
            'm': ', '.join(p.get('modelos') or []),
            'e': p.get('estado'),
            'c': bool(p.get('conflicto_descripciones')),
        })
    # partes LASER
    for p in laser_partes.get('partes', []):
        paquete['partes'].append({'n': p['numero_parte'],
                                  'd': (p.get('descripcion') or '')[:220],
                                  't': 'LASER'})

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, 'w', encoding='utf-8') as f:
        f.write('// Generado por tools/construir_app_datos.py - NO editar a mano.\n')
        f.write('window.DATOS = ')
        json.dump(paquete, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
    tam = os.path.getsize(SALIDA)
    print('OK %s (%.1f KB) | solventes=%d tintas=%d partes=%d (CIJ=%d) '
          'errores=%d ribbons=%d/%d mant=%d/%d modelos_laser=%d'
          % (os.path.relpath(SALIDA, RAIZ), tam / 1024.0,
             len(paquete['solventes']), len(paquete['tintas']),
             len(paquete['partes']),
             len(partes_cij.get('partes', [])), len(paquete['errores']),
             len(paquete['ribbons']['grados']), len(paquete['ribbons']['items']),
             len(paquete['mant']['docs']), len(paquete['mant']['tareas']),
             len(paquete['modelosLaser'])))


if __name__ == '__main__':
    main()
