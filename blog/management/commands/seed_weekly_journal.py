"""
blog/management/commands/seed_weekly_journal.py

Serie semanal en primera persona: experiencia real del autor aprendiendo
a invertir y construyendo DSMarketLearning. Es contenido editorial distinto
del catálogo de referencia técnica (seed_educational_posts) — aquí se
comparte criterio y experiencia, no solo definiciones.

Para agregar la entrega de la semana siguiente, añade un nuevo dict al
final de JOURNAL_ENTRIES y vuelve a correr el comando: publica las
entradas nuevas (por slug) y actualiza el contenido de las que ya
existen, sin tocar su published_at original (para no reordenar el
blog).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post

DISCLAIMER = (
    '<p class="disclaimer-note">Este artículo comparte una experiencia y opinión personal, '
    'con fines educativos. No es asesoría de inversión ni una recomendación de compra o venta '
    'bajo ninguna circunstancia. Lee nuestro <a href="/disclaimer/">aviso legal</a> antes de '
    'tomar cualquier decisión financiera.</p>'
)
DISCLAIMER_EN = (
    '<p class="disclaimer-note">This article shares a personal experience and opinion, '
    'for educational purposes. It is not investment advice nor a recommendation to buy or sell '
    'under any circumstance. Read our <a href="/disclaimer/">disclaimer</a> before '
    'making any financial decision.</p>'
)

JOURNAL_ENTRIES = [
    {
        "title": "Diario del inversionista #1: por qué construí DSMarketLearning",
        "slug": "diario-inversionista-1-por-que-construi-dsmarketscan",
        "excerpt": "Sin duda las tecnologías digitales permiten que el acceso a la bolsa de valores sea masivo. En mi experiencia, la curva de aprendizaje fue dura, con muchas pérdidas al inicio — y esa es exactamente la razón por la que construí este sitio.",
        "body": f"""
<p>Empiezo esta serie semanal con algo que llevaba tiempo queriendo escribir: por qué existe DSMarketLearning y qué espero que aporte a quien lo lea.</p>

<h2>El acceso se volvió masivo</h2>
<p>Sin duda las tecnologías digitales permiten que el acceso a la bolsa de valores sea masivo, colocando al alcance de todos la posibilidad de aprender y generar ingresos en el tiempo. Hace no tantos años, invertir era, en la práctica, algo reservado a quien tuviera un bróker de confianza, capital considerable, o trabajara cerca del mundo financiero. Hoy cualquier persona con un teléfono puede abrir una cuenta, comprar una fracción de una acción y tener acceso a datos de mercado que antes solo veían los profesionales.</p>
<p>Eso es genuinamente positivo. Pero democratizar el <em>acceso</em> no es lo mismo que democratizar el <em>conocimiento</em> para usarlo bien &mdash; y ahí es donde quiero aportar algo.</p>

<h2>Mi curva de aprendizaje fue dura</h2>
<p>En mi experiencia, la curva de aprendizaje fue dura, con muchas pérdidas al inicio. Soy ingeniero informático, así que cuando empecé a interesarme en los mercados asumí, con algo de soberbia técnica, que entender los números sería suficiente. No lo fue. Tuve pérdidas reales por razones que, en retrospectiva, eran evitables: operar sin entender qué significaba realmente un indicador, comprar por impulso al ver que algo "ya estaba subiendo", no tener ni idea de cómo pensar el riesgo de una posición antes de abrirla. Nada de eso se resuelve con más pantallas o más datos; se resuelve entendiendo la mecánica de fondo antes de tomar una decisión.</p>

<h2>Por qué construí este sitio</h2>
<p>Con este sitio quiero ayudar a la comunidad, principalmente a los que recién ingresan en este mundo, a entender conceptos básicos y a leer indicadores. Para eso combiné mi trabajo como ingeniero con lo que aprendí siguiendo mercados, y tomé dos decisiones deliberadas:</p>
<ul>
<li><strong>Un scanner sencillo, sin tanto indicador complejo.</strong> Es fácil llenar un dashboard de decenas de indicadores exóticos que impresionan pero no se entienden. Preferí un conjunto acotado de señales &mdash; un puntaje (score), precio, P/E, PEG, capitalización de mercado, volumen y precio objetivo &mdash; que permita entender la mecánica de los mercados antes de tomar una decisión, en vez de una pared de números sin contexto.</li>
<li><strong>Contenido que explica el "por qué", no solo el "qué".</strong> De ahí este blog: artículos que no asumen que ya sabes qué es un PEG o un RSI, escritos para quien está empezando exactamente donde yo empecé.</li>
</ul>

