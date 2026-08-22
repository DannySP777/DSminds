"""
blog/management/commands/seed_educational_posts.py

Publica el catálogo inicial de artículos educativos originales del
blog (no confundir con el resumen diario automático de mercado). Son
contenido editorial real, escrito para explicar la metodología del
scanner y conceptos de análisis técnico/fundamental en general.

Cada artículo incluye una traducción al inglés (title_en/excerpt_en/
body_en). Si en el futuro se agrega un artículo sin traducción, el
sitio en inglés simplemente muestra el contenido en español como
respaldo (ver Post.get_title/get_excerpt/get_body).

Se puede correr varias veces: usa update_or_create por slug, así que
si editas el texto de un artículo aquí y vuelves a correr el comando,
actualiza el existente en vez de duplicarlo.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post

DISCLAIMER = (
    '<p class="disclaimer-note">Este artículo es contenido educativo, no asesoría de inversión '
    'personalizada. Antes de tomar decisiones, lee nuestro <a href="/disclaimer/">aviso legal</a>.</p>'
)
DISCLAIMER_EN = (
    '<p class="disclaimer-note">This article is educational content, not personalized investment '
    'advice. Before making decisions, read our <a href="/disclaimer/">disclaimer</a>.</p>'
)

ARTICLES = [
    {
        "title": "Cómo usar el scanner de DSMarketLearning: guía completa",
        "slug": "como-usar-el-scanner-dsmarketscan",
        "excerpt": "Un recorrido paso a paso por el dashboard: cómo leer la tabla de screening, seleccionar una acción y usar los filtros avanzados.",
        "body": f"""
<p>El scanner de DSMarketLearning es la herramienta central del sitio: cada día hábil revisa un grupo de acciones de NYSE y NASDAQ y calcula un conjunto de señales técnicas y fundamentales para ordenarlas de mayor a menor "score". Esta guía explica cómo sacarle provecho, sin asumir que ya sabes qué es cada indicador.</p>

<h2>La tabla de screening</h2>
<p>Es el panel principal. Cada fila es una acción con su precio, RSI, volumen relativo, si rompió su rango de 20 periodos, su tendencia respecto a la media móvil de 200 días, fuerza relativa frente al S&amp;P 500, y datos fundamentales como market cap, P/E, PEG y deuda/patrimonio. El "score" (columna verde/naranja/roja) combina varias de estas señales en un solo número de 0 a 100 &mdash; entre más alto, más criterios técnicos favorables cumple la acción ese día. No es una nota de "qué tan buena es la empresa", es una nota de "qué tantas señales de impulso de corto plazo está mostrando hoy".</p>

<h2>Seleccionar una acción</h2>
<p>Haz clic en el círculo de selección (o en cualquier parte de la fila) y los paneles de abajo &mdash; gráfica e indicadores &mdash; se actualizan automáticamente con esa acción, sin recargar la página. La gráfica muestra velas japonesas con RSI y volumen, y puedes cambiar el periodo (de 1 minuto a mensual) con los botones de arriba.</p>

<h2>Filtros avanzados</h2>
<p>Arriba de la tabla puedes abrir "Filtros avanzados" para acotar el universo: por precio, RSI, volumen relativo, ruptura de rango, tendencia, fuerza relativa, precio objetivo, score mínimo, y datos fundamentales como market cap, P/E, PEG, deuda/patrimonio y bolsa. Son acumulativos &mdash; puedes combinar varios a la vez, por ejemplo "precio menor a $50 + P/E menor a 20 + tendencia alcista".</p>

<h2>Índices de referencia</h2>
<p>El panel de "Índices &amp; alertas" muestra Nasdaq, S&amp;P 500, Dow Jones, oro y petróleo con un semáforo según qué tan fuerte fue el movimiento del día &mdash; útil para tener contexto de si el mercado en general está en un día tranquilo o agitado antes de mirar acciones individuales.</p>

{DISCLAIMER}
""",
        "title_en": "How to use the DSMarketLearning scanner: full guide",
        "excerpt_en": "A step-by-step walkthrough of the dashboard: how to read the screening table, select a stock, and use the advanced filters.",
        "body_en": f"""
<p>The DSMarketLearning scanner is the site's central tool: every business day it scans a group of NYSE and NASDAQ stocks and calculates a set of technical and fundamental signals to rank them from highest to lowest "score." This guide explains how to get the most out of it, without assuming you already know what each indicator is.</p>

<h2>The screening table</h2>
<p>This is the main panel. Each row is a stock with its price, RSI, relative volume, whether it broke its 20-period range, its trend relative to the 200-day moving average, relative strength versus the S&amp;P 500, and fundamental data like market cap, P/E, PEG, and debt/equity. The "score" (green/orange/red column) combines several of these signals into a single number from 0 to 100 &mdash; the higher it is, the more favorable technical criteria the stock meets that day. It's not a grade for "how good the company is," it's a grade for "how many short-term momentum signals it's showing today."</p>

<h2>Selecting a stock</h2>
<p>Click the selection circle (or anywhere on the row) and the panels below &mdash; chart and indicators &mdash; update automatically for that stock, without reloading the page. The chart shows Japanese candlesticks with RSI and volume, and you can change the period (from 1 minute to monthly) using the buttons above it.</p>

<h2>Advanced filters</h2>
<p>Above the table you can open "Advanced filters" to narrow the universe: by price, RSI, relative volume, range breakout, trend, relative strength, target price, minimum score, and fundamental data like market cap, P/E, PEG, debt/equity, and exchange. They're cumulative &mdash; you can combine several at once, for example "price under $50 + P/E under 20 + uptrend."</p>

<h2>Reference indices</h2>
<p>The "Indices &amp; alerts" panel shows the Nasdaq, S&amp;P 500, Dow Jones, gold, and oil with a traffic-light indicator based on how strong the day's move was &mdash; useful for getting context on whether the overall market is having a quiet or a volatile day before you look at individual stocks.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Qué es el RSI y cómo interpretarlo al elegir una acción",
        "slug": "que-es-el-rsi-como-interpretarlo",
        "excerpt": "El RSI es uno de los indicadores más usados en análisis técnico. Explicamos qué mide, cómo se calcula y qué significan sus zonas de sobrecompra y sobreventa.",
        "body": f"""
<p>El RSI (Relative Strength Index, o índice de fuerza relativa) es un indicador de momentum que mide qué tan rápido y qué tan fuerte se ha movido el precio de una acción en un periodo reciente, normalmente 14 sesiones. Se expresa en una escala de 0 a 100.</p>

<h2>Cómo se calcula, en términos simples</h2>
<p>El RSI compara el promedio de las subidas contra el promedio de las bajadas durante el periodo elegido. Si en esos 14 días las subidas fueron mucho más grandes y frecuentes que las bajadas, el RSI sube hacia 100. Si pasó lo contrario, baja hacia 0. No necesitas calcularlo a mano &mdash; el scanner lo hace por ti para cada acción &mdash; pero entender la lógica ayuda a no tratarlo como una caja negra.</p>

<h2>Las zonas que importan</h2>
<ul>
<li><strong>Sobre 70:</strong> zona de sobrecompra. El precio ha subido con fuerza y rapidez; no significa que vaya a caer de inmediato, pero sí que el "combustible" de corto plazo puede estar agotándose.</li>
<li><strong>Bajo 30:</strong> zona de sobreventa. El precio ha caído con fuerza; puede ser una señal de rebote, o simplemente una tendencia bajista fuerte que sigue cayendo (el RSI puede quedarse "sobrevendido" por semanas en una caída seria).</li>
<li><strong>Entre 50 y 70:</strong> la zona que el scanner de DSMarketLearning pondera más en el score, porque suele indicar impulso alcista sano, sin estar todavía en el extremo de sobrecompra.</li>
</ul>

<h2>El error más común</h2>
<p>Usar el RSI solo, sin contexto. Un RSI en sobrecompra dentro de una tendencia alcista fuerte (por ejemplo, con el precio sobre su media de 200 días) es muy distinto a un RSI en sobrecompra dentro de un rebote dentro de una tendencia bajista. Por eso el scanner combina el RSI con la tendencia (MA200) y la fuerza relativa vs. el mercado, en vez de usarlo aislado.</p>

{DISCLAIMER}
""",
        "title_en": "What RSI is and how to read it when picking a stock",
        "excerpt_en": "RSI is one of the most widely used indicators in technical analysis. We explain what it measures, how it's calculated, and what its overbought and oversold zones mean.",
        "body_en": f"""
<p>RSI (Relative Strength Index) is a momentum indicator that measures how fast and how strongly a stock's price has moved over a recent period, typically 14 sessions. It's expressed on a 0 to 100 scale.</p>

<h2>How it's calculated, in simple terms</h2>
<p>RSI compares the average of the gains against the average of the losses over the chosen period. If in those 14 days the gains were much bigger and more frequent than the losses, RSI rises toward 100. If the opposite happened, it drops toward 0. You don't need to calculate it by hand &mdash; the scanner does it for you for every stock &mdash; but understanding the logic helps you avoid treating it as a black box.</p>

<h2>The zones that matter</h2>
<ul>
<li><strong>Above 70:</strong> overbought zone. The price has risen strongly and quickly; it doesn't mean it will fall immediately, but the short-term "fuel" may be running low.</li>
<li><strong>Below 30:</strong> oversold zone. The price has fallen sharply; it can be a sign of a bounce, or simply a strong downtrend that keeps falling (RSI can stay "oversold" for weeks in a serious decline).</li>
<li><strong>Between 50 and 70:</strong> the zone the DSMarketLearning scanner weighs most heavily in the score, because it usually signals healthy bullish momentum without yet being at the overbought extreme.</li>
</ul>

<h2>The most common mistake</h2>
<p>Using RSI alone, without context. An overbought RSI inside a strong uptrend (for example, with the price above its 200-day average) is very different from an overbought RSI inside a bounce within a downtrend. That's why the scanner combines RSI with trend (MA200) and relative strength vs. the market, instead of using it in isolation.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "La media móvil de 200 días: el filtro de tendencia que no deberías ignorar",
        "slug": "media-movil-200-dias-filtro-tendencia",
        "excerpt": "Por qué comparar el precio actual contra su media de 200 días es una de las formas más simples y efectivas de distinguir una tendencia real de un rebote pasajero.",
        "body": f"""
