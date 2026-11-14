# -*- coding: utf-8 -*-
"""Prueba de datos e i18n del examen generado de 5 niveles.

Comprueba los invariantes que sostienen los tipos de pregunta:
  - 21 ribbons con velocidad numérica y 14 con temperatura numérica;
  - 23 colores de ribbon utiles (se excluye el encabezado "Colors");
  - 800 curvas de solvente verificadas con al menos 4 valores unicos;
  - 16 temperaturas tabuladas (10..40 °C cada 2) y 800 referencias @30 °C;
  - claves i18n q_rib_vel, q_rib_temp y q_sol_temp en es/en/pt/it/zh;
  - 105 densidades, 117 inflamaciones, 119 volatilidades, 119 ebulliciones,
    119 presiones de vapor y 116 colores SDS;
  - 11 colores de tinta unicos (se excluye "No disponible.");
  - el generador integra los tres tipos y el pool global de componentes SDS;
  - resumen del historial (examenes, promedio ponderado y mejor) y sus claves;
  - 131 tintas con una sola base quimica (12 valores) y respuestas traducidas;
  - contraste explicito de pregunta (600) y opciones (500) con var(--txt);
  - respaldo con cuaderno de repaso y normalizacion de datos importados;
  - el CI ejecuta la auditoria y esta prueba.

Uso:
  python tools/test_examen_gen.py
"""
import json
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_JS = os.path.join(RAIZ, 'docs', 'app', 'datos.js')
INDICE = os.path.join(RAIZ, 'docs', 'app', 'index.html')
WORKFLOW = os.path.join(RAIZ, '.github', 'workflows', 'validar.yml')
IDIOMAS = ('es', 'en', 'pt', 'it', 'zh')
CLAVES_I18N = ('q_rib_vel', 'q_rib_temp', 'q_sol_temp',
               'q_sol_horas', 'q_sds_dens', 'q_sds_flash', 'q_sds_volat',
               'q_sds_ebull', 'q_sds_pvap', 'q_tinta_color')


def cargar_datos():
    with open(DATOS_JS, encoding='utf-8') as f:
        texto = f.read()
    m = re.search(r'window\.DATOS\s*=\s*(\{.*\});\s*$', texto, re.S)
    if not m:
        raise RuntimeError('no se encontro window.DATOS en datos.js')
    return json.loads(m.group(1))


def bloques_i18n(html, idioma):
    patron = re.compile(
        r'Object\.assign\(I18N\.' + re.escape(idioma) + r',\s*\{(.*?)\n\}\);',
        re.S)
    return '\n'.join(patron.findall(html))


def bloques_base(html, idioma):
    patron = re.compile(
        r'\n  ' + re.escape(idioma) + r': \{(.*?)\n  \}', re.S)
    return '\n'.join(patron.findall(html))


class ExamenGenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = cargar_datos()
        with open(INDICE, encoding='utf-8') as f:
            cls.html = f.read()
        cls.grados = cls.datos['ribbons']['grados']
        cls.solventes = cls.datos['solventes']

    def test_ribbons_con_velocidad_y_temperatura(self):
        velocidades = [g['vel'] for g in self.grados
                       if isinstance(g.get('vel'), (int, float))]
        temperaturas = [g['temp'] for g in self.grados
                        if isinstance(g.get('temp'), (int, float))]
        self.assertEqual(21, len(velocidades))
        self.assertEqual(14, len(temperaturas))
        self.assertEqual({200, 400, 500, 600, 800, 1000},
                         set(velocidades))
        self.assertEqual({100, 110, 180, 200, 250},
                         set(temperaturas))
        self.assertGreaterEqual(len(set(velocidades)), 4)
        self.assertGreaterEqual(len(set(temperaturas)), 4)

    def test_colores_de_ribbon(self):
        colores = [g['col'] for g in self.grados
                   if g.get('col') and g['col'] != 'Colors']
        self.assertEqual(23, len(colores))
        self.assertGreaterEqual(len(set(colores)), 4)

    def test_curvas_de_solvente(self):
        curvas = [s for s in self.solventes
                  if s.get('e') == 'verificado'
                  and isinstance(s.get('c'), list) and len(s['c']) >= 4]
        self.assertEqual(800, len(curvas))
        temperaturas = set()
        for s in curvas:
            valores = {u for _, u in s['c'] if u is not None}
            self.assertGreaterEqual(len(valores), 4, s.get('m'))
            temperaturas.update(t for t, _ in s['c'])
        self.assertEqual(set(range(10, 42, 2)), temperaturas)
        referencias = [s for s in self.solventes
                       if s.get('e') == 'verificado'
                       and isinstance(s.get('r'), dict)
                       and s['r'].get('uso_ml_hr') is not None]
        self.assertEqual(800, len(referencias))

    def test_horas_por_litro(self):
        referencias = [s for s in self.solventes
                       if s.get('e') == 'verificado'
                       and isinstance(s.get('r'), dict)
                       and s['r'].get('uso_ml_hr') is not None]
        usos = {s['r']['uso_ml_hr'] for s in referencias}
        self.assertEqual(800, len(referencias))
        self.assertEqual(48, len(usos))
        self.assertGreaterEqual(min(usos), 2.0)
        self.assertLessEqual(max(usos), 19.8)
        horas = {round(1000 / u, 1) for u in usos}
        self.assertEqual(48, len(horas))
        self.assertGreaterEqual(len(horas), 4)

    def test_propiedades_sds_con_valor_unico(self):
        dens, flash, volat, ebull, pvap, colores = [], [], [], [], [], []
        ambiguas = set()
        for codigo, tinta in self.datos['tintas'].items():
            fichas = tinta.get('fichas') or []
            def valores(prop):
                return {f.get('props', {}).get(prop) for f in fichas
                        if f.get('props', {}).get(prop)}
            d = valores('densidad_relativa')
            f = valores('punto_inflamacion')
            v = valores('volatilidad')
            e = valores('punto_ebullicion')
            pv = valores('presion_vapor')
            col = valores('color')
            if len(d) == 1:
                m = re.match(r'^-?\d+(?:\.\d+)?', next(iter(d)))
                if m:
                    dens.append(m.group(0))
            elif len(d) > 1:
                ambiguas.add(codigo)
            if len(f) == 1:
                m = re.match(r'^-?\d+', next(iter(f)))
                if m:
                    flash.append(m.group(0))
            elif len(f) > 1:
                ambiguas.add(codigo)
            if len(v) == 1:
                volat.append(next(iter(v)))
            elif len(v) > 1:
                ambiguas.add(codigo)
            if len(e) == 1:
                ebull.append(next(iter(e)))
            elif len(e) > 1:
                ambiguas.add(codigo)
            if len(pv) == 1:
                pvap.append(next(iter(pv)))
            elif len(pv) > 1:
                ambiguas.add(codigo)
            if len(col) == 1 and next(iter(col)) != 'No disponible.':
                colores.append(next(iter(col)))
            elif len(col) > 1:
                ambiguas.add(codigo)
        self.assertEqual(105, len(dens))
        self.assertEqual(25, len(set(dens)))
        self.assertEqual(117, len(flash))
        self.assertEqual(18, len(set(flash)))
        self.assertEqual(119, len(volat))
        self.assertEqual(25, len(set(volat)))
        self.assertEqual(119, len(ebull))
        self.assertEqual(12, len(set(ebull)))
        self.assertEqual(119, len(pvap))
        self.assertEqual(8, len(set(pvap)))
        self.assertEqual(116, len(colores))
        self.assertEqual(11, len(set(colores)))
        self.assertNotIn('No disponible.', set(colores))
        self.assertGreaterEqual(len(set(dens)), 4)
        self.assertGreaterEqual(len(set(flash)), 4)
        self.assertGreaterEqual(len(set(volat)), 4)
        self.assertGreaterEqual(len(set(ebull)), 4)
        self.assertGreaterEqual(len(set(pvap)), 4)
        self.assertGreaterEqual(len(set(colores)), 4)
        self.assertIn('V4278', ambiguas)
        self.assertIn('V4211', ambiguas)
        self.assertIn('V526', ambiguas)
        self.assertNotIn('V401', ambiguas)

    def test_i18n_de_los_tipos_nuevos(self):
        for idioma in IDIOMAS:
            bloque = bloques_i18n(self.html, idioma)
            self.assertTrue(bloque, 'sin bloque i18n para %s' % idioma)
            for clave in CLAVES_I18N:
                self.assertRegex(
                    bloque, r'\b' + re.escape(clave) + r'\s*:',
                    '%s falta en %s' % (clave, idioma))
        for idioma in IDIOMAS:
            bloque = bloques_i18n(self.html, idioma)
            self.assertIn('{g}', re.search(
                r"q_rib_vel\s*:\s*'([^']*)'", bloque).group(1), idioma)
            self.assertIn('{g}', re.search(
                r"q_rib_temp\s*:\s*'([^']*)'", bloque).group(1), idioma)
            sol = re.search(r"q_sol_temp\s*:\s*'([^']*)'", bloque).group(1)
            for marca in ('{m}', '{t}', '{T}'):
                self.assertIn(marca, sol, '%s en %s' % (marca, idioma))
            horas = re.search(r"q_sol_horas\s*:\s*'([^']*)'", bloque).group(1)
            for marca in ('{m}', '{t}', '{u}', '{T}'):
                self.assertIn(marca, horas, '%s en %s' % (marca, idioma))
            for clave in ('q_sds_dens', 'q_sds_flash', 'q_sds_volat',
                          'q_sds_ebull', 'q_sds_pvap', 'q_tinta_color'):
                texto = re.search(
                    r"%s\s*:\s*'((?:\\.|[^'\\])*)'" % clave,
                    bloque).group(1)
                self.assertIn('{c}', texto, '%s en %s' % (clave, idioma))

    def test_generador_integra_los_tipos(self):
        for fragmento in (
                "'q_rib_vel'", "'q_rib_temp'", "'q_sol_temp'",
                "'q_sol_horas'", "'q_sds_dens'", "'q_sds_flash'", "'q_sds_volat'",
                "'q_tinta_color'", "'q_sds_ebull'", "'q_sds_pvap'", "tipo:'rib_vel'", "tipo:'rib_temp'", "tipo:'sol_temp'",
                "tipo:'sol_horas'", "tipo:'sds_dens'", "tipo:'sds_flash'",
                "tipo:'sds_volat'", "tipo:'sds_ebull'", "tipo:'sds_pvap'", "tipo:'tinta_color'",
                'SDS_PROPS.volat', 'SDS_PROPS.ebull', 'SDS_PROPS.pvap',
                'TINTAS_COLOR', 'COLORES_TINTA',
                "typeof g.vel === 'number'", "typeof g.temp === 'number'",
                'Array.isArray(s.c)', "g.col !== 'Colors'", 'SDS_PROPS',
                'SOL_USOS', 'COMP_NAMES', 'TINTAS_CON_COMP'):
            self.assertIn(fragmento, self.html)
        self.assertIn('function generarPregunta(', self.html)

    def test_contraste_de_pregunta_y_opciones(self):
        for fragmento in (
                '.q > div:first-child{color:var(--txt);font-weight:600;font-size:16px',
                '.q .opt{',
                'color:var(--txt);font-weight:500',
                '.q .opt.right{',
                '.q .opt.wrong{'):
            self.assertIn(fragmento, self.html)

    def test_base_unica_y_traducida(self):
        tintas = self.datos['tintas']
        simples = {c: x['b'][0] for c, x in tintas.items()
                   if len(x.get('b') or []) == 1}
        ambiguas = [c for c, x in tintas.items() if len(x.get('b') or []) > 1]
        self.assertEqual(131, len(simples))
        self.assertEqual(12, len(set(simples.values())))
        self.assertEqual(['V459', 'V460', 'V461'], sorted(ambiguas))
        for fragmento in ("(x.b||[]).length === 1",
                          'const base = tr(x.b[0])',
                          'const pool = BASES.map(tr)',
                          "tipo:'base'"):
            self.assertIn(fragmento, self.html)

    def test_respaldo_incluye_repaso(self):
        for fragmento in ('function normalizarRepaso(',
                          "repaso: JSON.parse(localStorage.getItem('fvl_review')",
                          'normalizarRepaso(d.repaso)',
                          "localStorage.setItem('fvl_review'",
                          'Object.keys(repaso).length'):
            self.assertIn(fragmento, self.html)

    def test_resumen_de_historial(self):
        for fragmento in ('function resumenHistorial(',
                          'function renderHistorial(',
                          'resumenHistorial(h)', 'ex_hist_clear',
                          'hist_confirm'):
            self.assertIn(fragmento, self.html)
        for idioma in IDIOMAS:
            bloque = bloques_i18n(self.html, idioma) + bloques_base(self.html, idioma)
            for clave in ('hist_examenes', 'hist_promedio', 'hist_mejor',
                          'hist_borrar', 'hist_confirm'):
                self.assertIn(clave + ':', bloque, '%s en %s' % (clave, idioma))

    def test_ci_ejecuta_auditoria_y_prueba(self):
        with open(WORKFLOW, encoding='utf-8') as f:
            workflow = f.read()
        self.assertIn('tools/auditar_examen_gen.js', workflow)
        self.assertIn('tools/test_examen_gen.py', workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
