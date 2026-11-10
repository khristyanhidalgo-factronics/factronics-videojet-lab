# ✅ HECHO — v0.2.0 · App web offline (PWA)

> Lista de lo **completado y entregado** en la v0.2.0. Se actualiza a medida que avanza.

## Datos para la app
- [x] **`tools/construir_app_datos.py`** → `docs/app/datos.js` (692,0 KB): paquete compacto
      con estados por dato.
- [x] Incluye: 802 curvas de solvente, 134 tintas (bases, color, SDS con CAS/% y
      propiedades), **2.890 partes** (120 TTO + 200 CIJ + 2.570 LÁSER), 231 códigos de error,
      64 grados + 694 ítems de ribbons, mantenimiento (48 docs / 39 tareas), 21 modelos
      láser.
- [x] **Partes CIJ de 6 IPL 1000VJ**: 1.397 registros, **200 P/N únicos** (124
      verificados + 76 borradores; 0 por-definir) y 805 ítems sin P/N conservados como
      evidencia. Buscador por P/N, descripción y modelo; estado y conflictos visibles.

## App (PWA)
- [x] `docs/app/index.html` — Inicio, Estudiar (tintas/ribbons/láser/mantenimiento),
      Buscar unificado con filtros, Calcular, Examen, Aviso.
- [x] i18n **es/en/pt/it/zh** para la interfaz; tema claro/oscuro/sistema con persistencia.
- [x] Detalle de tinta con tabla de composición (nombre, CAS, %, estado) y propiedades.
- [x] Calculadora CIJ: interpolación 10–40 °C, ml/h, h/L, h/cartucho, costo/hora;
      aviso para `sin-datos-en-documento`.
- [x] Exámenes de 5 niveles generados de datos reales, corrección con referencia e
      historial local; el nivel 3 incluye preguntas de **parte CIJ → descripción**.
- [x] **Offline:** `manifest.webmanifest` + `sw.js` (precache y cache-first) + icono SVG;
      instalación como PWA desde el navegador.

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
- [x] **Respuestas de texto en preguntas «completar»** (p. ej. «intelligent motion») con comparación normalizada; `tools/test_banco_tto.py` valida 372 preguntas × 3 idiomas y sus 7 tipos, y quedó agregado al CI.
- [x] **Idiomas IT y ZH:** interfaz completa en 5 idiomas (ES/EN/PT/IT/ZH), con selector, cadenas dinámicas y constancia traducidas; 0 claves faltantes y pruebas en navegador sin errores. El banco TTO conserva es/en/pt y usa español como respaldo en IT/ZH (indicado en la app).
- [x] **Precache del shell verificado (7/7)** y registro del service worker con `updateViaCache:'none'` para recibir actualizaciones sin caché vieja.
- [x] **`docs/version.json` publicado** (copia del `version.json` raíz) y validado contra la versión/build para que Pages no sirva datos viejos.
