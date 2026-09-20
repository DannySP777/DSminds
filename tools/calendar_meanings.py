"""
tools/calendar_meanings.py

Qué significa cada evento del calendario económico y cómo suele tocar al
NASDAQ. El feed de calendario solo trae el título en inglés ("Core
Retail Sales m/m"), sin explicación, así que se empareja por palabras
clave (mismo criterio que dsprofeta/features.py::ECON_CATEGORY_KEYWORDS)
con esta tabla de significados redactados a mano.

Cada entrada: (palabras clave en minúscula, {es: ..., en: ...}) donde el
diccionario de idioma trae `name` (nombre legible), `what` (qué mide) y
`nasdaq` (cómo suele reaccionar el índice). La primera entrada que
coincida gana, por eso las más específicas van primero ("core cpi" antes
que "cpi"). Es contexto educativo general, no una señal de trading.

Los textos `nasdaq` de cada entrada son específicos del NASDAQ; para los
demás activos (oro, EUR/USD, Bitcoin) el efecto se toma de
_ASSET_EFFECTS según el "tono" del evento (tasas, inflación, empleo,
crecimiento, discurso u otro) — así no hay 4 redacciones por evento.
"""

_ENTRIES = [
    (("federal funds rate", "fed interest rate", "interest rate decision"), {
        "es": {
            "name": "Decisión de tasas de la Fed",
            "what": "La Reserva Federal fija el costo del dinero en EE.UU. Es la decisión económica más importante del mes: define qué tan barato o caro es financiarse.",
            "nasdaq": "Tasas más bajas de lo esperado suelen impulsar al NASDAQ (sus empresas tecnológicas valen por ganancias futuras, que se descuentan a menor tasa); tasas más altas o un tono duro lo presionan.",
        },
        "en": {
            "name": "Fed interest rate decision",
            "what": "The Federal Reserve sets the cost of money in the US. It is the single most important economic decision of the month: it defines how cheap or expensive borrowing is.",
            "nasdaq": "Lower-than-expected rates tend to lift the NASDAQ (its tech names are valued on future earnings, discounted at a lower rate); higher rates or a hawkish tone weigh on it.",
        },
    }),
    (("fomc statement",), {
        "es": {
            "name": "Comunicado del FOMC",
            "what": "El texto oficial que acompaña la decisión de tasas: cambia una o dos palabras y el mercado lo interpreta como un giro en la política monetaria.",
            "nasdaq": "Un lenguaje más 'paciente' con la inflación suele darle aire al NASDAQ; uno más restrictivo genera ventas rápidas en tecnología.",
        },
        "en": {
            "name": "FOMC statement",
            "what": "The official text released with the rate decision. Change one or two words and the market reads it as a shift in monetary policy.",
            "nasdaq": "More 'patient' language on inflation usually gives the NASDAQ room to run; more restrictive wording triggers quick selling in tech.",
        },
    }),
    (("fomc economic projections", "economic projections"), {
        "es": {
            "name": "Proyecciones económicas del FOMC",
            "what": "El 'dot plot': cada miembro de la Fed marca dónde cree que estarán las tasas, el crecimiento y la inflación en los próximos años.",
            "nasdaq": "Si proyectan menos recortes de tasas de los que el mercado espera, el NASDAQ suele corregir; si proyectan más, suele celebrarlo.",
        },
        "en": {
            "name": "FOMC economic projections",
            "what": "The 'dot plot': each Fed member marks where they expect rates, growth and inflation to be over the next years.",
            "nasdaq": "If they project fewer rate cuts than the market expects, the NASDAQ tends to pull back; more cuts than expected usually get cheered.",
        },
    }),
    (("fomc press conference", "press conference"), {
        "es": {
            "name": "Conferencia de prensa del presidente de la Fed",
            "what": "El presidente de la Fed explica la decisión y responde preguntas. Aquí suelen aparecer las pistas sobre los próximos pasos.",
            "nasdaq": "Es donde más se mueve el mercado tras el comunicado: la volatilidad del NASDAQ sube durante la conferencia y el precio puede revertir el movimiento inicial.",
        },
        "en": {
            "name": "Fed chair press conference",
            "what": "The Fed chair explains the decision and takes questions. Hints about the next steps usually surface here.",
            "nasdaq": "This is where the market moves most after the statement: NASDAQ volatility rises during the conference and price can reverse the initial reaction.",
        },
    }),
    (("fomc meeting minutes", "meeting minutes", "fomc minutes"), {
        "es": {
            "name": "Actas de la reunión de la Fed",
            "what": "El resumen detallado de lo que se discutió en la reunión anterior de la Fed, publicado tres semanas después.",
            "nasdaq": "Rara vez sorprende, pero puede mover al índice si revela que hubo más división o más urgencia por subir/bajar tasas de lo que se pensaba.",
        },
        "en": {
            "name": "Fed meeting minutes",
            "what": "The detailed record of what was discussed at the previous Fed meeting, published three weeks later.",
            "nasdaq": "Rarely a surprise, but it can move the index if it reveals more division or more urgency about hiking/cutting than was thought.",
        },
    }),
    (("adp",), {
        "es": {
            "name": "Empleo privado ADP",
            "what": "Un adelanto privado del informe oficial de empleo, elaborado con datos de nóminas de empresas.",
            "nasdaq": "Sirve de pista antes de las nóminas no agrícolas; su efecto es moderado salvo que sorprenda mucho.",
        },
        "en": {
            "name": "ADP private payrolls",
            "what": "A private preview of the official jobs report, built from company payroll data.",
            "nasdaq": "It works as a hint ahead of non-farm payrolls; the effect is moderate unless it surprises a lot.",
        },
    }),
    (("non-farm", "nonfarm", "non farm"), {
        "es": {
            "name": "Nóminas no agrícolas (empleo de EE.UU.)",
            "what": "Cuántos empleos nuevos creó la economía estadounidense el mes pasado. Es el dato de empleo más seguido del mundo.",
            "nasdaq": "Un dato mucho más fuerte que lo previsto puede asustar (la Fed mantendría tasas altas); uno muy débil también (miedo a recesión). El mejor escenario para el NASDAQ suele ser un dato 'justo', ni muy caliente ni muy frío.",
        },
        "en": {
            "name": "Non-Farm Payrolls (US jobs)",
            "what": "How many new jobs the US economy created last month. It is the most-watched employment report in the world.",
            "nasdaq": "A print far above forecast can spook the market (the Fed would keep rates high); a very weak one does too (recession fear). The best case for the NASDAQ is usually a 'Goldilocks' number, neither too hot nor too cold.",
        },
    }),
    (("unemployment rate",), {
        "es": {
            "name": "Tasa de desempleo",
            "what": "El porcentaje de personas que buscan trabajo y no lo encuentran. Se publica junto con las nóminas no agrícolas.",
            "nasdaq": "Una tasa que sube rápido enciende el temor a recesión; una que baja mucho puede alimentar la idea de tasas altas por más tiempo.",
        },
        "en": {
            "name": "Unemployment rate",
            "what": "The share of people looking for work who can't find it. Released together with non-farm payrolls.",
            "nasdaq": "A fast-rising rate ignites recession fears; a sharp drop can feed the idea of higher rates for longer.",
        },
    }),
    (("unemployment claims", "jobless claims"), {
        "es": {
            "name": "Peticiones semanales de subsidio por desempleo",
            "what": "Cuántas personas pidieron por primera vez el subsidio de desempleo esta semana. Es un termómetro rápido del mercado laboral.",
            "nasdaq": "Cifras estables pasan desapercibidas; un salto brusco sugiere que el empleo se enfría y puede alimentar apuestas a recortes de tasas.",
        },
        "en": {
            "name": "Weekly jobless claims",
            "what": "How many people filed for unemployment benefits for the first time this week. A quick thermometer of the labor market.",
            "nasdaq": "Steady numbers go unnoticed; a sudden jump suggests the labor market is cooling and can feed rate-cut bets.",
        },
    }),
    (("core cpi", "cpi"), {
        "es": {
            "name": "Índice de precios al consumidor (inflación)",
            "what": "Cuánto subieron los precios que pagan los consumidores. La versión 'core' excluye alimentos y energía y muestra la inflación de fondo, la que más mira la Fed.",
            "nasdaq": "Inflación por encima de lo previsto aleja los recortes de tasas y suele hundir a la tecnología; por debajo, la impulsa.",
        },
        "en": {
            "name": "Consumer Price Index (inflation)",
            "what": "How much the prices consumers pay rose. The 'core' version strips out food and energy and shows underlying inflation, the one the Fed watches most.",
            "nasdaq": "Inflation above forecast pushes rate cuts further away and tends to sink tech; below forecast lifts it.",
        },
    }),
    (("core ppi", "ppi"), {
        "es": {
            "name": "Precios al productor (PPI)",
            "what": "La inflación vista desde las fábricas y proveedores: lo que pagan las empresas por sus insumos. Suele anticipar el CPI.",
            "nasdaq": "Un PPI alto anticipa presión inflacionaria y tasas altas por más tiempo (negativo para el NASDAQ); uno bajo alivia.",
        },
        "en": {
            "name": "Producer Price Index (PPI)",
            "what": "Inflation seen from the factory gate: what businesses pay for inputs. It often foreshadows CPI.",
            "nasdaq": "A hot PPI hints at inflation pressure and higher-for-longer rates (negative for the NASDAQ); a soft one brings relief.",
        },
    }),
    (("core pce", "pce price"), {
        "es": {
            "name": "Índice PCE (inflación preferida de la Fed)",
            "what": "El indicador de inflación que la Reserva Federal usa oficialmente para su meta del 2 %.",
            "nasdaq": "Confirma o desmiente lo que ya mostró el CPI; si sorprende al alza, presiona a la tecnología por la vía de las tasas.",
        },
        "en": {
            "name": "PCE price index (the Fed's preferred inflation gauge)",
            "what": "The inflation measure the Federal Reserve officially uses for its 2% target.",
            "nasdaq": "It confirms or contradicts what CPI already showed; an upside surprise pressures tech through the rates channel.",
        },
    }),
    (("retail sales",), {
        "es": {
            "name": "Ventas minoristas",
            "what": "Cuánto gastaron los consumidores en tiendas y online. Como el consumo es ~70 % de la economía de EE.UU., es un gran termómetro de fuerza económica.",
            "nasdaq": "Un dato sólido respalda las ganancias de empresas de consumo y tecnología, pero uno muy fuerte puede retrasar recortes de tasas. Uno débil despierta miedo a desaceleración.",
        },
        "en": {
            "name": "Retail sales",
            "what": "How much consumers spent in stores and online. Consumption is ~70% of the US economy, so this is a big gauge of economic strength.",
            "nasdaq": "A solid print backs consumer and tech earnings, though a very strong one can delay rate cuts. A weak one stirs slowdown fears.",
        },
    }),
    (("ism manufacturing", "manufacturing pmi", "s&p global manufacturing"), {
        "es": {
            "name": "PMI manufacturero",
            "what": "Encuesta a gerentes de compras de fábricas: por encima de 50 la industria se expande, por debajo se contrae.",
            "nasdaq": "Es un indicador adelantado de la economía; el NASDAQ reacciona menos que a la inflación o al empleo, salvo que el dato cruce el nivel de 50.",
        },
        "en": {
            "name": "Manufacturing PMI",
            "what": "A survey of factory purchasing managers: above 50 the industry expands, below 50 it contracts.",
            "nasdaq": "A leading indicator of the economy; the NASDAQ reacts less than to inflation or jobs data, unless the reading crosses the 50 line.",
        },
    }),
    (("ism services", "services pmi", "s&p global services"), {
        "es": {
            "name": "PMI de servicios",
            "what": "La misma encuesta pero para el sector servicios, que es la mayor parte de la economía estadounidense.",
            "nasdaq": "Un PMI de servicios fuerte confirma una economía resistente; puede ser mixto para el NASDAQ si además presiona a la inflación.",
        },
        "en": {
            "name": "Services PMI",
            "what": "The same survey for the services sector, which is the largest part of the US economy.",
            "nasdaq": "A strong services PMI confirms a resilient economy; it can be mixed for the NASDAQ if it also adds to inflation pressure.",
        },
    }),
    (("philly fed", "empire state", "richmond fed", "kansas city fed", "dallas fed"), {
        "es": {
            "name": "Encuesta manufacturera regional de la Fed",
            "what": "Una encuesta mensual a fábricas de una región de EE.UU. que se publica antes del PMI nacional y sirve de adelanto.",
            "nasdaq": "Efecto normalmente pequeño; el mercado la usa para ajustar expectativas del PMI.",
        },
        "en": {
            "name": "Regional Fed manufacturing survey",
            "what": "A monthly survey of factories in one US region, published before the national PMI as an early read.",
            "nasdaq": "Usually a small effect; the market uses it to adjust PMI expectations.",
        },
    }),
    (("gdp",), {
        "es": {
            "name": "Producto Interno Bruto (PIB)",
            "what": "El crecimiento total de la economía en el trimestre: la medida más amplia de qué tan bien (o mal) va el país.",
            "nasdaq": "Crecimiento firme apoya las ganancias empresariales; una contracción activa el miedo a recesión.",
        },
        "en": {
            "name": "Gross Domestic Product (GDP)",
            "what": "Total economic growth in the quarter: the broadest measure of how well (or badly) the country is doing.",
            "nasdaq": "Firm growth supports corporate earnings; a contraction triggers recession fear.",
        },
    }),
    (("consumer sentiment", "consumer confidence", "michigan"), {
        "es": {
            "name": "Confianza del consumidor",
            "what": "Encuesta sobre qué tan optimistas se sienten los hogares con su economía y con la inflación futura.",
            "nasdaq": "Mueve poco por sí sola, pero las expectativas de inflación que incluye pueden influir en las apuestas sobre las tasas.",
        },
        "en": {
            "name": "Consumer sentiment",
            "what": "A survey of how optimistic households feel about their finances and future inflation.",
            "nasdaq": "It moves little on its own, but the inflation expectations it includes can shift rate bets.",
        },
    }),
    (("jolts", "job openings"), {
        "es": {
            "name": "Ofertas de empleo (JOLTS)",
            "what": "Cuántas vacantes abiertas hay en EE.UU. Muestra si las empresas siguen buscando gente o están frenando contrataciones.",
            "nasdaq": "Muchas vacantes = mercado laboral caliente = riesgo de tasas altas por más tiempo; pocas = enfriamiento.",
        },
        "en": {
            "name": "Job openings (JOLTS)",
            "what": "How many open positions there are in the US. It shows whether companies are still hiring or slowing down.",
            "nasdaq": "Many openings = hot labor market = risk of higher-for-longer rates; few openings = cooling.",
        },
    }),
    (("treasury", "bessent", "powell", "fed chair", "speaks"), {
        "es": {
            "name": "Discurso de una autoridad económica",
            "what": "Un funcionario del Tesoro o de la Fed habla en público. No trae un dato duro, pero sí pistas sobre política fiscal o monetaria.",
            "nasdaq": "El mercado analiza cada frase buscando cambios de tono; suele generar movimientos rápidos pero cortos.",
        },
        "en": {
            "name": "Speech by an economic official",
            "what": "A Treasury or Fed official speaks in public. It brings no hard data, but it does drop clues on fiscal or monetary policy.",
            "nasdaq": "The market parses every sentence for a change in tone; it tends to cause quick, short-lived moves.",
        },
    }),
    (("auction",), {
        "es": {
            "name": "Subasta de bonos del Tesoro",
            "what": "El gobierno vende deuda y se ve cuánta demanda hay y a qué rendimiento. Los rendimientos son el 'precio' que compite con las acciones.",
            "nasdaq": "Poca demanda hace subir los rendimientos y suele presionar a la tecnología, que es sensible a las tasas.",
        },
        "en": {
            "name": "Treasury bond auction",
            "what": "The government sells debt and we see how much demand there is and at what yield. Yields are the 'price' competing with stocks.",
            "nasdaq": "Weak demand pushes yields up and tends to pressure tech, which is rate-sensitive.",
        },
    }),
    (("crude oil", "oil inventories"), {
        "es": {
            "name": "Inventarios de petróleo",
            "what": "Cuánto crudo tiene almacenado EE.UU.; mueve el precio del petróleo y, de rebote, las expectativas de inflación.",
            "nasdaq": "Efecto indirecto y pequeño en el NASDAQ, vía inflación y costos de energía.",
        },
        "en": {
            "name": "Crude oil inventories",
            "what": "How much crude the US has in storage; it moves oil prices and, indirectly, inflation expectations.",
            "nasdaq": "Small, indirect effect on the NASDAQ, through inflation and energy costs.",
        },
    }),
    (("housing", "home sales", "building permits", "durable goods", "factory orders", "trade balance"), {
        "es": {
            "name": "Dato de actividad económica",
            "what": "Un indicador sectorial (vivienda, pedidos, comercio) que ayuda a medir la salud de la economía.",
            "nasdaq": "Impacto moderado o bajo: el mercado lo suma al cuadro general de crecimiento y tasas.",
        },
        "en": {
            "name": "Economic activity data",
            "what": "A sector indicator (housing, orders, trade) that helps gauge the health of the economy.",
            "nasdaq": "Moderate to low impact: the market adds it to the overall growth-and-rates picture.",
        },
    }),
]

