# Conflictos de descripción en partes CIJ

> Evidencia leída de los IPL originales. No se elige una descripción por
> consenso ni se reconstruye el dato: el P/N queda en estado `borrador` y con
> `conflicto_descripciones: true`. La app muestra «descripciones en conflicto».

| P/N | Descripción A | Documento / tabla | Descripción B | Documento / tabla |
|---|---|---|---|---|
| **399239** | `Filter Cover (IP55)` | 1210/1510 · Table 10-5: Ink Compartment · item 28 | `IP55 filter kit spares` | 1220/1520 · Table 10-5: Ink Compartment |
| **399474** | `Air Dryer Assembly` | 1620E · Table 10-9: Accessories | `Dry Air Kit Assembly` | 1650/1650 UHS · Table 8: Accessories |
| **399475** | `PCB 4 Assembly` | 1610 DH · Table 11-2: Electronics Compartment · item 13; 1620E · Table 10-3 · item 37; 1650/1650 UHS · Table 3 · item 35 | `25 way I/O (PCB 4) Cable Kit` | 1620E · Table 10-9: Accessories · item 84*; 1650/1650 UHS · Table 8: Accessories · item 78* |

## Lectura

- **399239**: el 1210/1510 imprime `Filter Cover (IP55)` en la fila del
  compartimiento de tinta; el 1220/1520 usa `IP55 filter kit spares` para el
  mismo número. Ambas son descripciones impresas, no una reconstrucción.
- **399474**: el 1620E lo lista como `Air Dryer Assembly`; el 1650/1650 UHS
  como `Dry Air Kit Assembly`. El P/N es el mismo; el nombre cambia entre
  manuales.
- **399475**: tres tablas de electrónica lo listan como `PCB 4 Assembly`; dos
  tablas de accesorios lo listan como `25 way I/O (PCB 4) Cable Kit`. La
  descripción canónica del JSON es la más frecuente (`PCB 4 Assembly`), pero
  el estado sigue siendo `borrador` por el conflicto.

## Regla aplicada

`tools/estructurar_partes_cij.py` compara las descripciones con
`desc_compatible` (igualdad, contención o Jaccard ≥ 0,8). Si el mismo P/N
aparece con descripciones incompatibles, marca `conflicto_descripciones` y
degrada el estado a `borrador` aunque la mayoría de los documentos coincida.
`tools/auditar_partes_cij.py` confirma además que estas cuatro apariciones son
las únicas cuya descripción canónica no está en el bloque de origen.
