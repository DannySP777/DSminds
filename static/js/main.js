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
        if (e.target.closest("a") || e.target.closest(".ticker-select") || e.target.closest(".remove-ticker-form")) {
            return; // los links navegan normal; el radio ya se maneja con "change"; quitar tiene su propio submit
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

function initCookieBanner() {
    var banner = document.getElementById("cookie-banner");
    if (!banner) {
        return;
    }

    var STORAGE_KEY = "dsms_cookie_consent";

    // NOTA: cuando se agreguen scripts de AdSense/Analytics reales, deben
    // consultar localStorage.getItem("dsms_cookie_consent") === "accepted"
    // antes de cargarse, para respetar la elección del usuario.
    if (!localStorage.getItem(STORAGE_KEY)) {
        banner.hidden = false;
    }

    function respond(value) {
        localStorage.setItem(STORAGE_KEY, value);
        banner.hidden = true;
    }

    document.getElementById("cookie-accept").addEventListener("click", function () {
        respond("accepted");
    });
    document.getElementById("cookie-decline").addEventListener("click", function () {
        respond("declined");
    });
}

function initAddTickerSearch() {
    var input = document.getElementById("add-ticker-input");
    var list = document.getElementById("add-ticker-suggestions");
    var symbolField = document.getElementById("add-ticker-symbol");
    var form = document.getElementById("add-ticker-form");
    var submitBtn = document.getElementById("add-ticker-submit");
    if (!input || !list || !symbolField || !form) {
        return;
    }

    var url = list.dataset.autocompleteUrl;
    var searchingText = list.dataset.searchingText;
    var noResultsText = list.dataset.noResultsText;
    var debounceTimer = null;
    var currentRequestId = 0;

    function hide() {
        list.hidden = true;
        list.innerHTML = "";
    }

    function renderEmpty(text) {
        list.innerHTML = "";
        var li = document.createElement("li");
        li.className = "add-ticker-suggestion add-ticker-suggestion--empty";
        li.textContent = text;
        list.appendChild(li);
        list.hidden = false;
    }

    function renderResults(results) {
        list.innerHTML = "";
        if (!results.length) {
            renderEmpty(noResultsText);
            return;
        }
        results.forEach(function (item) {
            var li = document.createElement("li");
            li.className = "add-ticker-suggestion";
            li.dataset.symbol = item.symbol;

            var symbolSpan = document.createElement("span");
            symbolSpan.className = "add-ticker-suggestion__symbol";
            symbolSpan.textContent = item.symbol;

            var nameSpan = document.createElement("span");
            nameSpan.className = "add-ticker-suggestion__name";
            nameSpan.textContent = item.name || "";

            var exchangeSpan = document.createElement("span");
            exchangeSpan.className = "add-ticker-suggestion__exchange";
            exchangeSpan.textContent = item.exchange || "";

            li.appendChild(symbolSpan);
            li.appendChild(nameSpan);
            li.appendChild(exchangeSpan);
            list.appendChild(li);
        });
        list.hidden = false;
    }

    function search(query) {
        var requestId = ++currentRequestId;
        renderEmpty(searchingText);
        fetch(url + "?q=" + encodeURIComponent(query))
            .then(function (res) {
                return res.json();
            })
            .then(function (data) {
                if (requestId !== currentRequestId) {
                    return; // respuesta obsoleta (el usuario ya siguió escribiendo)
                }
                renderResults(data.results || []);
            })
            .catch(function () {
                if (requestId === currentRequestId) {
                    hide();
                }
            });
    }

    input.addEventListener("input", function () {
        var query = input.value.trim();
        clearTimeout(debounceTimer);
        if (query.length < 2) {
            hide();
            return;
        }
        debounceTimer = setTimeout(function () {
            search(query);
        }, 350);
    });

    list.addEventListener("click", function (e) {
        var item = e.target.closest(".add-ticker-suggestion");
        if (!item || !item.dataset.symbol) {
            return;
        }
        symbolField.value = item.dataset.symbol;
        form.submit();
    });

    document.addEventListener("click", function (e) {
        if (!e.target.closest(".add-ticker-combo")) {
            hide();
        }
    });

    if (submitBtn) {
        submitBtn.addEventListener("click", function () {
            var value = input.value.trim();
            if (!value) {
                input.focus();
                return;
            }
            symbolField.value = value.toUpperCase();
            form.submit();
        });
    }

    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            if (submitBtn) {
                submitBtn.click();
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    initHoverPreview();
    initScannerDashboard();
    initCookieBanner();
    initAddTickerSearch();
});
