# ✅ HECHO — v0.2.0 · App web offline (PWA)

> Lista de lo **completado y entregado** en la v0.2.0. Se actualiza a medida que avanza.

## Datos para la app
- [x] **`tools/construir_app_datos.py`** → `docs/app/datos.js` (663,9 KB): paquete compacto
      con estados por dato.
- [x] Incluye: 802 curvas de solvente, 134 tintas (bases, color, SDS con CAS/% y
      propiedades), **2.690 partes** (120 TTO + 2.570 LÁSER), 231 códigos de error,
      64 grados + 694 ítems de ribbons, mantenimiento (48 docs / 39 tareas), 21 modelos
      láser.

## App (PWA)
- [x] `docs/app/index.html` — Inicio, Estudiar (tintas/ribbons/láser/mantenimiento),
      Buscar unificado con filtros, Calcular, Examen, Aviso.
- [x] i18n **es/en/pt** para la interfaz; tema claro/oscuro/sistema con persistencia.
- [x] Detalle de tinta con tabla de composición (nombre, CAS, %, estado) y propiedades.
- [x] Calculadora CIJ: interpolación 10–40 °C, ml/h, h/L, h/cartucho, costo/hora;
      aviso para `sin-datos-en-documento`.
- [x] Exámenes de 5 niveles generados de datos reales, corrección con referencia e
      historial local.
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