<p>La media móvil de 200 días (MA200) es el promedio del precio de cierre de una acción durante los últimos 200 días de trading &mdash; aproximadamente un año de mercado. Es uno de los indicadores de tendencia de largo plazo más usados, tanto por inversionistas individuales como por gestores institucionales.</p>

<h2>Por qué es útil</h2>
<p>El precio de una acción se mueve todos los días por ruido de corto plazo: noticias, resultados trimestrales, movimientos generales del mercado. La MA200, al promediar tanto tiempo, suaviza ese ruido y deja ver la dirección de fondo. Cuando el precio está por encima de su MA200, la tendencia de fondo es alcista; cuando está por debajo, es bajista.</p>

<h2>Por qué el scanner lo usa como filtro, no solo como dato</h2>
<p>Una acción puede tener un RSI atractivo y volumen alto en un solo día, y aun así estar en una tendencia bajista de fondo &mdash; es decir, ser un rebote dentro de una caída, no el inicio de algo sostenible. Por eso en el score del scanner, estar por encima de la MA200 pesa 25 de 100 puntos: es el filtro que evita confundir "se movió mucho hoy" con "está en una tendencia alcista real".</p>

<h2>Sus límites</h2>
<p>La MA200 reacciona con retraso, por diseño: al promediar 200 días, tarda en reflejar cambios recientes. Eso significa que confirma tendencias ya establecidas, pero no anticipa giros. Tampoco dice nada sobre la calidad del negocio detrás de la acción &mdash; es un indicador puramente de precio. Por eso en DSMarketLearning se combina con indicadores fundamentales (P/E, PEG, deuda) y no se usa solo.</p>

{DISCLAIMER}
""",
        "title_en": "The 200-day moving average: the trend filter you shouldn't ignore",
        "excerpt_en": "Why comparing the current price against its 200-day average is one of the simplest and most effective ways to tell a real trend apart from a passing bounce.",
        "body_en": f"""
<p>The 200-day moving average (MA200) is the average closing price of a stock over the last 200 trading days &mdash; roughly a year of market activity. It's one of the most widely used long-term trend indicators, used by both individual investors and institutional managers.</p>

<h2>Why it's useful</h2>
<p>A stock's price moves every day due to short-term noise: news, quarterly results, general market moves. By averaging over such a long span, the MA200 smooths out that noise and reveals the underlying direction. When the price is above its MA200, the underlying trend is bullish; when it's below, it's bearish.</p>

<h2>Why the scanner uses it as a filter, not just a data point</h2>
<p>A stock can have an attractive RSI and high volume on a single day and still be in an underlying downtrend &mdash; in other words, a bounce within a decline, not the start of something sustainable. That's why in the scanner's score, being above the MA200 is worth 25 of 100 points: it's the filter that prevents confusing "it moved a lot today" with "it's in a real uptrend."</p>

<h2>Its limits</h2>
<p>The MA200 reacts with a lag, by design: averaging 200 days means it takes time to reflect recent changes. That means it confirms trends already in place, but doesn't anticipate turns. It also says nothing about the quality of the business behind the stock &mdash; it's a purely price-based indicator. That's why DSMarketLearning combines it with fundamental indicators (P/E, PEG, debt) rather than using it alone.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "P/E, PEG y por qué el precio de una acción no dice nada por sí solo",
        "slug": "pe-peg-precio-accion-no-dice-nada",
        "excerpt": "Una acción de $500 no es automáticamente 'cara', y una de $5 no es automáticamente 'barata'. Estos dos ratios ayudan a comparar peras con peras.",
        "body": f"""
<p>Uno de los errores más comunes al empezar a invertir es juzgar si una acción está "cara" o "barata" mirando únicamente su precio en dólares. El precio por sí solo no dice nada: depende de cuántas acciones existen en circulación. Para comparar de forma útil, se usan ratios que relacionan el precio con algo del negocio.</p>

<h2>P/E (Price to Earnings)</h2>
<p>El P/E divide el precio de la acción entre la utilidad por acción. En otras palabras: cuánto está pagando el mercado por cada dólar de utilidad que genera la empresa. Un P/E de 30 significa que, al ritmo actual de utilidades, tomaría 30 años "recuperar" ese precio solo con las ganancias reportadas (una simplificación, pero útil para entender la lógica).</p>
<p>Un P/E alto no es necesariamente malo: puede reflejar que el mercado espera un crecimiento fuerte de utilidades a futuro. Un P/E bajo tampoco es automáticamente una oportunidad: puede reflejar que el mercado espera que las utilidades caigan, o que hay un riesgo que el precio ya está descontando.</p>

<h2>PEG: el P/E ajustado por crecimiento</h2>
<p>El PEG divide el P/E entre la tasa de crecimiento esperado de utilidades. Es un intento de responder la pregunta que el P/E solo no responde: "¿este precio es razonable dado cuánto se espera que crezca la empresa?". Como referencia general (no una regla fija): un PEG por debajo de 1 puede sugerir que el precio está barato relativo a su crecimiento esperado; por encima de 2, que está caro incluso considerando ese crecimiento.</p>

<h2>Por qué en DSMarketLearning se muestran juntos, con semáforo</h2>
<p>Ni el P/E ni el PEG tienen un "número correcto" universal &mdash; varían mucho por sector (una utility y una empresa de software casi nunca tienen el mismo P/E "normal"). Por eso en la página de cada acción se muestran con un medidor visual y una interpretación en texto, como referencia rápida y no como un veredicto absoluto.</p>

{DISCLAIMER}
""",
        "title_en": "P/E, PEG, and why a stock's price alone tells you nothing",
        "excerpt_en": "A $500 stock isn't automatically 'expensive,' and a $5 stock isn't automatically 'cheap.' These two ratios help you compare apples to apples.",
        "body_en": f"""
<p>One of the most common mistakes when starting to invest is judging whether a stock is "expensive" or "cheap" by looking only at its dollar price. Price alone tells you nothing: it depends on how many shares are outstanding. To compare stocks meaningfully, you need ratios that relate price to something about the business.</p>

<h2>P/E (Price to Earnings)</h2>
<p>P/E divides the stock's price by earnings per share. In other words: how much the market is paying for each dollar of profit the company generates. A P/E of 30 means that, at the current pace of earnings, it would take 30 years to "recoup" that price from reported profits alone (a simplification, but useful for understanding the logic).</p>
<p>A high P/E isn't necessarily bad: it can reflect that the market expects strong future earnings growth. A low P/E isn't automatically an opportunity either: it can reflect that the market expects earnings to decline, or that there's a risk already priced in.</p>

<h2>PEG: P/E adjusted for growth</h2>
<p>PEG divides P/E by the expected earnings growth rate. It's an attempt to answer the question P/E alone can't: "is this price reasonable given how much the company is expected to grow?" As a general reference (not a fixed rule): a PEG below 1 can suggest the price is cheap relative to its expected growth; above 2, that it's expensive even accounting for that growth.</p>

<h2>Why DSMarketLearning shows them together, with a gauge</h2>
<p>Neither P/E nor PEG has a universal "correct number" &mdash; they vary a lot by sector (a utility and a software company almost never share the same "normal" P/E). That's why each stock's page shows them with a visual gauge and a plain-language interpretation, as a quick reference rather than an absolute verdict.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Deuda/patrimonio: cómo saber si una empresa está sobreapalancada",
        "slug": "deuda-patrimonio-empresa-sobreapalancada",
        "excerpt": "Cuánta deuda tiene una empresa frente a su patrimonio determina qué tan expuesta está a subidas de tasas de interés o caídas en su flujo de caja.",
        "body": f"""
<p>El ratio deuda/patrimonio (debt-to-equity) compara cuánta deuda total tiene una empresa frente a su patrimonio (lo que técnicamente le pertenece a los accionistas). Es uno de los indicadores más directos de qué tan apalancado está un negocio.</p>

<h2>Por qué importa</h2>
<p>Una empresa con deuda alta no es necesariamente un mal negocio &mdash; muchas industrias (bancos, utilities, telecomunicaciones) operan de forma normal con niveles de deuda que serían preocupantes en otro sector. Pero, en igualdad de condiciones, más deuda significa más riesgo: más sensibilidad a subidas de tasas de interés, y menos margen de maniobra si el flujo de caja se reduce en un mal trimestre.</p>

<h2>Cómo leerlo en la práctica</h2>
<ul>
<li><strong>Menor a 50%:</strong> apalancamiento bajo, balance conservador.</li>
<li><strong>Entre 50% y 150%:</strong> apalancamiento moderado, normal en muchas industrias.</li>
<li><strong>Sobre 150%:</strong> apalancamiento alto &mdash; vale la pena entender por qué (¿es una industria intensiva en capital? ¿la empresa se endeudó para crecer o para tapar pérdidas?) antes de sacar conclusiones.</li>
</ul>

