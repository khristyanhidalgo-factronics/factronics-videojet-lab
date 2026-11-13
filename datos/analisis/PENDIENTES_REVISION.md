# Pendientes de revision documental

> Generado por `tools/generar_revision_pendientes.py` el 2026-11-13.
> Esta carpeta es evidencia de revision: no modifica los datasets ni
> asciende estados. Los datos siguen en `borrador-decodificado` hasta
> que el dueno confirme contra el documento original.

## Tablero

| Pendiente | Cantidad | Estado | Artefacto |
|---|---|---|---|
| P/N del OCR 1550/1710 | 193 | `borrador-decodificado` | `partes_cij_ocr_revision.csv` |
| Registros OCR con P/N | 277 | 275 apariciones unicas | `partes_cij_ocr_apariciones.csv` |
| Conflictos de descripcion | 5 | requiere revision humana | `conflictos_cij_ocr.md` |
| Avisos de velocidades | 56 | valor impreso conservado | `velocidades_cij_avisos.csv` |
| Items sin P/N | 336 | `sin-pn` | `items_sin_pn.csv` |
| Partes TTO | 120 | `verificado` | `partes_tto_cotejo.csv` |

## Conflictos que requieren confirmacion

P/N con dos descripciones incompatibles en el OCR: **395898, 395899, 399474, 399475, SP234081**.

Ver `conflictos_cij_ocr.md` para la pagina, tabla e item de cada
aparicion. No se elige una descripcion automaticamente.

## Como revisar

1. Abrir `partes_cij_ocr_revision.csv` y filtrar `conflicto = si` o
   `nuevo = si` para priorizar.
2. Para cada P/N dudoso, abrir la pagina indicada en
   `partes_cij_ocr_apariciones.csv` y comparar la descripcion impresa
   con `descripcion` y `descripcion_ocr`.
3. No reconstruir P/N a mano. Si el OCR no alcanza, dejar el estado
   actual y anotar la duda.
4. Para velocidades, revisar `velocidades_cij_avisos.md`: el valor
   impreso ya prevalece sobre el nombre de archivo.

## Criterios

- `verificado`: P/N confirmado y descripcion oficial coincidente.
- `borrador-decodificado`: lectura OCR/decodificada pendiente de
  confirmacion humana.
- `sin-pn`: hardware sin numero impreso; no se inventa.
- La traduccion es un dato separado; el texto original se conserva.

## Resumen legible por maquina

`revision_pendientes_resumen.json`.
