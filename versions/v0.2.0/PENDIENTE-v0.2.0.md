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
- [ ] Tablas de partes CIJ (`partes_cij`) tras OCR/revisión de la columna de números.
- [ ] Simplicity/EquivalenciaTintas: mapeo GID pendiente.
- [ ] Partes 4–12 del repo global `Proyecto-Simplicity-Global` (hoy 3/12).
- [ ] 31 escaneados láser sin JPEG (rasterizado/OCR si aportan).

## Después
- Fase 3 APK (v0.4.0) y Fase 4 actualización (v0.5.0) según ROADMAP.
- Rotación del token GitHub (nota de gestión de cuenta).
