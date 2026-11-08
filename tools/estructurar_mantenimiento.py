# -*- coding: utf-8 -*-
"""Estructura el mantenimiento (documentos y tareas con intervalo) de LÁSER y TTO.

Entrada: datos/extraccion/{laser,tto}_*_visual.txt
Salida:  datos/mantenimiento.json
  - documentos: archivos cuyo nombre indica mantenimiento/limpieza/servicio/reemplazo.
  - tareas: lineas con verbo de mantenimiento + intervalo (diario/semanal/mensual/
    anual/cada N horas...). Deduplicadas; estado borrador (contexto, sin inventar pasos).
"""
import json
import os
import re
import sys
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACCION = os.path.join(RAIZ, 'datos', 'extraccion')
DESTINO = os.path.join(RAIZ, 'datos', 'mantenimiento.json')

RE_DOC = re.compile(r'maint|clean|service|replace|replacement|limpieza|mantenim|'
                    r'sustitu|reemplaz|optics|resonator|mirror', re.I)
RE_VERBO = re.compile(r'(?i)\b(clean|cleaning|replace|replacing|check|checking|inspect|'
                      r'inspection|maintenance|service|limpiar|limpieza|sustitu\w*|'
                      r'reemplaz\w*|revis\w*|mantenimiento)\b')
RE_INTERVALO = re.compile(
    r'(?i)\b(daily|weekly|monthly|annually|annual|yearly|every\s+\d+\s*'
    r'(?:hours?|days?|weeks?|months?|years?)|cada\s+\d+\s*'
    r'(?:horas?|d[ií]as?|semanas?|meses?|a[nñ]os?)|diario|diaria|semanal|mensual|anual)\b')
RE_INTERVALO_CAPT = re.compile(
    r'(?i)(daily|weekly|monthly|annually|annual|yearly|every\s+\d+\s*'
    r'(?:hours?|days?|weeks?|months?|years?)|cada\s+\d+\s*'
    r'(?:horas?|d[ií]as?|semanas?|meses?|a[nñ]os?)|diario|diaria|semanal|mensual|anual)')


def tipo_documento(nombre):
    n = nombre.lower()
    if 'clean' in n or 'limpieza' in n:
        return 'limpieza'
    if 'replace' in n or 'reemplaz' in n or 'sustitu' in n:
        return 'reemplazo'
    if 'service' in n:
        return 'servicio'
    if 'maint' in n or 'mantenim' in n:
        return 'mantenimiento'
    return 'procedimiento'


def normalizar(linea):
    return re.sub(r'\s+', ' ', linea).strip()


def main():
    documentos = []
    tareas = {}
    for nombre in sorted(os.listdir(EXTRACCION)):
        if not (nombre.startswith(('laser_', 'tto_'))
                and nombre.endswith('_visual.txt')):
            continue
        tecnologia = 'LASER' if nombre.startswith('laser_') else 'TTO'
        ruta = os.path.join(EXTRACCION, nombre)
        texto = open(ruta, encoding='utf-8', errors='replace').read()
        cuerpo = '\n'.join(l for l in texto.splitlines() if not l.startswith('#'))
        if RE_DOC.search(nombre):
            documentos.append({
                'archivo_txt': nombre,
                'tecnologia': tecnologia,
                'tipo': tipo_documento(nombre),
                'caracteres': len(cuerpo.strip()),
            })
        for linea in cuerpo.splitlines():
            if len(linea) < 25 or len(linea) > 400:
                continue
            if not RE_VERBO.search(linea) or not RE_INTERVALO.search(linea):
                continue
            texto_tarea = normalizar(linea)
            # descartar lineas de menu/login/indice
            if re.search(r'(?i)login|password|menu|table of contents|https?://|'
                         r'price|fee|included|subscription|warranty', texto_tarea):
                continue
            mi = RE_INTERVALO_CAPT.search(texto_tarea)
            intervalo = mi.group(1).lower() if mi else None
            clave = texto_tarea.lower()[:160]
            if clave not in tareas:
                tareas[clave] = {
                    'tarea': texto_tarea[:220],
                    'intervalo': intervalo,
                    'tecnologia': tecnologia,
                    'archivo': nombre,
                }

    por_tec = {}
    for d in documentos:
        por_tec[d['tecnologia']] = por_tec.get(d['tecnologia'], 0) + 1
    por_tipo = {}
    for d in documentos:
        por_tipo[d['tipo']] = por_tipo.get(d['tipo'], 0) + 1

    datos = {
        'producto': 'Mantenimiento LÁSER y TTO (documentos y tareas con intervalo)',
        'schema': 1,
        'fecha': date.today().isoformat(),
        'total_documentos': len(documentos),
        'documentos_por_tecnologia': por_tec,
        'documentos_por_tipo': por_tipo,
        'total_tareas': len(tareas),
        'nota': ('Extraccion conservadora: los documentos se listan por evidencia de '
                 'nombre; las tareas recogen lineas con verbo de mantenimiento e '
                 'intervalo, sin reconstruir pasos. Estado borrador: revisar contra el '
                 'manual antes de usar como procedimiento.'),
        'documentos': documentos,
        'tareas': sorted(tareas.values(), key=lambda t: (t['tecnologia'], t['tarea'])),
    }
    with open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    print('OK %s | documentos=%d %s | tareas=%d'
          % (os.path.relpath(DESTINO, RAIZ), len(documentos), por_tipo, len(tareas)))
    for t in datos['tareas'][:8]:
        try:
            print('  [%s] (%s) %s' % (t['tecnologia'], t['intervalo'],
                                      t['tarea'][:110]))
        except UnicodeEncodeError:
            print('  [%s] (%s) tarea (no imprimible en consola)'
                  % (t['tecnologia'], t['intervalo']))


if __name__ == '__main__':
    main()
