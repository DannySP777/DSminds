/*
 * Trading Análisis — gráfica de velas interactiva (Plotly) y calendario.
 *
 * Todo lo que necesita viene en <script id="ta-data"> (velas, medias,
 * soportes/resistencias y las 5 velas proyectadas, calculado en
 * tools/analysis.py); acá solo se dibuja e interactúa. Los colores se
 * leen de las custom properties --ta-* de static/css/style.css para no
 * mantener dos paletas.
 */
(function () {
    'use strict';

    var root = document.querySelector('.ta');
    if (!root) return;
    var lang = root.getAttribute('data-lang') || 'es';
    var locale = lang === 'en' ? 'en-US' : 'es-ES';

    /* ------------------------------------------------ calendario (sin Plotly) */

    function formatTimes() {
        var stamps = root.querySelectorAll('time[data-fmt]');
        Array.prototype.forEach.call(stamps, function (el) {
            var fmt = el.getAttribute('data-fmt');
            var raw = el.getAttribute('datetime');
            var d = fmt === 'day' ? new Date(raw + 'T12:00:00Z') : new Date(raw);
            if (isNaN(d.getTime())) return;
            if (fmt === 'time') {
                el.textContent = d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
            } else {
                var opts = { weekday: 'short', day: 'numeric', month: 'short' };
                if (fmt === 'day') opts.timeZone = 'UTC';
                el.textContent = d.toLocaleDateString(locale, opts);
            }
        });
    }

    function initCalendarFilters() {
        var periodButtons = root.querySelectorAll('[data-cal-period]');
        var highBox = root.querySelector('[data-cal-high]');
        var rows = root.querySelectorAll('.ta-cal__event');
        var counter = document.getElementById('ta-cal-count');
        var rangeEl = document.getElementById('ta-cal-range');
        var table = root.querySelector('.ta-cal__table');
        if (!periodButtons.length) return;
        var period = 'month';

        function apply() {
            var onlyHigh = !!(highBox && highBox.checked);
            var visible = 0, high = 0;
            Array.prototype.forEach.call(rows, function (row) {
                var inPeriod = period === 'month' ? row.getAttribute('data-month') === '1' : row.getAttribute('data-week') === period;
                var show = inPeriod && (!onlyHigh || row.getAttribute('data-impact') === 'high');
                row.hidden = !show;
                if (show) {
                    visible++;
                    if (row.getAttribute('data-impact') === 'high') high++;
                }
            });
            if (table) table.hidden = visible === 0;
            // Aviso de vacío: el de la semana/mes si ese periodo no tiene nada;
            // el de "alto impacto" si el periodo sí tiene eventos pero ninguno lo es.
            var inPeriodCount = 0;
            Array.prototype.forEach.call(rows, function (row) {
                if (period === 'month' ? row.getAttribute('data-month') === '1' : row.getAttribute('data-week') === period) inPeriodCount++;
            });
            Array.prototype.forEach.call(root.querySelectorAll('[data-cal-empty]'), function (el) {
                var kind = el.getAttribute('data-cal-empty');
                el.hidden = !(inPeriodCount === 0 ? kind === period : (visible === 0 && kind === 'high'));
            });
            if (counter) {
                counter.hidden = visible === 0;
                counter.textContent = counter.getAttribute('data-template').replace('{count}', visible).replace('{high}', high);
            }
            var active = root.querySelector('[data-cal-period].is-active');
            if (rangeEl && active) {
                rangeEl.textContent = active.getAttribute('data-range-text');
                rangeEl.hidden = false;
            }
        }

        Array.prototype.forEach.call(periodButtons, function (btn) {
            btn.addEventListener('click', function () {
                period = btn.getAttribute('data-cal-period');
                Array.prototype.forEach.call(periodButtons, function (b) { b.classList.toggle('is-active', b === btn); });
                apply();
            });
        });
        if (highBox) highBox.addEventListener('change', apply);
        apply();
    }

    formatTimes();
    initCalendarFilters();

    /* --------------------------------------------------------------- gráfica */

    var dataEl = document.getElementById('ta-data');
    var chartEl = document.getElementById('ta-chart');
    if (!dataEl || !chartEl || !window.Plotly) return;

    var D = JSON.parse(dataEl.textContent);
    var B = D.bars;
    var F = D.forecast || [];
    var L = D.levels || { supports: [], resistances: [] };
    var I = D.i18n;
    var DG = D.digits || { price: 2, level: 0, tick: 0 };
    var WEEKENDS = !!D.weekends;   // cripto: opera sábado y domingo
    var HAS_VOLUME = B.v.some(function (v) { return v > 0; });   // EUR/USD no trae volumen
    var NARROW = window.innerWidth < 640;
    var n = B.x.length;
    var lastClose = D.last_close;
    var HALF_DAY = 12 * 3600 * 1000;
    var DAY = 24 * 3600 * 1000;

    var css = getComputedStyle(root);
    function token(name, fallback) {
        var value = css.getPropertyValue(name);
        return (value && value.trim()) || fallback;
    }
    var C = {
        bull: token('--ta-bull', '#0ea678'),
        bear: token('--ta-bear', '#ec4b5c'),
        ink: token('--ta-ink', '#0b1220'),
        muted: token('--ta-muted', '#5b6579'),
        line: token('--ta-line', '#dde3ee'),
        support: token('--ta-blue', '#3b7bff'),
        resistance: token('--ta-amber', '#f0a020'),
        sma20: token('--ta-sma20', '#8a5cf6'),
        sma50: token('--ta-sma50', '#e2703a'),
        sma200: token('--ta-sma200', '#0b1220'),
        accent: token('--ta-accent', '#3b7bff')
    };
    var FONT = token('--ta-font-mono', "'JetBrains Mono', Consolas, monospace");

    function rgba(hex, alpha) {
        var h = hex.replace('#', '');
        if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
        var num = parseInt(h, 16);
        if (isNaN(num)) return hex;
        return 'rgba(' + ((num >> 16) & 255) + ',' + ((num >> 8) & 255) + ',' + (num & 255) + ',' + alpha + ')';
    }
    function fmt(value, digits) {
        if (value === null || value === undefined) return '—';
        var d = digits === undefined ? DG.price : digits;
        return Number(value).toLocaleString(locale, { minimumFractionDigits: d, maximumFractionDigits: d });
    }
    function dayDate(day, opts) {
        return new Date(day + 'T12:00:00Z').toLocaleDateString(locale, Object.assign({ timeZone: 'UTC' }, opts));
    }
    function shortDay(day) { return dayDate(day, { day: 'numeric', month: 'short' }); }
    function weekdayDay(day) { return dayDate(day, { weekday: 'short', day: 'numeric' }); }
    function toMs(day) { return Date.parse(day + 'T00:00:00Z'); }
    function toIso(ms) { return new Date(ms).toISOString(); }

    /* Días hábiles sin vela (feriados): se le pasan a Plotly como saltos de
       eje para que no queden huecos, igual que el fin de semana. */
    function missingWeekdays() {
        var have = {};
        B.x.forEach(function (x) { have[x] = true; });
        var out = [];
        for (var t = toMs(B.x[0]); t < toMs(B.x[n - 1]); t += DAY) {
            var day = new Date(t).getUTCDay();
            var key = new Date(t).toISOString().slice(0, 10);
            if (day !== 0 && day !== 6 && !have[key]) out.push(key);
        }
        return out;
    }

    /* ----- trazas ----- */
    var T_CANDLE = 0, T_BAND_HI = 1, T_BAND_LO = 2, T_FC_LINE = 3, T_FC_CANDLE = 4,
        T_SMA20 = 5, T_SMA50 = 6, T_SMA200 = 7, T_VOL = 8;
    var FORECAST_TRACES = [T_BAND_HI, T_BAND_LO, T_FC_LINE, T_FC_CANDLE];

    var fx = F.map(function (f) { return f.x; });
    var coneX = [B.x[n - 1]].concat(fx);
    var maxVol = Math.max.apply(null, B.v.concat([1]));

    var traces = [];
    traces[T_CANDLE] = {
        type: 'candlestick', name: I.price, x: B.x, open: B.o, high: B.h, low: B.l, close: B.c,
        increasing: { line: { color: C.bull, width: 1.4 }, fillcolor: C.bull },
        decreasing: { line: { color: C.bear, width: 1.4 }, fillcolor: C.bear },
        hoverinfo: 'none', whiskerwidth: 0.4
    };
    traces[T_BAND_HI] = {
        type: 'scatter', mode: 'lines', x: coneX, y: [lastClose].concat(F.map(function (f) { return f.band_hi; })),
        line: { width: 0 }, hoverinfo: 'skip', showlegend: false
    };
    traces[T_BAND_LO] = {
        type: 'scatter', mode: 'lines', x: coneX, y: [lastClose].concat(F.map(function (f) { return f.band_lo; })),
        line: { width: 0 }, fill: 'tonexty', fillcolor: rgba(C.accent, 0.14), hoverinfo: 'skip', showlegend: false
    };
    traces[T_FC_LINE] = {
        type: 'scatter', mode: 'lines', x: coneX, y: [lastClose].concat(F.map(function (f) { return f.c; })),
        line: { color: C.accent, width: 1.5, dash: 'dot' }, hoverinfo: 'skip', showlegend: false
    };
    traces[T_FC_CANDLE] = {
        type: 'candlestick', name: I.forecast, x: fx,
        open: F.map(function (f) { return f.o; }), high: F.map(function (f) { return f.h; }),
        low: F.map(function (f) { return f.l; }), close: F.map(function (f) { return f.c; }),
        increasing: { line: { color: C.bull, width: 2 }, fillcolor: rgba(C.bull, 0.3) },
        decreasing: { line: { color: C.bear, width: 2 }, fillcolor: rgba(C.bear, 0.3) },
        hoverinfo: 'none', whiskerwidth: 0.4
    };
    function smaTrace(key, color, width, visible) {
        return {
            type: 'scatter', mode: 'lines', x: B.x, y: B[key], connectgaps: false,
            line: { color: color, width: width }, hoverinfo: 'skip', showlegend: false, visible: visible
        };
    }
    traces[T_SMA20] = smaTrace('sma20', C.sma20, 1.4, true);
    traces[T_SMA50] = smaTrace('sma50', C.sma50, 1.6, true);
    traces[T_SMA200] = smaTrace('sma200', C.sma200, 1.6, false);
    traces[T_VOL] = {
        type: 'bar', x: B.x, y: B.v, yaxis: 'y2', visible: false, hoverinfo: 'skip', showlegend: false,
        marker: { color: B.c.map(function (c, i) { return c >= B.o[i] ? rgba(C.bull, 0.28) : rgba(C.bear, 0.28); }) }
    };

    /* ----- shapes / anotaciones (niveles, precio actual, zona de pronóstico) ----- */
    var shapes = [];
    var annotations = [];
    var levelShapes = [], levelAnns = [], forecastShapes = [], forecastAnns = [];

    function addLevel(level, kind) {
        var color = kind === 'support' ? C.support : C.resistance;
        // En pantallas angostas la etiqueta se acorta (S/R + precio) para no tapar las velas.
        var label = NARROW
            ? (kind === 'support' ? 'S ' : 'R ') + fmt(level.price, DG.level)
            : (kind === 'support' ? I.support : I.resistance) + ' ' + fmt(level.price, DG.level) + ' · ' + level.touches + '×';
        var pad = level.price * 0.0009;
        levelShapes.push(shapes.length);
        shapes.push({
            type: 'rect', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: level.price - pad, y1: level.price + pad,
            fillcolor: rgba(color, 0.14), line: { width: 0 }, layer: 'below'
        });
        levelShapes.push(shapes.length);
        shapes.push({
            type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: level.price, y1: level.price,
            line: { color: color, width: level.touches >= 3 ? 1.8 : 1.2, dash: level.touches >= 2 ? 'solid' : 'dash' }
        });
        levelAnns.push(annotations.length);
        annotations.push({
            xref: 'paper', yref: 'y', x: 0.005, y: level.price, xanchor: 'left', yanchor: 'bottom', showarrow: false,
            text: label, font: { size: 11, color: color, family: FONT }, bgcolor: 'rgba(255,255,255,0.82)', borderpad: 2
        });
    }
    L.supports.forEach(function (lv) { addLevel(lv, 'support'); });
    L.resistances.forEach(function (lv) { addLevel(lv, 'resistance'); });

    shapes.push({
        type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: lastClose, y1: lastClose,
        line: { color: C.ink, width: 1, dash: 'dot' }
    });
    annotations.push({
        xref: 'paper', yref: 'y', x: 1, y: lastClose, xanchor: 'left', yanchor: 'middle', showarrow: false,
        text: fmt(lastClose, DG.level), font: { size: 11, color: '#fff', family: FONT }, bgcolor: C.ink, borderpad: 3
    });

    if (F.length) {
        forecastShapes.push(shapes.length);
        shapes.push({
            type: 'rect', xref: 'x', yref: 'paper', y0: 0, y1: 1,
            x0: toIso(toMs(B.x[n - 1]) + HALF_DAY), x1: toIso(toMs(F[F.length - 1].x) + HALF_DAY),
            fillcolor: rgba(C.accent, 0.05), line: { width: 0 }, layer: 'below'
        });
        // La proyección se rotula con FECHAS: encabezado con el rango de días y,
        // bajo cada vela proyectada, su día (en vertical para que quepan 5 en celular).
        var firstDay = new Date(F[0].x + 'T12:00:00Z'), lastDay = new Date(F[F.length - 1].x + 'T12:00:00Z');
        var fcRange = firstDay.getUTCMonth() === lastDay.getUTCMonth()
            ? firstDay.getUTCDate() + '–' + shortDay(F[F.length - 1].x)
            : shortDay(F[0].x) + ' – ' + shortDay(F[F.length - 1].x);
        // En pantallas angostas la banda mide ~30 px: el encabezado se ancla por la
        // derecha (crece hacia las velas, no hacia el margen) y solo se rotulan
        // el primer y el último día para que las fechas no se encimen.
        forecastAnns.push(annotations.length);
        annotations.push({
            xref: 'x', yref: 'paper', y: 1, yanchor: 'top', showarrow: false, borderpad: 4,
            x: toIso(toMs(NARROW ? F[F.length - 1].x : B.x[n - 1]) + HALF_DAY),
            xanchor: NARROW ? 'right' : 'left', align: NARROW ? 'right' : 'left',
            text: I.forecast.toUpperCase() + '<br>' + fcRange,
            font: { size: 10, color: C.accent, family: FONT }
        });
        F.forEach(function (f, i) {
            if (NARROW && i !== 0 && i !== F.length - 1) return;
            forecastAnns.push(annotations.length);
            annotations.push({
                xref: 'x', yref: 'paper', x: f.x, y: 0.01, xanchor: 'center', yanchor: 'bottom', textangle: -90, showarrow: false,
                text: weekdayDay(f.x), font: { size: 10, color: C.accent, family: FONT },
                bgcolor: 'rgba(255,255,255,0.75)', borderpad: 2
            });
        });
    }

    // Temporalidad de la gráfica, rotulada dentro del plot (como una plataforma de trading).
    annotations.push({
        xref: 'paper', yref: 'paper', x: 0.45, y: 0.005, xanchor: 'center', yanchor: 'bottom', showarrow: false,
        text: D.asset_name + ' · ' + I.timeframe_short, font: { size: 11, color: C.ink, family: FONT },
        bgcolor: 'rgba(255,255,255,0.85)', borderpad: 3
    });
    var BASE_SHAPE_COUNT = shapes.length;

    /* ----- layout ----- */
    // Mercados de lunes a viernes: se ocultan fines de semana y feriados para
    // que no queden huecos. Cripto opera todos los días: el eje va continuo.
    var breaks = [];
    if (!WEEKENDS) {
        breaks.push({ bounds: ['sat', 'mon'] });
        var holidays = missingWeekdays();
        if (holidays.length) breaks.push({ values: holidays });
    }

    function plotHeight() { return window.innerWidth < 720 ? 420 : 540; }

    var layout = {
        height: plotHeight(),
        margin: { l: 6, r: 62, t: 8, b: 30 },
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: FONT, size: 11, color: C.muted },
        showlegend: false, dragmode: 'pan', hovermode: 'x', separators: lang === 'en' ? '.,' : ',.',
        xaxis: {
            type: 'date', rangeslider: { visible: false }, rangebreaks: breaks, tickformat: '%d %b',
            showgrid: false, linecolor: C.line, ticks: 'outside', tickcolor: C.line,
            showspikes: true, spikemode: 'across', spikesnap: 'cursor', spikethickness: 1, spikedash: 'dot', spikecolor: C.muted,
            fixedrange: false
        },
        yaxis: {
            side: 'right', tickformat: ',.' + DG.tick + 'f', gridcolor: rgba(C.ink, 0.06), zeroline: false, fixedrange: true,
            showspikes: true, spikemode: 'across', spikethickness: 1, spikedash: 'dot', spikecolor: C.muted
        },
        yaxis2: { overlaying: 'y', side: 'left', showgrid: false, showticklabels: false, zeroline: false, range: [0, maxVol * 4.2], fixedrange: true },
        shapes: shapes, annotations: annotations,
        newshape: { line: { color: C.ink, width: 2 }, fillcolor: rgba(C.ink, 0.08), layer: 'above' }
    };
    var config = { responsive: true, displaylogo: false, displayModeBar: false, doubleClick: false, scrollZoom: false };

    var gd = chartEl;
    var state = { bars: 63, forecast: true };

    /* ----- rango y auto-escala vertical ----- */
    function lastVisibleX() {
        return state.forecast && F.length ? toMs(F[F.length - 1].x) : toMs(B.x[n - 1]);
    }
    function rangeFor(barCount) {
        var start = barCount ? Math.max(0, n - barCount) : 0;
        return [toIso(toMs(B.x[start]) - HALF_DAY), toIso(lastVisibleX() + DAY)];
    }
    function fitY(xRange) {
        var t0 = Date.parse(xRange[0]), t1 = Date.parse(xRange[1]);
        var lo = Infinity, hi = -Infinity;
        for (var i = 0; i < n; i++) {
            var t = toMs(B.x[i]);
            if (t < t0 || t > t1) continue;
            if (B.l[i] < lo) lo = B.l[i];
            if (B.h[i] > hi) hi = B.h[i];
        }
        if (state.forecast) {
            F.forEach(function (f) {
                var t = toMs(f.x);
                if (t < t0 || t > t1) return;
                lo = Math.min(lo, f.band_lo); hi = Math.max(hi, f.band_hi);
            });
        }
        if (!isFinite(lo) || !isFinite(hi)) return;
        var pad = (hi - lo) * 0.06 || hi * 0.01;
        Plotly.relayout(gd, { 'yaxis.range': [lo - pad, hi + pad] });
    }
    function applyRange(barCount) {
        var r = rangeFor(barCount);
        state.bars = barCount;
        Plotly.relayout(gd, { 'xaxis.range': r }).then(function () { fitY(r); });
    }

    /* ----- lectura (OHLC) ----- */
    var readout = document.getElementById('ta-readout');
    function showBar(idx, isForecast) {
        if (!readout) return;
        var o, h, l, c, prev, day, extra = '';
        if (isForecast) {
            var f = F[idx];
            o = f.o; h = f.h; l = f.l; c = f.c; prev = f.o; day = f.x;
            extra = '<span class="ta-readout__tag">' + I.forecast + '</span> <span>' + I.band + ' ' + fmt(f.band_lo, DG.level) + ' – ' + fmt(f.band_hi, DG.level) + '</span>';
        } else {
            o = B.o[idx]; h = B.h[idx]; l = B.l[idx]; c = B.c[idx]; prev = idx > 0 ? B.c[idx - 1] : o; day = B.x[idx];
            var s20 = B.sma20[idx], s50 = B.sma50[idx];
            if (s20 !== null) extra += '<span style="color:' + C.sma20 + '">SMA20 ' + fmt(s20, DG.level) + '</span> ';
            if (s50 !== null) extra += '<span style="color:' + C.sma50 + '">SMA50 ' + fmt(s50, DG.level) + '</span>';
        }
        var change = prev ? (c / prev - 1) * 100 : 0;
        var d = new Date(day + 'T12:00:00Z').toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
        readout.innerHTML =
            '<span class="ta-readout__tf">' + I.timeframe_short + '</span> <strong>' + d + '</strong> ' +
            '<span>' + I.open + ' ' + fmt(o) + '</span> <span>' + I.high + ' ' + fmt(h) + '</span> ' +
            '<span>' + I.low + ' ' + fmt(l) + '</span> <span>' + I.close + ' ' + fmt(c) + '</span> ' +
            '<span class="' + (change >= 0 ? 'is-up' : 'is-down') + '">' + (change >= 0 ? '+' : '') + change.toFixed(2) + '%</span> ' + extra;
    }

    /* ----- controles ----- */
    var section = document.getElementById('ta-chart-section');

    function bindControls() {
        var rangeButtons = section.querySelectorAll('[data-range]');
        Array.prototype.forEach.call(rangeButtons, function (btn) {
            btn.addEventListener('click', function () {
                Array.prototype.forEach.call(rangeButtons, function (b) { b.classList.toggle('is-active', b === btn); });
                applyRange(parseInt(btn.getAttribute('data-range'), 10));
            });
        });

        var toolButtons = section.querySelectorAll('[data-tool]');
        function setTool(name) {
            Array.prototype.forEach.call(toolButtons, function (b) {
                var on = b.getAttribute('data-tool') === name;
                b.classList.toggle('is-active', on);
                b.setAttribute('aria-pressed', on ? 'true' : 'false');
            });
            Plotly.relayout(gd, { dragmode: name });
        }
        Array.prototype.forEach.call(toolButtons, function (btn) {
            btn.addEventListener('click', function () { setTool(btn.getAttribute('data-tool')); });
        });

        function clearDrawings() {
            var kept = (gd.layout.shapes || []).slice(0, BASE_SHAPE_COUNT);
            Plotly.relayout(gd, { shapes: kept });
        }
        section.querySelector('[data-action="clear"]').addEventListener('click', clearDrawings);
        section.querySelector('[data-action="reset"]').addEventListener('click', function () {
            clearDrawings();
            setTool('pan');
            var target = section.querySelector('[data-range="63"]');
            Array.prototype.forEach.call(rangeButtons, function (b) { b.classList.toggle('is-active', b === target); });
            applyRange(63);
        });

        function setVisible(indices, visible) { Plotly.restyle(gd, { visible: visible }, indices); }
        function setShapesVisible(shapeIdx, annIdx, visible) {
            var update = {};
            shapeIdx.forEach(function (i) { update['shapes[' + i + '].visible'] = visible; });
            annIdx.forEach(function (i) { update['annotations[' + i + '].visible'] = visible; });
            Plotly.relayout(gd, update);
        }
        var layerHandlers = {
            sma20: function (on) { setVisible([T_SMA20], on); },
            sma50: function (on) { setVisible([T_SMA50], on); },
            sma200: function (on) { setVisible([T_SMA200], on); },
            volume: function (on) { setVisible([T_VOL], on); },
            levels: function (on) { setShapesVisible(levelShapes, levelAnns, on); },
            forecast: function (on) {
                state.forecast = on;
                setVisible(FORECAST_TRACES, on);
                setShapesVisible(forecastShapes, forecastAnns, on);
                applyRange(state.bars);
            }
        };
        Array.prototype.forEach.call(section.querySelectorAll('[data-layer]'), function (box) {
            var key = box.getAttribute('data-layer');
            if (key === 'forecast' && !F.length) { box.closest('label').hidden = true; return; }
            if (key === 'volume' && !HAS_VOLUME) { box.closest('label').hidden = true; return; }
            box.addEventListener('change', function () { layerHandlers[key](box.checked); });
        });
    }

    /* ----- arranque ----- */
    var initialRange = rangeFor(state.bars);
    layout.xaxis.range = initialRange;
    Plotly.newPlot(gd, traces, layout, config).then(function () {
        fitY(initialRange);
        showBar(n - 1, false);
        bindControls();

        gd.on('plotly_hover', function (ev) {
            var p = ev.points && ev.points[0];
            if (!p) return;
            if (p.curveNumber === T_FC_CANDLE) showBar(p.pointNumber, true);
            else if (p.curveNumber === T_CANDLE) showBar(p.pointNumber, false);
        });
        // Se vuelve a la última vela solo al salir de la gráfica (con plotly_unhover
        // parpadea entre vela y vela).
        gd.addEventListener('mouseleave', function () { showBar(n - 1, false); });

        // Al mover/zoomear en X se reajusta el eje de precio a lo visible
        // (como una plataforma de trading); el eje Y queda fijo para el usuario.
        gd.on('plotly_relayout', function (ev) {
            if (ev['xaxis.range[0]'] && ev['xaxis.range[1]']) {
                fitY([ev['xaxis.range[0]'], ev['xaxis.range[1]']]);
            }
        });
    });

    window.addEventListener('resize', function () {
        var h = plotHeight();
        if (gd.layout && gd.layout.height !== h) Plotly.relayout(gd, { height: h });
        if (macdGd && macdGd.layout) {
            var mh = NARROW ? 300 : 340;
            if (macdGd.layout.height !== mh) Plotly.relayout(macdGd, { height: mh });
        }
    });

    /* ------------------------------------------------------ MACD por hora */
    // Tres series sobre un eje "por barra" (sin huecos de noche/fin de semana):
    // histograma (verde/rojo según el signo), línea MACD y línea de señal.
    var macdGd = document.getElementById('ta-macd');
    var M = D.macd1h;
    if (M && macdGd) {
        var mn = M.x.length;
        var macdStamp = M.x.map(function (iso) { return new Date(iso); });
        var stampFmt = { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        var macdRead = document.getElementById('ta-macd-readout');

        // Una marca en el eje por cada día nuevo (hora local del visitante).
        var tickVals = [], tickText = [], lastDay = '';
        macdStamp.forEach(function (d, i) {
            var label = d.toLocaleDateString(locale, { day: 'numeric', month: 'short' });
            if (label !== lastDay) { tickVals.push(i); tickText.push(label); lastDay = label; }
        });

        var idx = M.x.map(function (_, i) { return i; });
        var histColors = M.hist.map(function (v) { return v >= 0 ? rgba(C.bull, 0.65) : rgba(C.bear, 0.65); });
        var macdTraces = [
            { type: 'bar', x: idx, y: M.hist, marker: { color: histColors }, name: I.macd_hist, hoverinfo: 'skip' },
            { type: 'scatter', mode: 'lines', x: idx, y: M.macd, name: 'MACD', hoverinfo: 'skip', line: { color: C.support, width: 2 } },
            { type: 'scatter', mode: 'lines', x: idx, y: M.signal, name: I.macd_signal, hoverinfo: 'skip', line: { color: C.sma50, width: 2 } }
        ];

        function showMacd(i) {
            if (!macdRead) return;
            var hist = M.hist[i];
            macdRead.innerHTML =
                '<strong>' + macdStamp[i].toLocaleString(locale, stampFmt) + '</strong> ' +
                '<span style="color:' + C.support + '">MACD ' + fmt(M.macd[i], M.digits) + '</span> ' +
                '<span style="color:' + C.sma50 + '">' + I.macd_signal + ' ' + fmt(M.signal[i], M.digits) + '</span> ' +
                '<span class="' + (hist >= 0 ? 'is-up' : 'is-down') + '">' + I.macd_hist + ' ' + fmt(hist, M.digits) + '</span>';
        }

        var macdView = Math.min(72, mn);
        function macdRange(count) { return [mn - count - 0.5, mn - 0.5 + 1]; }
        function macdFitY(range) {
            var from = Math.max(0, Math.ceil(range[0])), to = Math.min(mn - 1, Math.floor(range[1]));
            var lo = 0, hi = 0;
            for (var i = from; i <= to; i++) {
                lo = Math.min(lo, M.hist[i], M.macd[i], M.signal[i]);
                hi = Math.max(hi, M.hist[i], M.macd[i], M.signal[i]);
            }
            var pad = (hi - lo) * 0.12 || 1;
            Plotly.relayout(macdGd, { 'yaxis.range': [lo - pad, hi + pad] });
        }

        var macdLayout = {
            height: NARROW ? 300 : 340,
            margin: { l: 6, r: 62, t: 8, b: 44 },
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: FONT, size: 11, color: C.muted },
            showlegend: true, legend: { orientation: 'h', x: 0, y: 1.12, font: { size: 11 } },
            dragmode: 'pan', hovermode: 'x', bargap: 0.25, separators: lang === 'en' ? '.,' : ',.',
            xaxis: {
                range: macdRange(macdView), tickmode: 'array', tickvals: tickVals, ticktext: tickText,
                title: { text: '', font: { size: 11 }, standoff: 6 },
                showgrid: false, zeroline: false, linecolor: C.line, ticks: 'outside', tickcolor: C.line,
                showspikes: true, spikemode: 'across', spikethickness: 1, spikedash: 'dot', spikecolor: C.muted
            },
            yaxis: {
                side: 'right', tickformat: ',.' + M.digits + '~f', gridcolor: rgba(C.ink, 0.06), zeroline: true,
                zerolinecolor: rgba(C.ink, 0.5), zerolinewidth: 1.2, fixedrange: true
            }
        };
        macdLayout.xaxis.title.text = document.getElementById('ta-macd-section').getAttribute('data-x-title') || '';

        Plotly.newPlot(macdGd, macdTraces, macdLayout, { responsive: true, displaylogo: false, displayModeBar: false }).then(function () {
            macdFitY(macdRange(macdView));
            showMacd(mn - 1);
            macdGd.on('plotly_hover', function (ev) {
                var p = ev.points && ev.points[0];
                if (p) showMacd(Math.round(p.x));
            });
            macdGd.addEventListener('mouseleave', function () { showMacd(mn - 1); });
            macdGd.on('plotly_relayout', function (ev) {
                if (ev['xaxis.range[0]'] !== undefined && ev['xaxis.range[1]'] !== undefined) {
                    macdFitY([ev['xaxis.range[0]'], ev['xaxis.range[1]']]);
                }
            });
        });

        var macdButtons = document.querySelectorAll('[data-macd-range]');
        Array.prototype.forEach.call(macdButtons, function (btn) {
            btn.addEventListener('click', function () {
                Array.prototype.forEach.call(macdButtons, function (b) { b.classList.toggle('is-active', b === btn); });
                var r = macdRange(Math.min(parseInt(btn.getAttribute('data-macd-range'), 10), mn));
                Plotly.relayout(macdGd, { 'xaxis.range': r }).then(function () { macdFitY(r); });
            });
        });
    }
})();
