# ✅ HECHO — v0.2.0 · App web offline (PWA)

> Lista de lo **completado y entregado** en la v0.2.0. Se actualiza a medida que avanza.

## Datos para la app
- [x] **`tools/construir_app_datos.py`** → `docs/app/datos.js` (2015,0 KB): paquete compacto
      con estados por dato y memoria de traducción `D.tr` (3.449 entradas).
- [x] Incluye: 802 curvas de solvente, 134 tintas (bases, color, SDS con CAS/% y
      propiedades), **2.894 partes** (120 TTO + 204 CIJ + 2.570 LÁSER), 231 códigos de error,
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

## App (PWA)
- [x] `docs/app/index.html` — Inicio, Estudiar (tintas/ribbons/láser/mantenimiento),
      Buscar unificado con filtros, Calcular, Examen, Aviso.
- [x] i18n **es/en/pt/it/zh** para la interfaz; tema claro/oscuro/sistema con persistencia.
- [x] Detalle de tinta con tabla de composición (nombre, CAS, %, estado) y propiedades.
- [x] Calculadora CIJ: interpolación 10–40 °C, ml/h, h/L, h/cartucho, costo/hora;
      aviso para `sin-datos-en-documento`; formato numérico por idioma (coma decimal
      en es/pt) y referencia legible (`30 °C → 11,2 ml/h`).
- [x] **Prueba automática de la calculadora:** `tools/test_app_calculo.py` recorre las
      802 curvas, comprueba 800 referencias @30 °C y el caso VJ1210/V401 = 11,2 ml/h;
      también detecta si la app vuelve a imprimir objetos (`[object Object]`). En el CI.
- [x] Exámenes de 5 niveles generados de datos reales, corrección con referencia e
      historial local; el nivel 3 incluye preguntas de **parte CIJ → descripción**.
- [x] **Offline:** `manifest.webmanifest` + `sw.js` (precache y cache-first) + icono SVG;
      instalación como PWA desde el navegador. Caché actualizada a `fvl-v0.2.0-alpha-14`.

## Publicación
- [x] Landing con acceso directo a la app y tarjeta en Descargas (estado v0.2.0-alpha).
- [x] Notas de versión v0.2.0 (PLAN / BITÁCORA / HECHO / PENDIENTE).

## Pendiente para cerrar v0.2.0 (ver PENDIENTE)
- [x] **Verificación en navegador real**: consola limpia; calculadora 11,2 ml/h @30 °C (coincide con la referencia); buscador 84 resultados con «AL-69»; examen Básico 10 preguntas con corrección e historial; service worker activo.
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
