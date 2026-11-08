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
- [x] ~~Procesar los 45 PDFs restantes de uso de solvente~~ → **CERRADO: 802/802 procesados** (800 curvas verificado + 2 «sin-datos-en-documento»).
- [x] ~~Decodificador calibrado de fuentes subset~~ → **CERRADO**: `tools/decodificar_cipher_offset.py` v2 (decisión por bloque; offset +29 verificable con «Videojet Technologies» / «Illustrated Parts List»); salidas `*_dec.txt` para TS2205, 98039 y las 9 IPL.
- [ ] **Números de parte de las IPL** → `partes_cij`: los rótulos ya decodifican, pero cada número debe cruzarse contra el PDF original (revisión/OCR); el parser sigue bloqueado.
- [x] ~~Extraer las fichas V471/V4263/V4264~~ → **CERRADO**: las 564 fichas QSS se descifraron y extrayeron (V471-D/K, V4264-D/L, etc.); composición y propiedades estructuradas.
- [ ] Extraer velocidades CIJ por modelo/boquilla (calculadores «Line Speed Calculator v9.7») → dataset `cij_velocidades`.
- [x] ~~Extraer los datos de ribbons TTO~~ → **CERRADO**: `datos/tto_ribbons.json` (64 grados, 694 ítems, matrices y lógica de lote).
- [x] ~~Inventariar y clasificar `documentacion laser`~~ → **CERRADO**: 1.908 archivos inventariados; 1.253 PDFs extraídos; OCR nativo en los escaneados con JPEG.
- [ ] Cruzar las partes TTO (borrador) contra las Official Parts Lists PDF para elevarlas a `verificado`.

## Fase 1 - pendientes derivados del ciclo tintas/decodificador/ocr (2026-11-08)
- [ ] **Números de parte de las IPL:** revisión contra el PDF original u OCR antes de estructurar `partes_cij`.
- [x] ~~**OCR de las 562 fichas QSS**~~ → **CERRADO SIN OCR**: eran PDFs cifrados RC4-128; descifradas 564/564 y estructurada composición (1.773 componentes, CAS 100% validado) y propiedades (12.728 campos).
- [x] ~~**OCR de los PDFs láser escaneados**~~ → **PARCIAL CERRADO**: OCR nativo de Windows sobre los 29 con JPEG (17 con texto, +16.277 chars); quedan 31 sin JPEG (JBIG2/vector).
- [ ] **31 escaneados láser sin JPEG**: requerirían rasterizar el PDF a imagen para OCR (evaluar si aportan).
- [ ] **Simplicity / EquivalenciaTintas:** fuentes CID sin ToUnicode ("redundante-cifrado"); requieren OCR o remapeo por comparación.
- [ ] **Ampliar `cij_tintas.json`**: fichas QSS completas (composición/datos regulatorios) más allá de base+curva.
- [ ] **Refrescar `simplicity_global_inventario.json`** cuando el dueño suba las partes 4-12 del repo global (hoy 3/12) y clasificar por tecnología.
- [ ] **Muestreo visual de composiciones SDS** (nombres/porcentajes) contra los PDFs; el CAS ya está validado al 100%.
- [ ] **Datasets derivados de manuales** láser/TTO (tablas de partes, códigos de error, mantenimiento) desde el texto ya extraído.
- [ ] **Revisar títulos de boletines TTO** marcados dudosos/no-legibles (63 títulos fiables de 113).

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
