#!/usr/bin/env node
'use strict';
/*
 * Auditoria del banco de partes CIJ de la app.
 *
 * Extrae de docs/app/index.html las funciones reales del generador
 * (partesCijVerificadas, candidatosPartes, generarPreguntaPartes, opciones y
 * tr) y las ejecuta contra docs/app/datos.js en los cinco idiomas.
 *
 * Comprueba, para cada pregunta:
 *   - cuatro opciones distintas;
 *   - la respuesta correcta esta incluida una sola vez;
 *   - no quedan marcadores {n} ni {d} sin sustituir;
 *   - las 5 descripciones ambiguas nunca generan preguntas descripcion->P/N.
 *
 * Uso:
 *   node tools/auditar_banco_partes.js
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const RAIZ = path.resolve(__dirname, '..');
const IDIOMAS = ['es', 'en', 'pt', 'it', 'zh'];
const CLAVES = ['fuente_partes', 'q_part_pn', 'q_part_desc',
                'ref_partes', 'partes_nota'];
const AMBIGUAS = [
  'Filter Element',
  'Filter Cover',
  'Beacon Assembly',
  'Ribbon Cable Spare Kit',
  'Printhead Photocell Holder 6 mm, 8 mm, 18 mm',
];

function leer(ruta) {
  return fs.readFileSync(path.join(RAIZ, ruta), 'utf8');
}

function extraerFuncion(src, nombre) {
  const inicio = src.indexOf('function ' + nombre + '(');
  if (inicio < 0) throw new Error('no se encontro function ' + nombre);
  const llave = src.indexOf('{', inicio);
  let profundidad = 0;
  let comilla = null;
  let escape = false;
  let linea = false;
  let bloque = false;
  for (let i = llave; i < src.length; i++) {
    const c = src[i];
    const siguiente = src[i + 1];
    if (linea) { if (c === '\n') linea = false; continue; }
    if (bloque) {
      if (c === '*' && siguiente === '/') { bloque = false; i++; }
      continue;
    }
    if (comilla) {
      if (escape) { escape = false; continue; }
      if (c === '\\') { escape = true; continue; }
      if (c === comilla) comilla = null;
      continue;
    }
    if (c === "'" || c === '"' || c === '`') { comilla = c; continue; }
    if (c === '/' && siguiente === '/') { linea = true; i++; continue; }
    if (c === '/' && siguiente === '*') { bloque = true; i++; continue; }
    if (c === '{') profundidad++;
    if (c === '}') {
      profundidad--;
      if (profundidad === 0) return src.slice(inicio, i + 1);
    }
  }
  throw new Error('function ' + nombre + ' sin cierre');
}

function extraerI18N(src) {
  const i18n = {};
  IDIOMAS.forEach(idioma => { i18n[idioma] = {}; });
  for (const idioma of IDIOMAS) {
    const patron = new RegExp(
      'Object\\.assign\\(I18N\\.' + idioma + ', \\{([\\s\\S]*?)\\n\\}\\);', 'g');
    let bloque;
    while ((bloque = patron.exec(src))) {
      for (const clave of CLAVES) {
        const valor = bloque[1].match(
          new RegExp('(?:^|\\n)\\s*' + clave + "\\s*:\\s*'((?:\\\\.|[^'\\\\])*)'"));
        if (valor) i18n[idioma][clave] = valor[1].replace(/\\'/g, "'");
      }
    }
  }
  return i18n;
}

function principal() {
  const datosTxt = leer('docs/app/datos.js');
  const contextoDatos = {window: {}};
  vm.createContext(contextoDatos);
  vm.runInContext(datosTxt, contextoDatos);
  const D = contextoDatos.window.DATOS;

  const html = leer('docs/app/index.html');
  const script = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/);
  if (!script) throw new Error('no se encontro el script principal de index.html');
  const src = script[1];
  const i18n = extraerI18N(src);

  const faltan = [];
  for (const idioma of IDIOMAS) {
    for (const clave of CLAVES) {
      if (!i18n[idioma][clave]) faltan.push(idioma + '.' + clave);
    }
  }
  if (faltan.length) throw new Error('faltan claves i18n: ' + faltan.join(', '));

  let LANG = 'es';
  const t = k => (i18n[LANG] && i18n[LANG][k]) || i18n.es[k] || k;
  const contexto = {D, LANG, t, Map, Set, console};
  contexto.tr = function (s) {
    if (!s) return s;
    const clave = String(s).replace(/\s+/g, ' ').trim();
    const m = D.tr && D.tr[clave];
    return (m && m[LANG]) || s;
  };
  vm.createContext(contexto);
  const codigo = ['opciones', 'partesCijVerificadas', 'candidatosPartes',
                  'generarPreguntaPartes']
    .map(nombre => extraerFuncion(src, nombre)).join('\n');
  vm.runInContext(codigo, contexto);

  let fallos = 0;
  const fallo = msg => {
    fallos++;
    if (fallos <= 20) console.error('FALLO: ' + msg);
  };

  const partes = contexto.partesCijVerificadas();
  const candidatos = contexto.candidatosPartes();
  const pn = candidatos.filter(c => c.tipo === 'pn');
  const desc = candidatos.filter(c => c.tipo === 'desc');
  console.log('Banco: %d P/N, %d descripciones inequivocas, %d candidatos',
              partes.length, desc.length, candidatos.length);
  if (partes.length !== 124) fallo('se esperaban 124 P/N verificados');
  if (pn.length !== 124) fallo('se esperaban 124 preguntas P/N->descripcion');
  if (desc.length !== 113) fallo('se esperaban 113 preguntas descripcion->P/N');

  for (const idioma of IDIOMAS) {
    LANG = idioma;
    const descripciones = new Set(partes.map(p => contexto.tr(p.d)));
    const pns = new Set(partes.map(p => p.n));
    if (descripciones.size !== 118) {
      fallo(idioma + ': se esperaban 118 descripciones traducidas');
    }
    if (pns.size !== 124) fallo(idioma + ': se esperaban 124 P/N unicos');
    const ambiguas = new Set(AMBIGUAS.map(d => {
      const p = partes.find(x => x.d === d);
      return p ? contexto.tr(p.d) : d;
    }));
    for (const c of desc) {
      const d = contexto.tr(c.p.d);
      if (ambiguas.has(d)) {
        fallo(idioma + ': descripcion ambigua en candidato desc->P/N: ' + d);
      }
      const mismos = partes.filter(x => contexto.tr(x.d) === d);
      if (new Set(mismos.map(x => x.n)).size !== 1) {
        fallo(idioma + ': descripcion sin P/N unico: ' + d);
      }
    }
    for (const c of candidatos) {
      for (let k = 0; k < 25; k++) {
        const p = contexto.generarPreguntaPartes(c);
        if (!p.q || /\{(n|d)\}/.test(p.q)) {
          fallo(idioma + ': marcador sin sustituir en ' + c.p.n);
        }
        if (!Array.isArray(p.ops) || p.ops.length !== 4) {
          fallo(idioma + ': ' + c.p.n + ' no tiene 4 opciones');
          continue;
        }
        if (new Set(p.ops).size !== p.ops.length) {
          fallo(idioma + ': opciones repetidas en ' + c.p.n);
        }
        if (!p.ops.includes(p.a) || p.ops.filter(x => x === p.a).length !== 1) {
          fallo(idioma + ': respuesta ausente o repetida en ' + c.p.n);
        }
        if (c.tipo === 'pn') {
          if (p.a !== contexto.tr(c.p.d)) fallo(idioma + ': descripcion incorrecta');
          if (!p.q.includes(c.p.n)) fallo(idioma + ': falta el P/N en la pregunta');
        } else {
          if (p.a !== c.p.n) fallo(idioma + ': P/N incorrecto');
          if (!p.q.includes(contexto.tr(c.p.d))) {
            fallo(idioma + ': falta la descripcion en la pregunta');
          }
        }
      }
    }
  }

  // Simulacion de examenes completos: 20 preguntas sin repetir candidato.
  LANG = 'es';
  for (let e = 0; e < 2000; e++) {
    const copia = contexto.candidatosPartes();
    const elegidas = [];
    while (elegidas.length < 20 && copia.length) {
      elegidas.push(copia.splice(Math.floor(Math.random() * copia.length), 1)[0]);
    }
    if (elegidas.length !== 20) {
      fallo('un examen de 20 preguntas no se pudo completar');
      break;
    }
    const claves = new Set(elegidas.map(c => c.tipo + ':' + c.p.n));
    if (claves.size !== elegidas.length) fallo('candidato repetido en un examen');
    for (const c of elegidas) {
      const p = contexto.generarPreguntaPartes(c);
      if (p.ops.length !== 4 || new Set(p.ops).size !== 4 ||
          !p.ops.includes(p.a)) {
        fallo('pregunta invalida en simulacion de examen');
      }
    }
  }

  if (fallos) {
    console.error('FALLOS: ' + fallos);
    process.exit(1);
  }
  console.log('OK: 5 idiomas, 237 candidatos, 0 ambiguedades, 0 opciones invalidas');
}

try {
  principal();
} catch (e) {
  console.error('ERROR: ' + e.message);
  process.exit(1);
}
