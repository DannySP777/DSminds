"""
blog/services.py

Genera el resumen diario de mercado como un post del blog: combina los
resultados del scanner del día, el calendario económico de la semana y
los indicadores técnicos/fundamentales que ya se guardan en ScanResult
para armar una conclusión de mercado.

Es 100% determinístico (reglas simples sobre los mismos datos que ya se
muestran en el sitio) — no usa IA generativa ni inventa cifras.
"""
from django.utils import timezone

from news.models import EconomicEvent
from scanner.models import ScanResult

MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_ABR = ["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS_ABR = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]  # weekday(): 0 = lunes


def _fecha_larga_es(d) -> str:
    return f"{d.day:02d} de {MESES[d.month]} de {d.year}"


def _fecha_hora_corta_es(dt) -> str:
    return f"{DIAS_ABR[dt.weekday()]} {dt.day:02d} {MESES_ABR[dt.month]}, {dt:%H:%M}"


def _fecha_corta_es(dt) -> str:
    return f"{dt.day:02d} {MESES_ABR[dt.month]}"


DISCLOSURE_HTML = """
<p class="disclaimer-note">
    Este resumen se genera automáticamente combinando los resultados del
    <a href="/">scanner diario</a>, el <a href="/noticias/">calendario económico</a>
    e indicadores técnicos y fundamentales de Yahoo Finance. Es contenido
    informativo y educativo &mdash; no es una recomendación de compra o venta,
    ni asesoría financiera, legal o fiscal personalizada. Invertir implica
    riesgo, incluida la posible pérdida del capital invertido, y el
    rendimiento pasado no garantiza resultados futuros. Los datos pueden
    estar incompletos, retrasados o contener errores. Antes de tomar
    cualquier decisión, consulta a un asesor de inversión registrado y
    autorizado en tu jurisdicción, y lee nuestro
    <a href="/disclaimer/">aviso legal completo</a>.
</p>
"""


def build_daily_summary() -> dict | None:
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

    conclusion = _build_conclusion(total, bullish, outperformers, avg_rsi, events)
    body = _render_body(scan_date, results[:5], events, conclusion, total, bullish, outperformers, avg_rsi)
    excerpt = conclusion if len(conclusion) <= 280 else conclusion[:277].rsplit(" ", 1)[0] + "…"

    return {
        "title": f"Resumen de mercado — {_fecha_larga_es(scan_date)}",
        "slug": f"resumen-mercado-{scan_date.isoformat()}",
        "excerpt": excerpt,
        "body": body,
        "published_at": timezone.now(),
    }


def _build_conclusion(total, bullish, outperformers, avg_rsi, events) -> str:
    bullish_pct = len(bullish) / total if total else 0
    parts = []

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
        names = ", ".join(f"{e.title} ({_fecha_corta_es(e.event_time)})" for e in high_impact[:3])
        parts.append(
            f"Esta semana hay eventos de alto impacto en el calendario económico que podrían mover el "
            f"mercado: {names}."
        )

    return " ".join(parts)


def _render_body(scan_date, top_results, events, conclusion, total, bullish, outperformers, avg_rsi) -> str:
    rows = "".join(
        f"""<tr>
            <td><a href="/accion/{r.ticker.symbol}/">{r.ticker.symbol}</a></td>
            <td>${r.price}</td>
            <td><span class="score-badge {_score_class(r.score)}">{r.score}</span></td>
            <td><span class="trend-badge {'trend-badge--up' if r.above_ma200 else 'trend-badge--down'}">{'&uarr; Alcista' if r.above_ma200 else '&darr; Bajista'}</span></td>
            <td>{r.rsi if r.rsi is not None else 'N/D'}</td>
            <td>{f'{r.relative_strength}pp' if r.relative_strength is not None else 'N/D'}</td>
            <td>{r.trailing_pe if r.trailing_pe is not None else 'N/D'}</td>
        </tr>"""
        for r in top_results
    )

    event_items = "".join(
        f"<li><strong>{_fecha_hora_corta_es(e.event_time)}</strong> &mdash; {e.title} {e.stars_display}"
        f"{f' (pronóstico {e.forecast})' if e.forecast else ''}</li>"
        for e in events
    ) or "<li>No hay eventos de impacto medio/alto cargados para esta semana.</li>"

    avg_rsi_display = f"{avg_rsi:.1f}" if avg_rsi is not None else "N/D"

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
    {DISCLOSURE_HTML}
</section>"""


def _score_class(score) -> str:
    score = float(score)
    if score >= 70:
        return "score-badge--strong"
    if score >= 40:
        return "score-badge--moderate"
    return "score-badge--weak"
