# ✅ HECHO — v0.1.0 · Fundación del proyecto

> Lista verificable de lo **terminado**. Se acumula durante la versión y se congela al publicar.

## Sistema de notas
- [x] Sistema de 5 notas creado y documentado en `versions/CONVENCIONES.md` (PLAN, BITÁCORA, HECHO, PENDIENTE, ROADMAP).

## Documentación base
- [x] `PLAN-v0.1.0.md` escrito antes de empezar (con criterios de aceptación y mapa de fuentes).
- [x] README.md completo (qué es, tecnologías, niveles, sistema de notas, estructura, créditos).
- [x] LICENSE MIT (2026, Khristyan Hidalgo — Factronics Venezuela).
- [x] SECURITY.md y CONTRIBUTING.md.
- [x] .gitignore (Android, Node, secretos, APK de build).

## Datos
- [x] `datos/catalogo.json` semilla: TTO (6 modelos), CIJ (18 modelos de la serie 1000 VJ y 1700/1880), tintas documentadas (V471, V4250, V4263, V4264), consumibles (solventes por modelo), 5 niveles de examen, idiomas, festividades base Venezuela, fuentes locales descritas (sin rutas personales).

## Interfaz
- [x] Landing pública `docs/index.html`: tema claro/oscuro/sistema con persistencia, animaciones al hacer scroll, secciones de características, versión actual, notas (5 tipos enlazadas), roadmap y descargas.
- [x] Logo único del proyecto dibujado a mano como **SVG** (`docs/assets/logo.svg`), integrado al landing y favicon.

## Publicación (fundación)
- [x] Repositorio de GitHub creado y sincronizado con push inicial (commit `3aea8f8`): <https://github.com/khristyanhidalgo-factronics/factronics-videojet-lab>
- [x] GitHub Pages activo (rama `main`, carpeta `/docs`) → <https://khristyanhidalgo-factronics.github.io/factronics-videojet-lab/>
- [x] Notas de versión live en el repo y enlazadas desde la landing (publicadas).

## Fase 1 — Extracción de datos (en progreso)
- [x] Inventario verificado de fuentes (recuentos y nombres de archivo por carpeta clave).
- [x] `tools/leer_excel.py` corregido (detección automática de salida `.json`) y probado con 3 Excel reales.
- [x] `tools/leer_pdf.py` (PDF→texto sin dependencias) creado y probado con 4 PDFs reales.
- [x] `datos/extraccion/` con 7 extracciones reales (3 Excel TTO + 4 PDFs CIJ), limpiadas de bytes NUL.
- [x] `tools/estructurar_tto.py` → **`datos/partes_tto.json`**: 120 números de parte únicos TTO 6330/6530, anchos 32/53/107 mm derivados de la descripción, descripciones conservadas por fuente (pt/es/en), spares recomendados por flota (5/10/20/40 equipos). Estado: **borrador**.
- [x] `tools/estructurar_solvente.py` → **`datos/cij_uso_solvente.json`**: VJ1210 con V401 (base MEK) — curva completa 10–40 °C (5,1 → 16,7 ml/hr), cuadro 11,2 ml/hr @30 °C, 89 hrs por litro, 750 ml = 67 hrs. Referencia cruzada interna: coincide. Estado: **verificado**.
- [x] `datos/catalogo.json` actualizado: estado «en-extraccion», `dataset_vinculos` a ambos datasets, ficha **V4250** en borrador con aviso de extracción parcial, y avisos honestos (tintas: no hay Excel; 2 PDFs tabulares quedaron cifrados y no se usan).
