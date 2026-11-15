#!/usr/bin/env node
'use strict';
/*
 * Auditoria de los bancos de partes CIJ y TTO de la app.
 *
 * Extrae de docs/app/index.html las funciones reales del generador
 * (partesVerificadas, partesCijVerificadas, candidatosPartes,
 * generarPreguntaPartes, opciones y tr) y las ejecuta contra
 * docs/app/datos.js en los cinco idiomas.
 *
 * Comprueba, para cada banco y cada pregunta:
 *   - cuatro opciones distintas;
 *   - la respuesta correcta esta incluida una sola vez;
 *   - no quedan marcadores {n} ni {d} sin sustituir;
 *   - la referencia corresponde a la tecnologia de la pregunta;
 *   - las descripciones ambiguas de CIJ nunca generan preguntas
 *     descripcion->P/N;
 *   - el tipo modelo solo aparece cuando hay al menos 4 conjuntos de
 *     modelos (CIJ: 18; TTO: 3, por eso no genera).
 *
 * Uso:
 *   node tools/auditar_banco_partes.js
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const RAIZ = path.resolve(__dirname, '..');
const IDIOMAS = ['es', 'en', 'pt', 'it', 'zh'];

const BANCOS = [
  {
    tec: 'CIJ',
    nombre: 'CIJ',
    pn: 216,
    desc: 178,
    modelo: 216,
    descUnicasPorIdioma: {es: 196, en: 197, pt: 196, it: 196, zh: 197},
    modelosUnicos: 21,
    claves: ['fuente_partes', 'q_part_pn', 'q_part_desc', 'q_part_modelos',
             'ref_partes', 'partes_nota'],
    ref: 'ref_partes',
    ambiguas: [
      'Filter Element',
      'Filter Cover',
      'Beacon Assembly',
      'Ribbon Cable Spare Kit',
      'Printhead Photocell Holder 6 mm, 8 mm, 18 mm',
      'Control System Board (CSB) with Back Plate',
      'Finnish Molded Plug Power Cord',
      'India Molded Plug Power Cord (Type D)',
      'Ink Core Pump',
      'Ink Core with Pump',
      'Ink Door Assembly',
      'Norwegian Molded Plug Power Cord',
      'Printhead Engine (60 micron)',
      'Printhead Engine (70 micron)',
      'Printhead Valve Module',
      'Septum Assembly',
      'Swedish Molded Plug Power Cord',
    ],
  },
  {
    tec: 'TTO',
    nombre: 'TTO',
    pn: 120,
    desc: 120,
    modelo: 0,
    descUnicasPorIdioma: {es: 120, en: 120, pt: 120, it: 120, zh: 120},
    modelosUnicos: 3,
    claves: ['fuente_partes_tto', 'q_part_tto_pn', 'q_part_tto_desc',
             'ref_partes_tto', 'partes_tto_nota'],
    ref: 'ref_partes_tto',
    ambiguas: [],
  },
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

function extraerI18N(src, claves) {
  const i18n = {};
  IDIOMAS.forEach(idioma => { i18n[idioma] = {}; });
  for (const idioma of IDIOMAS) {
    const patron = new RegExp(
      'Object\\.assign\\(I18N\\.' + idioma + ', \\{([\\s\\S]*?)\\n\\}\\);', 'g');
    let bloque;
    while ((bloque = patron.exec(src))) {
      for (const clave of claves) {
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

  const clavesTodas = [...new Set(BANCOS.flatMap(b => b.claves))];
  const i18n = extraerI18N(src, clavesTodas);

  const faltan = [];
  for (const idioma of IDIOMAS) {
    for (const clave of clavesTodas) {
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
  const codigo = ['opciones', 'partesVerificadas', 'partesCijVerificadas',
                  'candidatosPartes', 'generarPreguntaPartes']
    .map(nombre => extraerFuncion(src, nombre)).join('\n');
  vm.runInContext(codigo, contexto);

  let fallos = 0;
  const fallo = msg => {
    fallos++;
    if (fallos <= 30) console.error('FALLO: ' + msg);
  };

  for (const banco of BANCOS) {
    const partes = contexto.partesVerificadas(banco.tec);
    const candidatos = contexto.candidatosPartes(banco.tec);
    const pn = candidatos.filter(c => c.tipo === 'pn');
    const desc = candidatos.filter(c => c.tipo === 'desc');
    const modelo = candidatos.filter(c => c.tipo === 'modelo');
    console.log('Banco %s: %d P/N, %d descripciones inequivocas, %d modelos, %d candidatos',
                banco.nombre, partes.length, desc.length, modelo.length,
                candidatos.length);
    if (partes.length !== banco.pn) {
      fallo(banco.nombre + ': se esperaban ' + banco.pn + ' P/N verificados');
    }
    if (pn.length !== banco.pn) {
      fallo(banco.nombre + ': se esperaban ' + banco.pn +
            ' preguntas P/N->descripcion');
    }
    if (desc.length !== banco.desc) {
      fallo(banco.nombre + ': se esperaban ' + banco.desc +
            ' preguntas descripcion->P/N');
    }
    if (modelo.length !== banco.modelo) {
      fallo(banco.nombre + ': se esperaban ' + banco.modelo +
            ' preguntas P/N->modelos');
    }
    for (const c of candidatos) {
      if (c.tec !== banco.tec) {
        fallo(banco.nombre + ': candidato con tecnologia ' + c.tec);
      }
      if (!['pn', 'desc', 'modelo'].includes(c.tipo)) {
        fallo(banco.nombre + ': tipo de candidato desconocido ' + c.tipo);
      }
    }

    for (const idioma of IDIOMAS) {
      LANG = idioma;
      const descripciones = new Set(partes.map(p => contexto.tr(p.d)));
      const pns = new Set(partes.map(p => p.n));
      const modelos = new Set(partes.map(p => p.m).filter(Boolean));
      if (modelos.size !== banco.modelosUnicos) {
        fallo(idioma + ': ' + banco.nombre + ': se esperaban ' +
              banco.modelosUnicos + ' conjuntos de modelos');
      }
      if (descripciones.size !== banco.descUnicasPorIdioma[idioma]) {
        fallo(idioma + ': ' + banco.nombre + ': se esperaban ' +
              banco.descUnicasPorIdioma[idioma] + ' descripciones traducidas');
      }
      if (pns.size !== banco.pn) {
        fallo(idioma + ': ' + banco.nombre + ': se esperaban ' +
              banco.pn + ' P/N unicos');
      }
      const ambiguas = new Set(banco.ambiguas.map(d => {
        const p = partes.find(x => x.d === d);
        return p ? contexto.tr(p.d) : d;
      }));
      for (const c of desc) {
        const d = contexto.tr(c.p.d);
        if (ambiguas.has(d)) {
          fallo(idioma + ': ' + banco.nombre +
                ': descripcion ambigua en candidato desc->P/N: ' + d);
        }
        const mismos = partes.filter(x => contexto.tr(x.d) === d);
        if (new Set(mismos.map(x => x.n)).size !== 1) {
          fallo(idioma + ': ' + banco.nombre +
                ': descripcion sin P/N unico: ' + d);
        }
      }
      for (const c of candidatos) {
        for (let k = 0; k < 25; k++) {
          const p = contexto.generarPreguntaPartes(c);
          if (!p.q || /\{(n|d)\}/.test(p.q)) {
            fallo(idioma + ': ' + banco.nombre +
                  ': marcador sin sustituir en ' + c.p.n);
          }
          if (!Array.isArray(p.ops) || p.ops.length !== 4) {
            fallo(idioma + ': ' + banco.nombre + ': ' + c.p.n +
                  ' no tiene 4 opciones');
            continue;
          }
          if (new Set(p.ops).size !== p.ops.length) {
            fallo(idioma + ': ' + banco.nombre +
                  ': opciones repetidas en ' + c.p.n);
          }
          if (!p.ops.includes(p.a) || p.ops.filter(x => x === p.a).length !== 1) {
            fallo(idioma + ': ' + banco.nombre +
                  ': respuesta ausente o repetida en ' + c.p.n);
          }
          if (p.ref !== t(banco.ref)) {
            fallo(idioma + ': ' + banco.nombre +
                  ': referencia incorrecta en ' + c.p.n);
          }
          if (c.tipo === 'pn') {
            if (p.a !== contexto.tr(c.p.d)) {
              fallo(idioma + ': ' + banco.nombre +
                    ': descripcion incorrecta en ' + c.p.n);
            }
            if (!p.q.includes(c.p.n)) {
              fallo(idioma + ': ' + banco.nombre +
                    ': falta el P/N en la pregunta ' + c.p.n);
            }
          } else if (c.tipo === 'modelo') {
            if (p.a !== c.p.m) {
              fallo(idioma + ': ' + banco.nombre +
                    ': modelos incorrectos en ' + c.p.n);
            }
            if (!p.q.includes(c.p.n)) {
              fallo(idioma + ': ' + banco.nombre +
                    ': falta el P/N en la pregunta ' + c.p.n);
            }
            if (!modelos.has(p.a)) {
              fallo(idioma + ': ' + banco.nombre +
                    ': modelos fuera del pool en ' + c.p.n);
            }
          } else {
            if (p.a !== c.p.n) {
              fallo(idioma + ': ' + banco.nombre +
                    ': P/N incorrecto en ' + c.p.n);
            }
            if (!p.q.includes(contexto.tr(c.p.d))) {
              fallo(idioma + ': ' + banco.nombre +
                    ': falta la descripcion en la pregunta ' + c.p.n);
            }
          }
        }
      }
    }

    // Simulacion de examenes completos: 20 preguntas sin repetir candidato.
    LANG = 'es';
    for (let e = 0; e < 2000; e++) {
      const copia = contexto.candidatosPartes(banco.tec);
      const elegidas = [];
      while (elegidas.length < 20 && copia.length) {
        elegidas.push(copia.splice(Math.floor(Math.random() * copia.length), 1)[0]);
      }
      if (elegidas.length !== 20) {
        fallo(banco.nombre + ': un examen de 20 preguntas no se pudo completar');
        break;
      }
      const claves = new Set(elegidas.map(c => c.tipo + ':' + c.p.n));
      if (claves.size !== elegidas.length) {
        fallo(banco.nombre + ': candidato repetido en un examen');
      }
      for (const c of elegidas) {
        const p = contexto.generarPreguntaPartes(c);
        if (p.ops.length !== 4 || new Set(p.ops).size !== 4 ||
            !p.ops.includes(p.a)) {
          fallo(banco.nombre + ': pregunta invalida en simulacion de examen');
        }
      }
    }
  }

  if (fallos) {
    console.error('FALLOS: ' + fallos);
    process.exit(1);
  }
  const resumen = BANCOS.map(b => b.nombre + ' ' + b.pn + ' P/N (' +
                                 (b.pn + b.desc + b.modelo) + ' preguntas)').join(', ');
  console.log('OK: 5 idiomas, ' + resumen +
              ', 0 ambiguedades, 0 opciones invalidas');
}

try {
  principal();
} catch (e) {
  console.error('ERROR: ' + e.message);
  process.exit(1);
}
