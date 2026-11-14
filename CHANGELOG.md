# 📋 CHANGELOG — Factronics Videojet Lab

> Resumen de cambios por versión. La memoria completa y permanente vive en
> [`versions/`](versions/): **PLAN**, **BITÁCORA**, **HECHO**, **PENDIENTE** y
> **ROADMAP**. Las notas publicadas no se borran; los errores se corrigen en la
> versión siguiente.

## [v0.2.0-alpha] — En desarrollo

**Última app publicada:** `alpha-35` / build 49 · **Notas:** build 50 · 2026-11-14
**Objetivo:** app web offline (PWA) con los datos reales de TTO, CIJ y LÁSER,
examen por niveles, buscador y calculadoras en cinco idiomas.

### Añadido

- **PWA offline** en `docs/app/` con service worker, caché de 7 recursos y
  funcionamiento sin internet.
- **Examen de 5 niveles** con preguntas generadas y banco TTO de 372 preguntas.
- **Bancos por tecnología:** 124 P/N CIJ verificados, 120 P/N TTO verificados y
  266 velocidades CIJ con aviso de borrador decodificado.
- **Buscador** de partes, tintas, **solventes (802 curvas)**, **SDS (527 pares
  tinta|CAS)**, códigos de error, ribbons (64 grados + 694 ítems) y mantenimiento.
- **Calculadora CIJ** con 802 curvas y 800 referencias @30 °C; referencia
  VJ1210/V401 = 11,2 ml/h.
- **Cinco idiomas completos:** español, inglés, portugués, italiano y chino.
- **Historial de exámenes** con promedio ponderado, mejor resultado y borrado
  confirmado.
- **Respaldo JSON** de perfil, idioma, tema, historial y cuaderno de repaso.
- **Repaso espaciado**, cuaderno de errores y constancia con QR offline.
- **Tipos de pregunta SDS:** densidad, punto de inflamación, volatilidad, punto
  de ebullición y presión de vapor.
- **Tipo de pregunta de color de tinta** y **base química** con datos traducidos.
- **Ficha SDS** accesible desde cada resultado del buscador.

### Corregido

- **Contraste de preguntas y opciones:** las opciones usaban el color negro
  nativo del botón y quedaban casi invisibles en tema oscuro; ahora usan
  `var(--txt)` con contraste 14,10:1 (oscuro) y 17,85:1 (claro).
- **Base química:** se excluyeron las 3 tintas con dos bases para evitar
  respuestas ambiguas y se tradujo la respuesta en los 5 idiomas.

### Notas de la versión

- [PLAN](versions/v0.2.0/PLAN-v0.2.0.md)
- [BITÁCORA](versions/v0.2.0/BITACORA-v0.2.0.md)
- [HECHO](versions/v0.2.0/HECHO-v0.2.0.md)
- [PENDIENTE](versions/v0.2.0/PENDIENTE-v0.2.0.md)
- [ROADMAP global](versions/ROADMAP.md)

### Pendiente principal

La revisión humana de los P/N OCR 1550/1710 y de los 5 conflictos CIJ, los
avisos de velocidades, las partes TTO dudosas, el estilo IT/ZH, el banco LÁSER
sin P/N verificados, la APK y los temas festivos. El detalle está en el
[PENDIENTE](versions/v0.2.0/PENDIENTE-v0.2.0.md).

## [v0.1.0] — Fundación

**Publicada.** Base del proyecto: estructura del repositorio, sistema de notas
de 5 tipos, landing en GitHub Pages, catálogo semilla, logo único y primer
flujo de publicación.

- [PLAN](versions/v0.1.0/PLAN-v0.1.0.md)
- [BITÁCORA](versions/v0.1.0/BITACORA-v0.1.0.md)
- [HECHO](versions/v0.1.0/HECHO-v0.1.0.md)
- [PENDIENTE](versions/v0.1.0/PENDIENTE-v0.1.0.md)

## Sistema de notas

Cada versión conserva su carpeta `versions/vX.Y.Z/` con PLAN, BITÁCORA, HECHO y
PENDIENTE. El ROADMAP es global y se congela por versión al publicar. El índice
maestro con SHA-256 está en [`versions/INDICE.json`](versions/INDICE.json) y las
convenciones en [`versions/CONVENCIONES.md`](versions/CONVENCIONES.md).
