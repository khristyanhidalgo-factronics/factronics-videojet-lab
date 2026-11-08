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
- [x] **Uso de solvente CIJ al 100% (802/802 documentos)** → `datos/cij_uso_solvente.json`: **800 curvas `verificado`** (25 combos modelo/variante; clave = modelo+variante+tinta+base_del_nombre) con curva 10–40 °C, hrs/litro, cartucho y hrs/cartucho; **2 entradas `sin-datos-en-documento`** (VJ1880 V4238 MEK/Methanol y V4251 Methanol/Water, marcadas `#N/D` por el propio PDF). Duplicado real VJ1560/V461 resuelto por base del nombre (ETHANOL_ISOPROP y ETHYL_ACETATE: curvas distintas, ref 5,6 vs 8,0 ml/hr @30 °C). Herramientas: `lote_solvente.py`, `estructurar_solvente.py` (tolerante a fuentes subset y sufijos de tinta), `reconstruir_dataset_solvente.py` (reconstruye el dataset desde los .txt sin releer PDFs).
- [x] **IPL 1000VJ extraídos (9/9)** a `datos/extraccion/cij_ipl_*.txt` con `tools/lote_ipl.py` (+ `_lote_ipl_resumen.json`). Estado honesto del dato: **borrador** — fuentes subset desplazadas/fragmentadas; estracto evaluable en el resumen (bloques/carácteres/líneas).
- [x] **Decodificador calibrado v2 de fuentes subset** (`tools/decodificar_cipher_offset.py`, decisión por bloque, lexicon de control): 13 documentos procesados, salidas `*_dec.txt`; offset **+29** con evidencia en TS2205 V471-D / 98039 / IPL 1550 / IPL 1650 y frases reales vistas en la salida. Cobertura parcial (mezcla de fuentes) documentada.
- [x] **Inventario fichas QSS** `tools/inventario_fichas.py` → `datos/fichas_tintas_inventario.json`: 564 PDFs cruzados con sus extracciones; estados legible / texto-escaso / sin-texto-sacado / sin-extraccion (562 quedan `sin-texto-sacado`).
- [x] **`datos/cij_tintas.json` v1** (`tools/construir_cij_tintas.py`): 134 tintas CIJ con bases quimicas reales (desde `cij_uso_solvente.json` verificado), modelos con curva y fichas QSS asociadas; colores/industrias del brochure US en estado `borrador`; composición parcial V471-D en `borrador-decodificado`.
- [x] `datos/catalogo.json` actualizado: fuentes `cij-partes-1000vj` (decodificador v2 con corridas legibles) y `cij-tintas` (inventario 564 QSS + brochure US); vínculos `cij_tintas` y `fichas_tintas_inventario`; ficha V471 en `borrador-decodificado` con composición parcial.
- [x] **564/564 fichas QSS descifradas y extraidas** (`tools/leer_pdf_cifrado.py` v2: RC4-128 handler estandar + CMaps ToUnicode + ObjStm; `tools/lote_fichas_descifrado.py`): 17.449.653 chars legibles en `datos/extraccion/*_descifrado.txt`. Censo del cifrado: 562 RC4-128 + 2 sin cifrado (`datos/extraccion/_censo_cifrado_fichas.json`). Inventario `fichas_tintas_inventario.json`: 564/564 `legible-descifrado`.
- [x] **Composicion SDS estructurada** (`tools/estructurar_sds_fichas.py`): `datos/sds_composicion.json` - 547 de 563 fichas con seccion 3, **1.773 componentes** con CAS, porcentaje y clasificacion GHS, mas version/fecha de cada SDS. Estado: borrador (revision humana pendiente).
- [x] **`datos/cij_tintas.json` regenerado**: cada ficha QSS lleva su SDS (version, fecha, componentes); V471-D y V471-K v6.07 con 6 componentes cada una; 134 tintas / 132 con curvas verificadas.
- [x] Catalogo `datos/catalogo.json`: fuente cij-tintas con el descifrado completo (562 RC4 + 2 sin cifrado), vinculos `fichas_tintas_inventario` y `sds_composicion`, nota de fuentes actualizada.
- [x] **Extractor visual v3** (`tools/leer_pdf_cifrado.py --visual`): matrices Tm/cm + orden de lectura real; 564/564 fichas en `*_visual.txt` (17.274.230 chars). Inventario: 564/564 `legible-visual`.
- [x] **`datos/sds_propiedades.json`**: sección 9 de 561 fichas, 12.728 campos (pH, inflamación, ebullición, densidad, presión de vapor, viscosidad, volatilidad...), integrados por ficha en `cij_tintas.json`. Estado: borrador.
- [x] **Composición con CAS validado**: 1.773/1.773 componentes con dígito de control CAS correcto → `estado: verificado` por componente (`cas_valido`); 547 fichas con composición.
- [x] **Repositorio global `Proyecto-Simplicity-Global` registrado** como fuente: `datos/simplicity_global_inventario.json` (3/12 partes, 3 archivos clasificados por tecnología) + catálogo actualizado; alcance TTO/CIJ/LASER documentado.
- [x] **`datos/tto_ribbons.json`**: 64 grados de ribbon + 694 ítems de suministros + longitudes/anchos por impresora/grado + lógica de lote (chart oficial 2.5.26). Estado: verificado.
- [x] **`datos/laser_inventario.json`**: 1.908 archivos inventariados (1.253 PDFs); `tools/lote_laser.py` en marcha para extraer el texto de todos los PDFs con el extractor visual v3.
- [x] **Descifrado completo RC4/AES-128/AES-256** (`tools/leer_pdf_cifrado.py` v3: sAlT, hash 2.B, O/U hex): 27/27 documentos bloqueados recuperados (manuscritos Allprint AES/BNS, manual 6330/6530, instrucciones 463xxx).
- [x] **LÁSER: extracción completa** de 1.253 PDFs (1.165 OK / 28 escasos / 60 escaneados) + inventario de 1.908 archivos con estado por archivo.
- [x] **TTO: extracción completa** de 163 PDFs (156 OK / 7 sin texto) además del chart de ribbons estructurado.
- [x] **`datos/laser_modelos.json`**: 21 modelos LASER con archivos de evidencia y menciones; CO2 y fibra separados; terceros (ALLPRINT, sensores) aparte.
- [x] **`datos/tto_boletines.json`**: índice de 113 boletines con legibilidad medida y 63 títulos fiables.
- [x] **OCR nativo**: `tools/ocr_windows.ps1` + `tools/lote_laser_ocr.py` — 29 escaneados con JPEG procesados (17 con texto, +16.277 chars; 12 sin resultado).
