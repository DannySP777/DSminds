function runInlineScripts(container) {
    var scripts = container.querySelectorAll("script");
    scripts.forEach(function (oldScript) {
        var newScript = document.createElement("script");
        newScript.text = oldScript.text;
        oldScript.replaceWith(newScript);
    });
}

function initHoverPreview() {
    var links = document.querySelectorAll(".ticker-link");
    if (!links.length) {
        return;
    }

    var tooltip = document.createElement("div");
    tooltip.className = "chart-hover-tooltip";
    document.body.appendChild(tooltip);

    var cache = {};
    var hideTimer = null;
    var activeSymbol = null;

    function positionTooltip(anchor) {
        var rect = anchor.getBoundingClientRect();
        var top = rect.bottom + window.scrollY + 8;
        var left = rect.left + window.scrollX;

        var maxLeft = window.scrollX + document.documentElement.clientWidth - 320;
        if (left > maxLeft) {
            left = Math.max(maxLeft, 0);
        }

        tooltip.style.top = top + "px";
        tooltip.style.left = left + "px";
    }

    function render(html) {
        tooltip.innerHTML = html;
        runInlineScripts(tooltip);
    }

    function show(anchor, symbol) {
        activeSymbol = symbol;
        positionTooltip(anchor);
        tooltip.classList.add("chart-hover-tooltip--visible");

        if (cache[symbol]) {
            render(cache[symbol]);
            return;
        }

        var i18n = window.DSMS_I18N || {};
        tooltip.innerHTML = '<p class="mini-chart-loading">' + (i18n.loadingChartOf || "Cargando gráfica de") + " " + symbol + "&hellip;</p>";

        fetch("/accion/" + encodeURIComponent(symbol) + "/mini/")
            .then(function (response) {
                return response.text();
            })
            .then(function (html) {
                cache[symbol] = html;
                if (activeSymbol === symbol) {
                    render(html);
                }
            })
            .catch(function () {
                if (activeSymbol === symbol) {
                    tooltip.innerHTML = '<p class="mini-chart-error">' + ((window.DSMS_I18N || {}).chartError || "No se pudo cargar la gráfica.") + '</p>';
                }
            });
    }

    function scheduleHide() {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(function () {
            tooltip.classList.remove("chart-hover-tooltip--visible");
            activeSymbol = null;
        }, 150);
    }

    links.forEach(function (link) {
        link.addEventListener("mouseenter", function () {
            clearTimeout(hideTimer);
            show(link, link.dataset.symbol);
        });
        link.addEventListener("mouseleave", scheduleHide);
    });

    tooltip.addEventListener("mouseenter", function () {
        clearTimeout(hideTimer);
    });
    tooltip.addEventListener("mouseleave", scheduleHide);
}

// Usado por el click de cada fila del Top 10 en home.html — un solo
// lugar que sabe pedir los paneles AJAX de gráfica/indicadores y
// ejecutar su <script> embebido (Plotly no corre si solo se hace
// innerHTML, ver runInlineScripts arriba).
var dsmsCurrentSymbol = null;

function dsmsSetLoading(el) {
    el.innerHTML = '<p class="mini-chart-loading">' + ((window.DSMS_I18N || {}).loading || "Cargando") + '&hellip;</p>';
}

function loadChart(symbol, interval) {
    var chartBody = document.getElementById("chart-panel-body");
    if (!chartBody) {
        return;
    }
    dsmsSetLoading(chartBody);
    fetch("/accion/" + encodeURIComponent(symbol) + "/panel-grafica/?interval=" + encodeURIComponent(interval))
        .then(function (r) { return r.text(); })
        .then(function (html) {
            chartBody.innerHTML = html;
            runInlineScripts(chartBody);
        })
        .catch(function () {
            chartBody.innerHTML = '<p class="mini-chart-error">' + ((window.DSMS_I18N || {}).chartError || "No se pudo cargar la gráfica.") + '</p>';
        });
}

function loadIndicators(symbol) {
    var indicatorsBody = document.getElementById("indicators-panel-body");
    if (!indicatorsBody) {
        return;
    }
    dsmsSetLoading(indicatorsBody);
    fetch("/accion/" + encodeURIComponent(symbol) + "/panel-indicadores/")
        .then(function (r) { return r.text(); })
        .then(function (html) {
            indicatorsBody.innerHTML = html;
            // El panel de indicadores incluye la gráfica de balances
            // financieros (Plotly, ver financials_panel.html), que trae
            // su propio <script> embebido — sin esto, ese script nunca
            // se ejecuta y la gráfica queda en blanco.
            runInlineScripts(indicatorsBody);
        })
        .catch(function () {
            indicatorsBody.innerHTML = '<p class="mini-chart-error">' + ((window.DSMS_I18N || {}).indicatorsError || "No se pudieron cargar los indicadores.") + '</p>';
        });
}

function selectSymbol(symbol) {
    if (symbol === dsmsCurrentSymbol) {
        return;
    }
    dsmsCurrentSymbol = symbol;
    loadChart(symbol, "1d");
    loadIndicators(symbol);
    document.dispatchEvent(new CustomEvent("dsms:symbol-selected", { detail: { symbol: symbol } }));
}

function initScannerDashboard() {
    var chartPanel = document.querySelector(".dashboard-panel--chart");
    var chartBody = document.getElementById("chart-panel-body");
    if (!chartPanel || !chartBody) {
        return;
    }

    var initialSymbol = chartBody.querySelector(".dashboard-chart-symbol");
    dsmsCurrentSymbol = initialSymbol ? initialSymbol.textContent.trim() : dsmsCurrentSymbol;

    chartPanel.addEventListener("click", function (e) {
        var intervalLink = e.target.closest(".interval-link");
        if (!intervalLink || !dsmsCurrentSymbol) {
            return;
        }
        e.preventDefault();
        chartPanel.querySelectorAll(".interval-link").forEach(function (a) {
            a.classList.toggle("interval-link--active", a === intervalLink);
        });
        loadChart(dsmsCurrentSymbol, intervalLink.dataset.interval);
    });
}

function updateConsent(granted) {
    // gtag ya existe desde el <head> (ver templates/base.html) si hay
    // Analytics o AdSense configurados; si no hay ninguno de los dos,
    // no existe y no hay nada que actualizar.
    if (typeof window.gtag !== "function") {
        return;
    }
    var state = granted ? "granted" : "denied";
    window.gtag("consent", "update", {
        ad_storage: state,
        ad_user_data: state,
        ad_personalization: state,
        analytics_storage: state
    });
}

function initCookieBanner() {
    var banner = document.getElementById("cookie-banner");
    if (!banner) {
        return;
    }

    var STORAGE_KEY = "dsms_cookie_consent";

    if (!localStorage.getItem(STORAGE_KEY)) {
        banner.hidden = false;
    }

    function respond(value) {
        localStorage.setItem(STORAGE_KEY, value);
        banner.hidden = true;
        updateConsent(value === "accepted");
    }

    document.getElementById("cookie-accept").addEventListener("click", function () {
        respond("accepted");
    });
    document.getElementById("cookie-decline").addEventListener("click", function () {
        respond("declined");
    });
}

document.addEventListener("DOMContentLoaded", function () {
    initHoverPreview();
    initScannerDashboard();
    initCookieBanner();
});
