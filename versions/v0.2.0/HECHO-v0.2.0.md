# ✅ HECHO — v0.2.0 · App web offline (PWA)

> Lista de lo **completado y entregado** en la v0.2.0. Se actualiza a medida que avanza.

## Datos para la app
- [x] **`tools/construir_app_datos.py`** → `docs/app/datos.js` (2.110,1 KB): paquete compacto
      con estados por dato, memoria de traducción `D.tr` (3.506 entradas) y
      **`D.velocidades`** (266 calculadores CIJ).
- [x] Incluye: 802 curvas de solvente, 134 tintas (bases, color, SDS con CAS/% y
      propiedades), **2.986 partes** (120 TTO + 296 CIJ + 2.570 LÁSER), 231 códigos de error,
      64 grados + 694 ítems de ribbons, mantenimiento (48 docs / 39 tareas), 21 modelos
      láser.
- [x] **Partes CIJ de 6 IPL 1000VJ**: 1.397 registros, **204 P/N únicos** (124
      verificados + 80 borradores; 0 por-definir) y 801 ítems sin P/N conservados como
      evidencia. Buscador por P/N, descripción y modelo; estado y conflictos visibles.
- [x] **Parser CIJ v5.1:** cantidades partidas en varias corridas (`1` + `0` = 10,
      `1` + `4` = 14) unidas desde la última celda o desde las corridas numéricas
      contiguas; tabla de variantes P/N | descripción | país del 1620E incorporada
      (4 P/N Excel: 399101, 399102, 399103, 399105).
- [x] **Auditoría de evidencia CIJ:** `tools/auditar_partes_cij.py` revisa las
      1.397 apariciones (596 de partes + 801 sin P/N) contra el bloque y la línea
      del PDF. 0 P/N fuera de línea, 0 cantidades distintas, 801/801
      descripciones sin P/N localizadas y 592/596 descripciones de partes
      localizadas; las 4 restantes son los 3 conflictos ya marcados (399239,
      399474, 399475). Evidencia: `datos/analisis/auditoria_partes_cij.csv`.
- [x] **Evidencia de conflictos CIJ:** `datos/analisis/conflictos_cij.md` reúne
      las descripciones impresas de 399239, 399474 y 399475 con documento,
      tabla e ítem; `datos/analisis/LEEME.md` documenta los archivos de
      análisis. Los 3 P/N siguen en `borrador` con
      `conflicto_descripciones=true`.
- [x] **IPL 1550/1710 por OCR, sin instalar nada:** `tools/ocr_pdf_paginas.py`
      (Windows.Data.Pdf + Windows.Media.Ocr) procesó **1550 = 56 páginas** y
      **1710 = 51 páginas**. `datos/partes_cij_ocr.json`: **277 registros, 193 P/N,
      92 P/N nuevos, 336 ítems sin P/N**, todos `borrador-decodificado` con
      `descripcion_ocr`/`pn_ocr` como evidencia. Las láminas 14, 15 y 18 del 1550
      se recuperaron a **1200 px** (la 15 aportó 4 P/N y 5 ítems); quedan
      **0 páginas omitidas**. `tools/test_partes_cij_ocr.py` lo valida.
- [x] **Conflictos OCR en la app:** `tools/construir_app_datos.py` propaga a los
      P/N ya existentes los conflictos reales (`395898`, `395899`, `399474`,
      `399475`, `SP234081`) sin ascender su estado; `SequenceMatcher` eliminó el
      falso positivo `202047` («Bottie» → «Bottle»).
- [x] **Artefactos de revisión de pendientes:** `tools/generar_revision_pendientes.py`
      produce `partes_cij_ocr_revision.csv` (193 P/N, 92 nuevos),
      `partes_cij_ocr_apariciones.csv` (275 apariciones únicas de 277 registros),
      `conflictos_cij_ocr.md` (5 casos), `velocidades_cij_avisos.csv` (56 avisos:
      22 boquilla, 31 modelo, 3 fuente), `velocidades_cij_avisos.md` y el tablero
      `PENDIENTES_REVISION.md`; `tools/test_revision_pendientes.py` lo valida en CI.
- [x] **PDFs escaneados TTO y láser:** TTO **7/7** (14.089 caracteres, 0 páginas
      omitidas). Láser: **14 casos del cierre clasificados** — **7 recuperados con
      texto (16.148 caracteres)**: 6 por OCR y `MedidoresPortenciaCO2.pdf` por
      **decodificación de su capa de texto** (`tools/decodificar_texto_pdf.py`),
      que aporta **AL-67438** y **AL-66517** con descripciones exactas. Los 2
      diagramas apaisados quedaron **rotados 90°** y los **7 planos/3D
      `sin-texto-por-diseno`**. La imagen `obj21.jpg` (270.110 bytes) y la lectura
      visual 029/581 se conservan como **evidencia secundaria descartada**. Texto
      por documento en `datos/extraccion/laser_*_ocr.txt`.
