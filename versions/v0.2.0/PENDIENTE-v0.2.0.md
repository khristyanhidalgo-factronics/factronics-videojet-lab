# ⏳ PENDIENTE — v0.2.0 · App web offline (PWA)

> Lo que falta para **cerrar la v0.2.0**. Al congelar, alimenta el PLAN de v0.3.0.

## Cierre de v0.2.0
- [x] **Verificación final en navegador real (alpha-16)**: consola sin errores ni
      avisos, service worker activo y caché `fvl-v0.2.0-alpha-16`; calculadora de
      velocidad (508 m/min · 1.667 fpm · 16.667 columnas/s), solvente (11,2 ml/h
      @30 °C), examen Básico 10/10 con constancia e historial y cambio a EN.
- [x] **Verificación en vivo de alpha-17/build 13**: CI «Validar» y Pages en
      `success`; `version.json` construccion 13, `sw.js` alpha-17 y caché
      `fvl-v0.2.0-alpha-17`. En la app publicada: consola sin errores ni avisos;
      búsqueda `AL-67438` muestra la descripción decodificada en ES y el texto
      original en EN; calculadora de velocidad 508 m/min · 1.667 fpm · 16.667
      columnas/s y solvente VJ1210/V401 @30 °C = 11,2 ml/h con `$0,11/h` a
      `$10/L`.
- [x] **Verificación en vivo de alpha-18/build 16**: CI «Validar» y Pages en
      `success`; `version.json` construccion 16, `sw.js` alpha-18 y caché
      `fvl-v0.2.0-alpha-18`; actualización desde alpha-17 con `reg.update()` +
      recarga. Examen «Velocidades CIJ (266)» con los 3 tipos, 10 preguntas,
      corrección, constancia, historial y consola limpia.
- [x] **Verificación en vivo de alpha-20/build 19**: CI «Validar» y Pages en
      `success`; `version.json` construccion 19, `sw.js` alpha-20 y caché
      `fvl-v0.2.0-alpha-20`; Lighthouse 1.0/1.0/1.0 en tema oscuro y claro,
      sin fallos, y consola limpia.
- [x] **Verificación en vivo de alpha-21/build 21**: CI «Validar» y Pages en
      `success`; `version.json` construccion 21 con `banco_partes_cij: 124`,
      `sw.js` alpha-21; examen «Partes CIJ (124)» con los 2 tipos, 4 opciones
      únicas por pregunta, aviso, corrección, historial y consola limpia.
- [x] **Verificación en vivo de alpha-22/build 23**: CI «Validar» (run
      `43602890817`) y Pages (run `43602890551`) en `success`; `version.json`
      construccion 23 con `banco_partes_cij: 124` y `banco_partes_tto: 120`,
      `sw.js` alpha-22 y caché `fvl-v0.2.0-alpha-22`; examen «Partes TTO (120)»
      con los 2 tipos, 4 opciones únicas por pregunta, aviso, corrección 10/10,
      historial, los 5 idiomas y consola limpia.
- [x] **Verificación en vivo de alpha-23/build 25**: CI «Validar» (run
      `43605031454`) y Pages (run `43605031038`) en `success`; `version.json`
      construccion 25, `sw.js` alpha-23 y caché `fvl-v0.2.0-alpha-23`; 1.500
      preguntas sin fallos, tipos nuevos de ribbon/solvente, corrección 10/10 e
      historial, 5 idiomas y consola limpia.
- [x] **Verificación en vivo de alpha-24/build 27**: CI «Validar» (run
      `43607329898`) y Pages (run `43607329363`) en `success`; `version.json`
      construccion 27, `sw.js` alpha-24 y caché `fvl-v0.2.0-alpha-24`; 2.000
      preguntas sin fallos, tipos nuevos en niveles 4 y 5, 4 opciones,
      corrección 10/10 e historial, 5 idiomas y consola limpia.
- [x] **Verificación en vivo de alpha-25/build 29**: CI «Validar» (run
      `43608611888`) y Pages (run `43608611712`) en `success`; `version.json`
      construccion 29, `sw.js` alpha-25 y caché `fvl-v0.2.0-alpha-25`; 527 pares
      tinta|CAS, búsquedas `78-93-3`, `metiletilcetona` y `V401`, variantes
      `chromium`/`cromo` según idioma, 5 idiomas y consola limpia.
- [x] **Verificación en vivo de alpha-26/build 31**: CI «Validar» (run
      `43609502890`) y Pages (run `43609502691`) en `success`; `version.json`
      construccion 31, `sw.js` alpha-26 y caché `fvl-v0.2.0-alpha-26` con 7
      recursos; 70 botones «Ver», ficha V401 con 5 componentes, consulta
      conservada al volver, «View» en EN y consola limpia.