_FALLBACK = {
    "high": {
        "es": {
            "name": None,
            "what": "Un dato de alto impacto para la economía de EE.UU. Los datos de esta categoría suelen mover los precios de forma brusca en pocos minutos.",
            "nasdaq": "Espera más volatilidad en el NASDAQ alrededor de la hora de publicación; compara el resultado con lo previsto.",
        },
        "en": {
            "name": None,
            "what": "A high-impact release for the US economy. Data in this category tends to move prices sharply within minutes.",
            "nasdaq": "Expect more NASDAQ volatility around the release time; compare the result with the forecast.",
        },
    },
    "medium": {
        "es": {
            "name": None,
            "what": "Un dato de impacto medio: aporta contexto sobre la economía de EE.UU. sin ser determinante por sí solo.",
            "nasdaq": "Puede mover el precio unos minutos si sorprende mucho frente a lo previsto; normalmente su efecto es moderado.",
        },
        "en": {
            "name": None,
            "what": "A medium-impact release: it adds context on the US economy without being decisive by itself.",
            "nasdaq": "It can move price for a few minutes if it surprises a lot versus the forecast; its effect is usually moderate.",
        },
    },
}


# Tono de cada evento, por la PRIMERA palabra clave de su entrada en _ENTRIES.
_TONE = {
    "federal funds rate": "rates", "fomc statement": "rates", "fomc economic projections": "rates",
    "fomc press conference": "rates", "fomc meeting minutes": "rates",
    "adp": "jobs", "non-farm": "jobs", "unemployment rate": "jobs", "unemployment claims": "jobs",
    "jolts": "jobs",
    "core cpi": "inflation", "core ppi": "inflation", "core pce": "inflation",
    "retail sales": "growth", "ism manufacturing": "growth", "ism services": "growth", "philly fed": "growth",
    "gdp": "growth", "consumer sentiment": "growth", "housing": "growth",
    "treasury": "speech", "auction": "speech", "crude oil": "other",
}

