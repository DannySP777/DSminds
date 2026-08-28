"""
blog/services.py

Genera el resumen diario de mercado como un post del blog: combina los
resultados del scanner del día, el calendario económico de la semana y
los indicadores técnicos/fundamentales que ya se guardan en ScanResult
para armar una conclusión de mercado.

Es 100% determinístico (reglas simples sobre los mismos datos que ya se
muestran en el sitio) — no usa IA generativa ni inventa cifras. Genera
las dos versiones (es/en) en la misma corrida, sobre los mismos datos —
así el post nunca "cae" a español cuando el sitio está en inglés (ver
Post.get_title/get_excerpt/get_body: sin title_en/excerpt_en/body_en
poblados, el post en inglés mostraba el texto en español como
respaldo).
"""
from django.utils import timezone

from news.models import EconomicEvent
from scanner.models import ScanResult

MESES = {
    "es": ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "en": ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}
MESES_ABR = {
    "es": ["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    "en": ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}
DIAS_ABR = {
    "es": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"],  # weekday(): 0 = lunes
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}


def _fecha_larga(d, lang="es") -> str:
    if lang == "en":
        return f"{MESES[lang][d.month]} {d.day}, {d.year}"
    return f"{d.day:02d} de {MESES[lang][d.month]} de {d.year}"


def _fecha_hora_corta(dt, lang="es") -> str:
    return f"{DIAS_ABR[lang][dt.weekday()]} {dt.day:02d} {MESES_ABR[lang][dt.month]}, {dt:%H:%M}"


def _fecha_corta(dt, lang="es") -> str:
    return f"{dt.day:02d} {MESES_ABR[lang][dt.month]}"


# Auditoría AdSense (27-28 ago 2026): sin mencionar la fuente de datos
# por nombre, y sin el link a /noticias/ (esa página ya no existe — ver
# scanner/views.py). El resto del aviso se mantiene igual.
DISCLOSURE_HTML = {
    "es": """
<p class="disclaimer-note">
    Este resumen se genera automáticamente combinando los resultados del
    <a href="/">scanner diario</a>, el calendario económico e indicadores
    técnicos y fundamentales de mercado. Es contenido informativo y
    educativo &mdash; no es una recomendación de compra o venta, ni
    asesoría financiera, legal o fiscal personalizada. Invertir implica
    riesgo, incluida la posible pérdida del capital invertido, y el
    rendimiento pasado no garantiza resultados futuros. Los datos pueden
    estar incompletos, retrasados o contener errores. Antes de tomar
    cualquier decisión, consulta a un asesor de inversión registrado y
    autorizado en tu jurisdicción, y lee nuestro
    <a href="/disclaimer/">aviso legal completo</a>.
</p>
""",
    "en": """
<p class="disclaimer-note">
    This summary is generated automatically by combining the results of
    the <a href="/">daily scanner</a>, the economic calendar, and
    technical and fundamental market indicators. It's informational and
    educational content &mdash; not a buy or sell recommendation, nor
    personalized financial, legal, or tax advice. Investing carries
    risk, including possible loss of invested capital, and past
    performance does not guarantee future results. Data may be
    incomplete, delayed, or contain errors. Before making any decision,
    consult a registered and authorized investment advisor in your
    jurisdiction, and read our
    <a href="/disclaimer/">full disclaimer</a>.
</p>
""",
}


def build_daily_summary(target_date=None) -> dict | None:
    """
    `target_date=None` (el uso normal, desde el comando diario) toma el
    scan más reciente. Un `target_date` explícito permite regenerar el
    resumen de un día pasado — por ejemplo para poblar title_en/
    excerpt_en/body_en de un post que ya existe en español (ver
    backfill_daily_summaries_en.py), sin depender de que ese día siga
    siendo "el más reciente".
    """
    if target_date is not None:
        scan_date = target_date
    else:
        latest = ScanResult.objects.select_related("ticker").order_by("-date").first()
        if not latest:
            return None
        scan_date = latest.date

    results = list(
        ScanResult.objects.select_related("ticker").filter(date=scan_date).order_by("-score")
    )
    total = len(results)
    if not total:
        return None

    bullish = [r for r in results if r.above_ma200]
    outperformers = [r for r in results if r.relative_strength is not None and r.relative_strength > 0]
    rsi_values = [float(r.rsi) for r in results if r.rsi is not None]
    avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else None

    events = list(EconomicEvent.objects.order_by("event_time"))
    top_results = results[:5]

    data = {"slug": f"resumen-mercado-{scan_date.isoformat()}", "published_at": timezone.now()}

    for lang, key_suffix in (("es", ""), ("en", "_en")):
        conclusion = _build_conclusion(lang, total, bullish, outperformers, avg_rsi, events)
        body = _render_body(lang, scan_date, top_results, events, conclusion, total, bullish, outperformers, avg_rsi)
        excerpt = conclusion if len(conclusion) <= 280 else conclusion[:277].rsplit(" ", 1)[0] + "…"
        title = (
            f"Resumen de mercado — {_fecha_larga(scan_date, lang)}" if lang == "es"
            else f"Market summary — {_fecha_larga(scan_date, lang)}"
        )
        data[f"title{key_suffix}"] = title
        data[f"excerpt{key_suffix}"] = excerpt
        data[f"body{key_suffix}"] = body

    return data


def _build_conclusion(lang, total, bullish, outperformers, avg_rsi, events) -> str:
    bullish_pct = len(bullish) / total if total else 0
    parts = []

    if lang == "en":
        if bullish_pct >= 0.7:
            parts.append(
                f"Breadth is healthy: {len(bullish)} of {total} covered stocks are above their 200-day "
                "moving average, suggesting a mostly bullish underlying trend in this group."
            )
        elif bullish_pct <= 0.3:
            parts.append(
                f"Breadth is weak: only {len(bullish)} of {total} stocks are above their 200-day moving "
                "average, a note of caution on this group's underlying trend."
            )
        else:
            parts.append(
                f"The picture is mixed: {len(bullish)} of {total} stocks are above their 200-day average, "
                "with no clear dominant trend."
            )

        if avg_rsi is not None:
            if avg_rsi >= 65:
                parts.append(
                    f"The group's average RSI ({avg_rsi:.1f}) is in the high zone, close to overbought — "
                    "don't rule out short-term pullbacks."
                )
            elif avg_rsi <= 40:
                parts.append(
                    f"The group's average RSI ({avg_rsi:.1f}) is low, reflecting little buying momentum "
                    "right now."
                )
            else:
                parts.append(f"The group's average RSI ({avg_rsi:.1f}) is in a neutral zone.")

        parts.append(
            f"{len(outperformers)} of {total} stocks are beating the S&P 500 over the last ~3 months "
            "(positive relative strength); the rest are moving slower than the broader market."
        )

        high_impact = [e for e in events if e.impact == "high"]
        if high_impact:
            names = ", ".join(f"{e.title} ({_fecha_corta(e.event_time, lang)})" for e in high_impact[:3])
            parts.append(
                f"This week there are high-impact events on the economic calendar that could move the "
                f"market: {names}."
            )
        return " ".join(parts)

    # es (default)
    if bullish_pct >= 0.7:
        parts.append(
            f"La amplitud es saludable: {len(bullish)} de {total} acciones cubiertas están por encima de su "
            "media móvil de 200 días, lo que sugiere una tendencia de fondo mayormente alcista en este grupo."
        )
    elif bullish_pct <= 0.3:
        parts.append(
            f"La amplitud es débil: solo {len(bullish)} de {total} acciones están por encima de su media "
            "móvil de 200 días, señal de cautela sobre la tendencia de fondo de este grupo."
        )
    else:
        parts.append(
            f"El panorama es mixto: {len(bullish)} de {total} acciones están sobre su media de 200 días, "
            "sin una tendencia dominante clara."
        )

    if avg_rsi is not None:
        if avg_rsi >= 65:
            parts.append(
                f"El RSI promedio del grupo ({avg_rsi:.1f}) está en zona alta, cerca de sobrecompra — "
                "no descartes ver correcciones de corto plazo."
            )
        elif avg_rsi <= 40:
            parts.append(
                f"El RSI promedio del grupo ({avg_rsi:.1f}) es bajo, reflejando poco impulso comprador "
                "en este momento."
            )
        else:
            parts.append(f"El RSI promedio del grupo ({avg_rsi:.1f}) está en zona neutral.")

    parts.append(
        f"{len(outperformers)} de {total} acciones le están ganando al S&P 500 en los últimos ~3 meses "
        "(fuerza relativa positiva); el resto se está moviendo más despacio que el mercado en general."
    )

    high_impact = [e for e in events if e.impact == "high"]
    if high_impact:
        names = ", ".join(f"{e.title} ({_fecha_corta(e.event_time, lang)})" for e in high_impact[:3])
        parts.append(
            f"Esta semana hay eventos de alto impacto en el calendario económico que podrían mover el "
            f"mercado: {names}."
        )

    return " ".join(parts)


def _render_body(lang, scan_date, top_results, events, conclusion, total, bullish, outperformers, avg_rsi) -> str:
    trend_up = "&uarr; Bullish" if lang == "en" else "&uarr; Alcista"
    trend_down = "&darr; Bearish" if lang == "en" else "&darr; Bajista"

    rows = "".join(
        f"""<tr>
            <td><a href="/accion/{r.ticker.symbol}/">{r.ticker.symbol}</a></td>
            <td>${r.price}</td>
            <td><span class="score-badge {_score_class(r.score)}">{r.score}</span></td>
            <td><span class="trend-badge {'trend-badge--up' if r.above_ma200 else 'trend-badge--down'}">{trend_up if r.above_ma200 else trend_down}</span></td>
            <td>{r.rsi if r.rsi is not None else 'N/A' if lang == 'en' else 'N/D'}</td>
            <td>{f'{r.relative_strength}pp' if r.relative_strength is not None else ('N/A' if lang == 'en' else 'N/D')}</td>
            <td>{r.trailing_pe if r.trailing_pe is not None else ('N/A' if lang == 'en' else 'N/D')}</td>
        </tr>"""
        for r in top_results
    )

    no_events_text = (
        "No high/medium-impact events loaded for this week." if lang == "en"
        else "No hay eventos de impacto medio/alto cargados para esta semana."
    )
    forecast_word = "forecast" if lang == "en" else "pronóstico"
    event_items = "".join(
        f"<li><strong>{_fecha_hora_corta(e.event_time, lang)}</strong> &mdash; {e.title} {e.stars_display}"
        f"{f' ({forecast_word} {e.forecast})' if e.forecast else ''}</li>"
        for e in events
    ) or f"<li>{no_events_text}</li>"

    avg_rsi_display = f"{avg_rsi:.1f}" if avg_rsi is not None else ("N/A" if lang == "en" else "N/D")

    if lang == "en":
        return f"""<section class="daily-summary">
    <h2>Scanner summary &mdash; {scan_date:%m/%d/%Y}</h2>
    <p><strong>{total}</strong> stocks were reviewed. <strong>{len(bullish)}</strong> are in a bullish
    underlying trend (above their MA200), <strong>{len(outperformers)}</strong> are beating the S&amp;P 500
    over the last ~3 months, and the group's average RSI is <strong>{avg_rsi_display}</strong>.</p>

    <h3>Top 5 by score</h3>
    <div class="table-wrap">
        <table>
            <thead>
                <tr><th>Ticker</th><th>Price</th><th>Score</th><th>Trend</th><th>RSI</th><th>RS vs S&amp;P</th><th>P/E</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
</section>

<section class="daily-summary">
    <h2>This week's economic calendar</h2>
    <ul>{event_items}</ul>
</section>

<section class="daily-summary">
    <h2>Today's takeaway</h2>
    <p>{conclusion}</p>
</section>

<section class="daily-summary">
    <h2>Disclaimer</h2>
    {DISCLOSURE_HTML["en"]}
</section>"""

    return f"""<section class="daily-summary">
    <h2>Resumen del scanner &mdash; {scan_date:%d/%m/%Y}</h2>
    <p>Se revisaron <strong>{total}</strong> acciones. <strong>{len(bullish)}</strong> están en tendencia
    alcista de fondo (sobre su MA200), <strong>{len(outperformers)}</strong> le están ganando al S&amp;P 500
    en los últimos ~3 meses, y el RSI promedio del grupo es <strong>{avg_rsi_display}</strong>.</p>

    <h3>Top 5 por score</h3>
    <div class="table-wrap">
        <table>
            <thead>
                <tr><th>Ticker</th><th>Precio</th><th>Score</th><th>Tendencia</th><th>RSI</th><th>RS vs S&amp;P</th><th>P/E</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
</section>

<section class="daily-summary">
    <h2>Calendario económico de la semana</h2>
    <ul>{event_items}</ul>
</section>

<section class="daily-summary">
    <h2>Conclusión del día</h2>
    <p>{conclusion}</p>
</section>

<section class="daily-summary">
    <h2>Aviso legal</h2>
    {DISCLOSURE_HTML["es"]}
</section>"""


def _score_class(score) -> str:
    score = float(score)
    if score >= 70:
        return "score-badge--strong"
    if score >= 40:
        return "score-badge--moderate"
    return "score-badge--weak"
