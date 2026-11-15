# 🎯 Factronics Videojet Lab

> Plataforma de estudio, exámenes, buscador de números de parte y calculadoras para las
> tecnologías de marcado e impresión **Videojet: TTO · CIJ · Láser**.
> **100% offline**: la web y la APK funcionan completamente sin internet.

| | |
|---|---|
| **Versión actual** | `v0.2.0-alpha` (`alpha-40`) — App web offline (ver [notas de versión](#--sistema-de-notas-de-versión)) |
| **Estado** | 🚧 En desarrollo activo |
| **Creador** | **Khristyan Hidalgo** — Técnico · [Factronics Venezuela](https://factronics.com.ve/) |
| **Licencia** | [MIT](LICENSE) |
| **Idiomas** | Español (principal) · English · Português · Italiano · 中文 |

---

## ¿Qué es?

Una aplicación moderna pensada para **hacer la vida más fácil a los compañeros** de Factronics
(usuarios nuevos, técnicos nuevos y el equipo de ventas):

1. **Estudiar** con la información de las 3 tecnologías Videojet organizada por niveles.
2. **Generar exámenes** por nivel: `Básico` → `Básico-Medio` → `Intermedio-Avanzado` → `Avanzado` → `Profesional`.
3. **Buscar números de parte** por tecnología / modelo / componente — por número de parte o por nombre.
4. **Calcular** consumo, costos y comparativas de consumibles (tintas CIJ, ribbons TTO) — útil para ventas.
5. Todo con **Material You 3** en Android (color según el fondo del dispositivo), **temas festivos**
   por fecha y país (Navidad, Halloween, San Patricio, Día de la Independencia, San Valentín,
   Día del Niño/Madre/Padre, vacaciones, vuelta a clases…), **animaciones** y modo claro/oscuro.

## Tecnologías cubiertas

| Tecnología | Modelos de arranque | Estado |
|---|---|---|
| **TTO** — Transferencia Térmica | 6210 · 6230 · 6320 · 6330 · 6420 · 6530 | 🟢 Datos y banco disponibles |
| **CIJ** — Inyección de Tinta Continua | VJ1210–1890 (18 modelos con datos de consumibles) | 🟢 Datos, curvas y bancos disponibles |
| **Láser** — Marcado Láser | 21 modelos documentados | 🟡 Partes sin P/N verificados |
| *(Futuras: TIJ, LPA, Large Character…)* | — | 📋 Roadmap |

## Entregables (a medida que avancen las versiones)

| Entregable | Estado | Dónde |
|---|---|---|
| 🌐 **Página principal** (landing) | ✅ Activa | [GitHub Pages](https://khristyanhidalgo-factronics.github.io/factronics-videojet-lab/) |
| 💻 **App web offline** (PWA) | ✅ alpha-40 | [App en vivo](https://khristyanhidalgo-factronics.github.io/factronics-videojet-lab/app/) · `docs/app/` |
| 📱 **APK Android nativa** | 🚧 v0.4.0 | [Releases](https://github.com/khristyanhidalgo-factronics/factronics-videojet-lab/releases) |

## 📘 Sistema de notas de versión

Cada versión documenta **sus 5 notas**, que se conservan **para siempre** y se publican aquí:

| Nota | Ruta |
|---|---|
| 🗺️ **PLAN** (lo que se va a hacer) | `versions/vX.Y.Z/PLAN-vX.Y.Z.md` |
| 🖊️ **BITÁCORA** (lo que se está haciendo) | `versions/vX.Y.Z/BITACORA-vX.Y.Z.md` |
| ✅ **HECHO** (lo que terminó) | `versions/vX.Y.Z/HECHO-vX.Y.Z.md` |
| ⏳ **PENDIENTE** (lo que faltó) | `versions/vX.Y.Z/PENDIENTE-vX.Y.Z.md` |
| 🗺️ **ROADMAP** (futuras versiones) | `versions/ROADMAP.md` |
| 📋 **CHANGELOG** (resumen por versión) | `CHANGELOG.md` |

Índice maestro: [`versions/INDICE.json`](versions/INDICE.json) · Convenciones: [`versions/CONVENCIONES.md`](versions/CONVENCIONES.md) · Historial: [`CHANGELOG.md`](CHANGELOG.md)

## Estructura del repositorio

```text
factronics-videojet-lab/
├─ docs/                 → GitHub Pages: landing + app offline
│  ├─ index.html         → Landing
│  ├─ app/               → PWA (index.html, datos.js, sw.js, banco_tto.js)
│  ├─ notas.html         → Notas publicadas con SHA-256
│  └─ assets/            → Logo y recursos propios
├─ datos/                → FUENTE ÚNICA de datos (catálogo JSON y análisis)
├─ versions/             → 🔒 Notas de versión (PLAN/BITÁCORA/HECHO/PENDIENTE/ROADMAP + índice)
├─ tools/                → Validadores, pruebas y scripts de publicación
├─ CHANGELOG.md          → Resumen permanente por versión
└─ version.json          → Manifiesto de versión pública
```

## Principios del proyecto

- **Offline primero** — cálculo, estudio, examen, historial y buscador funcionan sin internet.
- **Sin datos inventados** — solo datos de las fuentes del dueño o fuentes oficiales, con su estado.
- **Privacidad** — sin análisis, sin anuncios, sin cuentas; los datos nunca salen del dispositivo.
- **Notas inmutables** — el historial del proyecto no se borra nunca.
- **Cero secretos en el repo** — tokens y claves de firma viven fuera del repositorio.

## Aviso de marca

Proyecto independiente creado para uso interno del equipo de Factronics Venezuela.
Videojet® y sus marcas son propiedad de **Videojet Technologies Inc.** (una compañía de Danaher);
este proyecto no es oficial ni afiliado, y se basa en material técnico del equipo y en
documentación de acceso público para capacitación.

## Créditos

**Khristyan Hidalgo** — Técnico · Factronics Venezuela
Web de la empresa: <https://factronics.com.ve/>

## Licencia

[MIT](LICENSE) © 2026
