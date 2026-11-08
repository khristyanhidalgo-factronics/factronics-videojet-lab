# 📘 Sistema de notas de versión — Factronics Videojet Lab

Este es el sistema **permanente** de notas del proyecto. Las notas son la memoria a largo plazo
del proyecto: se crean, se conservan y se publican; **nunca se borran ni se reescriben**.

## Los 5 tipos de nota (regla establecida por el proyecto)

| Tipo | Archivo | ¿Cuándo se escribe? | ¿Qué contiene? |
|---|---|---|---|
| **PLAN** | `versions/vX.Y.Z/PLAN-vX.Y.Z.md` | **Antes** de empezar la versión | Todo lo que se **va a hacer** en esa versión, con criterios de aceptación y qué queda fuera de alcance |
| **BITÁCORA** | `versions/vX.Y.Z/BITACORA-vX.Y.Z.md` | **Durante** la versión | Registro cronológico de lo que se va **haciendo**, paso a paso, con fechas |
| **HECHO** | `versions/vX.Y.Z/HECHO-vX.Y.Z.md` | Durante la versión, se congela al publicar | Lo **terminado**, agrupado por fase, como lista verificable |
| **PENDIENTE** | `versions/vX.Y.Z/PENDIENTE-vX.Y.Z.md` | Durante la versión, se congela al publicar | Lo que **faltó por hacer**. Alimenta directamente la siguiente versión |
| **ROADMAP** | `versions/ROADMAP.md` (global) | Siempre vivo + minuto congelado `versions/vX.Y.Z/ROADMAP-vX.Y.Z.md` al publicar | Lo que se hará en **versiones futuras**, priorizado |

## Reglas no negociables

1. **Nunca se borra una nota publicada.** Los errores se corrigen en la nota de la versión siguiente.
2. Cada versión crea su carpeta `versions/vX.Y.Z/` con PLAN, BITÁCORA, HECHO y PENDIENTE.
3. Al publicar una versión se **congela**: la BITÁCORA y el HECHO quedan con su contenido final,
   el PENDIENTE se usa como base del PLAN de la siguiente versión, y se saca una copia
   congelada del ROADMAP (`ROADMAP-vX.Y.Z.md`) dentro de la carpeta de la versión.
4. `versions/INDICE.json` mantiene el índice maestro de todas las versiones para la landing.
5. `CHANGELOG.md` (raíz) resume cada versión con enlaces a sus notas.
6. Las notas se **publican** en el proyecto: la landing (`docs/`) enlaza siempre a las notas de
   la versión en desarrollo y al historial completo en GitHub.
7. Idioma de las notas: **español** (idioma principal del proyecto).
