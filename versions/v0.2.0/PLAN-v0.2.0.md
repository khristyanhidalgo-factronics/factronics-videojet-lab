# 🗺️ PLAN — v0.2.0 · App web offline (PWA)

> Alcance y criterios de aceptación de la versión **v0.2.0** (Fase 2 del proyecto).
> Se congela al publicar la versión; los avances se registran en la BITÁCORA v0.2.0.

## Objetivo
Entregar la **app web offline (PWA)** que use los datasets ya construidos (Fase 1) para
estudiar, buscar partes, calcular consumos y practicar exámenes por niveles — en
**español, inglés y portugués**, con tema claro/oscuro y funcionamiento **100% sin internet**.

## Alcance funcional (alpha → estable v0.2.0)
1. **Estudiar**
   - Tintas CIJ: bases químicas, color, curvas y fichas SDS (composición con CAS/%, propiedades).
   - Ribbons TTO: 64 grados (PN, color, velocidad, durabilidad, tipo, film) y 694 ítems.
   - LÁSER: 21 modelos documentados y partes `AL-` (enlazado al buscador).
   - CIJ: 204 números de parte de 6 IPL de la serie 1000 (1210/1510, 1220/1520,
     1520E, 1610 DH, 1620E, 1650/1650 UHS HR), con estado y modelos.
   - Mantenimiento: documentos y tareas con intervalo (estado borrador visible).
2. **Buscar** unificado: partes (2.894: TTO + CIJ + LÁSER), tintas, códigos de error (231),
   ribbons y mantenimiento, con filtros por tipo.
3. **Calcular**: consumo de solvente CIJ por curva oficial (10–40 °C), interpolación por
   temperatura, horas por litro y por cartucho, y costo/hora con precio del solvente.
4. **Examen** por 5 niveles y N preguntas, **generadas de datos reales** (tinta→base,
   ribbon→color, código→tecnología, parte CIJ→descripción, consumo de referencia,
   CAS→componente), corrección con referencia a la fuente e historial local.
5. **i18n** es/en/pt para la interfaz; **tema** claro/oscuro/sistema; **offline** vía
   service worker; instalación como PWA (manifest + icono).

## Criterios de aceptación
- La app abre desde GitHub Pages y funciona sin red tras la primera visita.
- Todos los datos mostrados llevan su **estado** (verificado/borrador/sin-datos) y la
  app **no inventa** información: las preguntas se derivan de datasets existentes.
- Exámenes de los 5 niveles generan preguntas válidas con distractores del mismo dominio.
- La calculadora interpola la curva y coincide con la referencia del documento en los
  puntos tabulados (verificación con VJ1210/V401 @30 °C = 11,2 ml/h).
- Notas de versión publicadas (4 tipos + ROADMAP global) y landing actualizada.

## Fuera de alcance de v0.2.0 (pasa a v0.3.0+)
- Página pública de notas (`docs/notas.html`) y CI de validadores JSON.
- Exportar/importar copia de seguridad completa y QR offline.
- Temas festivos completos por país (solo base de tema claro/oscuro/sistema).
- APK Android (v0.4.0) y sistema de actualización (v0.5.0).
