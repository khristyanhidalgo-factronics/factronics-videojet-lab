# ⏳ PENDIENTE — v0.1.0 · Fundación del proyecto

> Lo que **falta por hacer** después de la fundación. Al congelar esta versión, este documento
> alimenta el PLAN de la v0.2.0 (regla del sistema de notas).

## Fase 1 — Extracción de datos (datos desde las fuentes del dueño)
- [ ] Leer los PDFs/Excel de las carpetas de fuentes del dueño (partes por modelo, fichas de tintas,
      uso de solvente por modelo, velocidades CIJ por boquilla, partes TTO 6x30, ribbons, láser).
- [ ] Construir el catálogo de números de parte por tecnología/modelo/componente **solo con datos reales**.
- [ ] Extraer las velocidades de impresión (velocidades CIJ) para las exploradores especialmente.
- [ ] Marcar en el catálogo cada dato como: `verificado` / `borrador` / `por definir`.
- [ ] Láser: inventario de la carpeta `documentacion laser` y primera carga de contenido.

## Fase 1 — pendientes derivados de la segunda extracción (2026-11-08)
- [x] ~~Procesar los 45 PDFs restantes de uso de solvente~~ → **CERRADO: 802/802 procesados** (800 curvas verificado + 2 «sin-datos-en-documento»). Ver HECHO.
- [ ] **Decodificador calibrado de fuentes subset** (offset por bloque; pista 1: la familia IPL 1550 usa desplazamiento ASCII−3 verificable con «Illustrated parts»; pista 2: `#N/D` confirma hojas Excel exportadas). Aplica a: tablas de las 9 IPL, `EquivalenciaTintasVJ1000` y «Simplicity» Makeup. Regla: solo decodificación determinista validada con frases de control — nada reconstruido a mano.
- [ ] Parser de tablas de las 9 IPL 1000VJ → dataset `datos/partes_cij.json` (número de parte + descripción + cantidad + referencia de ilustración), bloqueado por el decodificador.
- [ ] Extraer las fichas V471, V4263 y V4264 (carpeta INFORMACION TINTAS; plantilla probada: `ss-ink-v4250-us.pdf`).
- [ ] Extraer velocidades CIJ por modelo/boquilla (calculadores «Line Speed Calculator v9.7») → dataset `cij_velocidades`.
- [ ] Extraer los datos de ribbons TTO (carpeta Ribbons del curso 6x30) → consumibles TTO.
- [ ] Inventariar y clasificar `documentacion laser` (1900+ archivos).
- [ ] Cruzar las partes TTO (borrador) contra las Official Parts Lists PDF para elevarlas a `verificado`.

## Fase 2 — App web offline (presentar en v0.2.0–v0.3.0)
- [ ] App web (PWA) con: exámenes de 5 niveles (Básico, Básico-Medio, Intermedio-Avanzado, Avanzado, Profesional), modos estudio/prueba rápida/repaso, buscador de partes, calculadoras (consumo/costo/comparador), perfiles e historial, exportar/importar copia de seguridad.
- [ ] i18n: es/en/pt desde el catálogo de textos; sin textos hardcodeados.
- [ ] Tema claro/oscuro/sistema + color de acento + temas festivos (fecha + país; Venezuela base).
- [ ] QR offline para compartir resultados y enlace de descarga.
- [ ] Página `docs/notas.html` pública de notas + CI básico (validadores JSON/links).

## Fase 3 — App Android (APK) (v0.4.0)
- [ ] Proyecto nativo Kotlin + Jetpack Compose + Material 3, minSdk 24.
- [ ] Material You (color dinámico según el muro del dispositivo, desactivable) + temas festivos.
- [ ] Paridad con el motor web; pruebas JVM con los mismos valores de referencia.
- [ ] Permisos mínimos; instalación firmada con keystore **persistente** (conserva datos del usuario).

## Fase 4 — Sistema de actualización (v0.5.0)
- [ ] `version.json` + verificación SHA-256 + aviso de nueva versión (sin bloquear la versión anterior).
- [ ] Firma con el mismo keystore en todas las versiones para actualizaciones sobreinstalables.

## Fase 5 — Release estable v1.0.0
- [ ] Compilar APK release firmada, publicar Release con tag `v1.0.0` y verificar descarga por hash.
- [ ] Congelar las notas de todas las versiones (incluida copia del ROADMAP).

## Fase 6+ — Mejoras públicas
- [ ] Generar PNG del logo (512/192/48) reintentando el generador de imágenes IA (hoy estaba indisponível) o rasterizando el SVG.
- [ ] CODE_OF_CONDUCT.md, CI avanzado (GitHub Actions), íconos PWA y Android.
- [ ] Ampliación de tecnologías (TIJ, LPA, Large Character, Labeling, Software CLARiSUITE) → ver ROADMAP.

## Nota de gestión de cuenta de GitHub
- [ ] Tras publicar fundación y estabilizar: apuntar la rotación del token expuesto en el chat
      (security del proyecto: regla propia "rotar cualquier token expuesto").