<h2>El contexto importa más que el número aislado</h2>
<p>Comparar el deuda/patrimonio de una acción contra el promedio de su propia industria es mucho más informativo que compararlo contra un número fijo. Una aerolínea con 120% de deuda/patrimonio puede ser normal para el sector; una empresa de software con el mismo nivel sería una señal de alerta, porque ese sector suele operar con muy poca deuda.</p>

{DISCLAIMER}
""",
        "title_en": "Debt/equity: how to tell if a company is overleveraged",
        "excerpt_en": "How much debt a company carries relative to its equity determines how exposed it is to rising interest rates or a drop in cash flow.",
        "body_en": f"""
<p>The debt-to-equity ratio compares how much total debt a company carries against its equity (what technically belongs to shareholders). It's one of the most direct indicators of how leveraged a business is.</p>

<h2>Why it matters</h2>
<p>A company with high debt isn't necessarily a bad business &mdash; many industries (banks, utilities, telecoms) operate normally with debt levels that would be concerning in another sector. But, all else equal, more debt means more risk: more sensitivity to rising interest rates, and less room to maneuver if cash flow drops in a bad quarter.</p>

<h2>How to read it in practice</h2>
<ul>
<li><strong>Below 50%:</strong> low leverage, conservative balance sheet.</li>
<li><strong>Between 50% and 150%:</strong> moderate leverage, normal in many industries.</li>
<li><strong>Above 150%:</strong> high leverage &mdash; worth understanding why (is it a capital-intensive industry? did the company take on debt to grow or to cover losses?) before drawing conclusions.</li>
</ul>

<h2>Context matters more than the isolated number</h2>
<p>Comparing a stock's debt/equity against its own industry's average is far more informative than comparing it against a fixed number. An airline with 120% debt/equity might be normal for the sector; a software company at the same level would be a red flag, because that sector typically operates with very little debt.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "ATR y stop-loss: cómo definir dónde limitar una pérdida",
        "slug": "atr-stop-loss-limitar-perdida",
        "excerpt": "El ATR mide la volatilidad reciente de una acción y es la base para calcular un stop-loss que se ajusta al comportamiento real de cada acción, no a un porcentaje fijo arbitrario.",
        "body": f"""
<p>Uno de los aspectos más descuidados por quienes empiezan a invertir no es "qué comprar", sino "en qué punto reconocer que la idea no funcionó y salir". El ATR (Average True Range) es una herramienta técnica pensada exactamente para eso.</p>

<h2>Qué mide el ATR</h2>
<p>El ATR calcula el rango de movimiento promedio de una acción durante un periodo (normalmente 14 sesiones), considerando gaps entre el cierre de un día y la apertura del siguiente. En términos simples: cuánto se mueve esta acción en un día "normal". Una acción con ATR alto es más volátil día a día que una con ATR bajo, independientemente de su precio.</p>

<h2>Por qué usarlo para el stop-loss en vez de un porcentaje fijo</h2>
<p>Un error común es poner el stop-loss a un porcentaje fijo (por ejemplo, "siempre 5% abajo") sin importar la acción. El problema: una acción que normalmente se mueve 6-7% en un día cualquiera activaría ese stop por simple ruido, no porque la idea de inversión haya cambiado. El ATR permite ajustar el stop a la volatilidad real de cada acción: en DSMarketLearning, el "stop sugerido" se calcula como el precio actual menos 1.5 veces el ATR de 14 periodos &mdash; una referencia que respira con el comportamiento normal de cada acción en particular.</p>

<h2>Una referencia técnica, no una recomendación</h2>
<p>Este cálculo es una herramienta de gestión de riesgo, no una predicción de hacia dónde va el precio. Sirve para responder de antemano la pregunta "¿en qué punto reconozco que estaba equivocado?", antes de que la emoción del momento haga esa decisión más difícil.</p>

{DISCLAIMER}
""",
        "title_en": "ATR and stop-loss: how to decide where to cap a loss",
        "excerpt_en": "ATR measures a stock's recent volatility and is the basis for calculating a stop-loss that adapts to each stock's actual behavior, instead of an arbitrary fixed percentage.",
        "body_en": f"""
<p>One of the most neglected aspects for people starting to invest isn't "what to buy," but "at what point do I admit the idea didn't work and get out." ATR (Average True Range) is a technical tool built exactly for that.</p>

<h2>What ATR measures</h2>
<p>ATR calculates a stock's average trading range over a period (typically 14 sessions), accounting for gaps between one day's close and the next day's open. In simple terms: how much this stock moves on a "normal" day. A stock with a high ATR is more volatile day to day than one with a low ATR, regardless of its price.</p>

<h2>Why use it for a stop-loss instead of a fixed percentage</h2>
<p>A common mistake is setting the stop-loss at a fixed percentage (for example, "always 5% below") regardless of the stock. The problem: a stock that normally moves 6-7% on any given day would trigger that stop from simple noise, not because the investment thesis changed. ATR lets you adjust the stop to each stock's actual volatility: on DSMarketLearning, the "suggested stop" is calculated as the current price minus 1.5 times the 14-period ATR &mdash; a reference that breathes with each particular stock's normal behavior.</p>

<h2>A technical reference, not a recommendation</h2>
<p>This calculation is a risk-management tool, not a prediction of where the price is headed. It helps answer, ahead of time, the question "at what point do I recognize I was wrong?" &mdash; before in-the-moment emotion makes that decision harder.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Fuerza relativa: por qué una acción que sube no siempre le está ganando al mercado",
        "slug": "fuerza-relativa-vs-mercado",
        "excerpt": "Si el S&P 500 sube 10% y tu acción sube 6%, técnicamente subió, pero le está perdiendo al mercado. Así se mide la fuerza relativa y por qué importa.",
        "body": f"""
<p>Es fácil alegrarse porque una acción "subió", pero esa cifra aislada puede ser engañosa. Si en el mismo periodo el mercado en general (el S&amp;P 500, por ejemplo) subió más, esa acción en realidad está rezagada &mdash; solo está subiendo porque casi todo sube quncuando el mercado está en tendencia alcista general.</p>

<h2>Qué es la fuerza relativa (RS)</h2>
<p>La fuerza relativa compara el rendimiento de una acción contra un índice de referencia durante el mismo periodo. En DSMarketLearning se calcula como el rendimiento de ~3 meses de la acción, menos el rendimiento del S&amp;P 500 en ese mismo periodo, expresado en puntos porcentuales. Un RS de +8pp significa que la acción le ganó al mercado por 8 puntos porcentuales en ese periodo; un RS de -5pp significa que se quedó 5 puntos por debajo.</p>

<h2>Por qué es una señal más honesta que "subió X%"</h2>
<p>Durante un mercado alcista generalizado, casi todas las acciones suben, así que "subió" deja de ser información útil por sí sola. La fuerza relativa aísla qué parte de ese movimiento es específico de la acción y no simplemente el mercado arrastrándola. Las acciones con fuerza relativa positiva sostenida suelen ser las que atraen más interés institucional dentro de un sector o del mercado en general.</p>

<h2>Cómo se usa en el score del scanner</h2>
<p>El score premia hasta 20 puntos de 100 cuando la fuerza relativa es positiva, con un tope en +10pp para evitar que un solo movimiento extremo domine el cálculo. Es la forma en que el scanner distingue "esta acción tiene impulso propio" de "esta acción solo se está moviendo con la marea del mercado".</p>

{DISCLAIMER}
""",
        "title_en": "Relative strength: why a stock going up isn't always beating the market",
        "excerpt_en": "If the S&P 500 rises 10% and your stock rises 6%, it technically went up, but it's losing to the market. Here's how relative strength is measured and why it matters.",
        "body_en": f"""
<p>It's easy to be pleased that a stock "went up," but that number alone can be misleading. If, over the same period, the overall market (the S&amp;P 500, for example) rose more, that stock is actually lagging &mdash; it's only going up because almost everything goes up when the market is in a broad uptrend.</p>

<h2>What relative strength (RS) is</h2>
<p>Relative strength compares a stock's performance against a benchmark index over the same period. On DSMarketLearning it's calculated as the stock's ~3-month return minus the S&amp;P 500's return over that same period, expressed in percentage points. An RS of +8pp means the stock beat the market by 8 percentage points over that period; an RS of -5pp means it fell 5 points short.</p>

<h2>Why it's a more honest signal than "it rose X%"</h2>
<p>During a broad bull market, almost every stock rises, so "it went up" stops being useful information on its own. Relative strength isolates how much of that move is specific to the stock, rather than the market simply carrying it along. Stocks with sustained positive relative strength tend to be the ones attracting more institutional interest within a sector or the market as a whole.</p>

