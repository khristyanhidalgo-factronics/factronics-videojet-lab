# -*- coding: utf-8 -*-
"""Prueba del buscador de solventes por modelo, tinta y variante.

Comprueba los invariantes del indice que usa la app:
  - 802 curvas de solvente (800 verificadas, 2 sin datos en documento);
  - 17 modelos, 134 tintas y 801 combinaciones modelo|variante|tinta;
  - el unico duplicado es VJ1560/V461 con dos bases y curvas distintas;
  - busquedas de ejemplo: modelo, tinta, variante y estado;
  - chip `solventes`, bloque `BUS==='solventes'` y clave i18n en 5 idiomas;
  - el CI ejecuta esta prueba.

Uso:
  python tools/test_busqueda_solventes.py
"""
import json
import os
import re
import unicodedata
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_JS = os.path.join(RAIZ, 'docs', 'app', 'datos.js')
INDICE = os.path.join(RAIZ, 'docs', 'app', 'index.html')
WORKFLOW = os.path.join(RAIZ, '.github', 'workflows', 'validar.yml')
IDIOMAS = ('es', 'en', 'pt', 'it', 'zh')


def cargar_datos():
    with open(DATOS_JS, encoding='utf-8') as f:
        texto = f.read()
    m = re.search(r'window\.DATOS\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.DATOS en datos.js')
    return json.loads(m.group(1))


def norm(texto):
    texto = re.sub(r'\s+', ' ', str(texto or '')).strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


def traduccion(datos, texto, idioma='es'):
    clave = re.sub(r'\s+', ' ', str(texto or '')).strip()
    registro = (datos.get('tr') or {}).get(clave) or {}
    return registro.get(idioma) or texto


def bloques_base(html, idioma):
    patron = re.compile(r'\n  ' + re.escape(idioma) + r': \{(.*?)\n  \}', re.S)
    return '\n'.join(patron.findall(html))


def fila(datos, s, idioma='es'):
    base = s.get('b')
    prefijo = traduccion(datos, base, idioma) + ' · ' if base and base != 'por-definir' else ''
    r = s.get('r') or {}
    uso = r.get('uso_ml_hr')
    temp = r.get('temp_c', 30)
    etiqueta = s['m'] + (' ' + s['v'] if s.get('v') else '') + ' · ' + s['t']
    detalle = '%s%s ml/h @ %s °C · %s h/L' % (prefijo, uso, temp, s.get('hl'))
    return etiqueta, detalle


def buscar(datos, consulta, idioma='es'):
    q = norm(consulta)
    out = []
    for s in datos['solventes']:
        etiqueta, detalle = fila(datos, s, idioma)
        if (not q or q in norm(etiqueta) or q in norm(detalle)
                or q in norm(s.get('e', ''))):
            out.append(s)
    return out


class BusquedaSolventesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = cargar_datos()
        with open(INDICE, encoding='utf-8') as f:
            cls.html = f.read()
        with open(WORKFLOW, encoding='utf-8') as f:
            cls.workflow = f.read()
        cls.solventes = cls.datos['solventes']

    def test_conteos_del_indice(self):
        self.assertEqual(802, len(self.solventes))
        self.assertEqual(800, sum(1 for s in self.solventes
                                 if s.get('e') == 'verificado'))
        self.assertEqual(2, sum(1 for s in self.solventes
                                 if s.get('e') == 'sin-datos-en-documento'))
        self.assertEqual(17, len({s['m'] for s in self.solventes}))
        self.assertEqual(134, len({s['t'] for s in self.solventes}))
        self.assertEqual(801, len({(s['m'], s.get('v', ''), s['t'])
                                   for s in self.solventes}))
        for s in self.solventes:
            self.assertTrue(s.get('m'))
            self.assertTrue(s.get('t'))
            self.assertIsInstance(s.get('c'), list)
            self.assertIsInstance(s.get('r'), dict)
        doble = [s for s in self.solventes
                 if (s['m'], s.get('v', ''), s['t']) == ('VJ1560', '', 'V461')]
        self.assertEqual(2, len(doble))
        self.assertEqual({'Ethanol/Isoprop', 'EthylAcetate'},
                         {s.get('b') for s in doble})
        self.assertEqual(2, len({s['r']['uso_ml_hr'] for s in doble}))

    def test_busquedas_de_ejemplo(self):
        for consulta, total in (('VJ1210', 46), ('V401', 13),
                                ('VJ1650', 80), ('VJ1880', 56),
                                ('UHS', 71), ('sin-datos-en-documento', 2),
                                ('', 802)):
            self.assertEqual(total, len(buscar(self.datos, consulta)),
                             consulta)
        vj1210 = buscar(self.datos, 'VJ1210')
        self.assertEqual(46, len({s['t'] for s in vj1210}))

    def test_base_y_traducciones(self):
        v461 = buscar(self.datos, 'V461')
        detalles = [fila(self.datos, s)[1] for s in v461
                    if s['m'] == 'VJ1560']
        self.assertEqual(2, len(detalles))
        self.assertTrue(any('Etanol/isoprop' in d for d in detalles))
        self.assertTrue(any('Acetato de etilo' in d for d in detalles))
        bases = {s.get('b') for s in self.solventes
                 if s.get('b') and s.get('b') != 'por-definir'}
        for base in bases:
            for idioma in IDIOMAS:
                self.assertTrue(traduccion(self.datos, base, idioma),
                                '%s en %s' % (base, idioma))

    def test_chip_e_indice_en_la_app(self):
        self.assertIn("['solventes','bus_solventes']", self.html)
        self.assertIn("BUS==='solventes'", self.html)
        self.assertIn('for (const s of D.solventes)', self.html)
        self.assertIn("tipo:'SOL'", self.html)
        self.assertIn("s.b !== 'por-definir'", self.html)
        self.assertIn('fmtNum(s.hl,1)', self.html)
        for idioma in IDIOMAS:
            bloque = bloques_base(self.html, idioma)
            self.assertIn('bus_solventes:', bloque, idioma)
        self.assertIn('python tools/test_busqueda_solventes.py', self.workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
