# -*- coding: utf-8 -*-
"""Prueba del banco de partes CIJ (solo P/N verificados).

Comprueba los invariantes del banco que usa la app:
  - 124 P/N CIJ verificados, unicos y con descripcion;
  - 118 descripciones, 5 ambiguas y 113 inequivocas;
  - candidatos P/N->descripcion (124) + descripcion->P/N (113);
  - las 5 descripciones ambiguas quedan fuera del segundo tipo;
  - traduccion completa de las descripciones en es/en/pt/it/zh;
  - claves i18n y opcion de fuente presentes en la app.

Uso:
  python tools/test_banco_partes.py
"""
import json
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_JS = os.path.join(RAIZ, 'docs', 'app', 'datos.js')
INDICE = os.path.join(RAIZ, 'docs', 'app', 'index.html')
IDIOMAS = ('es', 'en', 'pt', 'it', 'zh')
CLAVES_I18N = ('fuente_partes', 'q_part_pn', 'q_part_desc',
               'ref_partes', 'partes_nota')
AMBIGUAS = {
    'Filter Element': {'234081', 'SP234502'},
    'Filter Cover': {'395762', '395763', 'SP399029'},
    'Beacon Assembly': {'399089', 'SP399089'},
    'Ribbon Cable Spare Kit': {'399237', '399505'},
    'Printhead Photocell Holder 6 mm, 8 mm, 18 mm': {'399278', '399294'},
}


def cargar_datos():
    with open(DATOS_JS, encoding='utf-8') as f:
        texto = f.read()
    m = re.search(r'window\.DATOS\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.DATOS en datos.js')
    return json.loads(m.group(1))


def normalizar(texto):
    return re.sub(r'\s+', ' ', str(texto or '')).strip()


def traduccion(datos, texto, idioma):
    clave = normalizar(texto)
    registro = (datos.get('tr') or {}).get(clave) or {}
    return registro.get(idioma) or texto


def bloques_i18n(html, idioma):
    patron = re.compile(
        r'Object\.assign\(I18N\.' + re.escape(idioma) + r',\s*\{(.*?)\n\}\);',
        re.S)
    return '\n'.join(patron.findall(html))


class BancoPartesCijTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = cargar_datos()
        with open(INDICE, encoding='utf-8') as f:
            cls.html = f.read()
        cls.partes = [
            p for p in cls.datos.get('partes', [])
            if p.get('t') == 'CIJ' and p.get('e') == 'verificado'
            and p.get('n') and p.get('d')]
        cls.por_desc = {}
        for p in cls.partes:
            cls.por_desc.setdefault(p['d'], set()).add(p['n'])

    def test_conteos_del_banco(self):
        self.assertEqual(124, len(self.partes))
        self.assertEqual(124, len({p['n'] for p in self.partes}))
        self.assertEqual(118, len(self.por_desc))
        ambiguas = {d: pns for d, pns in self.por_desc.items()
                    if len(pns) > 1}
        self.assertEqual(AMBIGUAS, ambiguas)
        self.assertEqual(113, len(self.por_desc) - len(ambiguas))
        self.assertEqual(124 + 113, 237)

    def test_solo_verificados(self):
        for p in self.partes:
            self.assertEqual('CIJ', p['t'])
            self.assertEqual('verificado', p['e'])
            self.assertTrue(p['n'])
            self.assertTrue(p['d'])
        cij = [p for p in self.datos['partes'] if p.get('t') == 'CIJ']
        self.assertEqual(80, sum(1 for p in cij if p.get('e') == 'borrador'))
        self.assertEqual(92, sum(
            1 for p in cij if p.get('e') == 'borrador-decodificado'))
        incluidos = {p['n'] for p in self.partes}
        for p in cij:
            if p.get('e') != 'verificado':
                self.assertNotIn(p.get('n'), incluidos)

    def test_traducciones_de_descripciones(self):
        for p in self.partes:
            clave = normalizar(p['d'])
            registro = self.datos.get('tr', {}).get(clave)
            self.assertIsNotNone(registro, 'sin traduccion: %r' % p['d'])
            for idioma in IDIOMAS:
                self.assertTrue(registro.get(idioma),
                                '%s sin %s' % (p['d'], idioma))

    def test_ambiguedad_por_idioma(self):
        for idioma in IDIOMAS:
            por_traduccion = {}
            for p in self.partes:
                valor = traduccion(self.datos, p['d'], idioma)
                por_traduccion.setdefault(valor, set()).add(p['n'])
            ambiguas = {d: pns for d, pns in por_traduccion.items()
                        if len(pns) > 1}
            self.assertEqual(5, len(ambiguas), idioma)
            self.assertEqual(
                {traduccion(self.datos, d, idioma) for d in AMBIGUAS},
                set(ambiguas), idioma)
            self.assertEqual(113, len(por_traduccion) - len(ambiguas), idioma)

    def test_pools_de_opciones(self):
        for idioma in IDIOMAS:
            descripciones = {
                traduccion(self.datos, p['d'], idioma) for p in self.partes}
            pns = {p['n'] for p in self.partes}
            self.assertEqual(118, len(descripciones), idioma)
            self.assertEqual(124, len(pns), idioma)
            self.assertGreaterEqual(len(descripciones), 4, idioma)
            self.assertGreaterEqual(len(pns), 4, idioma)

    def test_i18n_en_cinco_idiomas(self):
        for idioma in IDIOMAS:
            bloque = bloques_i18n(self.html, idioma)
            self.assertTrue(bloque, 'sin bloque i18n para %s' % idioma)
            for clave in CLAVES_I18N:
                self.assertRegex(
                    bloque, r'\b' + re.escape(clave) + r'\s*:',
                    '%s falta en %s' % (clave, idioma))
            self.assertIn('124', bloque, idioma)
        self.assertIn('{n}', bloques_i18n(self.html, 'es'))
        self.assertIn('{d}', bloques_i18n(self.html, 'es'))

    def test_app_integra_la_fuente(self):
        self.assertIn('value="partes"', self.html)
        self.assertIn('data-i18n="fuente_partes"', self.html)
        for nombre in ('partesCijVerificadas', 'candidatosPartes',
                       'generarPreguntaPartes'):
            self.assertIn('function ' + nombre + '(', self.html)
        self.assertIn("fuente === 'partes'", self.html)
        self.assertIn("p.e === 'verificado'", self.html)
        self.assertIn("t('q_part_desc')", self.html)
        self.assertIn("t('q_part_pn')", self.html)
        self.assertIn("t('ref_partes')", self.html)


if __name__ == '__main__':
    unittest.main(verbosity=2)