<h2>How it's used in the scanner's score</h2>
<p>The score awards up to 20 of 100 points when relative strength is positive, capped at +10pp to prevent a single extreme move from dominating the calculation. It's how the scanner distinguishes "this stock has its own momentum" from "this stock is just moving with the market's tide."</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Rupturas de rango: qué son y por qué generan interés en el corto plazo",
        "slug": "rupturas-de-rango-corto-plazo",
        "excerpt": "Cuando el precio supera el máximo de varias sesiones anteriores, suele atraer atención y volumen adicional. Explicamos la lógica detrás de esta señal técnica clásica.",
        "body": f"""
<p>Una "ruptura de rango" (breakout) ocurre cuando el precio de cierre de una acción supera el máximo alcanzado durante un periodo reciente &mdash; en el caso del scanner de DSMarketLearning, los últimos 20 periodos. Es una de las señales técnicas más antiguas y estudiadas del análisis técnico.</p>

<h2>La lógica detrás de la señal</h2>
<p>Cuando una acción se mantiene "atrapada" dentro de un rango de precios por varias semanas, se acumulan órdenes de compra y venta alrededor de esos límites. Si el precio finalmente logra superar el techo de ese rango, dos cosas suelen pasar: los vendedores que estaban esperando ese nivel para vender ya lo hicieron (o se quedan esperando más arriba), y compradores que estaban al margen deciden entrar al ver la ruptura confirmada. Ese cambio de comportamiento puede generar un impulso de volumen y precio adicional.</p>

<h2>Por qué no es una señal infalible</h2>
<p>Las rupturas "falsas" (donde el precio supera el rango brevemente y luego vuelve a caer dentro de él) son comunes, especialmente en mercados con poco volumen o en acciones poco líquidas. Por eso el scanner no usa la ruptura como criterio único: la combina con el volumen relativo (¿hay volumen real respaldando el movimiento?) y con la tendencia de fondo (MA200), para reducir la cantidad de rupturas que en realidad son ruido.</p>

<h2>Cómo usarla en la práctica</h2>
<p>Una ruptura con volumen relativo alto (por encima de 1.5x-2x el promedio) y con la acción ya en tendencia alcista de fondo es una combinación bastante más sólida que una ruptura aislada con volumen bajo. Es exactamente la combinación que el score del scanner intenta capturar.</p>

{DISCLAIMER}
""",
        "title_en": "Range breakouts: what they are and why they draw short-term interest",
        "excerpt_en": "When the price clears the high of several previous sessions, it tends to attract extra attention and volume. We explain the logic behind this classic technical signal.",
        "body_en": f"""
<p>A "range breakout" occurs when a stock's closing price exceeds the high reached over a recent period &mdash; in the case of the DSMarketLearning scanner, the last 20 periods. It's one of the oldest and most studied technical signals in technical analysis.</p>

<h2>The logic behind the signal</h2>
<p>When a stock stays "trapped" inside a price range for several weeks, buy and sell orders pile up around those boundaries. If the price finally manages to clear the top of that range, two things tend to happen: sellers who were waiting for that level to sell have already done so (or are now waiting higher up), and buyers who were sitting on the sidelines decide to step in once they see the breakout confirmed. That shift in behavior can generate additional volume and price momentum.</p>

<h2>Why it's not a foolproof signal</h2>
<p>"False" breakouts (where the price briefly clears the range and then falls back inside it) are common, especially in low-volume markets or thinly traded stocks. That's why the scanner doesn't use breakouts as a standalone criterion: it combines them with relative volume (is there real volume backing the move?) and the underlying trend (MA200), to filter out breakouts that are really just noise.</p>

<h2>How to use it in practice</h2>
<p>A breakout with high relative volume (above 1.5x-2x the average) with the stock already in an underlying uptrend is a much sturdier combination than an isolated breakout on low volume. That's exactly the combination the scanner's score tries to capture.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Cómo leer la recomendación de consenso de los analistas (y sus límites)",
        "slug": "recomendacion-consenso-analistas-limites",
        "excerpt": "Cuando 40 analistas cubren una acción, casi nunca opinan lo mismo. Explicamos cómo se construye el consenso y por qué no debería ser tu única fuente de decisión.",
        "body": f"""
<p>Las acciones grandes suelen tener docenas de analistas de distintos bancos y casas de inversión que las cubren de forma continua, publicando recomendaciones de compra, mantener o venta, junto con un precio objetivo. En DSMarketLearning agregamos esa información en un formato visual (gráfica de dona) para cada acción.</p>

<h2>Cómo se construye el consenso</h2>
<p>Cada analista clasifica su recomendación en una escala que va de "compra fuerte" a "venta fuerte". El consenso que se muestra agrupa esas opiniones en tres categorías &mdash; compra, mantener, venta &mdash; y muestra cuántos analistas están en cada una, además de un puntaje promedio (donde 1 es compra fuerte y 5 es venta).</p>

<h2>El precio objetivo</h2>
<p>Junto al consenso se muestra el precio objetivo promedio a 12 meses que publican esos mismos analistas, con un rango entre el más bajo y el más alto. Ese rango suele ser más informativo que el promedio solo: un rango angosto sugiere que hay bastante acuerdo sobre hacia dónde va la empresa; un rango muy amplio sugiere que hay mucha incertidumbre o visiones muy distintas sobre su futuro.</p>

<h2>Por qué no debería ser tu única fuente</h2>
<p>Los analistas tienen incentivos y sesgos propios (relación con la empresa, banca de inversión, etc.), y sus estimados cambian con el tiempo &mdash; a veces reaccionando a la noticia en vez de anticipándola. Un consenso de "compra" no es una garantía, y un precio objetivo no es una promesa. Es un dato más para contextualizar, no una señal de entrada por sí sola.</p>

{DISCLAIMER}
""",
        "title_en": "How to read the analyst consensus recommendation (and its limits)",
        "excerpt_en": "When 40 analysts cover a stock, they almost never agree. We explain how the consensus is built and why it shouldn't be your only source for a decision.",
        "body_en": f"""
<p>Large-cap stocks usually have dozens of analysts from different banks and investment firms covering them continuously, publishing buy, hold, or sell recommendations along with a target price. On DSMarketLearning we aggregate that information into a visual format (a donut chart) for each stock.</p>

<h2>How the consensus is built</h2>
<p>Each analyst rates their recommendation on a scale that runs from "strong buy" to "strong sell." The consensus shown groups those opinions into three categories &mdash; buy, hold, sell &mdash; and shows how many analysts fall into each, plus an average score (where 1 is strong buy and 5 is sell).</p>

<h2>The target price</h2>
<p>Alongside the consensus, we show the average 12-month target price published by those same analysts, with a range from the lowest to the highest. That range is often more informative than the average alone: a narrow range suggests there's fairly strong agreement on where the company is headed; a very wide range suggests a lot of uncertainty or very different views on its future.</p>

<h2>Why it shouldn't be your only source</h2>
<p>Analysts have their own incentives and biases (relationships with the company, investment banking ties, etc.), and their estimates change over time &mdash; sometimes reacting to news rather than anticipating it. A "buy" consensus isn't a guarantee, and a target price isn't a promise. It's one more data point for context, not a standalone entry signal.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Market cap: qué significa el tamaño de una empresa para tu inversión",
        "slug": "market-cap-tamano-empresa-inversion",
        "excerpt": "El valor de mercado de una empresa no es solo una cifra de tamaño: influye directamente en su volatilidad, liquidez y en qué tan rápido puede moverse su precio.",
        "body": f"""
<p>El market cap (capitalización de mercado) es el valor total de una empresa en bolsa: el precio de la acción multiplicado por el número de acciones en circulación. Es la forma estándar de medir el "tamaño" de una empresa que cotiza en bolsa, y suele agruparse en categorías.</p>

<h2>Las categorías más comunes</h2>
<ul>
<li><strong>Mega/large-cap</strong> (generalmente sobre $10B): empresas grandes y establecidas, con más liquidez y, en general, menor volatilidad relativa. Suelen tener más cobertura de analistas y más información pública disponible.</li>
<li><strong>Mid-cap</strong> (entre ~$2B y $10B): empresas en una etapa de crecimiento más activa, con un balance entre estabilidad y potencial de crecimiento.</li>
<li><strong>Small/micro-cap</strong> (bajo $2B): empresas más pequeñas, con mayor potencial de crecimiento porcentual, pero también mayor volatilidad, menor liquidez y menos cobertura de analistas &mdash; lo que significa menos información disponible y movimientos de precio más bruscos con la misma noticia.</li>
</ul>

<h2>Por qué influye en cómo se mueve el precio</h2>
<p>En una empresa mega-cap, se necesita mucho dinero comprando o vendiendo para mover el precio de forma significativa. En una small-cap, la misma cantidad de dinero puede generar un movimiento de precio mucho más grande, simplemente porque hay menos acciones en circulación y menos volumen diario. Esto no la hace "mejor" ni "peor" &mdash; la hace diferente en términos de riesgo y comportamiento.</p>

<h2>Cómo usarlo junto a otros indicadores</h2>
<p>El market cap por sí solo no dice si una empresa es una buena inversión, pero sí ayuda a calibrar expectativas: cuánta volatilidad es "normal" esperar, y cuánta información pública vas a poder encontrar para investigarla más a fondo.</p>

{DISCLAIMER}
""",
        "title_en": "Market cap: what a company's size means for your investment",
        "excerpt_en": "A company's market value isn't just a size figure: it directly affects its volatility, liquidity, and how fast its price can move.",
        "body_en": f"""
<p>Market cap (market capitalization) is a company's total value on the market: the share price multiplied by the number of shares outstanding. It's the standard way to measure the "size" of a publicly traded company, and it's usually grouped into categories.</p>

<h2>The most common categories</h2>
<ul>
<li><strong>Mega/large-cap</strong> (generally above $10B): large, established companies, with more liquidity and, generally, lower relative volatility. They tend to have more analyst coverage and more public information available.</li>
<li><strong>Mid-cap</strong> (roughly $2B to $10B): companies in a more active growth stage, balancing stability with growth potential.</li>
<li><strong>Small/micro-cap</strong> (under $2B): smaller companies, with more percentage growth potential, but also more volatility, less liquidity, and less analyst coverage &mdash; meaning less available information and sharper price moves on the same piece of news.</li>
</ul>

<h2>Why it affects how the price moves</h2>
<p>In a mega-cap company, it takes a lot of money buying or selling to move the price meaningfully. In a small-cap, the same amount of money can produce a much bigger price move, simply because there are fewer shares outstanding and less daily volume. This doesn't make it "better" or "worse" &mdash; it makes it different in terms of risk and behavior.</p>

<h2>How to use it alongside other indicators</h2>
<p>Market cap alone doesn't tell you whether a company is a good investment, but it does help calibrate expectations: how much volatility is "normal" to expect, and how much public information you'll be able to find to research it further.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Dividendos: qué es el dividend yield y por qué no siempre es bueno que sea alto",
        "slug": "dividend-yield-no-siempre-alto-es-bueno",
        "excerpt": "Un dividend yield muy alto puede ser una señal de generosidad del negocio, o una señal de alerta de que el mercado espera problemas. Aprende a distinguirlos.",
        "body": f"""
