/*
 * Smart Scanner — gráfica de dispersión (Plotly) con tres grupos y tres lentes.
 *
 * Los datos vienen en <script id="scan-data"> (scanner/scatter.py): los puntos
 * de cada grupo (penny / standard = "medium" / monster) y la definición de cada
 * lente (ejes, líneas de referencia, nombres de los cuatro cuadrantes). Cambiar
 * de grupo o de lente no recarga la página: se redibuja la gráfica, se muestra
 * la guía de esa lente y la lista del grupo. Clic en una burbuja =
 * selectSymbol() de main.js (carga gráfica de velas e indicadores de esa acción,
 * igual que la lista). Al pasar el cursor, la burbuja cambia de color.
 */
(function () {
    'use strict';

    var dataEl = document.getElementById('scan-data');
    var chartEl = document.getElementById('scan-scatter');
    if (!dataEl || !chartEl) return;

    var D = JSON.parse(dataEl.textContent);
    var I = D.i18n;
    var lang = document.documentElement.lang === 'en' ? 'en' : 'es';
    var locale = lang === 'en' ? 'en-US' : 'es-ES';
    var NARROW = window.innerWidth < 640;

    var state = { group: D.initial.group, mode: D.initial.mode, selected: null };
    var modesById = {};
    D.modes.forEach(function (m) { modesById[m.id] = m; });

    var css = getComputedStyle(document.documentElement);
    function token(name, fallback) {
        var v = css.getPropertyValue(name);
        return (v && v.trim()) || fallback;
    }
    var C = {
        text: token('--text', '#23241f'),
        muted: token('--muted', '#6b6a5e'),
        border: token('--border', '#ded6c6'),
        surface: token('--surface', '#ffffff'),
        // Un color por cuadrante (los mismos tokens que usa la guía debajo de la gráfica).
        tr: token('--bull', '#1f8a5f'),
        tl: token('--group-monster', '#2f5fa8'),
        br: token('--group-penny', '#c2790f'),
        bl: token('--bear', '#c23b34'),
        hover: token('--tool-fvg', '#5844b0')
    };
    var FONT = token('--font-mono', 'Consolas, monospace');

    function rgba(hex, alpha) {
        var h = hex.replace('#', '');
        if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
        var num = parseInt(h, 16);
        if (isNaN(num)) return hex;
        return 'rgba(' + ((num >> 16) & 255) + ',' + ((num >> 8) & 255) + ',' + (num & 255) + ',' + alpha + ')';
    }
    function fmt(value, digits) {
        return Number(value).toLocaleString(locale, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }
    function quantile(sorted, q) {
        if (!sorted.length) return 0;
        var pos = (sorted.length - 1) * q;
        var lo = Math.floor(pos), hi = Math.ceil(pos);
        return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
    }

    /* Rango de un eje: cubre la referencia (mid) y el grueso de los datos
       (percentiles 5-95, o todo si son pocos) para que un solo valor
       extremo no aplaste al resto; lo que queda fuera se pega al borde. */
    function axisRange(values, mid) {
        var sorted = values.slice().sort(function (a, b) { return a - b; });
        var lo = values.length >= 8 ? quantile(sorted, 0.05) : sorted[0];
        var hi = values.length >= 8 ? quantile(sorted, 0.95) : sorted[sorted.length - 1];
        lo = Math.min(lo, mid);
        hi = Math.max(hi, mid);
        var pad = (hi - lo) * 0.16 || 1;
        return [lo - pad, hi + pad];
    }

    function bubbleSize(rv) {
        var v = rv === null || rv === undefined ? 1 : Math.max(0.3, Math.min(rv, 4));
        var min = NARROW ? 11 : 18, span = NARROW ? 20 : 38;
        return min + (v - 0.3) / 3.7 * span;
    }
    function plotHeight() {
        if (NARROW) return 460;
        return Math.max(560, Math.min(720, Math.round(window.innerHeight * 0.82)));
    }

    var clickBound = false;
    var noteEl = document.getElementById('scan-note');
    var view = null;   // colores/bordes base del gráfico actual, para restaurar tras el resaltado

    function visiblePoints(group, mode) {
        var m = modesById[mode];
        var pts = D.groups[group].points;
        var usable = pts.filter(function (p) {
            return p[m.x.key] !== null && p[m.x.key] !== undefined && p[m.y.key] !== null && p[m.y.key] !== undefined;
        });
        return { usable: usable, missing: pts.length - usable.length, total: pts.length, mode: m };
    }

    function quadrantOf(p, m) {
        var right = p[m.x.key] > m.x.mid, top = p[m.y.key] > m.y.mid;
        return (top ? 't' : 'b') + (right ? 'r' : 'l');
    }

    function renderNote(info, win) {
        if (!noteEl) return;
        var parts = [];
        if (!info.total) {
            parts.push(I.emptyGroup);
        } else if (!info.usable.length) {
            parts.push(I.noData);
        } else if (win.length) {
            parts.push(I.candidates.replace('{n}', win.length).replace('{total}', info.usable.length)
                .replace('{symbols}', win.map(function (p) { return p.s; }).join(', ')));
        } else {
            parts.push(I.noCandidates);
        }
        if (info.missing && info.usable.length) parts.push(I.missing.replace('{n}', info.missing));
        noteEl.textContent = parts.join(' ');
    }

    function showGuide(mode) {
        Array.prototype.forEach.call(document.querySelectorAll('[data-guide]'), function (el) {
            el.classList.toggle('is-active', el.getAttribute('data-guide') === mode);
        });
    }

    function draw() {
        var info = visiblePoints(state.group, state.mode);
        var m = info.mode;
        var win = info.usable.filter(function (p) { return quadrantOf(p, m) === 'tr'; });
        renderNote(info, win);
        showGuide(state.mode);

        if (!info.usable.length) {
            Plotly.purge(chartEl);
            clickBound = false;   // purge descarta los manejadores de eventos
            view = null;
            chartEl.classList.add('is-empty');
            chartEl.innerHTML = '';
            return;
        }
        chartEl.classList.remove('is-empty');

        var xs = info.usable.map(function (p) { return p[m.x.key]; });
        var ys = info.usable.map(function (p) { return p[m.y.key]; });
        var xr = axisRange(xs, m.x.mid), yr = axisRange(ys, m.y.mid);
        // Lo que cae fuera del rango se pega al borde (con un margen para que la burbuja no se corte).
        function clamp(v, r) { var inset = (r[1] - r[0]) * 0.03; return Math.max(r[0] + inset, Math.min(r[1] - inset, v)); }

        var quads = info.usable.map(function (p) { return quadrantOf(p, m); });
        view = {
            colors: quads.map(function (q) { return rgba(C[q], 0.72); }),
            lineColors: info.usable.map(function (p, i) { return p.s === state.selected ? C.text : C[quads[i]]; }),
            lineWidths: info.usable.map(function (p) { return p.s === state.selected ? 3.5 : 1.5; })
        };

        var trace = {
            type: 'scatter', mode: 'markers+text', cliponaxis: false,
            x: info.usable.map(function (p) { return clamp(p[m.x.key], xr); }),
            y: info.usable.map(function (p) { return clamp(p[m.y.key], yr); }),
            text: info.usable.map(function (p) { return p.s; }),
            textposition: 'top center',
            textfont: { size: NARROW ? 10 : 12, family: FONT, color: C.text },
            customdata: info.usable.map(function (p) { return p.s; }),
            hovertemplate: '%{hovertext}<extra></extra>',
            marker: {
                size: info.usable.map(function (p) { return bubbleSize(p.rv); }),
                color: view.colors.slice(),
                line: { width: view.lineWidths.slice(), color: view.lineColors.slice() }
            },
            hoverlabel: { bgcolor: C.surface, bordercolor: C.border, font: { family: FONT, size: 12, color: C.text } }
        };
        // Texto del tooltip armado a mano: varias líneas con formato por idioma.
        trace.hovertext = info.usable.map(function (p, i) {
            var q = m.quads[quads[i]];
            var lines = ['<b>' + p.s + '</b>' + (p.n ? ' · ' + p.n : '')];
            lines.push('<b>' + q.name + '</b>');
            lines.push(I.price + ': $' + fmt(p.p, 2) + '  ·  ' + I.score + ': ' + fmt(p.sc, 0));
            lines.push(m.x.label + ': ' + fmt(p[m.x.key], 1) + m.x.unit);
            lines.push(m.y.label + ': ' + fmt(p[m.y.key], 1) + m.y.unit);
            if (p.rv !== null) lines.push(I.rvol + ': ' + fmt(p.rv, 2) + 'x');
            var off = p[m.x.key] < xr[0] || p[m.x.key] > xr[1] || p[m.y.key] < yr[0] || p[m.y.key] > yr[1];
            if (off) lines.push('<i>(' + I.offScale + ')</i>');
            return lines.join('<br>');
        });

        var midLine = { color: C.text, width: 1.6, dash: 'dash' };
        var shapes = [
            // Los cuatro cuadrantes, cada uno con su tinte (las líneas de referencia los separan).
            { type: 'rect', xref: 'x', yref: 'y', x0: m.x.mid, x1: xr[1], y0: m.y.mid, y1: yr[1], fillcolor: rgba(C.tr, 0.13), line: { width: 0 }, layer: 'below' },
            { type: 'rect', xref: 'x', yref: 'y', x0: xr[0], x1: m.x.mid, y0: m.y.mid, y1: yr[1], fillcolor: rgba(C.tl, 0.09), line: { width: 0 }, layer: 'below' },
            { type: 'rect', xref: 'x', yref: 'y', x0: m.x.mid, x1: xr[1], y0: yr[0], y1: m.y.mid, fillcolor: rgba(C.br, 0.10), line: { width: 0 }, layer: 'below' },
            { type: 'rect', xref: 'x', yref: 'y', x0: xr[0], x1: m.x.mid, y0: yr[0], y1: m.y.mid, fillcolor: rgba(C.bl, 0.08), line: { width: 0 }, layer: 'below' },
            { type: 'line', xref: 'x', yref: 'paper', x0: m.x.mid, x1: m.x.mid, y0: 0, y1: 1, line: midLine },
            { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: m.y.mid, y1: m.y.mid, line: midLine }
        ];

        // En celular los nombres largos se parten en líneas para que los dos rótulos
        // de arriba (y de abajo) no se pisen entre sí.
        function wrapLabel(text, maxChars) {
            var words = text.split(' '), lines = [], line = '';
            words.forEach(function (w) {
                if (line && (line + ' ' + w).length > maxChars) { lines.push(line); line = w; }
                else line = line ? line + ' ' + w : w;
            });
            if (line) lines.push(line);
            return lines.join('<br>');
        }
        // Nombre de cada cuadrante, rotulado en su esquina de la gráfica.
        function corner(q, x, y, xanchor, yanchor) {
            var name = (q === 'tr' ? '★ ' : '') + m.quads[q].name;
            return {
                xref: 'paper', yref: 'paper', x: x, y: y, xanchor: xanchor, yanchor: yanchor, showarrow: false,
                align: xanchor,
                text: '<b>' + (NARROW ? wrapLabel(name, 14) : name) + '</b>',
                font: { size: NARROW ? 10 : 13, color: C[q], family: FONT },
                bgcolor: 'rgba(255,255,255,0.72)', borderpad: 4
            };
        }
        var annotations = [
            corner('tl', 0.005, 0.995, 'left', 'top'),
            corner('tr', 0.995, 0.995, 'right', 'top'),
            corner('bl', 0.005, 0.005, 'left', 'bottom'),
            corner('br', 0.995, 0.005, 'right', 'bottom')
        ];

        var layout = {
            height: plotHeight(),
            margin: { l: NARROW ? 48 : 66, r: NARROW ? 14 : 24, t: 30, b: NARROW ? 56 : 66 },
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: FONT, size: NARROW ? 10 : 12, color: C.muted },
            showlegend: false, hovermode: 'closest', dragmode: false,
            hoverdistance: 30,
            separators: lang === 'en' ? '.,' : ',.',
            xaxis: {
                title: { text: m.x.label, font: { size: NARROW ? 10 : 13, color: C.text }, standoff: 10 }, range: xr, zeroline: false,
                gridcolor: C.border, ticksuffix: m.x.unit === '%' ? '%' : '', fixedrange: true
            },
            yaxis: {
                title: { text: m.y.label, font: { size: NARROW ? 10 : 13, color: C.text }, standoff: 10 }, range: yr, zeroline: false,
                gridcolor: C.border, ticksuffix: m.y.unit === '%' ? '%' : '', fixedrange: true
            },
            shapes: shapes, annotations: annotations
        };

        Plotly.react(chartEl, [trace], layout, { responsive: true, displaylogo: false, displayModeBar: false });
        bindChartEvents();
    }

    /* ------------------------------------------------------- interacción */

    function dragLayer() { return chartEl.querySelector('.nsewdrag'); }

    // Resalta una burbuja (color de acento + borde blanco) y restaura las demás.
    function highlight(index) {
        if (!view) return;
        var colors = view.colors.slice(), lc = view.lineColors.slice(), lw = view.lineWidths.slice();
        if (index !== null && index !== undefined) {
            colors[index] = rgba(C.hover, 0.95);
            lc[index] = '#ffffff';
            lw[index] = 3;
        }
        Plotly.restyle(chartEl, { 'marker.color': [colors], 'marker.line.color': [lc], 'marker.line.width': [lw] }, [0]);
    }

    function bindChartEvents() {
        if (clickBound || !chartEl.on) return;
        clickBound = true;
        chartEl.on('plotly_hover', function (ev) {
            var p = ev.points && ev.points[0];
            if (!p) return;
            highlight(p.pointNumber);
            var layer = dragLayer();
            if (layer) layer.style.cursor = 'pointer';
        });
        chartEl.on('plotly_unhover', function () {
            highlight(null);
            var layer = dragLayer();
            if (layer) layer.style.cursor = '';
        });
        chartEl.on('plotly_click', function (ev) {
            var p = ev.points && ev.points[0];
            if (!p) return;
            var symbol = p.customdata;
            if (window.selectSymbol) window.selectSymbol(symbol);
            markSelected(symbol);
        });
    }

    function markSelected(symbol) {
        state.selected = symbol;
        Array.prototype.forEach.call(document.querySelectorAll('.top10-item'), function (btn) {
            btn.classList.toggle('is-active', btn.getAttribute('data-symbol') === symbol);
        });
        draw();
    }
    // Clic en la lista (onclick="selectSymbol(...)") o desde cualquier otro lado.
    document.addEventListener('dsms:symbol-selected', function (ev) {
        if (ev.detail && ev.detail.symbol !== state.selected) markSelected(ev.detail.symbol);
    });

    function setGroup(group, userInitiated) {
        state.group = group;
        Array.prototype.forEach.call(document.querySelectorAll('.scan-group'), function (b) {
            var on = b.getAttribute('data-group') === group;
            b.classList.toggle('is-active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-pane]'), function (el) {
            el.hidden = el.getAttribute('data-pane') !== group;
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-list]'), function (el) {
            el.hidden = el.getAttribute('data-list') !== group;
        });
        var first = D.groups[group].points[0];
        if (userInitiated && first && window.selectSymbol) {
            // Al cambiar de grupo, el panel de gráfica/indicadores pasa a la mejor acción del grupo.
            window.selectSymbol(first.s);
            state.selected = first.s;
            Array.prototype.forEach.call(document.querySelectorAll('.top10-item'), function (btn) {
                btn.classList.toggle('is-active', btn.getAttribute('data-symbol') === first.s);
            });
        }
        draw();
        syncUrl();
    }

    function setMode(mode) {
        state.mode = mode;
        Array.prototype.forEach.call(document.querySelectorAll('.scan-mode'), function (b) {
            var on = b.getAttribute('data-mode') === mode;
            b.classList.toggle('is-active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        draw();
        syncUrl();
    }

    function syncUrl() {
        try {
            var url = new URL(window.location.href);
            url.searchParams.set('group', state.group);
            url.searchParams.set('view', state.mode);
            window.history.replaceState(null, '', url.toString());
        } catch (e) { /* enlaces compartibles: mejora opcional */ }
    }

    Array.prototype.forEach.call(document.querySelectorAll('.scan-group'), function (btn) {
        btn.addEventListener('click', function () { setGroup(btn.getAttribute('data-group'), true); });
    });
    Array.prototype.forEach.call(document.querySelectorAll('.scan-mode'), function (btn) {
        btn.addEventListener('click', function () { setMode(btn.getAttribute('data-mode')); });
    });

    var first = D.groups[state.group].points[0];
    state.selected = first ? first.s : null;
    draw();

    window.addEventListener('resize', function () {
        // Solo cuando cruza el umbral de celular: redibuja con los tamaños de ese formato.
        var narrow = window.innerWidth < 640;
        if (narrow !== NARROW) { NARROW = narrow; draw(); }
    });
})();