<h2>Por qué vale la pena leer este sitio</h2>
<p>Si estás empezando, lo que vas a encontrar aquí es justo lo que a mí me hubiera ahorrado tiempo y pérdidas al inicio: explicaciones claras de cada indicador antes de que lo uses, un scanner que resume señales técnicas y fundamentales en un solo puntaje en vez de obligarte a interpretar una decena de números sueltos, y artículos pensados para construir criterio propio &mdash; no para decirte qué comprar. No vas a encontrar promesas de rentabilidad ni señales de "compra esto ya"; vas a encontrar las mismas herramientas y explicaciones que yo hubiera querido tener cuando empecé, para que entiendas la mecánica del mercado antes de arriesgar tu dinero.</p>

<h2>Lo que sí y lo que no es este sitio</h2>
<p>Quiero dejarlo en claro: este bloq es educativo y, bajo ninguna circunstancia, se puede tomar como una recomendación de inversión. Comparto lo que he aprendido y cómo interpreto ciertos indicadores, pero las decisiones de tu dinero son tuyas, con tu propio análisis y, en lo posible, el acompañamiento de un asesor financiero registrado. Mi objetivo es que entiendas la mecánica antes de decidir &mdash; no decidir por ti.</p>

<p>A partir de aquí, cada semana voy a compartir algo de esta experiencia: un concepto que me costó entender, un error que cometí, o cómo pienso una situación de mercado desde este lado del código. Gracias por leer hasta aquí.</p>

{DISCLAIMER}
""",
        "title_en": "Investor journal #1: why I built DSMarketLearning",
        "excerpt_en": "Digital technology has undoubtedly made access to the stock market massive. In my experience, the learning curve was hard, with plenty of losses at the start — and that's exactly why I built this site.",
        "body_en": f"""
<p>I'm starting this weekly series with something I'd been wanting to write for a while: why DSMarketLearning exists and what I hope it brings to whoever reads it.</p>

<h2>Access became massive</h2>
<p>Digital technology has undoubtedly made access to the stock market massive, putting the chance to learn and generate income over time within everyone's reach. Not that many years ago, investing was, in practice, something reserved for people with a trusted broker, significant capital, or a job close to the financial world. Today anyone with a phone can open an account, buy a fraction of a share, and access market data that only professionals used to see.</p>
<p>That's genuinely positive. But democratizing <em>access</em> isn't the same as democratizing the <em>knowledge</em> to use it well &mdash; and that's where I want to contribute something.</p>

<h2>My learning curve was hard</h2>
<p>In my experience, the learning curve was hard, with plenty of losses at the start. I'm a software engineer, so when I first got interested in markets I assumed, with a bit of technical arrogance, that understanding the numbers would be enough. It wasn't. I took real losses for reasons that, in hindsight, were avoidable: trading without really understanding what an indicator meant, buying on impulse when I saw something "already going up," having no idea how to think about a position's risk before opening it. None of that gets solved with more screens or more data; it gets solved by understanding the underlying mechanics before making a decision.</p>

<h2>Why I built this site</h2>
<p>With this site I want to help the community, mainly those who are just getting into this world, understand basic concepts and read indicators. To do that I combined my work as an engineer with what I learned following markets, and made two deliberate decisions:</p>
<ul>
<li><strong>A simple scanner, without too many complex indicators.</strong> It's easy to fill a dashboard with dozens of exotic indicators that impress but aren't understood. I preferred a limited set of signals &mdash; a score, price, P/E, PEG, market cap, volume, and target price &mdash; that lets you understand the mechanics of the markets before making a decision, instead of a wall of numbers without context.</li>
<li><strong>Content that explains the "why," not just the "what."</strong> Hence this blog: articles that don't assume you already know what a PEG or an RSI is, written for someone starting exactly where I started.</li>
</ul>