<p>El dividend yield (rendimiento por dividendo) mide cuánto paga una empresa en dividendos anuales como porcentaje de su precio actual. Es una de las formas más directas en que una empresa devuelve valor a sus accionistas, además de la apreciación del precio.</p>

<h2>Empresas que pagan dividendos vs. las que no</h2>
<p>No todas las empresas reparten dividendos, y eso no es necesariamente negativo. Las empresas en etapa de crecimiento fuerte suelen preferir reinvertir todas sus utilidades en el propio negocio (nuevos productos, expansión) en vez de repartirlas. Las empresas más maduras, con crecimiento más estable, suelen destinar una parte de sus utilidades a dividendos porque no necesitan reinvertir tanto capital para seguir creciendo.</p>

<h2>La trampa del yield "demasiado alto"</h2>
<p>Aquí está el matiz importante: el dividend yield es un porcentaje sobre el precio, así que si el precio de una acción cae fuerte pero la empresa no ha recortado el dividendo todavía, el yield sube automáticamente en el cálculo &mdash; aunque nada haya mejorado. Un yield inusualmente alto comparado con el resto de su industria suele ser una señal de que el mercado ya está anticipando un recorte de dividendo, no una oportunidad gratis.</p>

<h2>Qué revisar antes de dejarte llevar por un yield alto</h2>
<p>Vale la pena revisar si las utilidades de la empresa realmente cubren el dividendo que está pagando (el "payout ratio"), y si ese yield alto se debe a una caída reciente y fuerte del precio. Un dividendo consistente en una empresa financieramente sólida es muy distinto a un yield inflado por un precio en caída libre.</p>

{DISCLAIMER}
""",
        "title_en": "Dividends: what dividend yield is and why a high one isn't always good",
        "excerpt_en": "A very high dividend yield can be a sign of a generous business, or a warning sign that the market expects trouble. Learn to tell them apart.",
        "body_en": f"""
<p>Dividend yield measures how much a company pays in annual dividends as a percentage of its current price. It's one of the most direct ways a company returns value to shareholders, beyond price appreciation.</p>

<h2>Companies that pay dividends vs. those that don't</h2>
<p>Not every company pays dividends, and that's not necessarily bad. Companies in a strong growth stage usually prefer to reinvest all their earnings back into the business (new products, expansion) instead of paying them out. More mature companies with steadier growth typically allocate a portion of earnings to dividends because they don't need to reinvest as much capital to keep growing.</p>

<h2>The "too high" yield trap</h2>
<p>Here's the important nuance: dividend yield is a percentage of price, so if a stock's price drops sharply but the company hasn't cut the dividend yet, the yield automatically rises in the calculation &mdash; even though nothing actually improved. An unusually high yield compared to the rest of its industry is often a sign the market is already pricing in a dividend cut, not a free opportunity.</p>

<h2>What to check before getting drawn in by a high yield</h2>
<p>It's worth checking whether the company's earnings actually cover the dividend it's paying (the "payout ratio"), and whether that high yield is due to a recent, sharp price decline. A consistent dividend from a financially solid company is very different from a yield inflated by a price in free fall.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Beta: cómo medir qué tan volátil es una acción frente al mercado",
        "slug": "beta-volatilidad-frente-al-mercado",
        "excerpt": "El beta compara los movimientos de una acción contra el mercado en general. Un beta de 1.5 no es 'más riesgo' en abstracto: es más riesgo Y más potencial de retorno.",
        "body": f"""
<p>El beta es un indicador estadístico que mide qué tan sensible es el precio de una acción a los movimientos del mercado en general, usando el S&amp;P 500 como referencia (beta = 1.0).</p>

<h2>Cómo interpretar el número</h2>
<ul>
<li><strong>Beta menor a 1:</strong> la acción históricamente se mueve menos que el mercado. Si el S&amp;P 500 sube o baja 10%, esta acción tiende a moverse menos que eso en la misma dirección.</li>
<li><strong>Beta cercano a 1:</strong> se mueve de forma similar al mercado en general.</li>
<li><strong>Beta mayor a 1:</strong> se mueve más que el mercado, en ambas direcciones. Un beta de 1.8 sugiere que, históricamente, cuando el mercado sube o baja fuerte, esta acción tiende a amplificar ese movimiento.</li>
</ul>

<h2>Más riesgo no es sinónimo de "peor"</h2>
<p>Un beta alto no es automáticamente negativo: significa mayor potencial de ganancia en mercados alcistas, junto con mayor potencial de pérdida en mercados bajistas. Es una característica de riesgo/retorno, no una calificación de calidad del negocio. Empresas de sectores cíclicos (tecnología de alto crecimiento, materias primas) suelen tener betas más altos; empresas de sectores defensivos (utilities, consumo básico) suelen tener betas más bajos.</p>

<h2>Por qué es útil conocerlo antes de invertir</h2>
<p>El beta ayuda a calibrar expectativas sobre cuánto podría moverse una posición en un día de alta volatilidad del mercado en general, y a construir una combinación de acciones con distintos niveles de sensibilidad según cuánta volatilidad estás dispuesto a tolerar.</p>

{DISCLAIMER}
""",
        "title_en": "Beta: how to measure how volatile a stock is versus the market",
        "excerpt_en": "Beta compares a stock's moves against the overall market. A beta of 1.5 isn't 'more risk' in the abstract: it's more risk AND more return potential.",
        "body_en": f"""
<p>Beta is a statistical indicator that measures how sensitive a stock's price is to overall market moves, using the S&amp;P 500 as the reference (beta = 1.0).</p>

<h2>How to read the number</h2>
<ul>
<li><strong>Beta below 1:</strong> the stock has historically moved less than the market. If the S&amp;P 500 rises or falls 10%, this stock tends to move less than that in the same direction.</li>
<li><strong>Beta close to 1:</strong> it moves similarly to the overall market.</li>
<li><strong>Beta above 1:</strong> it moves more than the market, in both directions. A beta of 1.8 suggests that, historically, when the market rises or falls sharply, this stock tends to amplify that move.</li>
</ul>

<h2>More risk isn't the same as "worse"</h2>
<p>A high beta isn't automatically bad: it means greater upside potential in bull markets, along with greater downside potential in bear markets. It's a risk/return characteristic, not a quality rating for the business. Companies in cyclical sectors (high-growth tech, commodities) tend to have higher betas; companies in defensive sectors (utilities, staples) tend to have lower ones.</p>

<h2>Why it's useful to know before investing</h2>
<p>Beta helps calibrate expectations for how much a position might move on a day of high overall market volatility, and helps you build a mix of stocks with different sensitivity levels depending on how much volatility you're willing to tolerate.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "El calendario económico: por qué el CPI y el PPI mueven el mercado",
        "slug": "calendario-economico-cpi-ppi",
        "excerpt": "Ciertos datos macroeconómicos, como la inflación (CPI) o los precios al productor (PPI), pueden mover el mercado completo en minutos. Así funciona el calendario económico.",
        "body": f"""
<p>Más allá de las noticias específicas de cada empresa, hay datos macroeconómicos que se publican en fechas programadas y que pueden mover el mercado completo &mdash; no solo una acción o un sector &mdash; en cuestión de minutos. El calendario económico de DSMarketLearning reúne los eventos de impacto medio y alto para la semana.</p>

<h2>CPI: el índice de precios al consumidor</h2>
<p>Mide cuánto han subido los precios que pagan los consumidores por bienes y servicios &mdash; es la medida de inflación más seguida. Cuando el CPI sale más alto de lo esperado, suele generar preocupación de que la Reserva Federal mantenga o suba las tasas de interés por más tiempo, lo que típicamente presiona a la baja tanto a acciones como a bonos. Cuando sale más bajo de lo esperado, suele generar el efecto contrario.</p>

<h2>PPI: el índice de precios al productor</h2>
<p>Mide la inflación desde el lado de los productores, antes de que esos costos lleguen al consumidor final. Se considera un adelanto de hacia dónde podría dirigirse el CPI en los meses siguientes, así que el mercado también le presta atención de cerca.</p>

<h2>Por qué el sistema de estrellas importa</h2>
<p>No todos los datos económicos tienen el mismo impacto. Datos de "bajo impacto" rara vez mueven el mercado de forma notable; los de impacto medio y alto (como CPI, PPI, decisiones de tasas de interés, o el reporte de empleo) sí pueden generar movimientos bruscos en cuestión de minutos tras su publicación. Por eso el calendario económico del sitio filtra específicamente esos eventos de impacto medio (★★) y alto (★★★), para que sepas qué días de la semana podrían traer más volatilidad de lo normal.</p>

{DISCLAIMER}
""",
        "title_en": "The economic calendar: why CPI and PPI move the market",
        "excerpt_en": "Certain macroeconomic data, like inflation (CPI) or producer prices (PPI), can move the entire market in minutes. Here's how the economic calendar works.",
        "body_en": f"""
<p>Beyond company-specific news, there's macroeconomic data released on scheduled dates that can move the entire market &mdash; not just one stock or one sector &mdash; within minutes. DSMarketLearning's economic calendar gathers the medium- and high-impact events for the week.</p>

