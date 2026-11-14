#!/usr/bin/env node
'use strict';
/*
 * Auditoria del examen generado de 5 niveles.
 *
 * Extrae de docs/app/index.html las funciones reales del generador
 * (aleatorio, opciones, fmtNum, tr, refUso, generarPregunta) y las ejecuta
 * contra docs/app/datos.js en los cinco idiomas.
 *
 * Comprueba, para cada nivel y cada idioma:
 *   - cuatro opciones distintas y la respuesta correcta incluida una sola vez;
 *   - ausencia de marcadores {x} y de respuestas vacias o "—";
 *   - que los tipos nuevos (velocidad y temperatura de ribbon, consumo a
 *     temperatura tabulada) aparecen y sus respuestas existen en los datos;
 *   - que el consumo a temperatura no usa los 30 °C de la referencia fija.
 *
 * Uso:
 *   node tools/auditar_examen_gen.js
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const RAIZ = path.resolve(__dirname, '..');
const IDIOMAS = ['es', 'en', 'pt', 'it', 'zh'];
const NIVELES = [1, 2, 3, 4, 5];
const CLAVES = [
  'q_base', 'q_color', 'q_rib_vel', 'q_rib_temp', 'q_tec', 'q_sol_temp',
  'q_sol_horas', 'q_sds_dens', 'q_sds_flash', 'q_ref', 'q_cas', 'q_part',
  'ref_cij', 'ref_ribbons', 'ref_err', 'ref_sol', 'ref_sds', 'ref_part',
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

function extraerConstante(src, nombre) {
  const inicio = src.indexOf('const ' + nombre + ' =');
  if (inicio < 0) throw new Error('no se encontro const ' + nombre);
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
      if (profundidad === 0) {
        const fin = src.indexOf(';', i);
        if (fin < 0) throw new Error('const ' + nombre + ' sin cierre');
        return src.slice(inicio, fin + 1);
      }
    }
  }
  throw new Error('const ' + nombre + ' sin cierre');
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
          new RegExp('(?:^|[,{\\n])\\s*' + clave + "\\s*:\\s*'((?:\\\\.|[^'\\\\])*)'"));
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

  const locales = src.match(/const LOCALES\s*=\s*\{[^}]*\};/);
  if (!locales) throw new Error('no se encontro const LOCALES');
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
  vm.runInContext(locales[0].replace('const ', 'var '), contexto);
  const codigo = extraerConstante(src, 'SDS_PROPS').replace('const ', 'var ') + '\n' +
    src.slice(src.indexOf('/* Pools de datos reutilizados'),
              src.indexOf('function generarPregunta('))
      .replace(/\bconst /g, 'var ') + '\n' +
    ['aleatorio', 'opciones', 'fmtNum', 'tr', 'refUso', 'generarPregunta']
      .map(nombre => extraerFuncion(src, nombre)).join('\n');
  vm.runInContext(codigo, contexto);

  const grados = D.ribbons.grados;
  const conVel = grados.filter(g => typeof g.vel === 'number');
  const conTemp = grados.filter(g => typeof g.temp === 'number');
  const curvas = D.solventes.filter(s => s.e === 'verificado' &&
    Array.isArray(s.c) && s.c.length >= 4);
  const refs = D.solventes.filter(s => s.e === 'verificado' &&
    contexto.refUso(s.r) !== null && contexto.refUso(s.r) !== undefined);
  const dens = contexto.SDS_PROPS.dens;
  const flash = contexto.SDS_PROPS.flash;
  const volat = contexto.SDS_PROPS.volat;
  const ebull = contexto.SDS_PROPS.ebull;
  const pvap = contexto.SDS_PROPS.pvap;
  const tcolor = contexto.TINTAS_COLOR;
  const tbase = contexto.TINTAS_BASE;
  console.log('Datos: %d ribbons con velocidad, %d con temperatura, %d curvas, %d referencias, %d densidades, %d inflamaciones, %d volatilidades, %d ebulliciones, %d presiones de vapor, %d colores de tinta, %d tintas de base unica',
              conVel.length, conTemp.length, curvas.length, refs.length,
              dens.length, flash.length, volat.length, ebull.length, pvap.length,
              tcolor.length, tbase.length);
  if (conVel.length < 4) throw new Error('faltan ribbons con velocidad');
  if (conTemp.length < 4) throw new Error('faltan ribbons con temperatura');
  if (curvas.length < 4) throw new Error('faltan curvas de solvente verificadas');
  if (refs.length < 4) throw new Error('faltan referencias de solvente');
  if (dens.length < 4) throw new Error('faltan densidades SDS con valor unico');
  if (flash.length < 4) throw new Error('faltan puntos de inflamacion SDS con valor unico');
  if (volat.length < 4) throw new Error('faltan volatilidades SDS con valor unico');
  if (ebull.length < 4) throw new Error('faltan puntos de ebullicion SDS con valor unico');
  if (pvap.length < 4) throw new Error('faltan presiones de vapor SDS con valor unico');
  if (tcolor.length < 4) throw new Error('faltan colores de tinta SDS con valor unico');
  if (tbase.length < 4) throw new Error('faltan tintas con una sola base quimica');

  let fallos = 0;
  const fallo = msg => {
    fallos++;
    if (fallos <= 30) console.error('FALLO: ' + msg);
  };

  const resumen = {};
  for (const idioma of IDIOMAS) {
    LANG = idioma;
    contexto.LANG = idioma;
    const validVel = new Set(conVel.map(g => contexto.fmtNum(g.vel, 0) + ' mm/s'));
    const validTemp = new Set(conTemp.map(g => contexto.fmtNum(g.temp, 0) + ' °C'));
    const validSol = new Set();
    curvas.forEach(s => s.c.forEach(([, u]) => {
      if (u !== null && u !== undefined) {
        validSol.add(contexto.fmtNum(u, 1) + ' ml/h');
      }
    }));
    const validHoras = new Set(refs.map(s =>
      contexto.fmtNum(1000 / contexto.refUso(s.r), 1) + ' h'));
    const validDens = new Set(dens.map(x => x.v));
    const validFlash = new Set(flash.map(x => x.v));
    const validVolat = new Set(volat.map(x => contexto.tr(x.v)));
    const validEbull = new Set(ebull.map(x => contexto.tr(x.v)));
    const validPvap = new Set(pvap.map(x => contexto.tr(x.v)));
    const validColor = new Set(tcolor.map(x => contexto.tr(x.v)));
    const validBase = new Set(tbase.map(([,x]) => contexto.tr(x.b[0])));
    const tipos = {base: 0, rib_vel: 0, rib_temp: 0, sol_temp: 0,
                   sol_horas: 0, sds_dens: 0, sds_flash: 0, sds_volat: 0,
                   sds_ebull: 0, sds_pvap: 0, tinta_color: 0};
    let total = 0;

    for (const nivel of NIVELES) {
      for (let k = 0; k < 3000; k++) {
        const p = contexto.generarPregunta(nivel);
        total++;
        if (!p.q || p.q === '—' || /\{[a-zA-Z]+\}/.test(p.q)) {
          fallo(idioma + ' nivel ' + nivel + ': enunciado invalido');
        }
        if (!p.a || p.a === '—') {
          fallo(idioma + ' nivel ' + nivel + ': respuesta vacia');
        }
        if (!p.ref) {
          fallo(idioma + ' nivel ' + nivel + ': referencia vacia');
        }
        const minimo = nivel === 3 ? 3 : 4;
        if (!Array.isArray(p.ops) || p.ops.length < minimo || p.ops.length > 4) {
          fallo(idioma + ' nivel ' + nivel + ': opciones fuera de rango (' +
                (p.ops ? p.ops.length : 'sin array') + ')');
          continue;
        }
        if (p.ops.length === 3) {
          const conjunto = new Set(p.ops);
          const tecnologias = ['LASER', 'TTO', 'CIJ'];
          if (nivel !== 3 || conjunto.size !== 3 ||
              tecnologias.some(x => !conjunto.has(x))) {
            fallo(idioma + ' nivel ' + nivel +
                  ': 3 opciones que no son las 3 tecnologias');
          }
        }
        if (new Set(p.ops).size !== p.ops.length) {
          fallo(idioma + ' nivel ' + nivel + ': opciones repetidas');
        }
        if (p.ops.filter(x => x === p.a).length !== 1) {
          fallo(idioma + ' nivel ' + nivel + ': respuesta ausente o repetida');
        }
        if (p.ops.some(x => !x || x === '—')) {
          fallo(idioma + ' nivel ' + nivel + ': opcion vacia');
        }
        if (p.tipo) {
          if (!(p.tipo in tipos)) {
            fallo(idioma + ' nivel ' + nivel + ': tipo desconocido ' + p.tipo);
            continue;
          }
          tipos[p.tipo]++;
          if (p.tipo === 'base' && !validBase.has(p.a)) {
            fallo(idioma + ': base fuera de las tintas de base unica: ' + p.a);
          }
          if (p.tipo === 'rib_vel' && !validVel.has(p.a)) {
            fallo(idioma + ': velocidad fuera de los datos: ' + p.a);
          }
          if (p.tipo === 'rib_temp' && !validTemp.has(p.a)) {
            fallo(idioma + ': temperatura fuera de los datos: ' + p.a);
          }
          if (p.tipo === 'sol_temp') {
            if (!validSol.has(p.a)) {
              fallo(idioma + ': consumo fuera de las curvas: ' + p.a);
            }
            if (p.q.includes('30 °C')) {
              fallo(idioma + ': consumo a temperatura usa los 30 °C fijos');
            }
          }
          if (p.tipo === 'sol_horas' && !validHoras.has(p.a)) {
            fallo(idioma + ': horas fuera de las referencias: ' + p.a);
          }
          if (p.tipo === 'sds_dens' && !validDens.has(p.a)) {
            fallo(idioma + ': densidad fuera de las SDS: ' + p.a);
          }
          if (p.tipo === 'sds_flash' && !validFlash.has(p.a)) {
            fallo(idioma + ': inflamacion fuera de las SDS: ' + p.a);
          }
          if (p.tipo === 'sds_volat' && !validVolat.has(p.a)) {
            fallo(idioma + ': volatilidad fuera de las SDS: ' + p.a);
          }
          if (p.tipo === 'sds_ebull' && !validEbull.has(p.a)) {
            fallo(idioma + ': ebullicion fuera de las SDS: ' + p.a);
          }
          if (p.tipo === 'sds_pvap' && !validPvap.has(p.a)) {
            fallo(idioma + ': presion de vapor fuera de las SDS: ' + p.a);
          }
          if (p.tipo === 'tinta_color' && !validColor.has(p.a)) {
            fallo(idioma + ': color de tinta fuera de las SDS: ' + p.a);
          }
        }
      }
    }

    if (!tipos.base) fallo(idioma + ': no aparecio base');
    if (!tipos.rib_vel) fallo(idioma + ': no aparecio rib_vel');
    if (!tipos.rib_temp) fallo(idioma + ': no aparecio rib_temp');
    if (!tipos.sol_temp) fallo(idioma + ': no aparecio sol_temp');
    if (!tipos.sol_horas) fallo(idioma + ': no aparecio sol_horas');
    if (!tipos.sds_dens) fallo(idioma + ': no aparecio sds_dens');
    if (!tipos.sds_flash) fallo(idioma + ': no aparecio sds_flash');
    if (!tipos.sds_volat) fallo(idioma + ': no aparecio sds_volat');
    if (!tipos.sds_ebull) fallo(idioma + ': no aparecio sds_ebull');
    if (!tipos.sds_pvap) fallo(idioma + ': no aparecio sds_pvap');
    if (!tipos.tinta_color) fallo(idioma + ': no aparecio tinta_color');
    resumen[idioma] = {total, tipos};
    console.log('%s: %d preguntas, tipos nuevos %j', idioma, total, tipos);
  }

  // Simulacion de examenes completos de 20 preguntas en los niveles tocados.
  LANG = 'es';
  contexto.LANG = 'es';
  for (const nivel of [2, 4, 5]) {
    for (let e = 0; e < 1000; e++) {
      for (let k = 0; k < 20; k++) {
        const p = contexto.generarPregunta(nivel);
        if (p.ops.length !== 4 || new Set(p.ops).size !== 4 ||
            p.ops.filter(x => x === p.a).length !== 1) {
          fallo('examen simulado invalido en nivel ' + nivel);
        }
      }
    }
  }

  // Resumen del historial: promedio ponderado, mejor y datos invalidos.
  vm.runInContext(extraerFuncion(src, 'resumenHistorial'), contexto);
  const casosHistorial = [
    [[], {n:0, pct:0, mejor:0}],
    [[{bien:8,total:10}], {n:1, pct:80, mejor:80}],
    [[{bien:10,total:10},{bien:0,total:10}], {n:2, pct:50, mejor:100}],
    [[{bien:12,total:10}], {n:1, pct:100, mejor:100}],
    [[null,{bien:1,total:0},{bien:3,total:4}], {n:1, pct:75, mejor:75}]
  ];
  for (const [h, esperado] of casosHistorial) {
    const r = contexto.resumenHistorial(h);
    if (r.n !== esperado.n || r.pct !== esperado.pct || r.mejor !== esperado.mejor) {
      fallo('historial: ' + JSON.stringify(h) + ' -> ' + JSON.stringify(r));
    }
  }
  console.log('Historial: %d casos de resumen validados', casosHistorial.length);

  // Respaldo: normalizacion del cuaderno de repaso importado.
  vm.runInContext(extraerFuncion(src, 'normalizarRepaso'), contexto);
  const casosRepaso = [
    [null, {}],
    [[], {}],
    [{a:{box:2,fails:1,due:'2026-11-20',last:'2026-11-14'}},
     {a:{box:2,fails:1,due:'2026-11-20',last:'2026-11-14'}}],
    [{a:{box:9,fails:-1,due:'x',last:123}},
     {a:{box:5,fails:0,due:'',last:''}}],
    [{a:null,b:{box:'2'}},
     {b:{box:2,fails:0,due:'',last:''}}],
  ];
  for (const [entrada, esperado] of casosRepaso) {
    const r = contexto.normalizarRepaso(entrada);
    if (JSON.stringify(r) !== JSON.stringify(esperado)) {
      fallo('repaso: ' + JSON.stringify(entrada) + ' -> ' + JSON.stringify(r));
    }
  }
  console.log('Respaldo: %d casos de repaso validados', casosRepaso.length);

  if (fallos) {
    console.error('FALLOS: ' + fallos);
    process.exit(1);
  }
  console.log('OK: 5 idiomas, 5 niveles, %d preguntas auditadas, 0 opciones invalidas',
              IDIOMAS.reduce((n, i) => n + resumen[i].total, 0));
}

try {
  principal();
} catch (e) {
  console.error('ERROR: ' + e.message);
  process.exit(1);
}
