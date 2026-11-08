# 🗺️ PLAN — v0.1.0 · Fundación del proyecto

> Escrito **antes** de empezar la versión (regla del sistema de notas).
> v0.1.0 es la versión fundacional: crea la estructura, las reglas y los cimientos.
> No incluye todavía la aplicación completa (eso llega en v0.2.0 → v1.0.0, ver `versions/ROADMAP.md`).

## Objetivo

Dejar el proyecto **fundado en GitHub y visible**: repositorio creado y sincronizado, sistema de
notas operando, landing publicada en GitHub Pages, catálogo semilla de datos basado en las fuentes
reales del dueño del proyecto, y logo único del proyecto.

## Tareas del alcance (Fase 0)

| # | Tarea | Criterio de aceptación |
|---|---|---|
| A | Sistema de notas de versión (PLAN/BITÁCORA/HECHO/PENDIENTE/ROADMAP) con convenciones | `versions/CONVENCIONES.md` escrito y aplicado desde el primer commit |
| B | Estructura del repositorio + README + LICENSE + SECURITY + CONTRIBUTING + .gitignore | Repositorio navegable y entendible por cualquier compañero |
| C | Catálogo semilla `datos/catalogo.json` | Contiene las tecnologías, modelos, tintas y niveles de examen reales extraídos de los documentos del dueño, marcando estado (verificado / borrador / por definir). **Sin datos inventados** |
| D | Landing pública `docs/index.html` con logo único | Publicada en GitHub Pages y funcional; enlaza a notas, roadmap y descargas |
| E | Usuario/repo: crear repositorio público, push inicial, habilitar Pages | Repo accesible; `https://<usuario>.github.io/factronics-videojet-lab/` respondiendo |
| F | Logo único del proyecto (SVG vectorial) | `docs/assets/logo.svg` usado en landing y disponible para la app |

## Fuera del alcance de v0.1.0 (planificado en ROADMAP)

- La aplicación web completa (exámenes, buscador de partes, calculadoras) → **v0.2.0 / v0.3.0**
- La app Android (APK) → **v0.4.0**
- Sistema de actualización con `version.json` + SHA-256 → **v0.5.0**
- Release estable v1.0.0 con APK firmada → **v1.0.0**

## Principios aplicados desde hoy

1. **Offline primero:** nada del proyecto depende de internet para funcionar; la red solo sirve para publicar/actualizar.
2. **Sin datos inventados:** si un dato no viene de las fuentes del dueño o de fuentes oficiales, se marca "por definir".
3. **Cero secretos en el repo:** ni tokens, ni claves de firma, ni datos personales en el código.
4. **Notas conservadas para siempre**, publicadas en el proyecto (esta versión las inaugura).

## Registro de fuentes reales del dueño (inventario de Fase 0)

- **CIJ:** carpetas `uso de solvente` (17 modelos con su uso de solvente), `velocidades cij`
  (velocidades por modelo/boquilla), `DOCUMENTOS VJ…` por modelo (manuales, boletines, diagramas,
  instrucciones, partes), `ILUSTRACION DE PARTES 1000VJ`, `LISTA DE PARTES RECOMENDADA 1000VJ`,
  `TINTAS CIJ EXCELLLL`, `INFORMACION TINTAS` (V471, V4250, V4263, V4264…).
- **TTO:** carpeta `TTO 6x30` (modelos 6210/6230/6320/6330/6420/6530) con `Partes-Pecas`, `Ribbons`,
  `Manuales`, `Boletines Tecnicos`, `Instrucciones`, `Software 63-6530`.
- **Láser:** carpeta `documentacion laser` (a extraer en Fase 1).

*Nota: las rutas completas de las carpetas locales del dueño no se publican en el repositorio
(privacidad); en el catálogo solo se registran las descripciones de cada fuente.*