- [x] **Decodificador de capas de texto PDF:** `tools/decodificar_texto_pdf.py`
      resuelve fuentes TrueType subseteadas con `/Differences` y `cmap` propio
      (GID→Unicode con Arial Narrow), sin instalar dependencias. Evidencia y detalle
      en `datos/extraccion/medidores_portencia_co2/`.
- [x] **Descripciones láser exactas y traducidas:** `laser_partes.json` usa las
      descripciones decodificadas de AL-67438/AL-66517 y conserva `descripcion_ocr`;
      `tools/agregar_traducciones_laser_decodificado.py` añade es/pt/it/zh.
- [x] **Velocidades CIJ (`datos/cij_velocidades.json`):** **270 calculadores leídos,
      271 PDFs, 266 entradas, 12 modelos, 0 conflictos de valores**; 22 avisos de
      boquilla, 31 de modelo, 3 de fuente y 1 calculador experto. Se descarta
      `v9.7z.pdf` (tabla resumen); UHS queda en 50 µm y HR en 40 µm. Validado contra
      los charts 1280/1580/1880 y el experto `1620-50 UHS|50|4x5_single`
      (508 m/min, 3333 c/s, 16667 col/s). `tools/validar_velocidades_cij.py` y
      `tools/test_velocidades_cij.py` (8 pruebas) están en el CI.
- [x] **23 descripciones TTO oficiales traducidas** a es/en/pt/it/zh con
      `tools/agregar_traducciones_tto_oficial.py`; cobertura final **3.506 cadenas ×
      5 idiomas**.
- [x] **Cotejo de P/N conocidos del OCR:** `399362` Mobile Stand Standard, `399086`
      Printhead Stand, `399474` Dry Air Kit Assembly (1550+1710), `399099` Static
      Stand Standard, `234116` Adapter Plate, `SP399089` Beacon Assembly y
      `SP399971W` CSB with Back Plate aparecen con la descripción esperada; los
      demás siguen como `borrador-decodificado` hasta revisión humana.

## App (PWA)
- [x] `docs/app/index.html` — Inicio, Estudiar (tintas/ribbons/láser/mantenimiento),
      Buscar unificado con filtros, Calcular, Examen, Aviso.
- [x] i18n **es/en/pt/it/zh** para la interfaz; tema claro/oscuro/sistema con persistencia.
- [x] Detalle de tinta con tabla de composición (nombre, CAS, %, estado) y propiedades.
- [x] Calculadora CIJ: interpolación 10–40 °C, ml/h, h/L, h/cartucho, costo/hora;
      aviso para `sin-datos-en-documento`; formato numérico por idioma (coma decimal
      en es/pt) y referencia legible (`30 °C → 11,2 ml/h`).
- [x] **Calculadora de velocidad de línea CIJ:** tarjeta modelo → boquilla → fuente
      con m/min, fpm, caracteres/s o columnas/s, tipo de calculador, archivo fuente y
      avisos de boquilla/modelo/fuente, traducida en los 5 idiomas.
- [x] **Prueba automática de la calculadora:** `tools/test_app_calculo.py` recorre las
      802 curvas, comprueba 800 referencias @30 °C y el caso VJ1210/V401 = 11,2 ml/h;
      también detecta si la app vuelve a imprimir objetos (`[object Object]`). En el CI.
- [x] Exámenes de 5 niveles generados de datos reales, corrección con referencia e
      historial local; el nivel 3 incluye preguntas de **parte CIJ → descripción**.
- [x] **Offline:** `manifest.webmanifest` + `sw.js` (precache y cache-first) + icono SVG;
      instalación como PWA desde el navegador. Caché actualizada a `fvl-v0.2.0-alpha-17`.

## Publicación
- [x] Landing con acceso directo a la app y tarjeta en Descargas (estado v0.2.0-alpha).
- [x] Notas de versión v0.2.0 (PLAN / BITÁCORA / HECHO / PENDIENTE).