- [x] **Verificación en vivo de alpha-27/build 33**: CI «Validar» (run
      `43610608987`) y Pages (run `43610609127`) en `success`; `version.json`
      construccion 33, `sw.js` alpha-27 y caché `fvl-v0.2.0-alpha-27` con 7
      recursos; historial 9/10 + 6/10 + 10/10 → 3 exámenes, 83 % y 100 %,
      borrado con confirmación, HTML escapado, 5 idiomas y consola limpia.
- [x] **Verificación en vivo de alpha-28/build 35**: CI «Validar» (run
      `43622899676`) y Pages (run `43622899568`) en `success`; `version.json`
      construccion 35, `sw.js` alpha-28 y caché `fvl-v0.2.0-alpha-28` con 7
      recursos; `sds_volat` con 119 tintas y 25 valores, 4 opciones traducidas
      en es/en/pt/it/zh, corrección 1/1, constancia y consola limpia.
- [x] **Verificación en vivo de alpha-29/build 37**: CI «Validar» (run
      `43623748302`) y Pages (run `43623747992`) en `success`; `version.json`
      construccion 37, `sw.js` alpha-29 y caché `fvl-v0.2.0-alpha-29` con 7
      recursos; `tinta_color` con 116 tintas y 11 colores, 4 opciones
      traducidas, corrección 1/1, constancia y consola limpia.
- [x] **Verificación en vivo de alpha-30/build 39**: CI «Validar» (run
      `43624507272`) y Pages (run `43624506914`) en `success`; `version.json`
      construccion 39, `sw.js` alpha-30 y caché `fvl-v0.2.0-alpha-30` con 7
      recursos; importación real con perfil, historial y repaso saneado, mensaje
      con 3 registros y consola limpia.
- [x] **Verificación en vivo de alpha-31/build 41**: CI «Validar» (run
      `43629528851`) y Pages (run `43629528591`) en `success`; `version.json`
      construccion 41, `sw.js` alpha-31 y caché `fvl-v0.2.0-alpha-31` con 7
      recursos; `sds_ebull` con 119 tintas y 12 valores, 4 opciones traducidas,
      corrección 1/1, constancia y consola limpia.
- [x] **Verificación en vivo de alpha-32/build 43**: CI «Validar» (run
      `43630259434`) y Pages (run `43630258738`) en `success`; `version.json`
      construccion 43, `sw.js` alpha-32 y caché `fvl-v0.2.0-alpha-32` con 7
      recursos; `sds_pvap` con 119 tintas y 8 valores, 4 opciones traducidas,
      corrección 1/1, constancia y consola limpia.
- [x] **Verificación en vivo de alpha-33/build 45**: CI «Validar» (run
      `43631015656`) y Pages (run `43631014991`) en `success`; `version.json`
      construccion 45, `sw.js` alpha-33 y caché `fvl-v0.2.0-alpha-33` con 7
      recursos; base química con 131 tintas y 12 bases traducidas, 4 opciones,
      corrección 1/1, constancia y consola limpia.
- [x] **Verificación en vivo de alpha-34/build 47**: CI «Validar» (run
      `43632425887`) y Pages (run `43632425696`) en `success`; `version.json`
      construccion 47, `sw.js` alpha-34 y caché `fvl-v0.2.0-alpha-34` con 7
      recursos; pregunta y opciones con contraste 14,10:1 (oscuro) y 17,85:1
      (claro), estados 11,06–15,63:1, capturas y consola limpia.
- [ ] **Verificación en vivo de alpha-35/build 49**: CI «Validar» y Pages en
      `success`; `version.json` construccion 49, `sw.js` alpha-35; chip
      Solventes con 802 curvas, búsquedas VJ1210/V401/VJ1650/UHS/sin datos,
      duplicado VJ1560/V461, 5 idiomas y consola limpia.
- [x] **Verificación en vivo de alpha-35/build 49**: CI «Validar» (run
      `43635962772`) y Pages (run `43635961942`) en `success`; `version.json`
      construccion 49, `sw.js` alpha-35 y caché `fvl-v0.2.0-alpha-35` con 7
      recursos; 802 curvas, búsquedas VJ1210/V401/UHS/sin datos, VJ1560/V461
      con dos bases, 5 idiomas y consola limpia.
- [x] **CHANGELOG y ROADMAP permanentes:** `CHANGELOG.md` en la raíz, ROADMAP
      actualizado con el estado de alpha-35 y validación de existencia en CI.
- [x] **Verificación en vivo de alpha-36/build 51**: CI «Validar» (run
      `43637148231`) y Pages (run `43637147879`) en `success`; `version.json`
      construccion 51, `sw.js` alpha-36 y caché `fvl-v0.2.0-alpha-36` con 7
      recursos; banco CIJ con 361 candidatos (124 modelos), TTO 240, 4 opciones,
      corrección 1/1, constancia y consola limpia.
