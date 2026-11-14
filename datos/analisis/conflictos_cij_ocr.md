# Conflictos de descripcion en partes CIJ (OCR 1550/1710)

> Evidencia leida de los IPL 1550 y 1710. **Revisado el 2026-11-14** contra
> las paginas renderizadas de los IPL 1550, 1650 y 1710. No se elige una
> descripcion por heuristica: cuando el documento imprime dos, se conservan
> ambas; la app muestra la primaria y la alterna (`d_alt`). El unico sinonimo
> confirmado (399474) se promovio a `verificado`; los otros 4 quedan fuera del
> banco por ambiguedad de fuente.

| P/N | Descripcion principal | Descripciones detectadas | Modelos |
|---|---|---|---|
| 395898 | Ethernet Connector Kit Spares | Ethernet Connector Kit Spares / USB A-B BULKHEAD | 1550 |
| 395899 | USB Connector Kit Spares | ETHERNET BULKHEAD / USB Connector Kit Spares | 1550 |
| 399474 | Dry Air Kit Assembly | Air Dryer Assembly / Dry Air Kit Assembly | 1550, 1710 |
| 399475 | PCB 4 Assembly - I/O 25 way (Optional) | 25 way I/O (PCB 4) Cable Kit / PCB 4 Assembly - I/O 25 way (Optional) | 1710 |
| SP234081 | Filter Element | Fan Filter / Filter Element | 1710 |

## Evidencia por aparicion

### 395898 — Ethernet Connector Kit Spares

| Documento | Pagina | Tabla | Item | Descripcion | P/N OCR | Correcciones |
|---|---|---|---|---|---|---|
| 1550 - Illustrated Parts List.pdf | 1-16 | Table 3: Electronics Compartment (Continued) | 35 | USB A-B BULKHEAD | 395898 | — |
| 1550 - Illustrated Parts List.pdf | 1-52 | Table 1-9: Power Cord |  | Ethernet Connector Kit Spares | 395898 | — |

**Lectura (revisada):** el IPL 1550 imprime USB A-B BULKHEAD en 1-16 y Ethernet Connector Kit Spares en 1-52; el 1650 repite el mismo cruce. Se conservan ambas; primaria = USB A-B BULKHEAD, alterna = Ethernet Connector Kit Spares. Fuera del banco por ambiguedad de fuente.

### 395899 — USB Connector Kit Spares

| Documento | Pagina | Tabla | Item | Descripcion | P/N OCR | Correcciones |
|---|---|---|---|---|---|---|
| 1550 - Illustrated Parts List.pdf | 1-16 | Table 3: Electronics Compartment (Continued) | 36 | ETHERNET BULKHEAD | 395899 | — |
| 1550 - Illustrated Parts List.pdf | 1-52 | Table 1-9: Power Cord |  | USB Connector Kit Spares | 395899 | — |

**Lectura (revisada):** el IPL 1550 imprime ETHERNET BULKHEAD en 1-16 y USB Connector Kit Spares en 1-52; el 1650 repite el mismo cruce. Se conservan ambas; primaria = ETHERNET BULKHEAD, alterna = USB Connector Kit Spares. Fuera del banco por ambiguedad de fuente.

### 399474 — Dry Air Kit Assembly

| Documento | Pagina | Tabla | Item | Descripcion | P/N OCR | Correcciones |
|---|---|---|---|---|---|---|
| 1550 - Illustrated Parts List.pdf | 49 | Table 8: Accessories |  | Dry Air Kit Assembly | 399474 | — |
| 1710_IPL(ENG).pdf | 44 | Table 10-7: Accessories |  | Air Dryer Assembly | 399474 | — |

**Lectura (revisada):** el IPL 1550 (p. 49) lo llama **Dry Air Kit Assembly** y el 1710 (p. 44) **Air Dryer Assembly**; es el mismo kit de accesorios. Se promueve a `verificado` con descripcion canonica Dry Air Kit Assembly y alias Air Dryer Assembly.

### 399475 — PCB 4 Assembly - I/O 25 way (Optional)

| Documento | Pagina | Tabla | Item | Descripcion | P/N OCR | Correcciones |
|---|---|---|---|---|---|---|
| 1710_IPL(ENG).pdf | 10-17 | Table 10-3: Electronics Compartment (Continued) | 40 | PCB 4 Assembly - I/O 25 way (Optional) | 399475 | \b1/0\b -> I/O |
| 1710_IPL(ENG).pdf | 10-47 | Table 10-7: Accessories (Continued) |  | 25 way I/O (PCB 4) Cable Kit | 399475 | \b1/0\b -> I/O |

**Lectura (revisada):** el IPL 1710 imprime PCB 4 Assembly - I/O 25 way (Optional) en 10-17 y 25 way I/O (PCB 4) Cable Kit en 10-47. Son dos items distintos con el mismo P/N impreso; se conservan ambas y queda fuera del banco por ambiguedad.

### SP234081 — Filter Element

| Documento | Pagina | Tabla | Item | Descripcion | P/N OCR | Correcciones |
|---|---|---|---|---|---|---|
| 1710_IPL(ENG).pdf | 10-28 | Table 10-5: Ink Compartment (Continued) | 31 | Filter Element | SP234081 | — |
| 1710_IPL(ENG).pdf | 10-29 | Table 10-5: Ink Compartment (Continued) | 36 | Fan Filter | SP234081 | — |

**Lectura (revisada):** el IPL 1710 imprime Filter Element en el kit IP55 (10-28) y Fan Filter en el ensamble del ventilador (10-29); se conservan ambas y queda fuera del banco por ambiguedad.
