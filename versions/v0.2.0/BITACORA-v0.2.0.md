# 🖊️ BITÁCORA — v0.2.0 · App web offline (PWA)

> Registro de **lo que se está haciendo** para la v0.2.0, en orden cronológico.
> Se congela al publicar la versión.

| Fecha | Registro |
|---|---|
| 2026-11-08 | **Comienza la Fase 2 (app web).** Se genera el paquete de datos para el navegador con `tools/construir_app_datos.py` → `docs/app/datos.js` (663,9 KB): 802 curvas de solvente, 134 tintas con SDS/propiedades, **2.690 partes** (120 TTO + 2.570 LÁSER), 231 códigos de error, 64 grados + 694 ítems de ribbons, mantenimiento (48 docs/39 tareas) y 21 modelos láser. Los estados por dato se conservan. |
| 2026-11-08 | **App creada:** `docs/app/index.html` (vanilla JS, sin dependencias) con pestañas Inicio / Estudiar / Buscar / Calcular / Examen / Aviso, i18n **es/en/pt**, tema claro-oscuro-sistema, diseño responsive. Buscador unificado con filtros; detalle de tintas con composición CAS/% y propiedades; ribbons y mantenimiento consultables. |
| 2026-11-08 | **Calculadora CIJ:** selección modelo/variante → tinta, interpolación lineal de la curva oficial 10–40 °C, ml/h, horas/litro, horas/cartucho y costo/hora con precio del solvente. Maneja el estado `sin-datos-en-documento` con aviso explícito. |
| 2026-11-08 | **Exámenes generados de datos reales:** 5 niveles (tinta→base; ribbon→color; código→tecnología; consumo de referencia @30 °C; CAS→componente). Corrección con referencia a la fuente, historial local del alumno (localStorage). |
| 2026-11-08 | **PWA offline:** `manifest.webmanifest` + `sw.js` (precache del shell, cache-first con actualización), icono del logo, instalación desde el navegador. Registro del service worker solo en http(s) (GitHub Pages). |
| 2026-11-08 | **Landing actualizada:** botón «🚀 Abrir la app (PWA)», tarjeta de la app en Descargas y estado v0.2.0-alpha. |
| 2026-11-08 | Notas v0.2.0 creadas (PLAN / BITÁCORA / HECHO / PENDIENTE). Queda **verificar la app en navegador** (consola, offline, exámenes) antes de congelar la versión. |
| 2026-11-08 | **Verificación en navegador (local)**: la app carga sin errores de consola; KPIs 802/134/2690/231/64/21; calculadora VJ1210/V401 @30 °C = **11,2 ml/h** (coincide con la referencia), 89 h/L y 67 h/cartucho; buscador «AL-69» devuelve 84 filas; examen Básico de 10 preguntas corrige y guarda historial; service worker cachea el shell (`fvl-v0.2.0-alpha-*`). Se corrigió un bug del parser de % en la sección 3 (patrón anclado) y se regeneró todo: **1.716/1.773 componentes con %**; la tabla de la app muestra CAS + % + estado `verificado`. |
