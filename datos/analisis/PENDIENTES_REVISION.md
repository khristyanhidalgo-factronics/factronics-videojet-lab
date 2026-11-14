# Pendientes de revision documental

> Generado por `tools/generar_revision_pendientes.py` el 2026-11-13.
> **Revisado el 2026-11-14** contra las paginas renderizadas de los IPL
> 1550/1650/1710. Los 5 conflictos quedaron documentados: 1 sinonimo
> promovido y 4 ambiguedades de fuente conservadas con descripcion alterna.
> El resto de los P/N OCR sigue en `borrador-decodificado`.

## Tablero

| Pendiente | Cantidad | Estado | Artefacto |
|---|---|---|---|
| P/N del OCR 1550/1710 | 193 | `borrador-decodificado` | `partes_cij_ocr_revision.csv` |
| Registros OCR con P/N | 277 | 275 apariciones unicas | `partes_cij_ocr_apariciones.csv` |
| Conflictos de descripcion | 5 | revisados: 1 sinonimo + 4 ambiguedades | `conflictos_cij_ocr.md` |
| Avisos de velocidades | 56 | valor impreso conservado | `velocidades_cij_avisos.csv` |
| Items sin P/N | 336 | `sin-pn` | `items_sin_pn.csv` |
| Partes TTO | 120 | `verificado` | `partes_tto_cotejo.csv` |

## Conflictos revisados (2026-11-14)

P/N con dos descripciones en el documento original: **395898, 395899, 399474, 399475, SP234081**.

- **399474**: sinonimo confirmado (Dry Air Kit Assembly / Air Dryer Assembly); promovido a `verificado` con alias.
- **395898, 395899, 399475, SP234081**: el documento imprime dos descripciones para el mismo P/N; se conservan ambas como evidencia (`d_alt`) y quedan fuera del banco por ambiguedad.

No quedan conflictos pendientes de revision. Ver `conflictos_cij_ocr.md` para la pagina, tabla e item de cada aparicion.

## Como revisar

1. Abrir `partes_cij_ocr_revision.csv` y filtrar `nuevo = si` para priorizar;
   los 5 conflictos ya estan revisados y documentados.
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