## Pendiente para cerrar v0.2.0 (ver PENDIENTE)
- [x] **Verificación en navegador real**: consola limpia; calculadora 11,2 ml/h @30 °C (coincide con la referencia); buscador 84 resultados con «AL-69»; examen Básico 10 preguntas con corrección e historial; service worker activo.
- [x] **Verificación de la alpha-17 publicada (build 13)**: CI y Pages en success; SW `fvl-v0.2.0-alpha-17`; búsqueda de `AL-67438` con descripción decodificada en ES y original en EN; velocidad 508 m/min · 1.667 fpm · 16.667 columnas/s; solvente 11,2 ml/h con `$0,11/h`; consola sin errores ni avisos.
- [x] **Fix de % en composición**: patrón anclado corregido → 1.716/1.773 componentes con porcentaje; app muestra CAS + % + estado.
- [x] Ajustes de UX menores detectados en la prueba (título de tabla).
- [x] **Revisión de los proyectos de la cuenta personal** (2 repos Videojet): arquitectura, datos, i18n, validadores y sistemas de actualización analizados; registrado en `catalogo.json → proyectos_referencia`.
- [x] **Banco TTO de 372 preguntas importado** (`docs/app/banco_tto.js`) y modo de examen con 7 tipos, corrección y respuesta modelo; verificado en navegador.
- [x] **`version.json` + `docs/notas.html` con SHA-256** (`tools/publicar_notas.py`): índice maestro con huellas, página pública de notas y version.json legible por máquina.
- [x] **Copia de seguridad en la app** (exportar/importar perfil e historial).
- [x] **Validador `tools/validar_repo.py` + CI** (`.github/workflows/validar.yml`): JSON, hashes de notas, app y enlaces. TODO OK.
- [x] **Constancia imprimible con QR offline** (`docs/app/vendor/qrcode.js`): botón 🎓 Constancia en todo resultado, con logo, nombre del perfil, evaluación, puntaje, fecha, versión y QR del resultado; ventana lista para imprimir. Verificado sin errores de consola.
- [x] **Repaso espaciado y cuaderno de errores:** cajas 1–5 con intervalos 1/3/7/14/30 días, pendientes del día, errores acumulados y repaso de hasta 20 preguntas; persistencia local. Verificado en navegador.
- [x] **Respuestas de texto en preguntas «completar»** (p. ej. «intelligent motion») con comparación normalizada; `tools/test_banco_tto.py` valida 372 preguntas × 5 idiomas y sus 7 tipos, y quedó agregado al CI.
- [x] **Cinco idiomas reales en todo el contenido:** `datos/traducciones_contenido.json`
      cubre 3.445 cadenas visibles × 5 idiomas (17.225/17.225), incluidos textos de
      origen alemán, japonés y chino; `docs/app/datos.js` incrusta `D.tr` y la app
      traduce partes, tintas, SDS, ribbons, mantenimiento, errores y calculadora.
      `tools/test_traducciones.py` verifica cobertura y ausencia de centinelas.
- [x] **Banco TTO en 5 idiomas:** las 372 preguntas (1.134 cadenas) se tradujeron a
      italiano y chino desde español con `tools/traducir_banco_tto.py`; se conservan
      IDs de opciones, respuestas numéricas y de texto, **unidades impresas** (mm, ppm,
      PPR, TCP, min, USD) y etiquetas técnicas revisadas. `tools/test_banco_tto.py`
      valida 372 × 5 idiomas, centinelas, alineación de opciones, campos y unidades.
- [x] **Precache del shell verificado (7/7)** y registro del service worker con `updateViaCache:'none'` para recibir actualizaciones sin caché vieja.
- [x] **`docs/version.json` publicado** (copia del `version.json` raíz) y validado contra la versión/build para que Pages no sirva datos viejos.
- [x] **Examen de velocidades CIJ (266):** fuente separada con preguntas de velocidad nominal, boquilla y fuente; aviso `borrador-decodificado`, corrección, constancia e historial; auditoría de 10.640 preguntas sin ambigüedad y verificación en los 5 idiomas.
- [x] **Verificación en vivo de alpha-18/build 16:** CI y Pages en success; actualización desde alpha-17 aplicada sin reinstalar; examen de velocidades con los 3 tipos, corrección, constancia, historial y consola limpia.
- [x] **Accesibilidad y UX de controles:** etiquetas `for`, `aria-label` en campos dinámicos, `aria-pressed` en opciones, resultados `role="status"`, foco visible, objetivos táctiles de 44 px en móvil y `meta description`; Lighthouse 1.0 en accesibilidad, buenas prácticas y SEO.
- [x] **Contraste en tema oscuro:** `--on-accent` para botones/chips y `--muted` claro ajustado; Lighthouse 1.0 en claro y oscuro (antes 0.95 en oscuro por `#ex_go` a 2.54:1).
- [x] **Verificación en vivo de alpha-20/build 19:** CI y Pages en success; actualización desde alpha-19 aplicada; Lighthouse 1.0/1.0/1.0 en oscuro y claro y consola limpia.
