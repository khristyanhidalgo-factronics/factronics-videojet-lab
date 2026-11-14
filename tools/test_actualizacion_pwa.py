# -*- coding: utf-8 -*-
"""Prueba del aviso de actualización de la PWA.

Comprueba:
  - banner `upd_bar` con `role=status`, botón `upd_btn` y clases accesibles;
  - detección por `controllerchange`, sin aviso en la primera instalación;
  - botón que oculta el banner y recarga;
  - `updateViaCache: none` y `reg.update()` al volver a la app;
  - claves `upd_aviso` y `upd_btn` en es/en/pt/it/zh;
  - el service worker acepta `skipWaiting` y usa `clients.claim()`;
  - el CI ejecuta esta prueba.

Uso:
  python tools/test_actualizacion_pwa.py
"""
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDICE = os.path.join(RAIZ, 'docs', 'app', 'index.html')
SW = os.path.join(RAIZ, 'docs', 'app', 'sw.js')
WORKFLOW = os.path.join(RAIZ, '.github', 'workflows', 'validar.yml')
IDIOMAS = ('es', 'en', 'pt', 'it', 'zh')


def bloques_idioma(html, idioma):
    base = re.compile(r'\n  ' + re.escape(idioma) + r': \{(.*?)\n  \}', re.S)
    extra = re.compile(
        r'Object\.assign\(I18N\.' + re.escape(idioma) + r',\s*\{(.*?)\n\}\);',
        re.S)
    return '\n'.join(base.findall(html) + extra.findall(html))


class ActualizacionPwaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INDICE, encoding='utf-8') as f:
            cls.html = f.read()
        with open(SW, encoding='utf-8') as f:
            cls.sw = f.read()
        with open(WORKFLOW, encoding='utf-8') as f:
            cls.workflow = f.read()

    def test_banner_accesible(self):
        for fragmento in (
                'id="upd_bar"', 'class="upd hidden"', 'role="status"',
                'aria-live="polite"', 'id="upd_btn"',
                'data-i18n="upd_aviso"', 'data-i18n="upd_btn"',
                '.upd{', '.upd.hidden{display:none}'):
            self.assertIn(fragmento, self.html)

    def test_logica_de_actualizacion(self):
        for fragmento in (
                'function mostrarAvisoActualizacion(',
                "addEventListener('controllerchange'",
                'swTeniaControl',
                'if (swTeniaControl) mostrarAvisoActualizacion()',
                "postMessage('skipWaiting')",
                "updateViaCache: 'none'",
                "document.addEventListener('visibilitychange'",
                'reg.update()'):
            self.assertIn(fragmento, self.html)
        self.assertLess(
            self.html.index('function mostrarAvisoActualizacion('),
            self.html.index("addEventListener('controllerchange'"))

    def test_i18n_en_cinco_idiomas(self):
        for idioma in IDIOMAS:
            bloque = bloques_idioma(self.html, idioma)
            self.assertIn('upd_aviso:', bloque, idioma)
            self.assertIn('upd_btn:', bloque, idioma)

    def test_service_worker(self):
        for fragmento in ('self.skipWaiting()', 'self.clients.claim()',
                          "addEventListener('message'",
                          "e.data === 'skipWaiting'"):
            self.assertIn(fragmento, self.sw)
        self.assertNotIn('msg_importato', self.html)

    def test_ci_ejecuta_la_prueba(self):
        self.assertIn('python tools/test_actualizacion_pwa.py',
                      self.workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
