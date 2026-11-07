/* SIGEA — comportamiento del shell y de los componentes. Sin dependencias. */
(function () {
  'use strict';

  var guardar = {
    leer: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    escribir: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }
  };

  /* ── Riel contraíble (escritorio) ─────────────────────── */
  function iniciarRiel() {
    var app = document.querySelector('.sg-app');
    var boton = document.querySelector('[data-riel-alternar]');
    if (!app || !boton) return;
    if (guardar.leer('sigea:riel') === 'corto') app.classList.add('es-riel-corto');
    var sincronizar = function () {
      var corto = app.classList.contains('es-riel-corto');
      boton.setAttribute('aria-expanded', String(!corto));
      boton.setAttribute('aria-label', corto ? 'Expandir menú' : 'Contraer menú');
    };
    sincronizar();
    boton.addEventListener('click', function () {
      app.classList.toggle('es-riel-corto');
      guardar.escribir('sigea:riel', app.classList.contains('es-riel-corto') ? 'corto' : 'largo');
      sincronizar();
    });
  }

  /* ── Hoja "Más" (móvil) ───────────────────────────────── */
  function iniciarHojaMas() {
    var hoja = document.getElementById('sg-hoja-mas');
    if (!hoja || typeof hoja.showModal !== 'function') return;
    document.querySelectorAll('[data-abrir-mas]').forEach(function (b) {
      b.addEventListener('click', function () { hoja.showModal(); });
    });
    hoja.querySelectorAll('[data-cerrar]').forEach(function (b) {
      b.addEventListener('click', function () { hoja.close(); });
    });
    hoja.addEventListener('click', function (e) { if (e.target === hoja) hoja.close(); });
  }

  /* ── Confirmación accesible con <dialog> ──────────────── */
  var dialogo, pendiente;
  function prepararDialogo() {
    dialogo = document.getElementById('sg-confirmar');
    if (!dialogo) return;
    dialogo.addEventListener('close', function () {
      var accion = pendiente; pendiente = null;
      if (dialogo.returnValue === 'si' && accion) accion();
    });
  }

  function confirmar(titulo, mensaje, alConfirmar, opciones) {
    opciones = opciones || {};
    if (!dialogo || typeof dialogo.showModal !== 'function') {
      if (window.confirm(mensaje)) alConfirmar();
      return;
    }
    dialogo.querySelector('[data-titulo]').textContent = titulo || 'Confirmar';
    dialogo.querySelector('[data-mensaje]').textContent = mensaje || '';
    var si = dialogo.querySelector('[value="si"]');
    var peligro = opciones.variant === 'danger' || /eliminar|quitar|revocar|rechazar|inhabilitar|deshabilitar/i.test(titulo + ' ' + mensaje);
    si.textContent = opciones.confirmText || (peligro ? 'Sí, continuar' : 'Confirmar');
    si.className = 'sg-btn ' + (peligro ? 'sg-btn--peligro' : 'sg-btn--marca');
    pendiente = alConfirmar;
    dialogo.returnValue = '';
    dialogo.showModal();
    dialogo.querySelector('[value="no"]').focus();
  }
  window.sigeaConfirm = confirmar;
  window.sigeaConfirmClose = function () { if (dialogo && dialogo.open) dialogo.close('no'); };

  function iniciarConfirmaciones() {
    document.addEventListener('click', function (e) {
      var boton = e.target.closest('[data-confirmar]');
      if (!boton || boton.dataset.confirmado === '1') return;
      e.preventDefault();
      confirmar(boton.dataset.confirmarTitulo || 'Confirmar', boton.dataset.confirmar, function () {
        boton.dataset.confirmado = '1';
        if (boton.form) {
          if (typeof boton.form.requestSubmit === 'function') boton.form.requestSubmit(boton);
          else boton.form.submit();
        } else if (boton.href) {
          window.location.href = boton.href;
        }
      });
    });
  }

  /* ── Estado de carga en formularios ───────────────────── */
  function iniciarCarga() {
    document.addEventListener('submit', function (e) {
      var form = e.target;
      if (form.method && form.method.toLowerCase() === 'get') return;
      var boton = e.submitter || form.querySelector('[type=submit]');
      if (!boton || boton.getAttribute('aria-busy') === 'true') {
        if (boton) e.preventDefault();
        return;
      }
      window.setTimeout(function () {
        boton.setAttribute('aria-busy', 'true');
        boton.setAttribute('aria-disabled', 'true');
      }, 0);
    });
    /* Volver con "atrás" no debe dejar botones bloqueados */
    window.addEventListener('pageshow', function () {
      document.querySelectorAll('[aria-busy="true"]').forEach(function (b) {
        b.removeAttribute('aria-busy'); b.removeAttribute('aria-disabled');
      });
    });
  }

  /* ── Avisos cerrables ─────────────────────────────────── */
  function iniciarAvisos() {
    document.querySelectorAll('.sg-aviso__cerrar').forEach(function (b) {
      b.addEventListener('click', function () { b.closest('.sg-aviso').remove(); });
    });
  }

  /* ── Archivo: muestra el nombre elegido (siempre como texto) ── */
  function iniciarArchivos() {
    document.querySelectorAll('.sg-archivo input[type=file]').forEach(function (input) {
      var zona = input.closest('.sg-archivo');
      var nombre = zona.querySelector('[data-archivo-nombre]');
      var original = nombre ? nombre.textContent : '';
      input.addEventListener('change', function () {
        var f = input.files && input.files[0];
        if (nombre) nombre.textContent = f ? f.name + ' · ' + Math.max(1, Math.round(f.size / 1024)) + ' KB' : original;
        zona.classList.toggle('es-activo', Boolean(f));
      });
      ['dragenter', 'dragover'].forEach(function (t) { zona.addEventListener(t, function () { zona.classList.add('es-activo'); }); });
      ['dragleave', 'drop'].forEach(function (t) { zona.addEventListener(t, function () { if (!input.files.length) zona.classList.remove('es-activo'); }); });
    });
  }

  /* ── Mostrar u ocultar contraseña ─────────────────────── */
  function iniciarClaves() {
    document.querySelectorAll('[data-alternar-clave]').forEach(function (b) {
      var input = document.getElementById(b.getAttribute('aria-controls'));
      if (!input) return;
      b.addEventListener('click', function () {
        var visible = input.type === 'text';
        input.type = visible ? 'password' : 'text';
        b.setAttribute('aria-pressed', String(!visible));
        b.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
      });
    });
  }

  /* ── Búsqueda rápida (nodos de texto, nunca HTML) ─────── */
  function escaparRegex(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function iniciarBuscador() {
    var input = document.getElementById('sg-buscar');
    var lista = document.getElementById('sg-buscar-resultados');
    if (!input || !lista) return;
    var temporizador, controlador;

    function cerrar() { lista.classList.remove('es-visible'); input.setAttribute('aria-expanded', 'false'); }

    function pintar(resultados, consulta) {
      lista.replaceChildren();
      if (!resultados.length) {
        var vacio = document.createElement('p');
        vacio.className = 'sg-buscador__vacio';
        vacio.textContent = 'No hay evidencias con ese título.';
        lista.appendChild(vacio);
      }
      var regex = new RegExp('(' + escaparRegex(consulta) + ')', 'gi');
      resultados.forEach(function (r) {
        var a = document.createElement('a');
        a.href = r.url;
        a.setAttribute('role', 'option');
        String(r.titulo).split(regex).forEach(function (parte, i) {
          if (!parte) return;
          if (i % 2 === 1) { var m = document.createElement('mark'); m.textContent = parte; a.appendChild(m); }
          else a.appendChild(document.createTextNode(parte));
        });
        lista.appendChild(a);
      });
      lista.classList.add('es-visible');
      input.setAttribute('aria-expanded', 'true');
    }

    input.addEventListener('input', function () {
      var q = input.value.trim();
      window.clearTimeout(temporizador);
      if (q.length < 2) { cerrar(); return; }
      temporizador = window.setTimeout(function () {
        if (controlador) controlador.abort();
        controlador = new AbortController();
        fetch(input.dataset.url + '?q=' + encodeURIComponent(q), { signal: controlador.signal, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
          .then(function (r) { return r.ok ? r.json() : { results: [] }; })
          .then(function (d) { pintar(d.results || [], q); })
          .catch(function () { /* abortado o sin red */ });
      }, 220);
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { cerrar(); }
      if (e.key === 'ArrowDown') { var p = lista.querySelector('a'); if (p) { e.preventDefault(); p.focus(); } }
    });
    lista.addEventListener('keydown', function (e) {
      var enlaces = Array.prototype.slice.call(lista.querySelectorAll('a'));
      var i = enlaces.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && i < enlaces.length - 1) { e.preventDefault(); enlaces[i + 1].focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); (i > 0 ? enlaces[i - 1] : input).focus(); }
      if (e.key === 'Escape') { cerrar(); input.focus(); }
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('.sg-buscador')) cerrar(); });
  }

  /* Casilla maestra que marca o desmarca todas las de un grupo (Por revisar) */
  function iniciarMarcarTodos() {
    document.querySelectorAll('[data-marcar-todos]').forEach(function (maestro) {
      var nombre = maestro.dataset.marcarTodos;
      maestro.addEventListener('change', function () {
        document.querySelectorAll('input[name="' + nombre + '"]').forEach(function (c) { c.checked = maestro.checked; });
      });
    });
  }

  /* Resalta en los resultados lo que se buscó. C2: solo nodos de texto, nunca HTML. */
  function iniciarResaltado() {
    var q = new URLSearchParams(window.location.search).get('q');
    if (!q || !q.trim()) return;
    var palabras = q.trim().split(/\s+/).filter(Boolean).map(escaparRegex);
    var regex = new RegExp('(' + palabras.join('|') + ')', 'gi');
    document.querySelectorAll('.sa-highlight-target').forEach(function (el) {
      var partes = el.textContent.split(regex);
      if (partes.length < 2) return;
      var fragmento = document.createDocumentFragment();
      partes.forEach(function (parte, i) {
        if (!parte) return;
        if (i % 2 === 1) {
          var mark = document.createElement('mark');
          mark.className = 'highlight-amber';
          mark.textContent = parte;
          fragmento.appendChild(mark);
        } else {
          fragmento.appendChild(document.createTextNode(parte));
        }
      });
      el.replaceChildren(fragmento);
    });
  }

  /* Selects que envían su formulario al cambiar (orden de resultados, filtros rápidos) */
  function iniciarEnvioAlCambiar() {
    document.addEventListener('change', function (e) {
      if (e.target.matches('[data-enviar-al-cambiar]') && e.target.form) e.target.form.submit();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    prepararDialogo();
    iniciarEnvioAlCambiar();
    iniciarMarcarTodos();
    iniciarResaltado();
    iniciarRiel();
    iniciarHojaMas();
    iniciarConfirmaciones();
    iniciarCarga();
    iniciarAvisos();
    iniciarArchivos();
    iniciarClaves();
    iniciarBuscador();
  });
})();
