# -*- coding: utf-8 -*-
"""Prueba del indice de boletines TTO.

Comprueba:
  - 113 boletines en el indice;
  - 63 titulos impresos legibles y 50 derivados del nombre del archivo;
  - ningun boletin sin titulo ni etiqueta de origen;
  - idioma es/en/pt y metodo de revision en los derivados;
  - el CI ejecuta esta prueba.

Uso:
  python tools/test_tto_boletines.py
"""
import json
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'datos', 'tto_boletines.json')
WORKFLOW = os.path.join(RAIZ, '.github', 'workflows', 'validar.yml')


class TtoBoletinesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DATOS, encoding='utf-8') as f:
            cls.datos = json.load(f)
        cls.boletines = cls.datos['boletines']
        with open(WORKFLOW, encoding='utf-8') as f:
            cls.workflow = f.read()

    def test_conteos_y_titulos(self):
        self.assertEqual(113, len(self.boletines))
        impresos = [b for b in self.boletines
                    if b.get('titulo_estado') == 'impreso']
        derivados = [b for b in self.boletines
                     if b.get('titulo_estado') == 'derivado-del-archivo']
        self.assertEqual(63, len(impresos))
        self.assertEqual(50, len(derivados))
        self.assertEqual({'impresos': 63, 'derivados_del_archivo': 50,
                          'total': 113},
                         self.datos.get('resumen_titulos'))
        for b in self.boletines:
            self.assertTrue(b.get('archivo_txt'))
            self.assertIn(b.get('idioma'), ('es', 'en', 'pt'))
            if b.get('titulo_estado') == 'impreso':
                self.assertTrue(b.get('titulo'), b['archivo_txt'])
            else:
                self.assertTrue(b.get('titulo_archivo'), b['archivo_txt'])
                self.assertEqual('2026-11-14', b.get('revision'))
                self.assertTrue(b.get('revision_metodo'))

    def test_no_hay_titulos_inventados(self):
        for b in self.boletines:
            if b.get('titulo_estado') == 'derivado-del-archivo':
                self.assertNotIn('titulo', {k for k, v in b.items() if v})

    def test_ci_ejecuta_la_prueba(self):
        self.assertIn('python tools/test_tto_boletines.py', self.workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