- [x] **Verificación en vivo de alpha-37/build 53**: CI «Validar» (run
      `43637787063`) y Pages (run `43637786870`) en `success`; `version.json`
      construccion 53, `sw.js` alpha-37 y caché `fvl-v0.2.0-alpha-37` con 7
      recursos; banner oculto inicial, visible al simular actualización, 5
      idiomas, accesibilidad y consola limpia.
- [x] **Verificación en vivo de alpha-38/build 55**: CI «Validar» (run
      `43642778940`) y Pages (run `43642778595`) en `success`; `version.json`
      construccion 55, `sw.js` alpha-38 y caché `fvl-v0.2.0-alpha-38`; 399474
      verificado, 4 alternas con conflicto, banco CIJ 125/364, 5 idiomas y
      consola limpia.
- [ ] **Verificación en vivo de alpha-39/build 57**: CI «Validar» y Pages en
      `success`; `version.json` construccion 57, `sw.js` alpha-39; 91 P/N OCR
      promovidos, 3 erratas corregidas, banco CIJ 216, búsqueda y consola limpias.
- [x] ~~**Prueba de la calculadora** contra referencia: VJ1210/V401 @30 °C = 11,2 ml/h~~
      → `tools/test_app_calculo.py` recorre 802 curvas y 800 referencias @30 °C.
- [x] ~~Revisión de textos i18n (es/en/pt)~~ → 5 idiomas completos (es/en/pt/it/zh),
      cobertura 17.225/17.225 y pruebas automáticas; queda la revisión humana de estilo.
- [ ] Revisión humana de estilo de las traducciones IT/ZH (`borrador-de-traduccion`):
      confirmar términos técnicos con el dueño o con documentación Videojet.
- [x] ~~Nombres accesibles, foco visible y tamaño táctil de los controles~~ →
      etiquetas `for`, `aria-label` en campos dinámicos, `aria-pressed` en las
      opciones del examen, resultados `role="status"`, objetivos de 44 px en móvil
      y `meta description`; Lighthouse 1.0 en accesibilidad, buenas prácticas y SEO
      en claro y oscuro (`--on-accent` y `--muted` ajustados).
- [ ] Ajustes finos de teclado móvil y contraste tras una prueba en dispositivo.

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
- [x] ~~Banco de examen específico de velocidades CIJ~~ → fuente «Velocidades CIJ (266)» con preguntas de velocidad, boquilla y fuente, aviso de `borrador-decodificado` y auditoría de 10.640 preguntas sin ambigüedad; verificado en navegador.
- [x] ~~Banco separado por tecnología (partes CIJ)~~ → fuente «Partes CIJ (124)» con
      solo P/N verificados: 124 preguntas P/N→descripción + 113 descripción→P/N,
      aviso de exclusión de borradores/OCR y auditoría de 237 candidatos en 5 idiomas;
      verificado en navegador.
- [ ] Más variedad de preguntas por nivel (nuevos casos de falla, diagnóstico y
      cálculos) y revisión humana de las 5 descripciones CIJ compartidas para decidir
      si son variantes reales o duplicados de catálogo.
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
- [x] **Revisión de los 5 conflictos CIJ del OCR 1550/1710:** revisados contra las
      páginas renderizadas de los IPL 1550, 1650 y 1710. `399474` es un sinónimo
      real (Dry Air Kit Assembly / Air Dryer Assembly) y se promovió a `verificado`;
      `395898`, `395899`, `399475` y `SP234081` tienen dos descripciones impresas
      para el mismo P/N y se conservan como `d_alt` fuera del banco. El banco CIJ
      queda en **125 P/N y 364 preguntas**.
- [x] **Revisión de los 193 P/N del OCR 1550/1710:** 193/193 con todas sus
      apariciones en la misma fila que la descripción; 91 P/N nuevos promovidos
      con `estado_revisado`, 3 erratas corregidas y SP234081 como único nuevo
      con conflicto. Los 101 P/N restantes ya estaban en la base digital.
      Se conserva `descripcion_ocr` y `pn_ocr` como evidencia. **Artefactos:**
      `datos/analisis/partes_cij_ocr_revision.csv`, `partes_cij_ocr_apariciones.csv`
      y el tablero `PENDIENTES_REVISION.md`.
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
      **Artefactos listos:** `datos/analisis/velocidades_cij_avisos.csv` (56 filas)
      y `velocidades_cij_avisos.md`; el valor impreso ya prevalece sobre el nombre
      de archivo y las 5 notas documentadas están recogidas.
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