_ASSET_EFFECTS = {
    "gold": {
        "rates": {
            "es": "El oro no paga interés: tasas más altas o un tono duro de la Fed fortalecen al dólar y a los rendimientos y suelen presionarlo; recortes o un tono suave lo favorecen.",
            "en": "Gold pays no interest: higher rates or a hawkish Fed strengthen the dollar and yields and tend to weigh on it; cuts or a dovish tone favor it.",
        },
        "inflation": {
            "es": "Inflación alta puede sostener al oro como refugio, pero si obliga a la Fed a mantener tasas altas el efecto neto suele ser negativo; una inflación baja alimenta apuestas a recortes y lo ayuda.",
            "en": "High inflation can support gold as a hedge, but if it forces the Fed to keep rates high the net effect is usually negative; low inflation feeds rate-cut bets and helps it.",
        },
        "jobs": {
            "es": "Empleo fuerte suele fortalecer al dólar y alejar recortes de tasas (negativo para el oro); empleo débil hace lo contrario y suele impulsarlo.",
            "en": "Strong jobs data tends to strengthen the dollar and push rate cuts away (negative for gold); weak jobs data does the opposite and tends to lift it.",
        },
        "growth": {
            "es": "Datos económicos débiles refuerzan la demanda de refugio y las apuestas a recortes (a favor del oro); datos muy fuertes le quitan atractivo como refugio.",
            "en": "Weak economic data boosts safe-haven demand and rate-cut bets (good for gold); very strong data takes away some of its appeal as a refuge.",
        },
        "speech": {
            "es": "El oro reacciona rápido a cualquier cambio de tono sobre tasas, dólar o deuda; suele ser un movimiento corto.",
            "en": "Gold reacts quickly to any change of tone on rates, the dollar or debt; the move is usually short-lived.",
        },
        "other": {
            "es": "Impacto indirecto y normalmente pequeño en el oro, vía dólar y expectativas de inflación.",
            "en": "Indirect and usually small impact on gold, through the dollar and inflation expectations.",
        },
    },
    "eurusd": {
        "rates": {
            "es": "Tasas de EE.UU. más altas de lo esperado, o un tono duro de la Fed, fortalecen al dólar y empujan al EUR/USD a la baja; recortes o un tono suave lo empujan al alza.",
            "en": "Higher-than-expected US rates, or a hawkish Fed tone, strengthen the dollar and push EUR/USD down; cuts or a dovish tone push it up.",
        },
        "inflation": {
            "es": "Inflación de EE.UU. por encima de lo previsto sugiere una Fed más dura, dólar más fuerte y EUR/USD a la baja; por debajo, lo contrario.",
            "en": "US inflation above forecast suggests a tougher Fed, a stronger dollar and a lower EUR/USD; below forecast, the opposite.",
        },
        "jobs": {
            "es": "Un empleo de EE.UU. fuerte suele fortalecer al dólar (EUR/USD baja); uno débil lo debilita (EUR/USD sube). Es de los datos que más mueven este par.",
            "en": "Strong US jobs data tends to strengthen the dollar (EUR/USD falls); weak data weakens it (EUR/USD rises). It is one of the releases that moves this pair the most.",
        },
        "growth": {
            "es": "Datos de EE.UU. mejores de lo esperado fortalecen al dólar y presionan al EUR/USD; peores, lo alivian.",
            "en": "US data better than expected strengthens the dollar and pressures EUR/USD; worse data relieves it.",
        },
        "speech": {
            "es": "Cualquier pista sobre tasas o dólar mueve al par en minutos; el mercado analiza cada frase.",
            "en": "Any hint about rates or the dollar moves the pair within minutes; the market parses every sentence.",
        },
        "other": {
            "es": "Impacto normalmente pequeño en el EUR/USD, salvo que sorprenda mucho frente a lo previsto.",
            "en": "Usually a small impact on EUR/USD unless it surprises a lot versus the forecast.",
        },
    },
    "btc": {
        "rates": {
            "es": "Bitcoin se comporta como activo de riesgo sensible a la liquidez: tasas más bajas o un tono suave suelen ayudarlo; tasas altas o un tono duro lo presionan.",
            "en": "Bitcoin behaves like a liquidity-sensitive risk asset: lower rates or a dovish tone tend to help it; higher rates or a hawkish tone weigh on it.",
        },
        "inflation": {
            "es": "Inflación alta significa tasas altas por más tiempo y suele pesar sobre Bitcoin; inflación baja alivia y suele impulsarlo junto con el resto de activos de riesgo.",
            "en": "High inflation means higher-for-longer rates and tends to weigh on Bitcoin; low inflation brings relief and tends to lift it along with other risk assets.",
        },
        "jobs": {
            "es": "Un dato de empleo 'justo' favorece el apetito por riesgo; uno muy fuerte (más tasas) o muy débil (recesión) suele provocar caídas en Bitcoin.",
            "en": "A 'just right' jobs number favors risk appetite; one that is too strong (more rate pressure) or too weak (recession) tends to trigger drops in Bitcoin.",
        },
        "growth": {
            "es": "Bitcoin sigue el ánimo de riesgo del mercado: datos que alejan la recesión ayudan; datos que la acercan, o que alimentan más tasas, suelen pesar.",
            "en": "Bitcoin follows the market's risk mood: data that pushes recession away helps; data that brings it closer, or fuels higher rates, tends to weigh.",
        },
        "speech": {
            "es": "Bitcoin opera las 24 horas y reacciona de inmediato a cambios de tono sobre tasas y liquidez, a veces con movimientos exagerados.",
            "en": "Bitcoin trades 24 hours a day and reacts immediately to changes of tone on rates and liquidity, sometimes with exaggerated moves.",
        },
        "other": {
            "es": "Impacto indirecto en Bitcoin, vía liquidez y apetito por riesgo; normalmente pequeño.",
            "en": "Indirect impact on Bitcoin, through liquidity and risk appetite; usually small.",
        },
    },
}


def explain_event(title, impact, lang="es", asset_key="ndx"):
    """Significado del evento: {name, what, effect}. `name` cae al título
    original del feed si no hay una entrada específica. `effect` es cómo
    suele afectar al activo `asset_key` (ndx, gold, eurusd o btc)."""
    lang = "en" if lang == "en" else "es"
    lowered = (title or "").lower()
    for keywords, texts in _ENTRIES:
        if any(k in lowered for k in keywords):
            entry = dict(texts[lang])
            tone = _TONE.get(keywords[0], "other")
            if asset_key == "ndx":
                effect = entry.pop("nasdaq")
            else:
                effect = _ASSET_EFFECTS[asset_key][tone][lang]
                entry.pop("nasdaq")
            entry["effect"] = effect
            return entry

    fallback = dict(_FALLBACK.get(impact, _FALLBACK["medium"])[lang])
    fallback["name"] = title
    nasdaq_text = fallback.pop("nasdaq")
    fallback["effect"] = nasdaq_text if asset_key == "ndx" else _ASSET_EFFECTS[asset_key]["other"][lang]
    return fallback
