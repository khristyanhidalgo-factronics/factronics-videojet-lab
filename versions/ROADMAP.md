# 🗺️ ROADMAP — Factronics Videojet Lab

> Documento **vivo** y acumulado: lo que se hará en versiones futuras.  
> Al publicar una versión se congela una copia en `versions/vX.Y.Z/ROADMAP-vX.Y.Z.md`.
> Última actualización: 2026-11-14.

## Camino hacia la v1.0.0 (publicación estable)

| Versión | Meta principal | Incluye |
|---|---|---|
| **v0.1.0** (publicada) | **Fundación** | Estructura, sistema de notas (5 tipos), landing en Pages, catálogo semilla, logo único, repo+push+Pages |
| **v0.2.0** (en desarrollo, `alpha-37`) | **Datos reales + app web beta** | Fuentes TTO/CIJ/LÁSER, OCR 1550/1710, catálogo verificado, PWA con examen de 5 niveles, bancos por tecnología, buscador (partes, tintas, solventes, SDS, errores, ribbons, mantenimiento), calculadora y **es/en/pt/it/zh** |
| **v0.3.0** | **App web completa** | Calculadoras (consumo/costo/comparador), perfiles/historial, copia de seguridad JSON, temas festivos (Venezuela base + extensión), QR offline, 100% offline comprobado |

## Estado actual (2026-11-14)

- **App:** `alpha-37` / build 53, publicada en Pages y verificada en vivo.
- **Notas:** build 54, con índice SHA-256 y este ROADMAP actualizado.
- **Datos:** 802 curvas de solvente, 564 tintas, 2.986 partes, 64 grados + 694
  ítems de ribbon, 1773 componentes SDS y 266 velocidades CIJ.
- **Calidad:** suite completa en CI, auditoría de 75.000 preguntas del examen y
  pruebas de bancos, búsquedas, láser y notas.
- **Siguiente no bloqueado:** prueba en dispositivo real, más variedad de
  mantenimiento cuando el OCR lo permita y revisión de textos de interfaz.
- **Bloqueado por revisión humana:** P/N OCR 1550/1710, 5 conflictos CIJ, 266
  velocidades y 56 avisos, partes TTO dudosas, títulos de boletines y estilo
  IT/ZH.
- **Bloqueado por entorno:** APK Android (sin herramientas), prueba en
  dispositivo real y rotación de tokens.
| **v0.4.0** | **App Android nativa** | Kotlin + Compose + Material 3 + Material You, festividades, minSdk 24, pruebas JVM paralelas a la web |
| **v0.5.0** | **Actualizaciones** | `version.json` + SHA-256, aviso de nueva versión, keystore persistente (conserva datos), instalación sobreinstalable |
| **v1.0.0** | **🎉 Primera release estable** | Pages y artefactos verificados con hash, APK firmada en GitHub Releases, notas congeladas, QA en modo avión |

## Después de la v1.0.0 (ideas priorizadas)

- **v1.1.0** — Más festividades/países; certificados PDF/PNG con QR de verificación pública; certificación de intentos.
- **v1.2.0** — Nuevas tecnologías: **TIJ, LPA (Print & Apply), Large Character, Labeling, Software CLARiSUITE/CLARiTY** — cada una con su canal de contenido y su banco de preguntas (sin mezclar bancos).
- **v2.0.0** — Funciones sociales opt-in (ranking con alias, sin correos públicos), sincronización opcional, backup en nubes; backend a decidir (Supabase/Firebase) SOLO si el dueño lo aprueba.
- **v2.1.0** — Videos educativos animados (posible uso del motor ManimGX sugerido por el dueño) para principios de CIJ/TTO/Láser, incrustados offline.
- **Permanente** — Más idiomas (it, zh…), amoled/temas extra, tablet/landscape, exportador para instructores.

## Regla del roadmap

Cada PLAN de versión toma su alcance desde el **PENDIENTE** de la versión anterior y las
prioridades aquí registradas. El dueño (Khristyan Hidalgo) tiene la palabra final sobre prioridades.
