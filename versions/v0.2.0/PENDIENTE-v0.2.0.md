# ⏳ PENDIENTE — v0.2.0 · App web offline (PWA)

> Lo que falta para **cerrar la v0.2.0**. Al congelar, alimenta el PLAN de v0.3.0.

## Cierre de v0.2.0
- [x] **Verificación final en navegador real (alpha-16)**: consola sin errores ni
      avisos, service worker activo y caché `fvl-v0.2.0-alpha-16`; calculadora de
      velocidad (508 m/min · 1.667 fpm · 16.667 columnas/s), solvente (11,2 ml/h
      @30 °C), examen Básico 10/10 con constancia e historial y cambio a EN.
      `alpha-17` solo cambia el paquete de datos y la caché; se comprueba la carga
      tras publicar.
- [x] ~~**Prueba de la calculadora** contra referencia: VJ1210/V401 @30 °C = 11,2 ml/h~~
      → `tools/test_app_calculo.py` recorre 802 curvas y 800 referencias @30 °C.
- [x] ~~Revisión de textos i18n (es/en/pt)~~ → 5 idiomas completos (es/en/pt/it/zh),
      cobertura 17.225/17.225 y pruebas automáticas; queda la revisión humana de estilo.
- [ ] Revisión humana de estilo de las traducciones IT/ZH (`borrador-de-traduccion`):
      confirmar términos técnicos con el dueño o con documentación Videojet.
- [ ] Ajustes de UX tras la prueba (teclado móvil, tamaños, contraste).

## Superar la referencia (cuenta personal)
- [x] ~~`version.json` + `docs/notas.html` con índice SHA-256~~ → hecho (`tools/publicar_notas.py`).
- [x] ~~Idiomas IT y ZH~~ → interfaz y **contenido completo** en 5 idiomas (ES/EN/PT/IT/ZH); banco TTO traducido a IT/ZH.
- [x] ~~Resultado con QR + constancia imprimible~~ → botón 🎓 Constancia con QR offline (`vendor/qrcode.js`).
- [x] ~~Repaso espaciado y cuaderno de errores~~ → cajas 1–5, pendientes del día y errores acumulados.
- [x] ~~CI de validadores~~ (JSON, notas SHA-256, app, enlaces) → `tools/validar_repo.py` + workflow, más `tools/test_banco_tto.py` (372 preguntas × 5 idiomas), `tools/test_app_calculo.py` y `tools/test_traducciones.py` en el mismo CI.
- [x] ~~Backup/restore de perfil e historial~~ → exportar/importar en la app.
- [ ] **Rotar los dos tokens expuestos** (cuenta de proyecto y cuenta personal) al estabilizar.

## Fase 2 – resto (v0.2.x / v0.3.0)
- [x] ~~Exportar/importar copia de seguridad (JSON) de perfil e historial~~ → hecho.
- [x] ~~QR offline para compartir resultados~~ → incluido en la constancia.
- [x] ~~Página pública de notas `docs/notas.html` + CI~~ → publicada con SHA-256.
- [ ] **Temas festivos** por país (Venezuela base) sobre el tema claro/oscuro/sistema.
- [ ] Más variedad de preguntas por nivel y banco separado por tecnología.
- [x] ~~Traducir el banco TTO a IT/ZH (372 × 2 preguntas)~~ → hecho: 372 preguntas × 5 idiomas, con IDs de opciones y respuestas intactos.

## Datos (continuación)
- [x] ~~Tablas de partes CIJ (`partes_cij`) tras OCR/revisión de la columna de números.~~
      → 6 IPL estructurados: 1.397 registros, 204 P/N, 124 verificados + 80 borradores,
      801 ítems sin P/N. Con el OCR 1550/1710 la app muestra **296 P/N CIJ**
      (204 digitales + 92 nuevos) y 336 ítems OCR sin P/N.
- [x] ~~Extraer las **velocidades CIJ por modelo/boquilla** de los calculadores
      «Line Speed Calculator v9.7» → dataset `cij_velocidades`.~~
      → `datos/cij_velocidades.json`: **270 calculadores, 271 PDFs, 266 entradas,
      12 modelos, 0 conflictos de valores**; 22 avisos de boquilla, 31 de modelo,
      3 de fuente y 1 experto. Integrado en la PWA como `D.velocidades` y validado
      contra los charts 1280/1580/1880 (`tools/validar_velocidades_cij.py`).
      Queda la **revisión humana** de los avisos de boquilla/modelo/fuente y de los
      valores `borrador-decodificado` antes de usarlos como dato firme.
- [ ] **Cruzar las 120 partes TTO** (hoy en borrador) contra las Official Parts Lists
      PDF para elevarlas a `verificado`. Venía del PENDIENTE de v0.1.0.
