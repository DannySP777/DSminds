// static/js/tools.js
//
// Las 3 calculadoras de /herramientas/ — 100% client-side, sin roundtrip
// al servidor. Cada página incluye este mismo archivo; qué calculadora
// arrancar se decide leyendo el atributo data-tool del .tool-workspace
// presente en esa página (una sola por página).

(function () {
    "use strict";

    function fmtMoney(value, lang, decimals) {
        if (!isFinite(value)) value = 0;
        if (decimals === undefined) decimals = Math.abs(value) < 1000 ? 2 : 0;
        var locale = lang === "en" ? "en-US" : "es-AR";
        var formatted;
        try {
            formatted = value.toLocaleString(locale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
        } catch (e) {
            formatted = value.toFixed(decimals);
        }
        return "$" + formatted;
    }

    function fmtNumber(value, lang, decimals) {
        if (!isFinite(value)) value = 0;
        var locale = lang === "en" ? "en-US" : "es-AR";
        try {
            return value.toLocaleString(locale, { maximumFractionDigits: decimals === undefined ? 2 : decimals });
        } catch (e) {
            return value.toFixed(decimals === undefined ? 2 : decimals);
        }
    }

    function syncPair(rangeEl, numberEl, onChange) {
        rangeEl.addEventListener("input", function () {
            numberEl.value = rangeEl.value;
            onChange();
        });
        numberEl.addEventListener("input", function () {
            var v = parseFloat(numberEl.value);
            if (!isNaN(v)) {
                var min = parseFloat(rangeEl.min), max = parseFloat(rangeEl.max);
                rangeEl.value = Math.min(max, Math.max(min, v));
            }
            onChange();
        });
    }

    function getLang() {
        return (window.DSMS_TOOLS_I18N || {}).lang || "es";
    }

    // ---------- Interés compuesto ----------
    function initCompoundInterest() {
        var initialRange = document.getElementById("ci-initial-range");
        if (!initialRange) return;
        var initialNumber = document.getElementById("ci-initial-number");
        var monthlyRange = document.getElementById("ci-monthly-range");
        var monthlyNumber = document.getElementById("ci-monthly-number");
        var rateRange = document.getElementById("ci-rate-range");
        var rateNumber = document.getElementById("ci-rate-number");
        var yearsRange = document.getElementById("ci-years-range");
        var yearsNumber = document.getElementById("ci-years-number");
        var finalValueEl = document.getElementById("ci-final-value");
        var contributedValueEl = document.getElementById("ci-contributed-value");
        var interestValueEl = document.getElementById("ci-interest-value");
        var chartTotal = document.getElementById("ci-chart-total");
        var chartContributed = document.getElementById("ci-chart-contributed");

        function calc() {
            var initial = parseFloat(initialNumber.value) || 0;
            var monthly = parseFloat(monthlyNumber.value) || 0;
            var annualRate = parseFloat(rateNumber.value) || 0;
            var years = Math.max(1, parseInt(yearsNumber.value, 10) || 1);
            var monthlyRate = annualRate / 100 / 12;
            var months = years * 12;

            var balance = initial;
            var contributed = initial;
            var yearlyBalances = [balance];
            var yearlyContributed = [contributed];

            for (var m = 1; m <= months; m++) {
                balance = balance * (1 + monthlyRate) + monthly;
                contributed += monthly;
                if (m % 12 === 0) {
                    yearlyBalances.push(balance);
                    yearlyContributed.push(contributed);
                }
            }

            var lang = getLang();
            finalValueEl.textContent = fmtMoney(balance, lang);
            contributedValueEl.textContent = fmtMoney(contributed, lang);
            interestValueEl.textContent = fmtMoney(balance - contributed, lang);

            drawAreaChart(chartTotal, chartContributed, yearlyBalances, yearlyContributed);
        }

        syncPair(initialRange, initialNumber, calc);
        syncPair(monthlyRange, monthlyNumber, calc);
        syncPair(rateRange, rateNumber, calc);
        syncPair(yearsRange, yearsNumber, calc);
        calc();
    }

    function drawAreaChart(totalEl, contributedEl, totalSeries, contributedSeries) {
        var W = 400, H = 180, padTop = 10;
        var maxVal = Math.max.apply(null, totalSeries) || 1;
        var n = totalSeries.length - 1;

        function pts(series) {
            var out = [];
            for (var i = 0; i <= n; i++) {
                var x = n === 0 ? 0 : (i / n) * W;
                var y = H - (series[i] / maxVal) * (H - padTop);
                out.push(x.toFixed(1) + "," + y.toFixed(1));
            }
            return out;
        }

        var totalPts = pts(totalSeries);
        var contribPts = pts(contributedSeries);

        totalEl.setAttribute("points", "0," + H + " " + totalPts.join(" ") + " " + W + "," + H);
        contributedEl.setAttribute("points", "0," + H + " " + contribPts.join(" ") + " " + W + "," + H);
    }

    // ---------- Riesgo / beneficio ----------
    function initRiskReward() {
        var capitalRange = document.getElementById("rr-capital-range");
        if (!capitalRange) return;
        var capitalNumber = document.getElementById("rr-capital-number");
        var riskPctRange = document.getElementById("rr-risk-pct-range");
        var riskPctNumber = document.getElementById("rr-risk-pct-number");
        var entryEl = document.getElementById("rr-entry-number");
        var stopEl = document.getElementById("rr-stop-number");
        var targetEl = document.getElementById("rr-target-number");
        var amountValueEl = document.getElementById("rr-amount-value");
        var sizeValueEl = document.getElementById("rr-size-value");
        var ratioValueEl = document.getElementById("rr-ratio-value");
        var gainValueEl = document.getElementById("rr-gain-value");
        var barRiskFill = document.getElementById("rr-bar-risk-fill");
        var barRiskValue = document.getElementById("rr-bar-risk-value");
        var barRewardFill = document.getElementById("rr-bar-reward-fill");
        var barRewardValue = document.getElementById("rr-bar-reward-value");
        var warningEl = document.getElementById("rr-warning");

        function calc() {
            var lang = getLang();
            var capital = parseFloat(capitalNumber.value) || 0;
            var riskPct = parseFloat(riskPctNumber.value) || 0;
            var entry = parseFloat(entryEl.value);
            var stop = parseFloat(stopEl.value);
            var target = parseFloat(targetEl.value);

            var riskAmount = capital * (riskPct / 100);
            var riskPerUnit = Math.abs(entry - stop);
            var rewardPerUnit = Math.abs(target - entry);
            var invalid = !riskPerUnit || isNaN(entry) || isNaN(stop) || isNaN(target);

            warningEl.hidden = !invalid;

            var positionSize = invalid ? 0 : riskAmount / riskPerUnit;
            var potentialGain = positionSize * rewardPerUnit;
            var rrRatio = riskPerUnit ? rewardPerUnit / riskPerUnit : 0;

            amountValueEl.textContent = fmtMoney(riskAmount, lang);
            sizeValueEl.textContent = invalid ? "0" : fmtNumber(positionSize, lang, 2);
            ratioValueEl.textContent = invalid ? "—" : "1:" + rrRatio.toFixed(2);
            gainValueEl.textContent = fmtMoney(potentialGain, lang);

            var maxBar = Math.max(riskAmount, potentialGain, 1);
            barRiskFill.style.width = Math.min(100, (riskAmount / maxBar) * 100) + "%";
            barRewardFill.style.width = Math.min(100, (potentialGain / maxBar) * 100) + "%";
            barRiskValue.textContent = fmtMoney(riskAmount, lang);
            barRewardValue.textContent = fmtMoney(potentialGain, lang);
        }

        syncPair(capitalRange, capitalNumber, calc);
        syncPair(riskPctRange, riskPctNumber, calc);
        [entryEl, stopEl, targetEl].forEach(function (el) {
            el.addEventListener("input", calc);
        });
        calc();
    }

    // ---------- Fair Value Gap ----------
    function initFairValueGap() {
        var c1HighEl = document.getElementById("fvg-c1-high-number");
        if (!c1HighEl) return;
        var c1LowEl = document.getElementById("fvg-c1-low-number");
        var c3HighEl = document.getElementById("fvg-c3-high-number");
        var c3LowEl = document.getElementById("fvg-c3-low-number");
        var typeValueEl = document.getElementById("fvg-type-value");
        var sizeValueEl = document.getElementById("fvg-size-value");
        var midValueEl = document.getElementById("fvg-mid-value");
        var gapZoneEl = document.getElementById("fvg-gap-zone");
        var bar1El = document.getElementById("fvg-bar1");
        var bar3El = document.getElementById("fvg-bar3");
        var midLineEl = document.getElementById("fvg-mid-line");
        var gapLabelEl = document.getElementById("fvg-gap-label");

        function calc() {
            var lang = getLang();
            var i18n = window.DSMS_TOOLS_I18N || {};
            var c1h = parseFloat(c1HighEl.value), c1l = parseFloat(c1LowEl.value);
            var c3h = parseFloat(c3HighEl.value), c3l = parseFloat(c3LowEl.value);
            if ([c1h, c1l, c3h, c3l].some(function (v) { return isNaN(v); })) return;

            var bullish = c3l > c1h;
            var bearish = c3h < c1l;
            var type, gapLow, gapHigh;

            if (bullish) {
                type = "bullish"; gapLow = c1h; gapHigh = c3l;
            } else if (bearish) {
                type = "bearish"; gapLow = c3h; gapHigh = c1l;
            } else {
                type = "none"; gapLow = null; gapHigh = null;
            }

            typeValueEl.textContent = type === "bullish" ? i18n.bullish : type === "bearish" ? i18n.bearish : i18n.none;
            typeValueEl.style.color = type === "bullish" ? "var(--bull)" : type === "bearish" ? "var(--bear)" : "var(--muted)";

            if (type === "none") {
                sizeValueEl.textContent = fmtMoney(0, lang);
                midValueEl.textContent = "—";
                gapLabelEl.style.opacity = "0";
            } else {
                var size = gapHigh - gapLow;
                var mid = (gapHigh + gapLow) / 2;
                sizeValueEl.textContent = fmtMoney(size, lang);
                midValueEl.textContent = fmtMoney(mid, lang);
                gapLabelEl.style.opacity = "1";
            }

            drawFvgSvg(c1h, c1l, c3h, c3l, gapLow, gapHigh);
        }

        function drawFvgSvg(c1h, c1l, c3h, c3l, gapLow, gapHigh) {
            var H = 160, padTop = 20, padBottom = 20;
            var allVals = [c1h, c1l, c3h, c3l];
            var min = Math.min.apply(null, allVals);
            var max = Math.max.apply(null, allVals);
            var span = max - min || 1;
            var pad = span * 0.15;
            min -= pad; max += pad;
            span = max - min;

            function y(v) {
                return padTop + (1 - (v - min) / span) * (H - padTop - padBottom);
            }

            var bar1Top = y(c1h), bar1Bottom = y(c1l);
            var bar3Top = y(c3h), bar3Bottom = y(c3l);

            bar1El.setAttribute("y", bar1Top.toFixed(1));
            bar1El.setAttribute("height", Math.max(2, bar1Bottom - bar1Top).toFixed(1));
            bar3El.setAttribute("y", bar3Top.toFixed(1));
            bar3El.setAttribute("height", Math.max(2, bar3Bottom - bar3Top).toFixed(1));

            if (gapLow !== null) {
                var gapTop = y(gapHigh), gapBottom = y(gapLow);
                gapZoneEl.setAttribute("x", "0");
                gapZoneEl.setAttribute("width", "200");
                gapZoneEl.setAttribute("y", gapTop.toFixed(1));
                gapZoneEl.setAttribute("height", Math.max(1, gapBottom - gapTop).toFixed(1));

                var midY = y((gapHigh + gapLow) / 2);
                midLineEl.setAttribute("x1", "0");
                midLineEl.setAttribute("x2", "200");
                midLineEl.setAttribute("y1", midY.toFixed(1));
                midLineEl.setAttribute("y2", midY.toFixed(1));
                gapLabelEl.setAttribute("y", (gapTop - 4).toFixed(1));
            } else {
                gapZoneEl.setAttribute("width", "0");
                gapZoneEl.setAttribute("height", "0");
            }
        }

        [c1HighEl, c1LowEl, c3HighEl, c3LowEl].forEach(function (el) {
            el.addEventListener("input", calc);
        });
        calc();
    }

    // ---------- Acordeón "Top 10 estrategias de trading" ----------
    function initStrategyAccordion() {
        var accordion = document.getElementById("strategy-accordion");
        if (!accordion) return;
        var items = accordion.querySelectorAll(".strategy-item");
        items.forEach(function (item) {
            var header = item.querySelector(".strategy-item__header");
            header.addEventListener("click", function () {
                var wasOpen = item.classList.contains("is-open");
                items.forEach(function (other) {
                    other.classList.remove("is-open");
                    other.querySelector(".strategy-item__header").setAttribute("aria-expanded", "false");
                });
                if (!wasOpen) {
                    item.classList.add("is-open");
                    header.setAttribute("aria-expanded", "true");
                }
            });
        });
        // El primero abierto por defecto, para que la sección no se vea
        // vacía antes de que alguien haga click.
        items[0].classList.add("is-open");
        items[0].querySelector(".strategy-item__header").setAttribute("aria-expanded", "true");
    }

    document.addEventListener("DOMContentLoaded", function () {
        initStrategyAccordion();

        var workspace = document.querySelector(".tool-workspace[data-tool]");
        if (!workspace) return;
        var tool = workspace.dataset.tool;
        if (tool === "compound-interest") initCompoundInterest();
        else if (tool === "risk-reward") initRiskReward();
        else if (tool === "fair-value-gap") initFairValueGap();
    });
})();
