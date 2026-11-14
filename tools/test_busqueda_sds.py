# -*- coding: utf-8 -*-
"""Prueba de la busqueda SDS por CAS, componente y tinta.

Comprueba los invariantes del indice que usa la app:
  - 817 componentes verificados en 119 tintas (47 nombres, 44 CAS);
  - 527 pares unicos tinta|CAS, deduplicados aunque el CAS tenga nombre ES/EN;
  - nombre canonico = el mas completo de cada CAS;
  - traduccion completa de los 47 nombres en es/en/pt/it/zh;
  - chip `sds`, indice `SDS_BUS` y clave i18n `bus_sds` en los 5 idiomas;
  - busquedas de ejemplo: CAS, nombre y tinta devuelven lo esperado.

Uso:
  python tools/test_busqueda_sds.py
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


def normalizar(texto):
    return re.sub(r'\s+', ' ', str(texto or '')).strip()


def norm(texto):
    """Equivalente a norm() de la app: minusculas y sin acentos."""
    texto = normalizar(texto).lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


def traduccion(datos, texto, idioma):
    clave = normalizar(texto)
    registro = (datos.get('tr') or {}).get(clave) or {}
    return registro.get(idioma) or texto


def bloques_i18n(html, idioma):
    patron = re.compile(
        r'Object\.assign\(I18N\.' + re.escape(idioma) + r',\s*\{(.*?)\n\}\);',
        re.S)
    return '\n'.join(patron.findall(html))


def bloques_base(html, idioma):
    """Bloque base de idioma dentro de `const I18N = { ... }`."""
    patron = re.compile(
        r'\n  ' + re.escape(idioma) + r': \{(.*?)\n  \}', re.S)
    return '\n'.join(patron.findall(html))


def construir_indice(tintas):
    """Replica SDS_BUS: una entrada por tinta|CAS con todas las variantes."""
    mapa = {}
    for codigo, tinta in tintas.items():
        for ficha in tinta.get('fichas') or []:
            for comp in ficha.get('comp') or []:
                cas = comp.get('cas')
                if not cas:
                    continue
                clave = (codigo, cas)
                r = mapa.setdefault(clave, {
                    'c': codigo, 'cas': cas, 'ns': [], 'p': ''})
                nombre = comp.get('n')
                if nombre and nombre not in r['ns']:
                    r['ns'].append(nombre)
                if not r['p'] and comp.get('p'):
                    r['p'] = comp['p']
    indice = []
    for r in mapa.values():
        canon = sorted(r['ns'], key=len, reverse=True)[0] if r['ns'] else ''
        indice.append({'c': r['c'], 'cas': r['cas'], 'ns': r['ns'],
                       'n': canon, 'p': r['p']})
    return indice


def buscar(indice, datos, consulta, idioma='es'):
    q = norm(consulta)
    out = []
    for r in indice:
        nombres = [traduccion(datos, n, idioma) for n in r['ns']]
        if (not q or q in norm(r['cas']) or q in norm(r['c'])
                or any(q in norm(n) or q in norm(t)
                       for n, t in zip(r['ns'], nombres))):
            out.append(r)
    return out


class BusquedaSdsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = cargar_datos()
        with open(INDICE, encoding='utf-8') as f:
            cls.html = f.read()
        with open(WORKFLOW, encoding='utf-8') as f:
            cls.workflow = f.read()
        cls.tintas = cls.datos['tintas']
        cls.componentes = [
            (codigo, comp)
            for codigo, tinta in cls.tintas.items()
            for ficha in tinta.get('fichas') or []
            for comp in ficha.get('comp') or []]
        cls.indice = construir_indice(cls.tintas)

    def test_conteos_de_componentes(self):
        self.assertEqual(817, len(self.componentes))
        self.assertEqual(119, len({c for c, _ in self.componentes}))
        self.assertEqual(47, len({x['n'] for _, x in self.componentes}))
        self.assertEqual(44, len({x['cas'] for _, x in self.componentes}))
        for _, comp in self.componentes:
            self.assertEqual('verificado', comp.get('e'))
            self.assertTrue(comp.get('cas'))
            self.assertTrue(comp.get('n'))

    def test_deduplicacion_por_tinta_y_cas(self):
        self.assertEqual(527, len(self.indice))
        self.assertEqual(527, len({(r['c'], r['cas']) for r in self.indice}))
        por_cas = {}
        for _, comp in self.componentes:
            por_cas.setdefault(comp['cas'], set()).add(comp['n'])
        variantes = {cas: ns for cas, ns in por_cas.items() if len(ns) > 1}
        self.assertEqual(3, len(variantes))
        self.assertEqual({'1029600-34-7', '2897-60-1', '1474044-65-9'},
                         set(variantes))
        for r in self.indice:
            self.assertEqual(1, len(r['ns']), (r['c'], r['cas']))
            self.assertEqual(sorted(r['ns'], key=len, reverse=True)[0], r['n'])
            self.assertTrue(r['n'])
        for cas, nombres in variantes.items():
            union = set()
            for r in self.indice:
                if r['cas'] == cas:
                    union.update(r['ns'])
            self.assertEqual(nombres, union, cas)

    def test_traducciones_completas(self):
        nombres = {x['n'] for _, x in self.componentes}
        for nombre in nombres:
            for idioma in IDIOMAS:
                self.assertTrue(traduccion(self.datos, nombre, idioma),
                                '%s en %s' % (nombre, idioma))
        for r in self.indice:
            for idioma in IDIOMAS:
                self.assertTrue(traduccion(self.datos, r['n'], idioma),
                                '%s en %s' % (r['n'], idioma))

    def test_busquedas_de_ejemplo(self):
        por_cas = buscar(self.indice, self.datos, '78-93-3')
        self.assertEqual(70, len(por_cas))
        self.assertTrue(all(r['cas'] == '78-93-3' for r in por_cas))
        self.assertIn('V401', {r['c'] for r in por_cas})

        por_nombre = buscar(self.indice, self.datos, 'metiletilcetona')
        self.assertEqual(70, len(por_nombre))
        self.assertEqual({r['c'] for r in por_cas},
                         {r['c'] for r in por_nombre})

        por_tinta = buscar(self.indice, self.datos, 'V401')
        self.assertEqual(5, len(por_tinta))
        self.assertEqual({'78-93-3', '108-21-4', '64-17-5', '67-63-0',
                          '1029600-34-7'}, {r['cas'] for r in por_tinta})

        # Las variantes ES/EN del mismo CAS encuentran las mismas tintas.
        for consulta, cas, total, idioma in (
                ('chromium', '1029600-34-7', 7, 'es'),
                ('cromo', '1029600-34-7', 10, 'es'),
                ('chromium', '1029600-34-7', 10, 'en'),
                ('cromo', '1029600-34-7', 3, 'en'),
                ('2897-60-1', '2897-60-1', 7, 'es'),
                ('1474044-65-9', '1474044-65-9', 4, 'es')):
            filas = buscar(self.indice, self.datos, consulta, idioma)
            self.assertEqual(total, len(filas), (consulta, idioma))
            self.assertTrue(all(r['cas'] == cas for r in filas),
                            (consulta, idioma))

        self.assertEqual(527, len(buscar(self.indice, self.datos, '')))

    def test_chip_e_indice_en_la_app(self):
        self.assertIn("['sds','bus_sds']", self.html)
        self.assertIn('const SDS_BUS', self.html)
        self.assertIn("BUS==='sds'", self.html)
        self.assertIn('for (const r of SDS_BUS)', self.html)
        self.assertIn('r.ns.some(', self.html)
        self.assertIn('data-sds=', self.html)
        self.assertIn('detalleTinta(b.dataset.sds)', self.html)
        self.assertIn("c.dataset.est === 'tintas'", self.html)
        for idioma in IDIOMAS:
            bloque = bloques_i18n(self.html, idioma) + bloques_base(self.html, idioma)
            self.assertIn("bus_sds:'SDS'", bloque, idioma)
        self.assertIn('function buscar(', self.html)
        self.assertIn('python tools/test_busqueda_sds.py', self.workflow)


if __name__ == '__main__':
    unittest.main()
