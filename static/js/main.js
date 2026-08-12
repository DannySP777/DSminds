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

        tooltip.innerHTML = '<p class="mini-chart-loading">Cargando gráfica de ' + symbol + "&hellip;</p>";

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
                    tooltip.innerHTML = '<p class="mini-chart-error">No se pudo cargar la gráfica.</p>';
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

function initScannerDashboard() {
    var table = document.querySelector(".dashboard-panel--table");
    var chartBody = document.getElementById("chart-panel-body");
    var indicatorsBody = document.getElementById("indicators-panel-body");
    if (!table || !chartBody || !indicatorsBody) {
        return;
    }

    var currentSymbol = chartBody.querySelector(".dashboard-chart-symbol");
    currentSymbol = currentSymbol ? currentSymbol.textContent.trim() : null;

    function setLoading(el) {
        el.innerHTML = '<p class="mini-chart-loading">Cargando&hellip;</p>';
    }

    function loadChart(symbol, interval) {
        setLoading(chartBody);
        fetch("/accion/" + encodeURIComponent(symbol) + "/panel-grafica/?interval=" + encodeURIComponent(interval))
            .then(function (r) { return r.text(); })
            .then(function (html) {
                chartBody.innerHTML = html;
                runInlineScripts(chartBody);
            })
            .catch(function () {
                chartBody.innerHTML = '<p class="mini-chart-error">No se pudo cargar la gráfica.</p>';
            });
    }

    function loadIndicators(symbol) {
        setLoading(indicatorsBody);
        fetch("/accion/" + encodeURIComponent(symbol) + "/panel-indicadores/")
            .then(function (r) { return r.text(); })
            .then(function (html) {
                indicatorsBody.innerHTML = html;
            })
            .catch(function () {
                indicatorsBody.innerHTML = '<p class="mini-chart-error">No se pudieron cargar los indicadores.</p>';
            });
    }

    function selectSymbol(symbol) {
        document.querySelectorAll(".scan-row").forEach(function (row) {
            row.classList.toggle("is-selected", row.dataset.symbol === symbol);
        });
        document.querySelectorAll(".ticker-select").forEach(function (input) {
            input.checked = input.dataset.symbol === symbol;
        });

        if (symbol === currentSymbol) {
            return;
        }
        currentSymbol = symbol;

        loadChart(symbol, "1d");
        loadIndicators(symbol);
    }

    table.addEventListener("change", function (e) {
        var radio = e.target.closest(".ticker-select");
        if (radio) {
            selectSymbol(radio.dataset.symbol);
        }
    });

    table.addEventListener("click", function (e) {
        if (e.target.closest("a") || e.target.closest(".ticker-select")) {
            return; // los links navegan normal; el radio ya se maneja con "change"
        }
        var row = e.target.closest(".scan-row");
        if (row) {
            selectSymbol(row.dataset.symbol);
        }
    });

    document.querySelector(".dashboard-panel--chart").addEventListener("click", function (e) {
        var intervalLink = e.target.closest(".interval-link");
        if (!intervalLink || !currentSymbol) {
            return;
        }
        e.preventDefault();
        document.querySelectorAll(".dashboard-panel--chart .interval-link").forEach(function (a) {
            a.classList.toggle("interval-link--active", a === intervalLink);
        });
        loadChart(currentSymbol, intervalLink.dataset.interval);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    initHoverPreview();
    initScannerDashboard();
});
