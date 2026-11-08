# Cómo contribuir — Factronics Videojet Lab

Gracias por querer ayudar a los compañeros. Este proyecto tiene reglas simples y firmes:

## Reglas

1. **Offline primero** — nada del proyecto puede volverse dependiente de internet para funcionar.
2. **Sin datos inventados** — si agregas datos técnicos (partes, velocidades, consumibles),
   deben venir de una fuente real (documentos del equipo o documentación oficial). Indica la
   fuente y marca el estado: `verificado` / `borrador` / `por definir`.
3. **Las notas de versión no se tocan** — nunca borrar ni reescribir notas publicadas
   (`versions/`). Las correcciones van en la versión siguiente.
4. **Idioma principal: español.** Las plataformas tienen es/en/pt, nada de textos hardcodeados.
5. **Cero secretos** — no subir tokens, keystore, ni datos de clientes.
6. **Sin dependencias externas en runtime** — la app web es un producto autosuficiente.

## Flujo

1. Propón en un issue (o por mensaje directo a Khristyan) qué quieres agregar.
2. Los cambios de datos pasan por `datos/` (fuente única) — no duplicar datos en el código.
3. Cada versión nueva empieza con su nota **PLAN** en `versions/vX.Y.Z/` — seguimiento por
   BITÁCORA + HECHO + PENDIENTE.

> Este proyecto es interno del equipo de Factronics Venezuela. ¡Contamos contigo para hacerlo mejor!