<h2>CPI: the Consumer Price Index</h2>
<p>Measures how much prices consumers pay for goods and services have risen &mdash; it's the most closely followed inflation gauge. When CPI comes in higher than expected, it usually raises concern that the Federal Reserve will hold or raise interest rates for longer, which typically pressures both stocks and bonds lower. When it comes in lower than expected, it usually has the opposite effect.</p>

<h2>PPI: the Producer Price Index</h2>
<p>Measures inflation from the producers' side, before those costs reach the end consumer. It's considered a leading indicator of where CPI might head in the following months, so the market watches it closely too.</p>

<h2>Why the star system matters</h2>
<p>Not all economic data has the same impact. "Low-impact" data rarely moves the market noticeably; medium- and high-impact data (like CPI, PPI, interest rate decisions, or the jobs report) can trigger sharp moves within minutes of release. That's why the site's economic calendar specifically filters for those medium- (★★) and high-impact (★★★) events, so you know which days of the week might bring more volatility than usual.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Rotación sectorial: cómo el dinero institucional cambia de sector",
        "slug": "rotacion-sectorial-dinero-institucional",
        "excerpt": "El dinero grande no entra ni sale del mercado por completo: se mueve entre sectores según la etapa del ciclo económico. Entender esto ayuda a leer el contexto detrás de un movimiento.",
        "body": f"""
<p>La "rotación sectorial" describe cómo los grandes inversionistas institucionales &mdash; fondos de pensiones, fondos mutuos, aseguradoras &mdash; mueven capital entre distintos sectores de la economía según en qué etapa del ciclo económico se encuentren, en vez de simplemente entrar o salir del mercado por completo.</p>

<h2>La lógica del ciclo económico</h2>
<p>En etapas de expansión económica temprana, suele haber más apetito por sectores cíclicos: consumo discrecional, tecnología, industriales &mdash; negocios que se benefician de que la gente y las empresas gasten más. En etapas de desaceleración o incertidumbre, el capital tiende a rotar hacia sectores defensivos: consumo básico, salud, utilities &mdash; negocios cuya demanda no depende tanto de qué tan bien esté la economía en general (la gente sigue comprando medicinas y pagando electricidad en una recesión).</p>

<h2>Por qué es útil prestarle atención</h2>
<p>Cuando ves que un sector completo empieza a mostrar fuerza relativa positiva de forma sostenida &mdash; no solo una acción, sino varias del mismo sector a la vez &mdash; suele ser una señal más significativa que el movimiento aislado de una sola empresa. Puede reflejar un cambio real en cómo los inversionistas grandes están posicionando su capital, no solo ruido de una noticia puntual.</p>

<h2>Cómo cruzarlo con el scanner</h2>
<p>Si al revisar los resultados del día notas que varias acciones del mismo sector aparecen con score alto, tendencia alcista y fuerza relativa positiva al mismo tiempo, vale la pena preguntarse si es una coincidencia o si refleja algo más amplio pasando en ese sector &mdash; y de ahí partir para investigar más a fondo qué lo está impulsando.</p>

{DISCLAIMER}
""",
        "title_en": "Sector rotation: how institutional money shifts between sectors",
        "excerpt_en": "Big money doesn't fully enter or exit the market: it shifts between sectors depending on the stage of the economic cycle. Understanding this helps you read the context behind a move.",
        "body_en": f"""
<p>"Sector rotation" describes how large institutional investors &mdash; pension funds, mutual funds, insurers &mdash; move capital between different sectors of the economy depending on what stage of the economic cycle they're in, rather than simply entering or exiting the market entirely.</p>

<h2>The logic of the economic cycle</h2>
<p>In early economic expansion stages, there's usually more appetite for cyclical sectors: discretionary consumer goods, technology, industrials &mdash; businesses that benefit from people and companies spending more. In slowdown or uncertain stages, capital tends to rotate toward defensive sectors: staples, healthcare, utilities &mdash; businesses whose demand doesn't depend as much on how well the overall economy is doing (people keep buying medicine and paying for electricity during a recession).</p>

<h2>Why it's worth paying attention to</h2>
<p>When you see an entire sector start showing sustained positive relative strength &mdash; not just one stock, but several from the same sector at once &mdash; it's usually a more meaningful signal than an isolated move by a single company. It can reflect a real shift in how large investors are positioning their capital, not just noise from a single headline.</p>

<h2>How to cross-reference it with the scanner</h2>
<p>If, while reviewing the day's results, you notice several stocks from the same sector showing up with high scores, an uptrend, and positive relative strength at the same time, it's worth asking whether that's a coincidence or reflects something broader happening in that sector &mdash; and use that as a starting point to dig into what's driving it.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Gestión de riesgo básica: lo primero que deberías definir antes de comprar",
        "slug": "gestion-de-riesgo-basica-antes-de-comprar",
        "excerpt": "Antes de preguntarte 'qué comprar', vale la pena responder tres preguntas de gestión de riesgo que casi nadie se hace al empezar.",
        "body": f"""
<p>Es común que quien empieza a invertir dedique casi todo su tiempo a decidir "qué comprar" y muy poco a decidir "cómo voy a manejar el riesgo de esa decisión". Esta es, probablemente, la diferencia más grande entre un enfoque improvisado y uno con algo de disciplina.</p>

<h2>1. ¿Cuánto estoy dispuesto a perder en esta posición?</h2>
<p>No en abstracto ("no mucho"), sino en un número concreto, definido antes de comprar. Esto es lo que en la práctica sirve un stop-loss basado en volatilidad (como el que calcula el ATR): fija de antemano el punto en el que reconoces que la idea no funcionó, en vez de decidirlo en caliente cuando el precio ya está cayendo y las emociones entran en juego.</p>

<h2>2. ¿Qué porcentaje de mi capital total representa esta posición?</h2>
<p>Concentrar una parte muy grande del capital en una sola acción &mdash; sin importar qué tan convencido estés de la idea &mdash; multiplica el impacto de estar equivocado. Diversificar entre varias posiciones, sectores e incluso tipos de activos reduce el efecto de que una sola decisión mala arruine el resultado general.</p>

<h2>3. ¿Este riesgo es coherente con mi horizonte de tiempo?</h2>
<p>Una posición pensada para mantenerse años no debería reaccionar a la volatilidad de un solo día, y una posición de corto plazo no debería justificarse con argumentos de "la empresa es buena a largo plazo". Mezclar horizontes de tiempo es una fuente común de decisiones inconsistentes.</p>

<h2>Por qué esto va antes que el análisis técnico o fundamental</h2>
<p>Ningún indicador &mdash; ni el RSI, ni el score del scanner, ni la recomendación de un analista &mdash; elimina la incertidumbre. La gestión de riesgo no busca acertar siempre; busca que, cuando te equivoques (y en algún momento va a pasar), el costo sea manejable.</p>

{DISCLAIMER}
""",
        "title_en": "Basic risk management: the first thing to define before you buy",
        "excerpt_en": "Before asking yourself 'what to buy,' it's worth answering three risk-management questions almost nobody asks when starting out.",
        "body_en": f"""
<p>It's common for people starting to invest to spend almost all their time deciding "what to buy" and very little deciding "how am I going to manage the risk of that decision." This is probably the biggest difference between an improvised approach and one with some discipline.</p>

<h2>1. How much am I willing to lose on this position?</h2>
<p>Not in the abstract ("not much"), but as a concrete number, defined before buying. This is, in practice, what a volatility-based stop-loss (like the one ATR calculates) does for you: it sets the point where you admit the idea didn't work ahead of time, instead of deciding it in the heat of the moment when the price is already falling and emotions kick in.</p>

<h2>2. What percentage of my total capital does this position represent?</h2>
<p>Concentrating too large a share of your capital in a single stock &mdash; no matter how convinced you are of the idea &mdash; multiplies the impact of being wrong. Diversifying across several positions, sectors, and even asset types reduces the effect of any single bad decision wrecking the overall outcome.</p>

<h2>3. Is this risk consistent with my time horizon?</h2>
<p>A position meant to be held for years shouldn't react to a single day's volatility, and a short-term position shouldn't be justified with "the company is good long-term" arguments. Mixing time horizons is a common source of inconsistent decisions.</p>

