/*
 * Vista "sistema solar" del scanner (reemplaza la tabla de home.html).
 * Tres grupos (penny/monster/standard), cada uno con su propio sol (el
 * grupo) y planetas orbitando (las acciones, ordenadas por
 * momentum_rank — ver scanner/universe.py). Datos vía JSON
 * (scanner/views.py::solar_system_data), Three.js cargado por CDN en
 * home.html justo antes de este archivo (mismo criterio que Plotly:
 * no bloquear el primer paint).
 *
 * Sin build tooling en este repo (ver static/js/main.js) — Three.js se
 * usa desde su build UMD global (window.THREE), sin OrbitControls (es
 * un addon que en versiones recientes de three.js solo se distribuye
 * como módulo ES, lo que exigiría un <script type="module"> aparte);
 * en su lugar hay un drag-to-rotate manual, unas ~20 líneas, más simple
 * que meter un segundo mecanismo de carga.
 */
(function () {
    "use strict";

    var MOBILE_BREAKPOINT = 640;
    var MOBILE_PLANET_CAP = 15;

    function supportsWebGL() {
        try {
            var canvas = document.createElement("canvas");
            return !!(window.WebGLRenderingContext && (canvas.getContext("webgl") || canvas.getContext("experimental-webgl")));
        } catch (e) {
            return false;
        }
    }

    function cssVar(name, fallback) {
        var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return v || fallback;
    }

    function fmtPct(value) {
        if (value === null || value === undefined) return "N/D";
        return (value >= 0 ? "+" : "") + value + "%";
    }

    function fmtRelVol(value) {
        if (value === null || value === undefined) return "N/D";
        return value + "x";
    }

    function fmtCompactCurrency(dollars) {
        if (dollars >= 1e12) return "$" + (dollars / 1e12).toFixed(1) + "T";
        if (dollars >= 1e9) return "$" + (dollars / 1e9).toFixed(1) + "B";
        if (dollars >= 1e6) return "$" + (dollars / 1e6).toFixed(1) + "M";
        if (dollars >= 1e3) return "$" + (dollars / 1e3).toFixed(1) + "K";
        return "$" + Math.round(dollars);
    }

    function reasonLine(i18n, p) {
        if (p.target_upside_pct !== null && p.target_upside_pct !== undefined && p.relative_volume !== null && p.relative_volume !== undefined) {
            return (i18n.reasonLine || "{upside}% upside, {relvol}x volumen")
                .replace("{upside}", p.target_upside_pct).replace("{relvol}", p.relative_volume);
        }
        if (p.relative_volume !== null && p.relative_volume !== undefined) {
            return (i18n.reasonLineNoUpside || "{relvol}x volumen").replace("{relvol}", p.relative_volume);
        }
        return i18n.reasonLineNoData || "";
    }

    function initSolarSystem() {
        var root = document.getElementById("solar-system");
        var stage = document.getElementById("solar-canvas-container");
        var fallback = document.getElementById("solar-fallback");
        if (!root || !stage || !fallback) {
            return;
        }

        var i18n = window.DSMS_SOLAR_I18N || {};
        var loadingEl = document.getElementById("solar-loading");
        var noDataEl = document.getElementById("solar-no-data");
        var tooltip = document.getElementById("solar-tooltip");
        var fallbackCaption = document.getElementById("solar-fallback-caption");
        var fallbackBody = document.getElementById("solar-fallback-body");
        var tabs = root.querySelectorAll(".solar-tab");
        var groupDesc = document.getElementById("solar-group-desc");
        var selectedLabel = document.getElementById("solar-selected-symbol");

        var urls = { penny: root.dataset.urlPenny, monster: root.dataset.urlMonster, standard: root.dataset.urlStandard };
        var dataByGroup = {};
        var activeGroup = "standard";
        var selectedSymbol = root.dataset.selectedSymbol || null;
        var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var isMobile = window.matchMedia("(max-width: " + MOBILE_BREAKPOINT + "px)").matches;

        var filterState = {
            breakout: false, minRelVol: 0, minMarketCap: 0, minUpside: 0,
            tiers: { best: true, mid: true, worst: true }, sortBy: "rank",
        };

        // Tercio de ranking dentro de la lista ORDENADA y visible
        // actual (no un campo del servidor) — así el color se recalcula
        // solo si el usuario cambia el criterio de orden (rank/market
        // cap/upside/vol. relativo): "mejor" siempre significa "mejor
        // bajo el criterio que se está mirando ahora".
        function tierForIndex(idx, total) {
            if (idx < total / 3) return "best";
            if (idx < (total * 2) / 3) return "mid";
            return "worst";
        }

        // Cualquier selección de símbolo en la página (click de planeta,
        // o cualquier otra cosa que dispare este evento — ver
        // static/js/main.js::selectSymbol) actualiza acá el resaltado del
        // planeta y la etiqueta "Seleccionado:", sin importar de dónde
        // vino el click — un solo lugar que sabe "qué está seleccionado".
        function setSelected(symbol) {
            selectedSymbol = symbol;
            if (selectedLabel) {
                selectedLabel.textContent = symbol || selectedLabel.dataset.noneText || "";
            }
            applySelectionHighlight();
        }
        document.addEventListener("dsms:symbol-selected", function (e) {
            setSelected(e.detail.symbol);
        });

        function renderFallbackList(group, list) {
            var activeTab = root.querySelector('.solar-tab[data-group="' + group + '"]');
            if (fallbackCaption && activeTab) {
                fallbackCaption.textContent = activeTab.dataset.caption || "";
            }
            if (!fallbackBody) return;
            fallbackBody.innerHTML = "";
            list.forEach(function (p) {
                var tr = document.createElement("tr");
                var link = '<a href="/accion/' + encodeURIComponent(p.symbol) + '/">' + p.symbol + "</a>";
                tr.innerHTML =
                    "<td>" + (p.rank !== null && p.rank !== undefined ? p.rank : "&mdash;") + "</td>" +
                    "<td>" + link + "</td>" +
                    "<td>$" + p.price + "</td>" +
                    "<td>" + fmtPct(p.target_upside_pct) + "</td>" +
                    "<td>" + fmtRelVol(p.relative_volume) + "</td>";
                fallbackBody.appendChild(tr);
            });
        }

        function passesFilters(p, tier) {
            if (filterState.breakout && !p.breakout) return false;
            if (filterState.minRelVol > 0 && (p.relative_volume || 0) < filterState.minRelVol) return false;
            if (filterState.minMarketCap > 1 && (p.market_cap || 0) < filterState.minMarketCap) return false;
            if (filterState.minUpside > 0) {
                if (p.target_upside_pct === null || p.target_upside_pct === undefined) return false;
                if (p.target_upside_pct < filterState.minUpside) return false;
            }
            if (tier && !filterState.tiers[tier]) return false;
            return true;
        }

        function sortedList(planets) {
            var arr = planets.slice();
            switch (filterState.sortBy) {
                case "market_cap":
                    arr.sort(function (a, b) { return (b.market_cap || 0) - (a.market_cap || 0); });
                    break;
                case "upside":
                    arr.sort(function (a, b) {
                        var au = a.target_upside_pct === null || a.target_upside_pct === undefined ? -Infinity : a.target_upside_pct;
                        var bu = b.target_upside_pct === null || b.target_upside_pct === undefined ? -Infinity : b.target_upside_pct;
                        return bu - au;
                    });
                    break;
                case "relvol":
                    arr.sort(function (a, b) { return (b.relative_volume || 0) - (a.relative_volume || 0); });
                    break;
                default:
                    arr.sort(function (a, b) { return (a.rank || 999) - (b.rank || 999); });
            }
            return arr;
        }

        // ----- si no hay WebGL/Three.js: solo el fallback accesible -----
        if (typeof THREE === "undefined" || !supportsWebGL()) {
            if (loadingEl) loadingEl.textContent = i18n.webglUnsupported || "";
            fetchAllGroups().then(function () {
                renderFallbackList(activeGroup, sortedList(dataByGroup[activeGroup] || []).filter(passesFilters));
            });
            wireTabs(function (group) {
                activeGroup = group;
                renderFallbackList(activeGroup, sortedList(dataByGroup[activeGroup] || []).filter(passesFilters));
            });
            return;
        }

        // ----- escena Three.js, una sola vez -----
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(50, 1, 0.1, 3000);
        var cameraAzimuth = 0.6;
        var cameraPolar = 1.05;
        var cameraDistance = 230;

        function updateCameraPosition() {
            camera.position.set(
                cameraDistance * Math.sin(cameraPolar) * Math.sin(cameraAzimuth),
                cameraDistance * Math.cos(cameraPolar),
                cameraDistance * Math.sin(cameraPolar) * Math.cos(cameraAzimuth)
            );
            camera.lookAt(0, 0, 0);
        }
        updateCameraPosition();

        // antialias:false y sin luces dinámicas a propósito — con
        // MeshStandardMaterial + PointLight + antialiasing, en una laptop
        // con GPU integrada esta escena caía a un puñado de FPS (se sentía
        // "trabada", el drag no respondía). MeshBasicMaterial (sin luz, el
        // color que le pongo es exactamente lo que se ve — que es
        // justamente el efecto de "planeta que brilla" que se buscaba) más
        // menos segmentos por esfera resuelve eso sin cambiar cómo se ve.
        var renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: "high-performance" });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
        stage.appendChild(renderer.domElement);

        var raycaster = new THREE.Raycaster();
        var pointer = new THREE.Vector2();

        var sunMesh = null;
        var planetMeshes = []; // {mesh, data, speed}

        function planetSize(marketCap) {
            if (!marketCap || marketCap <= 0) return 2.4;
            var v = Math.log10(marketCap) - 4;
            return Math.max(2, Math.min(9, v));
        }

        function sunSize(group) {
            return group === "monster" ? 18 : group === "standard" ? 13 : 9;
        }

        function colorForTier(tier) {
            if (tier === "best") return cssVar("--tier-best", "#3fbf7f");
            if (tier === "worst") return cssVar("--tier-worst", "#e5484d");
            return cssVar("--tier-mid", "#ff6347");
        }

        var SELECTED_SCALE = 1.35;

        function makeLabelSprite(text) {
            var canvas = document.createElement("canvas");
            var ctx = canvas.getContext("2d");
            var fontSize = 40;
            ctx.font = "700 " + fontSize + "px " + cssVar("--font-mono", "monospace");
            var textWidth = ctx.measureText(text).width;
            canvas.width = Math.ceil(textWidth) + 24;
            canvas.height = fontSize + 16;
            // Cambiar canvas.width/height reinicia el contexto — hay que
            // volver a setear el font después del resize.
            ctx.font = "700 " + fontSize + "px " + cssVar("--font-mono", "monospace");
            ctx.fillStyle = "rgba(10, 10, 13, 0.65)";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "#f2f1ee";
            ctx.textBaseline = "middle";
            ctx.fillText(text, 12, canvas.height / 2 + 1);

            var texture = new THREE.CanvasTexture(canvas);
            texture.minFilter = THREE.LinearFilter;
            var material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });
            var sprite = new THREE.Sprite(material);
            var pxToWorld = 0.055;
            sprite.scale.set(canvas.width * pxToWorld, canvas.height * pxToWorld, 1);
            return sprite;
        }

        // "Prender" el planeta seleccionado: más brillo emisivo + un poco
        // más grande, sobre lo que ya haya en la escena actual (no
        // reconstruye nada) — se llama tanto al hacer click como después
        // de cada buildScene(), para que la selección sobreviva un cambio
        // de filtro o de tab (si el símbolo sigue en el grupo activo).
        function applySelectionHighlight() {
            if (!planetMeshes || !planetMeshes.length) return;
            planetMeshes.forEach(function (p) {
                var isSelected = selectedSymbol && p.data.symbol === selectedSymbol;
                // MeshBasicMaterial no tiene "emissive" (no reacciona a
                // luces, así que no hace falta) — "prenderlo" es mezclar
                // su color base hacia blanco, guardado en userData al
                // crearlo para no ir y volver por la conversión de color.
                p.mesh.material.color.copy(isSelected ? p.mesh.userData.litColor : p.mesh.userData.baseColor);
                p.mesh.scale.setScalar(isSelected ? SELECTED_SCALE : 1);
            });
        }

        function clearScene() {
            planetMeshes.forEach(function (p) {
                p.mesh.children.forEach(function (child) {
                    if (child.material) {
                        if (child.material.map) child.material.map.dispose();
                        child.material.dispose();
                    }
                });
                scene.remove(p.mesh);
                p.mesh.geometry.dispose();
                p.mesh.material.dispose();
            });
            planetMeshes = [];
            if (sunMesh) {
                scene.remove(sunMesh);
                sunMesh.geometry.dispose();
                sunMesh.material.dispose();
                sunMesh = null;
            }
        }

        function buildScene(group) {
            clearScene();
            var all = dataByGroup[group] || [];
            var ordered = sortedList(all);
            if (isMobile) {
                ordered = ordered.slice(0, MOBILE_PLANET_CAP);
            }

            var sunColor = cssVar("--sun-color", "#f2c94a");
            var sunGeo = new THREE.SphereGeometry(sunSize(group), 16, 16);
            var sunMat = new THREE.MeshBasicMaterial({ color: sunColor });
            sunMesh = new THREE.Mesh(sunGeo, sunMat);
            sunMesh.userData = { isSun: true };
            scene.add(sunMesh);

            var baseRadius = sunSize(group) + 12;
            var radiusStep = isMobile ? 4 : 2.8;

            ordered.forEach(function (p, idx) {
                var radius = baseRadius + idx * radiusStep;
                var size = planetSize(p.market_cap);
                var geo = new THREE.SphereGeometry(size, 10, 10);
                var tier = tierForIndex(idx, ordered.length);
                var visible = passesFilters(p, tier);
                var baseColor = new THREE.Color(colorForTier(tier));
                var litColor = baseColor.clone().lerp(new THREE.Color(0xffffff), 0.55);
                var mat = new THREE.MeshBasicMaterial({
                    color: baseColor, transparent: true, opacity: visible ? 1 : 0.15,
                });
                var mesh = new THREE.Mesh(geo, mat);
                var angle = (idx / Math.max(ordered.length, 1)) * Math.PI * 2;
                mesh.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
                mesh.userData = { planet: p, visible: visible, tier: tier, baseColor: baseColor, litColor: litColor };

                var label = makeLabelSprite(p.symbol);
                label.position.set(0, size + 3, 0);
                // Mismo userData que la esfera — el raycaster es
                // recursivo por defecto y puede pegarle al sprite de la
                // etiqueta en vez de a la esfera; sin esto, pasar el mouse
                // justo sobre el texto del símbolo no mostraría tooltip.
                label.userData = mesh.userData;
                mesh.add(label);

                scene.add(mesh);

                planetMeshes.push({
                    mesh: mesh,
                    data: p,
                    radius: radius,
                    angle: angle,
                    speed: reducedMotion ? 0 : (0.35 / (idx + 3)) * 0.02,
                });
            });

            applySelectionHighlight();
            renderFallbackList(group, ordered);
        }

        function resize() {
            var w = stage.clientWidth || 600;
            var h = Math.max(360, Math.min(560, Math.round(w * 0.62)));
            stage.style.height = h + "px";
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        }

        function refreshView() {
            buildScene(activeGroup);
        }

        function fetchAllGroups() {
            var pending = ["penny", "monster", "standard"].map(function (group) {
                return fetch(urls[group])
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        dataByGroup[group] = data.planets || [];
                    })
                    .catch(function () {
                        dataByGroup[group] = [];
                    });
            });
            return Promise.all(pending);
        }

        function wireTabs(onSwitch) {
            tabs.forEach(function (tab) {
                tab.addEventListener("click", function () {
                    tabs.forEach(function (t) {
                        t.classList.toggle("is-active", t === tab);
                        t.setAttribute("aria-selected", t === tab ? "true" : "false");
                    });
                    if (groupDesc) groupDesc.textContent = tab.dataset.desc || "";
                    onSwitch(tab.dataset.group);
                });
            });
        }

        function wireFilters() {
            var breakoutInput = document.getElementById("solar-filter-breakout");
            var relvolInput = document.getElementById("solar-filter-relvol");
            var relvolOutput = document.getElementById("solar-filter-relvol-output");
            var mcapInput = document.getElementById("solar-filter-mcap");
            var mcapOutput = document.getElementById("solar-filter-mcap-output");
            var upsideInput = document.getElementById("solar-filter-upside");
            var upsideOutput = document.getElementById("solar-filter-upside-output");
            var sortSelect = document.getElementById("solar-filter-sort");
            var trendChips = root.querySelectorAll(".solar-trend-chip");

            if (breakoutInput) {
                breakoutInput.addEventListener("change", function () {
                    filterState.breakout = breakoutInput.checked;
                    refreshView();
                });
            }
            if (relvolInput) {
                relvolInput.addEventListener("input", function () {
                    filterState.minRelVol = parseFloat(relvolInput.value) || 0;
                    if (relvolOutput) relvolOutput.textContent = filterState.minRelVol + "x";
                    refreshView();
                });
            }
            if (mcapInput) {
                mcapInput.addEventListener("input", function () {
                    // Escala logarítmica: 0 → $1 (efectivamente "sin
                    // filtro"), 13 → $10T — el market cap real abarca
                    // varios órdenes de magnitud dentro de un mismo grupo,
                    // un slider lineal sería inútil en casi todo su rango.
                    var dollars = Math.pow(10, parseFloat(mcapInput.value) || 0);
                    filterState.minMarketCap = dollars;
                    if (mcapOutput) mcapOutput.textContent = fmtCompactCurrency(dollars);
                    refreshView();
                });
            }
            if (upsideInput) {
                upsideInput.addEventListener("input", function () {
                    filterState.minUpside = parseFloat(upsideInput.value) || 0;
                    if (upsideOutput) upsideOutput.textContent = filterState.minUpside + "%";
                    refreshView();
                });
            }
            if (sortSelect) {
                sortSelect.addEventListener("change", function () {
                    filterState.sortBy = sortSelect.value;
                    refreshView();
                });
            }
            trendChips.forEach(function (chip) {
                chip.addEventListener("click", function () {
                    var tier = chip.dataset.tier;
                    filterState.tiers[tier] = !filterState.tiers[tier];
                    chip.classList.toggle("is-active", filterState.tiers[tier]);
                    refreshView();
                });
            });
        }

        function planetAtPointer(clientX, clientY) {
            var rect = renderer.domElement.getBoundingClientRect();
            pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
            pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(pointer, camera);
            var hits = raycaster.intersectObjects(planetMeshes.map(function (p) { return p.mesh; }));
            for (var i = 0; i < hits.length; i++) {
                var data = hits[i].object.userData;
                if (data.planet && data.visible) {
                    return data.planet;
                }
            }
            return null;
        }

        // El raycast (planetAtPointer) recorre hasta ~20 esferas + sus
        // sprites — barato una vez, pero pointermove puede disparar
        // muchas veces más rápido de lo que se pinta un frame. Guardar
        // solo la última posición y resolverla en animate() (una vez por
        // frame) evita apilar trabajo de más — antes se sentía "trabado"
        // justo durante el drag, que es cuando más eventos de pointermove
        // llegan.
        var pendingHoverPos = null;

        function updateHover(clientX, clientY) {
            var planet = planetAtPointer(clientX, clientY);
            if (planet) {
                tooltip.hidden = false;
                tooltip.style.left = (clientX - stage.getBoundingClientRect().left + 14) + "px";
                tooltip.style.top = (clientY - stage.getBoundingClientRect().top + 14) + "px";
                tooltip.innerHTML =
                    "<strong>" + planet.symbol + "</strong> &middot; " + (i18n.rank || "#") + planet.rank + "<br>" +
                    (i18n.price || "") + ": $" + planet.price + " &middot; " +
                    (i18n.upside || "") + ": " + fmtPct(planet.target_upside_pct) + "<br>" +
                    reasonLine(i18n, planet);
                renderer.domElement.style.cursor = "pointer";
            } else {
                tooltip.hidden = true;
                renderer.domElement.style.cursor = "grab";
            }
        }

        function wireInteraction() {
            var dragging = false;
            var lastX = 0;
            var lastY = 0;
            var moved = false;

            // Arrastrar para rotar y la rueda para zoom funcionan siempre
            // (mouse o touch, vía Pointer Events) — antes se apagaban por
            // completo si la ventana medía menos de 640px, así que
            // cualquiera con el navegador no maximizado se quedaba sin
            // poder mover la escena. El recorte a 15 planetas en pantallas
            // chicas (ver MOBILE_PLANET_CAP) es la única diferencia real
            // que debería depender del tamaño.
            renderer.domElement.addEventListener("pointermove", function (e) {
                if (dragging) {
                    var dx = e.clientX - lastX;
                    var dy = e.clientY - lastY;
                    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) moved = true;
                    cameraAzimuth -= dx * 0.005;
                    cameraPolar = Math.min(Math.max(cameraPolar - dy * 0.005, 0.3), Math.PI - 0.3);
                    lastX = e.clientX;
                    lastY = e.clientY;
                    updateCameraPosition();
                    return;
                }
                pendingHoverPos = { x: e.clientX, y: e.clientY };
            });

            renderer.domElement.addEventListener("pointerdown", function (e) {
                dragging = true;
                moved = false;
                lastX = e.clientX;
                lastY = e.clientY;
                renderer.domElement.style.cursor = "grabbing";
            });
            window.addEventListener("pointerup", function () {
                dragging = false;
                renderer.domElement.style.cursor = "grab";
            });
            renderer.domElement.addEventListener("wheel", function (e) {
                e.preventDefault();
                cameraDistance = Math.min(Math.max(cameraDistance + e.deltaY * 0.15, 60), 500);
                updateCameraPosition();
            }, { passive: false });

            renderer.domElement.addEventListener("click", function (e) {
                if (moved) { moved = false; return; }
                var planet = planetAtPointer(e.clientX, e.clientY);
                if (!planet) return;
                if (typeof selectSymbol === "function") {
                    selectSymbol(planet.symbol);
                } else {
                    window.location.href = "/accion/" + encodeURIComponent(planet.symbol) + "/";
                }
            });

            tooltip.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
        }

        function animate() {
            requestAnimationFrame(animate);
            planetMeshes.forEach(function (p) {
                if (p.speed) {
                    p.angle += p.speed;
                    p.mesh.position.set(Math.cos(p.angle) * p.radius, 0, Math.sin(p.angle) * p.radius);
                }
            });
            if (sunMesh) {
                sunMesh.rotation.y += reducedMotion ? 0 : 0.0015;
            }
            if (pendingHoverPos) {
                updateHover(pendingHoverPos.x, pendingHoverPos.y);
                pendingHoverPos = null;
            }
            renderer.render(scene, camera);
        }

        resize();
        wireFilters();
        wireInteraction();
        window.addEventListener("resize", function () {
            var wasMobile = isMobile;
            isMobile = window.matchMedia("(max-width: " + MOBILE_BREAKPOINT + "px)").matches;
            resize();
            if (wasMobile !== isMobile) {
                refreshView();
            }
        });

        if (loadingEl) loadingEl.hidden = false;
        fetchAllGroups().then(function () {
            if (loadingEl) loadingEl.hidden = true;
            var hasAny = ["penny", "monster", "standard"].some(function (g) { return (dataByGroup[g] || []).length > 0; });
            if (!hasAny) {
                if (noDataEl) noDataEl.hidden = false;
                return;
            }
            // El canvas nunca es accesible en sí mismo (aria-hidden se
            // queda en true) — esta clase solo oculta VISUALMENTE la
            // lista de respaldo, que sigue en el DOM para lectores de
            // pantalla y como progressive-enhancement si WebGL falla
            // a mitad de sesión.
            root.classList.add("solar-js-ready");
            wireTabs(function (group) {
                activeGroup = group;
                refreshView();
            });
            buildScene(activeGroup);
            animate();
        });

        // Si venimos de un primer paint server-side con un símbolo ya
        // seleccionado (ver views.py::home), mantenemos ese estado como
        // "actual" para que el click de gráfica de intervalo siga
        // funcionando sin recargar antes de que el usuario toque un planeta.
        if (root.dataset.selectedSymbol && typeof window.dsmsCurrentSymbol === "undefined") {
            window.dsmsCurrentSymbol = root.dataset.selectedSymbol;
        }
    }

    function initSolarTutorial() {
        var root = document.getElementById("solar-tutorial");
        if (!root) return;
        var steps = Array.prototype.slice.call(root.querySelectorAll(".solar-tutorial__step"));
        var descEl = document.getElementById("solar-tutorial-desc");
        if (!steps.length || !descEl) return;

        var current = 0;
        var timer = null;
        var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var CYCLE_MS = 4500;

        function activate(idx) {
            current = idx;
            steps.forEach(function (s, i) { s.classList.toggle("is-active", i === idx); });
            descEl.textContent = steps[idx].dataset.desc || "";
        }

        function next() {
            activate((current + 1) % steps.length);
        }

        function stopCycle() {
            if (timer) clearInterval(timer);
            timer = null;
        }

        function startCycle() {
            if (reducedMotion) return; // se queda en el paso 1, fijo, sin animar
            stopCycle();
            timer = setInterval(next, CYCLE_MS);
        }

        steps.forEach(function (step, idx) {
            step.addEventListener("click", function () {
                activate(idx);
                stopCycle();
            });
            step.addEventListener("mouseenter", function () {
                activate(idx);
                stopCycle();
            });
        });
        root.addEventListener("mouseleave", startCycle);

        activate(0);
        startCycle();
    }

    document.addEventListener("DOMContentLoaded", function () {
        initSolarTutorial();
        initSolarSystem();
    });
})();