<h2>Why it's worth reading this site</h2>
<p>If you're just starting out, what you'll find here is exactly what would have saved me time and losses at the beginning: clear explanations of each indicator before you use it, a scanner that summarizes technical and fundamental signals into a single score instead of forcing you to interpret a dozen loose numbers, and articles designed to build your own judgment &mdash; not to tell you what to buy. You won't find promises of returns or "buy this now" signals; you'll find the same tools and explanations I wish I'd had when I started, so you understand the market's mechanics before risking your money.</p>

<h2>What this site is and isn't</h2>
<p>I want to be clear about this: this blog is educational and, under no circumstances, should be taken as investment advice. I share what I've learned and how I interpret certain indicators, but decisions about your money are yours, based on your own analysis and, where possible, the guidance of a registered financial advisor. My goal is for you to understand the mechanics before deciding &mdash; not to decide for you.</p>

<p>From here on, every week I'll share a bit of this experience: a concept that was hard for me to grasp, a mistake I made, or how I think about a market situation from this side of the code. Thanks for reading this far.</p>

{DISCLAIMER_EN}
""",
    },
    {
        "title": "Diario del inversionista #2: qué hay detrás de la recuperación del Nasdaq y de SpaceX",
        "slug": "diario-inversionista-2-recuperacion-nasdaq-spacex",
        "excerpt": "La recuperación reciente del Nasdaq y de SpaceX no es una sola historia, sino dos: alivio macroeconómico en el mercado en general, y una acción digiriendo su propia volatilidad post-IPO sobre confianza a largo plazo.",
        "body": f"""
<p>Retomo la serie "Diario del inversionista" para comentar algo que seguramente ya viste si sigues el scanner esta semana: tanto el Nasdaq como SpaceX vienen recuperando terreno, pero por razones bastante distintas entre sí. Vale la pena separarlas, porque mezclarlas lleva a sacar conclusiones equivocadas sobre cualquiera de las dos.</p>

<h2>El Nasdaq: alivio macro más impulso</h2>
<p>La recuperación reciente del Nasdaq se explica por una mezcla de alivio económico y puro impulso de mercado. Por un lado, la inflación por fin dio tregua y los rendimientos de los bonos se calmaron, lo que le devolvió aire a las tecnológicas: cuando los rendimientos de los bonos bajan, el "costo de oportunidad" de tener acciones de crecimiento (que valen más por sus utilidades futuras que por las de hoy) baja también, y eso vuelve a atraer compras fuertes hacia el sector tech. Por otro lado, una vez que el índice empieza a subir, entra en juego el impulso puro: más compradores entran simplemente porque el precio ya está subiendo, no necesariamente porque hayan recalculado el valor de cada empresa una por una.</p>
<p>Es una distinción que vale la pena tener presente: parte de este movimiento tiene una base macroeconómica real (tasas, inflación), y parte es momentum de mercado, que puede revertirse tan rápido como apareció si el dato de inflación del próximo mes decepciona.</p>

<h2>SpaceX: digerir la volatilidad post-IPO</h2>
<p>Con SpaceX la historia es distinta: acá la cosa va más por digerir la volatilidad después de su salida a bolsa. El precio logró superar su valor de IPO inicial, y detrás de eso hay confianza del mercado en lo que viene con Starlink y Starship a largo plazo &mdash; son las dos apuestas que sostienen buena parte de la narrativa de crecimiento de la empresa hacia adelante.</p>
<p>Vale la pena recordar algo básico pero que se olvida rápido: es normal que una acción recién salida a bolsa tenga varias semanas (o meses) de volatilidad mientras el mercado "encuentra" el precio correcto, sin el histórico de cotización que sí tienen empresas con años en bolsa. Que el precio haya recuperado su nivel de IPO no es, por sí solo, una señal de que la volatilidad terminó &mdash; es un punto de referencia psicológico más que técnico.</p>

<h2>Por qué separo estas dos historias</h2>
<p>Comparto esto tal cual lo pienso porque es exactamente el tipo de distinción que trato de explicar en este sitio: un índice completo (Nasdaq) se mueve por fuerzas macro y de flujo de dinero agregado, mientras que una acción individual recién listada (SpaceX) se mueve por su propia narrativa y por la mecánica específica de una salida a bolsa. Tratar ambos movimientos como "el mercado subiendo" sin más lleva a conclusiones apresuradas &mdash; ni el Nasdaq sube por Starlink, ni SpaceX sube por el CPI.</p>

