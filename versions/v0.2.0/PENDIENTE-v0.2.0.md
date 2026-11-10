# ⏳ PENDIENTE — v0.2.0 · App web offline (PWA)

> Lo que falta para **cerrar la v0.2.0**. Al congelar, alimenta el PLAN de v0.3.0.

## Cierre de v0.2.0
- [ ] **Verificación en navegador real**: consola sin errores, service worker activo,
      funcionamiento offline tras la primera carga, calculadora y exámenes de los 5 niveles.
- [ ] **Prueba de la calculadora** contra referencia: VJ1210/V401 @30 °C = 11,2 ml/h
      (curva verificada de `cij_uso_solvente.json`).
- [ ] Revisión de textos i18n (es/en/pt) y de la redacción de preguntas.
- [ ] Ajustes de UX tras la prueba (teclado móvil, tamaños, contraste).

## Superar la referencia (cuenta personal)
- [x] ~~`version.json` + `docs/notas.html` con índice SHA-256~~ → hecho (`tools/publicar_notas.py`).
- [x] ~~Idiomas IT y ZH~~ → interfaz en 5 idiomas (ES/EN/PT/IT/ZH), cadenas dinámicas y constancia traducidas; banco TTO en es/en/pt con respaldo documentado.
- [x] ~~Resultado con QR + constancia imprimible~~ → botón 🎓 Constancia con QR offline (`vendor/qrcode.js`).
- [x] ~~Repaso espaciado y cuaderno de errores~~ → cajas 1–5, pendientes del día y errores acumulados.
- [x] ~~CI de validadores~~ (JSON, notas SHA-256, app, enlaces) → `tools/validar_repo.py` + workflow, más `tools/test_banco_tto.py` (372 preguntas × 3 idiomas) en el mismo CI.
- [x] ~~Backup/restore de perfil e historial~~ → exportar/importar en la app.
- [ ] **Rotar los dos tokens expuestos** (cuenta de proyecto y cuenta personal) al estabilizar.

## Fase 2 – resto (v0.2.x / v0.3.0)
- [x] ~~Exportar/importar copia de seguridad (JSON) de perfil e historial~~ → hecho.
- [x] ~~QR offline para compartir resultados~~ → incluido en la constancia.
- [x] ~~Página pública de notas `docs/notas.html` + CI~~ → publicada con SHA-256.
- [ ] **Temas festivos** por país (Venezuela base) sobre el tema claro/oscuro/sistema.
- [ ] Más variedad de preguntas por nivel y banco separado por tecnología.
- [ ] Traducir el banco TTO a IT/ZH (372 × 2 preguntas) si se necesita contenido completo en esos idiomas.

## Datos (continuación)
- [x] ~~Tablas de partes CIJ (`partes_cij`) tras OCR/revisión de la columna de números.~~
      → 6 IPL estructurados: 1.397 registros, 204 P/N, 124 verificados + 80 borradores,
      801 ítems sin P/N. Integrado en la app.
- [ ] Completar los IPL **1550** y **1710** (los otros 2 de los 9 PDFs de la serie 1000).
      **Bloqueo técnico:** sus tablas usan fuentes Type0 sin ToUnicode utilizable y
      codificación mezclada/no constante; el parser devuelve 0 filas. Requieren OCR o
      rasterizado con revisión visual; no se reconstruyen P/N a mano. El 1550 usa una
      fuente de 2 bytes desplazada (-29) en algunas páginas, pero el mapeo de recursos
      es por página y el `/TT0` global no sirve para todas.
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
      no localizadas (399239, 399474, 399475). Queda la revisión visual humana de
      esos 4 casos y el muestreo de páginas.
- [ ] Simplicity/EquivalenciaTintas: mapeo GID pendiente.
- [ ] Partes 4–12 del repo global `Proyecto-Simplicity-Global` (hoy 3/12).
- [ ] 31 escaneados láser sin JPEG (rasterizado/OCR si aportan).

## Después
- Fase 3 APK (v0.4.0) y Fase 4 actualización (v0.5.0) según ROADMAP.
- Rotación del token GitHub (nota de gestión de cuenta).
