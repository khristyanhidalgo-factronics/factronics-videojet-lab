# -*- coding: utf-8 -*-
"""Prueba del consolidado de velocidades CIJ.

Se ejecuta en el CI sin la carpeta externa de PDFs: usa el JSON consolidado y
los OCR de los charts que viven en el repo.

Uso:
  python tools/test_velocidades_cij.py
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))

import validar_velocidades_cij as V  # noqa: E402


class VelocidadesCijTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.errores, cls.avisos, cls.datos = V.validar()
        cls.entradas = cls.datos['entradas']
        cls.resumen = cls.datos['resumen']

    def test_sin_errores_de_validacion(self):
        self.assertEqual([], self.errores)

    def test_conteos_del_consolidado(self):
        self.assertEqual(270, self.resumen['calculadores_leidos'])
        self.assertEqual(271, self.resumen['pdfs_leidos'])
        self.assertEqual(266, len(self.entradas))
        self.assertEqual(12, self.resumen['modelos'])
        self.assertEqual(0, self.resumen['conflictos'])
        self.assertEqual(22, self.resumen['conflictos_boquilla'])
        self.assertEqual(31, self.resumen['conflictos_modelo'])
        self.assertEqual(3, self.resumen['conflictos_fuente'])
        self.assertEqual(0, self.resumen['errores'])

    def test_descarte_de_la_tabla_resumen(self):
        descartados = self.datos['descartados']
        self.assertEqual(1, len(descartados))
        self.assertIn('v9.7z.pdf', descartados[0]['archivo'])
        for entrada in self.entradas:
            for archivo in entrada['archivos']:
                self.assertNotIn('v9.7z', archivo.lower())

    def test_estados_y_evidencia(self):
        for entrada in self.entradas:
            self.assertEqual('borrador-decodificado', entrada['estado'])
            self.assertTrue(entrada['archivos'])
            self.assertTrue(entrada['evidencias_ocr'])
            self.assertFalse(entrada['conflicto'])
            self.assertIsNotNone(entrada['velocidad_nominal_m_min'])
            self.assertTrue(
                entrada['caracteres_por_segundo'] is not None
                or entrada['columnas_por_segundo'] is not None)

    def test_duplicados_fusionados(self):
        duplicados = [e for e in self.entradas if len(e['archivos']) > 1]
        self.assertEqual(4, len(duplicados))
        claves = {e['clave'] for e in duplicados}
        self.assertEqual({
            '1210-20|60|5x5_single',
            '1620-50 UHS|50|4x5_single',
            '1710|60|7x9_single',
            '1880 UHS|50|7x9_twin',
        }, claves)

    def test_uhs_50_y_hr_40(self):
        por_modelo = {}
        for entrada in self.entradas:
            por_modelo.setdefault(entrada['modelo'], []).append(entrada)
        self.assertEqual(19, len(por_modelo['1880 UHS']))
        self.assertEqual(18, len(por_modelo['1620-50 UHS']))
        for modelo in ('1880 UHS', '1620-50 UHS'):
            for entrada in por_modelo[modelo]:
                self.assertEqual(50, entrada['boquilla_um'])
        for modelo in ('1880 HR', '1620-50 HR'):
            for entrada in por_modelo[modelo]:
                self.assertEqual(40, entrada['boquilla_um'])
        # Los nombres _60_ se conservan como evidencia del conflicto.
        self.assertTrue(any(
            '_60_' in archivo
            for entrada in por_modelo['1880 UHS']
            for archivo in entrada['archivos']))

    def test_calculador_experto(self):
        expertos = [e for e in self.entradas
                    if e['tipo_calculador'] == 'experto']
        self.assertEqual(1, len(expertos))
        experto = expertos[0]
        self.assertEqual('1620-50 UHS|50|4x5_single', experto['clave'])
        self.assertEqual(508, experto['velocidad_nominal_m_min'])
        self.assertEqual(3333, experto['caracteres_por_segundo'])
        self.assertEqual(16667, experto['columnas_por_segundo'])

    def test_anclas_de_los_charts(self):
        for familia, cfg in V.ANCLAS.items():
            valores = V.valores_chart(cfg['chart'])
            for fpm in cfg['fpm']:
                self.assertIn(fpm, valores,
                              '%s: falta %d fpm' % (familia, fpm))
        combinado = V.valores_chart(V.CHART_COMBINADO)
        for fpm in V.ANCLAS['1580']['fpm']:
            self.assertIn(fpm, combinado)


if __name__ == '__main__':
    unittest.main(verbosity=2)