- [ ] Revisar los **títulos de boletines TTO** marcados dudosos/no legibles
      (63 títulos fiables de 113). Venía del PENDIENTE de v0.1.0.
- [x] ~~Completar los IPL **1550** y **1710** (los otros 2 de los 9 PDFs de la serie 1000).~~
      → OCR con Windows.Data.Pdf + Windows.Media.Ocr, sin instalar nada:
      **1550 = 56 páginas, 1710 = 51 páginas**; consolidado `datos/partes_cij_ocr.json`
      con **193 P/N, 277 registros, 336 ítems sin P/N, 92 P/N nuevos** y estado
      `borrador-decodificado`. Las **3 láminas del 1550** (PDF 14, 15 y 18) se
      recuperaron a **1200 px**; la 15 aportó 4 P/N y 5 ítems, y quedan **0 páginas
      omitidas**.
- [ ] **Revisión humana/cotejo de los 193 P/N del OCR 1550/1710** antes de ascenderlos:
      hoy todos son `borrador-decodificado`; se conserva `descripcion_ocr` y `pn_ocr`
      como evidencia. No se reconstruyen P/N a mano. Los 5 conflictos reales
      (`395898`, `395899`, `399474`, `399475`, `SP234081`) ya se muestran en la app.
- [ ] Revisión visual muestra a muestra de los 204 P/N y de los 801 ítems sin P/N;
      hoy hay muestras verificadas (1210 p27/p50, 1220 p33, 1610 p11, 1620E p48,
      1650 b51) y el conflicto real de 399475 marcado como borrador. Los 801 ítems
      sin P/N ya están agrupados en `datos/analisis/items_sin_pn.csv` (193
      descripciones únicas; categorías heurísticas) para revisión humana. Se
      conservan tal como están impresos (p. ej. `100 m Castor` en el 1620E).
      La **auditoría automática** (`tools/auditar_partes_cij.py`,
      `datos/analisis/auditoria_partes_cij.csv`) ya comprobó bloque, línea, P/N,
      descripción base y cantidad de los 1.397 registros: 0 P/N fuera de línea,
      0 cantidades distintas y solo los 3 conflictos conocidos como descripciones
      no localizadas (399239, 399474, 399475). La evidencia impresa de esos
      4 casos está en `datos/analisis/conflictos_cij.md`; queda la revisión
      visual humana de las páginas y el muestreo.
- [ ] Simplicity/EquivalenciaTintas: mapeo GID pendiente.
- [ ] Partes 4–12 del repo global `Proyecto-Simplicity-Global` (hoy 3/12).
- [x] ~~31 escaneados láser sin JPEG (rasterizado/OCR si aportan).~~
      → **lote láser cerrado**: 14 casos clasificados, **7 recuperados con texto
      (16.148 caracteres: 6 OCR + 1 capa de texto decodificada)**, 2 diagramas
      rotados 90°, **7 planos/3D `sin-texto-por-diseno`**; **0 casos
      `sin-resultado`/`error`**. `MedidoresPortenciaCO2.pdf` se decodificó con
      `tools/decodificar_texto_pdf.py`: **AL-67438** y **AL-66517** con sus
      descripciones exactas; la imagen JPEG y la lectura visual 029/581 quedan
      como evidencia secundaria descartada. Detalle en
      `datos/extraccion/_lote_laser_resumen.json` y prueba en
      `tools/test_lote_laser.py`.
- [ ] Revisión humana de las **266 velocidades CIJ** y de sus 56 avisos
      (22 boquilla, 31 modelo, 3 fuente): hoy todas son `borrador-decodificado` y
      no sustituyen al calculador oficial. Los 4 duplicados ya están fusionados.
- [x] ~~Confirmar con el dueño la lectura visual **029/581** de
      `MedidoresPortenciaCO2.pdf`~~ → la capa de texto original decodificada
      (**AL-67438** / **AL-66517**) es la evidencia principal; 029/581 queda como
      lectura secundaria descartada.
- [x] ~~7 PDFs escaneados TTO sin texto~~ → OCR completo **7/7, 14.089 caracteres,
      0 páginas omitidas**; resumen en `datos/extraccion/_lote_tto_resumen.json` y
      texto por documento en `datos/extraccion/tto_*_ocr.txt`.

## Después
- Fase 3 APK (v0.4.0) y Fase 4 actualización (v0.5.0) según ROADMAP.
- Fase 6: generar PNG del logo (512/192/48), CODE_OF_CONDUCT.md, CI avanzado,
  íconos PWA/Android y ampliación a TIJ/LPA/Large Character/Labeling/CLARiSUITE.
- Rotación del token GitHub (nota de gestión de cuenta).
