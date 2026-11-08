# Seguridad y privacidad — Factronics Videojet Lab

## Cómo reportar un problema

Escribe directamente al creador del proyecto:

**Khristyan Hidalgo** — <khristyan.hidalgo@factronics.com.ve>
(Técnico de campo — Factronics Venezuela · <https://factronics.com.ve/>)

Por favor incluye: descripción del problema, pasos para reproducirlo y versión del proyecto.

## Alcance

- La aplicación **no recopila, nunca, datos de los usuarios**: sin análisis, sin anuncios, sin
  cuentas ni telemetría. Toda la información (precios, historial, resultados) permanece en el
  dispositivo.
- La única comunicación de red de la APK (en versiones futuras) es la **verificación opcional de
  nueva versión** contra `version.json` del repositorio público. Se puede desactivar.

## Política de tokens y claves

- Los **tokens de GitHub** nunca se escriben en el repositorio (ni en el código, ni en notas,
  ni en logs). Se usan por variables de sesión y **se rotan si quedan expuestos en chats o
  documentos** (regla propia del proyecto).
- La clave de firma (keystore) de la APK vive **fuera del repositorio**, resguardada por el
  dueño; una copia de seguridad fuera del dispositivo es responsabilidad del dueño.
- Toda entrada de texto de usuario en las aplicaciones se valida y se escapa antes de
  mostrarla o exportarla.
