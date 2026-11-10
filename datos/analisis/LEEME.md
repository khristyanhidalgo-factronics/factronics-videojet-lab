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

## Regenerar

```bat
python tools\revisar_items_sin_pn.py
python tools\auditar_partes_cij.py
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