<h2>Why this comes before technical or fundamental analysis</h2>
<p>No indicator &mdash; not RSI, not the scanner's score, not an analyst's recommendation &mdash; eliminates uncertainty. Risk management isn't about always being right; it's about making sure that when you're wrong (and at some point you will be), the cost is manageable.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Velas japonesas: cómo leer un gráfico de precios paso a paso",
        "slug": "velas-japonesas-como-leer-grafico",
        "excerpt": "Cada vela en un gráfico cuenta una pequeña historia de la sesión: apertura, cierre, máximo y mínimo. Así se interpreta, sin necesidad de memorizar patrones complejos.",
        "body": f"""
<p>El gráfico de velas japonesas es el formato más usado en análisis técnico para representar el movimiento de precio de una acción a lo largo del tiempo. A diferencia de un simple gráfico de línea (que solo muestra el precio de cierre), cada vela contiene cuatro datos de un mismo periodo: apertura, cierre, máximo y mínimo.</p>

<h2>Anatomía de una vela</h2>
<p>El "cuerpo" de la vela representa la distancia entre el precio de apertura y el de cierre de ese periodo. Las líneas finas que sobresalen por arriba y por abajo (las "mechas" o "sombras") muestran el máximo y el mínimo alcanzados durante ese mismo periodo, aunque el precio no haya cerrado ahí.</p>

<h2>Por qué el color importa</h2>
<p>En DSMarketLearning, como en la mayoría de las plataformas, una vela verde significa que el precio cerró por encima de donde abrió en ese periodo (presión compradora neta); una vela roja significa que cerró por debajo de donde abrió (presión vendedora neta). Ver varias velas verdes seguidas con cuerpos grandes suele indicar impulso comprador sostenido; varias rojas seguidas, lo contrario.</p>

<h2>El periodo cambia la historia que cuenta cada vela</h2>
<p>Una vela diaria resume lo que pasó en un día completo de trading; una vela semanal resume una semana entera; una de 5 minutos resume solo esos 5 minutos. Por eso el scanner permite cambiar el periodo de la gráfica &mdash; de 1 minuto a mensual &mdash; según qué estés analizando: movimientos intradía muy específicos, o la tendencia de fondo de meses.</p>

<h2>Un punto de partida, no un lenguaje mágico</h2>
<p>Existen decenas de "patrones" de velas con nombres específicos (martillo, envolvente, doji, etc.) que muchos traders siguen. Son útiles como contexto adicional, pero ninguno predice el futuro con certeza &mdash; funcionan mejor combinados con otros indicadores (tendencia, volumen, RSI) que de forma aislada.</p>

{DISCLAIMER}
""",
        "title_en": "Japanese candlesticks: how to read a price chart step by step",
        "excerpt_en": "Each candle on a chart tells a small story of that session: open, close, high, and low. Here's how to interpret them, without memorizing complex patterns.",
        "body_en": f"""
<p>The Japanese candlestick chart is the most widely used format in technical analysis for representing a stock's price movement over time. Unlike a simple line chart (which only shows the closing price), each candle contains four data points for a single period: open, close, high, and low.</p>

<h2>Anatomy of a candle</h2>
<p>The candle's "body" represents the distance between that period's opening and closing price. The thin lines sticking out above and below (the "wicks" or "shadows") show the high and low reached during that same period, even if the price didn't close there.</p>

<h2>Why color matters</h2>
<p>On DSMarketLearning, as on most platforms, a green candle means the price closed above where it opened that period (net buying pressure); a red candle means it closed below where it opened (net selling pressure). Seeing several green candles in a row with large bodies usually indicates sustained buying momentum; several red ones in a row, the opposite.</p>

<h2>The period changes the story each candle tells</h2>
<p>A daily candle summarizes what happened over one full trading day; a weekly candle summarizes an entire week; a 5-minute candle summarizes just those 5 minutes. That's why the scanner lets you change the chart's period &mdash; from 1 minute to monthly &mdash; depending on what you're analyzing: very specific intraday moves, or the underlying trend over months.</p>

<h2>A starting point, not a magic language</h2>
<p>There are dozens of candle "patterns" with specific names (hammer, engulfing, doji, etc.) that many traders follow. They're useful as additional context, but none of them predicts the future with certainty &mdash; they work better combined with other indicators (trend, volume, RSI) than in isolation.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "NYSE vs. NASDAQ: diferencias que sí importan",
        "slug": "nyse-vs-nasdaq-diferencias",
        "excerpt": "Ambas son bolsas de Estados Unidos, pero no son intercambiables: difieren en cómo operan, qué tipo de empresas suelen listar, y eso se refleja en el filtro de bolsa del scanner.",
        "body": f"""
<p>NYSE (New York Stock Exchange) y NASDAQ son las dos bolsas de valores más grandes de Estados Unidos, y juntas cotizan la gran mayoría de las acciones que sigue el scanner de DSMarketLearning. Aunque para un inversionista individual comprar una acción en una u otra se siente igual, hay diferencias reales detrás.</p>

<h2>Cómo operan</h2>
<p>El NYSE tradicionalmente combina un sistema electrónico con "market makers" humanos (especialistas) que ayudan a gestionar la oferta y demanda de acciones específicas. NASDAQ, en cambio, es una bolsa completamente electrónica desde su creación, sin piso de operaciones físico, donde múltiples market makers compiten electrónicamente por cada acción.</p>

<h2>El tipo de empresas que suelen listar</h2>
<p>Como generalización útil (no una regla absoluta): NASDAQ tiene una concentración histórica mayor de empresas de tecnología y crecimiento &mdash; muchas de las grandes tecnológicas cotizan ahí. El NYSE tiende a tener una base más amplia de empresas industriales, financieras y de consumo tradicionales, junto con muchas tecnológicas también. Ninguna bolsa es "mejor"; simplemente reflejan historias e incentivos de listado distintos.</p>

<h2>NasdaqGS, NasdaqGM, NasdaqCM: los niveles dentro de NASDAQ</h2>
<p>NASDAQ tiene, a su vez, distintos niveles de listado según el tamaño y los requisitos financieros de la empresa: Global Select (el más exigente, para las empresas más grandes), Global Market, y Capital Market (para empresas más pequeñas). El filtro de bolsa del scanner agrupa estas tres variantes bajo "NASDAQ" para simplificar la búsqueda.</p>

<h2>Por qué esto es relevante al filtrar</h2>
<p>Más allá de la curiosidad, saber en qué bolsa cotiza una acción da una pista rápida sobre su perfil general (aunque siempre hay excepciones) y es útil como un criterio más al usar los filtros avanzados del scanner.</p>

{DISCLAIMER}
""",
        "title_en": "NYSE vs. NASDAQ: differences that actually matter",
        "excerpt_en": "Both are U.S. exchanges, but they're not interchangeable: they differ in how they operate and what kind of companies tend to list, and that's reflected in the scanner's exchange filter.",
        "body_en": f"""
<p>NYSE (New York Stock Exchange) and NASDAQ are the two largest stock exchanges in the United States, and together they list the vast majority of the stocks tracked by the DSMarketLearning scanner. Although buying a stock on one or the other feels the same for an individual investor, there are real differences behind the scenes.</p>

<h2>How they operate</h2>
<p>The NYSE traditionally combines an electronic system with human "market makers" (specialists) who help manage supply and demand for specific stocks. NASDAQ, by contrast, has been a fully electronic exchange since its founding, with no physical trading floor, where multiple market makers compete electronically for each stock.</p>

<h2>The type of companies that tend to list</h2>
<p>As a useful generalization (not an absolute rule): NASDAQ has historically had a higher concentration of technology and growth companies &mdash; many of the big tech names list there. The NYSE tends to have a broader base of traditional industrial, financial, and consumer companies, alongside plenty of tech names too. Neither exchange is "better"; they simply reflect different listing histories and incentives.</p>

<h2>NasdaqGS, NasdaqGM, NasdaqCM: the tiers within NASDAQ</h2>
<p>NASDAQ, in turn, has different listing tiers based on a company's size and financial requirements: Global Select (the most demanding, for the largest companies), Global Market, and Capital Market (for smaller companies). The scanner's exchange filter groups these three variants under "NASDAQ" to simplify the search.</p>

<h2>Why this matters when filtering</h2>
<p>Beyond curiosity, knowing which exchange a stock trades on gives a quick hint about its general profile (though there are always exceptions) and is useful as one more criterion when using the scanner's advanced filters.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "5 errores comunes de un inversionista principiante (y cómo evitarlos)",
        "slug": "5-errores-comunes-inversionista-principiante",
        "excerpt": "La mayoría de los errores al empezar a invertir no son de análisis, sino de proceso y disciplina. Repasamos los cinco más frecuentes.",
        "body": f"""
<p>Después de varios años siguiendo mercados, los errores que más se repiten entre quienes empiezan casi nunca son "no saber leer un gráfico" &mdash; son errores de proceso, disciplina y expectativas. Aquí van cinco de los más comunes.</p>

<h2>1. No definir el riesgo antes de comprar</h2>
<p>Comprar primero y decidir "hasta dónde aguantar la pérdida" después, en caliente, casi siempre lleva a decisiones peores que definirlo de antemano con algo como un stop-loss basado en volatilidad (ver nuestro artículo sobre <a href="/blog/atr-stop-loss-limitar-perdida/">ATR y stop-loss</a>).</p>

<h2>2. Concentrar demasiado capital en una sola idea</h2>
<p>Estar "muy convencido" de una acción no elimina el riesgo de estar equivocado. Ninguna combinación de indicadores técnicos o fundamentales garantiza un resultado; diversificar reduce el impacto de que una sola decisión salga mal.</p>

<h2>3. Perseguir una acción después de que ya subió mucho</h2>
<p>Ver que una acción subió 40% en un mes y comprar solo por miedo a quedarse fuera ("FOMO") es distinto a haber identificado la oportunidad con criterios claros desde antes. El mismo movimiento que emociona a último momento también puede estar mucho más cerca de agotarse.</p>

<h2>4. Ignorar el contexto del mercado en general</h2>
<p>Analizar una acción de forma aislada, sin mirar si el mercado en general está en tendencia alcista o bajista, lleva a subestimar el riesgo. Una acción con fundamentos sólidos puede caer igual si el mercado completo entra en corrección &mdash; por eso vale la pena revisar el contexto de los índices principales antes de tomar una decisión.</p>

<h2>5. Confundir información con una señal de compra</h2>
<p>Un RSI favorable, una recomendación de "compra" de analistas, o un score alto en el scanner son puntos de partida para investigar más, no un semáforo verde automático. Ninguna herramienta &mdash; incluida esta &mdash; reemplaza el análisis propio ni garantiza un resultado.</p>

{DISCLAIMER}
""",
        "title_en": "5 common beginner investor mistakes (and how to avoid them)",
        "excerpt_en": "Most mistakes when starting to invest aren't about analysis, but about process and discipline. We cover the five most frequent ones.",
        "body_en": f"""
<p>After several years following markets, the mistakes that repeat most often among beginners are almost never "not knowing how to read a chart" &mdash; they're mistakes of process, discipline, and expectations. Here are five of the most common ones.</p>

<h2>1. Not defining risk before buying</h2>
<p>Buying first and deciding "how much loss to tolerate" later, in the heat of the moment, almost always leads to worse decisions than defining it ahead of time with something like a volatility-based stop-loss (see our article on <a href="/blog/atr-stop-loss-limitar-perdida/">ATR and stop-loss</a>).</p>

<h2>2. Concentrating too much capital in a single idea</h2>
<p>Being "very convinced" about a stock doesn't eliminate the risk of being wrong. No combination of technical or fundamental indicators guarantees an outcome; diversifying reduces the impact of any single decision going badly.</p>

<h2>3. Chasing a stock after it's already risen a lot</h2>
<p>Seeing a stock rise 40% in a month and buying purely out of fear of missing out ("FOMO") is different from having identified the opportunity with clear criteria beforehand. The same move that excites you at the last minute may also be much closer to running out of steam.</p>

<h2>4. Ignoring the overall market context</h2>
<p>Analyzing a stock in isolation, without checking whether the overall market is in an uptrend or downtrend, leads to underestimating risk. A stock with solid fundamentals can still fall if the entire market enters a correction &mdash; that's why it's worth checking the context of the major indices before making a decision.</p>

<h2>5. Confusing information with a buy signal</h2>
<p>A favorable RSI, a "buy" recommendation from analysts, or a high score on the scanner are starting points for further research, not an automatic green light. No tool &mdash; including this one &mdash; replaces your own analysis or guarantees an outcome.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "IA en el trading: cómo potencia el análisis de mercado",
        "slug": "ia-en-el-trading-analisis-de-mercado",
        "excerpt": "Redes neuronales, ciclos de mercado y por qué la verdadera ventaja de la IA en el trading es la velocidad y precisión del análisis, no la adivinación.",
        "body": f"""
