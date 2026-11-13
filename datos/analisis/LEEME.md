# Análisis de partes CIJ

Esta carpeta contiene evidencia de revisión, no datos nuevos del manual. Todos
los archivos se derivan de `datos/partes_cij.json` y de los IPL originales; no
modifican el dataset ni reconstruyen números de parte.

| Archivo | Qué contiene |
|---|---|
| `items_sin_pn.csv` | 801 ítems sin P/N agrupados por descripción normalizada (193 descripciones únicas), con categoría heurística, apariciones, modelos, tablas, grupos e ítems. |
| `items_sin_pn_resumen.json` | Totales y conteos por categoría/documento de los 801 ítems sin P/N. |
| `auditoria_partes_cij.csv` | 1.397 registros (596 apariciones de partes + 801 ítems sin P/N) comprobados contra su bloque y su línea del PDF: P/N en línea/celda, descripción base en la ventana de la fila (±32 pt) y cantidad de la última columna. |
| `auditoria_partes_cij_resumen.json` | Resumen de la auditoría: 0 P/N fuera de línea, 0 cantidades distintas, 4 descripciones no localizadas (los 3 P/N en conflicto). |
| `conflictos_cij.md` | Evidencia de los 3 P/N con descripciones incompatibles entre manuales: 399239, 399474 y 399475. |
| `partes_cij_ocr_revision.csv` | 193 P/N del OCR de los IPL 1550/1710, con `nuevo` (92), conflicto, modelos, páginas, tablas y correcciones OCR. |
| `partes_cij_ocr_apariciones.csv` | 275 apariciones únicas (277 registros OCR) con documento, página, tabla, ítem, cantidad, descripción y P/N OCR. |
| `conflictos_cij_ocr.md` | Evidencia de los 5 P/N con descripciones incompatibles en el OCR: 395898, 395899, 399474, 399475 y SP234081. |
| `velocidades_cij_avisos.csv` | 56 calculadores con aviso de boquilla (22), modelo (31) o fuente (3); conserva el valor impreso. |
| `velocidades_cij_avisos.md` | Resumen de los 56 avisos y de las 5 notas documentadas de boquilla/modelo/fuente. |
| `PENDIENTES_REVISION.md` | Tablero único de revisión: 193 P/N OCR, 5 conflictos, 56 avisos, 336 ítems sin P/N y 120 partes TTO verificadas. |
| `revision_pendientes_resumen.json` | Conteos legibles por máquina de los pendientes y sus artefactos. |

## Regenerar

```bat
python tools\revisar_items_sin_pn.py
python tools\auditar_partes_cij.py
python tools\generar_revision_pendientes.py
```

`auditar_partes_cij.py` vuelve a extraer los 6 IPL, por lo que tarda varios
minutos. No requiere instalar nada: usa el extractor visual del proyecto.

## Criterios

- **Estado honesto:** `verificado` solo si ≥2 documentos coinciden en una
  descripción compatible; `borrador` si aparece en uno solo o si hay conflicto;
  `sin-pn` para hardware sin número impreso.
- **Sin reconstrucción:** los ítems sin P/N se conservan tal como están
  impresos (por ejemplo, `100 m Castor` en el 1620E). No se inventan P/N ni se
  corrigen textos dudosos.
- **Auditoría:** una alerta es una candidata a revisión visual, no una
  corrección automática.