{DISCLAIMER}
""",
        "title_en": "Investor journal #2: what's behind the Nasdaq and SpaceX recovery",
        "excerpt_en": "The recent recovery in the Nasdaq and in SpaceX isn't one story, it's two: macroeconomic relief across the broader market, and a stock digesting its own post-IPO volatility on long-term confidence.",
        "body_en": f"""
<p>I'm picking the "Investor journal" series back up to talk about something you've probably already noticed if you've been following the scanner this week: both the Nasdaq and SpaceX have been recovering ground, but for fairly different reasons. It's worth separating them, because mixing them together leads to the wrong conclusions about either one.</p>

<h2>The Nasdaq: macro relief plus momentum</h2>
<p>The Nasdaq's recent recovery comes down to a mix of economic relief and pure market momentum. On one hand, inflation finally eased and bond yields calmed down, which gave tech stocks some breathing room: when bond yields fall, the "opportunity cost" of holding growth stocks (worth more for their future earnings than today's) falls too, and that pulls strong buying back into the tech sector. On the other hand, once the index starts climbing, pure momentum kicks in: more buyers step in simply because the price is already rising, not necessarily because they've re-priced every company one by one.</p>
<p>It's a distinction worth keeping in mind: part of this move has a real macroeconomic basis (rates, inflation), and part of it is market momentum, which can reverse as fast as it showed up if next month's inflation print disappoints.</p>

<h2>SpaceX: digesting post-IPO volatility</h2>
<p>SpaceX's story is different: this one is more about digesting volatility after its stock market debut. The price managed to climb back above its initial IPO value, and behind that is market confidence in what's coming with Starlink and Starship over the long run &mdash; the two bets that carry a big part of the company's forward growth narrative.</p>
<p>It's worth remembering something basic that's easy to forget: it's normal for a newly public stock to go through weeks (or months) of volatility while the market "finds" the right price, without the trading history that companies with years on the exchange already have. The price recovering its IPO level isn't, on its own, a sign the volatility is over &mdash; it's more of a psychological reference point than a technical one.</p>

<h2>Why I'm separating these two stories</h2>
<p>I'm sharing this exactly as I think about it because it's exactly the kind of distinction I try to explain on this site: a whole index (the Nasdaq) moves on macro forces and aggregate money flows, while a newly listed individual stock (SpaceX) moves on its own narrative and the specific mechanics of an IPO. Treating both moves as just "the market going up" leads to hasty conclusions &mdash; the Nasdaq isn't rallying because of Starlink, and SpaceX isn't rallying because of CPI.</p>

{DISCLAIMER_EN}
""",
    },
]


class Command(BaseCommand):
    help = "Publica entregas nuevas del diario semanal y actualiza el contenido de las existentes."

    def handle(self, *args, **options):
        now = timezone.now()
        created_count = 0
        updated_count = 0

        for entry in JOURNAL_ENTRIES:
            try:
                post = Post.objects.get(slug=entry["slug"])
                post.title = entry["title"]
                post.excerpt = entry["excerpt"]
                post.body = entry["body"].strip()
                post.title_en = entry.get("title_en", "")
                post.excerpt_en = entry.get("excerpt_en", "")
                post.body_en = entry.get("body_en", "").strip()
                post.is_published = True
                post.save()
                self.stdout.write(f"Actualizado: {entry['title']}")
                updated_count += 1
            except Post.DoesNotExist:
                Post.objects.create(
                    slug=entry["slug"],
                    title=entry["title"],
                    excerpt=entry["excerpt"],
                    body=entry["body"].strip(),
                    title_en=entry.get("title_en", ""),
                    excerpt_en=entry.get("excerpt_en", ""),
                    body_en=entry.get("body_en", "").strip(),
                    published_at=now,
                    is_published=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Publicado: {entry['title']}"))
                created_count += 1

        self.stdout.write(f"Listo: {created_count} nuevas, {updated_count} actualizadas.")