<p>La IA en el trading dejó de ser un concepto futurista: hoy es una herramienta activa detrás de cómo se analizan precios, indicadores técnicos y contexto económico a gran escala en los mercados financieros. Este artículo explica, en términos simples, qué hay realmente detrás de esa idea &mdash; y qué tan lejos llega.</p>

<img src="/static/img/blog/ia-analisis-mercado.svg" alt="Ilustración de una serie de precios con patrones cíclicos, analizada por una red de nodos que representa un modelo de inteligencia artificial" style="width:100%;height:auto;border-radius:8px;margin:1.5rem 0;">

<h2>Redes neuronales que aprenden de la historia</h2>
<p>Un modelo de machine learning &mdash; como el LightGBM que usa <a href="/prediccion/">DSprofeta</a> &mdash; no "adivina" hacia dónde va un precio: aprende relaciones estadísticas a partir de miles de ejemplos históricos, combinando precio, RSI, MACD, niveles de Fibonacci y calendario económico con lo que ocurrió después de cada combinación. Cuantos más ciclos de mercado observa un modelo durante su entrenamiento, más patrones recurrentes puede llegar a identificar entre esas variables.</p>

<h2>La historia no se repite, pero el mercado sí puede ser cíclico</h2>
<p>Una idea central del análisis técnico &mdash; resumida en la frase, atribuida a Mark Twain, "la historia no se repite, pero rima" &mdash; es que los mercados no van a replicar un ciclo pasado de forma exacta, pero sí tienden a mostrar comportamientos recurrentes: zonas de sobrecompra y sobreventa, tendencias que se agotan, reacciones parecidas cerca de ciertos niveles de precio. Un modelo entrenado con suficiente historia puede reconocer ese tipo de patrones de forma más sistemática que una revisión manual, gráfica por gráfica.</p>

<h2>La ventaja real: velocidad y precisión, no adivinación</h2>
<p>La contribución más concreta de la inteligencia artificial en este campo no es "predecir el futuro" &mdash; es procesar volúmenes de datos que serían poco prácticos de revisar a mano, en fracciones de segundo y con el mismo criterio cada vez. Eso es lo que la vuelve relevante como herramienta de apoyo para el análisis de mercado: más variables, revisadas más rápido, de forma consistente.</p>

<h2>Un ejemplo aplicado: DSprofeta</h2>
<p>En DSMarketLearning, <a href="/prediccion/">DSprofeta</a> aplica justamente este enfoque: un modelo entrenado con precio, RSI, MACD, Fibonacci y calendario económico genera una predicción de precio para NASDAQ&nbsp;100, Oro, EUR/USD y S&amp;P&nbsp;500, y cada predicción se guarda para compararse después contra lo que realmente ocurrió &mdash; construyendo con el tiempo un historial real de aciertos y errores, no una promesa abstracta.</p>

<h2>En video</h2>
<p>Un resumen rápido de esta misma idea, en video:</p>
<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@dsmarketlearning/video/7675176204151966994" data-video-id="7675176204151966994" style="max-width: 605px; min-width: 325px; margin: 1.5rem auto;">
  <section></section>
</blockquote>
<script async src="https://www.tiktok.com/embed.js"></script>

{DISCLAIMER}
""",
        "title_en": "AI in trading: how it powers market analysis",
        "excerpt_en": "Neural networks, market cycles, and why AI's real advantage in trading is analysis speed and precision, not fortune-telling.",
        "body_en": f"""
<p>AI in trading stopped being a futuristic concept a while ago: today it's an active tool behind how prices, technical indicators, and economic context get analyzed at scale in financial markets. This article explains, in simple terms, what's actually behind that idea &mdash; and how far it really goes.</p>

<img src="/static/img/blog/ia-analisis-mercado.svg" alt="Illustration of a price series with cyclical patterns, analyzed by a network of nodes representing an artificial intelligence model" style="width:100%;height:auto;border-radius:8px;margin:1.5rem 0;">

<h2>Neural networks that learn from history</h2>
<p>A machine learning model &mdash; like the LightGBM one <a href="/prediccion/">DSprophecy</a> uses &mdash; doesn't "guess" where a price is headed: it learns statistical relationships from thousands of historical examples, combining price, RSI, MACD, Fibonacci levels, and economic calendar data with what happened after each combination. The more market cycles a model observes during training, the more recurring patterns it can identify among those variables.</p>

<h2>History doesn't repeat, but markets can still be cyclical</h2>
<p>A core idea in technical analysis &mdash; summed up in the phrase, often attributed to Mark Twain, "history doesn't repeat itself, but it rhymes" &mdash; is that markets won't replay a past cycle exactly, but they do tend to show recurring behaviors: overbought and oversold zones, trends running out of steam, similar reactions near certain price levels. A model trained on enough history can recognize that kind of pattern more systematically than a manual, chart-by-chart review.</p>

<h2>The real advantage: speed and precision, not fortune-telling</h2>
<p>AI's most concrete contribution in this field isn't "predicting the future" &mdash; it's processing volumes of data that would be impractical to review by hand, in fractions of a second, with the same criteria every time. That's what makes it a relevant support tool for market analysis: more variables, reviewed faster, consistently.</p>

<h2>An applied example: DSprophecy</h2>
<p>At DSMarketLearning, <a href="/prediccion/">DSprophecy</a> applies exactly this approach: a model trained on price, RSI, MACD, Fibonacci, and the economic calendar generates a price forecast for NASDAQ&nbsp;100, Gold, EUR/USD, and S&amp;P&nbsp;500, and each prediction is saved to be compared later against what actually happened &mdash; building a real track record of hits and misses over time, not an abstract promise.</p>

<h2>On video</h2>
<p>A quick summary of this same idea, on video:</p>
<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@dsmarketlearning/video/7675176204151966994" data-video-id="7675176204151966994" style="max-width: 605px; min-width: 325px; margin: 1.5rem auto;">
  <section></section>
</blockquote>
<script async src="https://www.tiktok.com/embed.js"></script>

{DISCLAIMER_EN}
""",
    },
]


class Command(BaseCommand):
    help = "Publica (o actualiza) el catálogo de artículos educativos originales del blog."

    def handle(self, *args, **options):
        now = timezone.now()
        total = len(ARTICLES)
        saved = 0

        for i, article in enumerate(ARTICLES):
            try:
                post = Post.objects.get(slug=article["slug"])
                # Ya existe: actualizamos el texto pero NO la fecha de
                # publicación, para que corregir un artículo no reordene
                # todo el blog cada vez que se vuelva a correr el comando.
                post.title = article["title"]
                post.excerpt = article["excerpt"]
                post.body = article["body"].strip()
                post.title_en = article.get("title_en", "")
                post.excerpt_en = article.get("excerpt_en", "")
                post.body_en = article.get("body_en", "").strip()
                post.is_published = True
                post.save()
                action = "Actualizado"
            except Post.DoesNotExist:
                # Nuevo: se espacía en los últimos ~18 días, del más
                # antiguo al más reciente, para que el blog se vea como
                # lo que es — un catálogo publicado progresivamente, no
                # todo de golpe el mismo segundo.
                published_at = now - timedelta(days=(total - i))
                post = Post.objects.create(
                    slug=article["slug"],
                    title=article["title"],
                    excerpt=article["excerpt"],
                    body=article["body"].strip(),
                    title_en=article.get("title_en", ""),
                    excerpt_en=article.get("excerpt_en", ""),
                    body_en=article.get("body_en", "").strip(),
                    published_at=published_at,
                    is_published=True,
                )
                action = "Creado"

            self.stdout.write(f"{action}: {post.title}")
            saved += 1

        self.stdout.write(self.style.SUCCESS(f"Listo: {saved} artículos educativos publicados."))
