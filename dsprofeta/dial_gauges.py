"""
Velocímetro (rojo=baja, amarillo=indecisión, verde=alza) para la
DIRECCIÓN del precio en DSprofeta — construido con Plotly (go.Indicator +
una aguja dibujada a mano), que ya se carga en la página.

Es una cosa distinta de la confianza (qué tanto confiar en la
predicción): la confianza se muestra aparte, como un semáforo simple
(punto de color + texto, ver templates/dsprofeta/partials/confidence_panel.html)
y no como otro velocímetro — mezclar ambos en un solo medidor confundía
más de lo que aclaraba.
"""
import math

import plotly.graph_objects as go

from config.translations import get_translations

# Sincronizado con las variables --surface/--text/--bull/--warning/--bear
# de static/css/style.css; Python no lee custom properties CSS, así que
# estos valores se mantienen a mano.
BG = "#121218"
TEXT = "#f2f1ee"
GREEN = "#3fbf7f"
YELLOW = "#f2994a"
RED = "#e5484d"

_LEVEL_SCORE = {"bullish": 1, "bearish": -1, "neutral": 0}


# Pivote de la aguja en coordenadas "paper" (0-1 relativo a toda la figura):
# calibrado para height=130 / margin top=15,bottom=0 en modo "gauge+number"
# (Plotly reserva la franja de arriba para el número y deja el semicírculo
# pegado abajo). Si al verlo la aguja queda desalineada de la franja de
# color, es cuestión de ajustar estos 3 valores, no la lógica del ángulo.
NEEDLE_PIVOT = (0.5, 0.08)
NEEDLE_LENGTH = 0.42


def _add_needle(fig, value, min_value=0, max_value=100, color=TEXT):
    """
    Dibuja la aguja a mano con add_shape (línea + triángulo + pivote),
    todo en coordenadas "paper". add_annotation NO sirve para esto en
    esta versión de Plotly: sus ax/ay son offsets en píxeles relativos a
    x/y, no un segundo punto en coordenadas de página — axref="paper"
    directamente no es un valor válido ahí (sí lo es para shapes).
    """
    pivot_x, pivot_y = NEEDLE_PIVOT
    fraction = (value - min_value) / (max_value - min_value)
    angle = math.pi * (1 - fraction)  # 180° (izquierda) en min, 0° (derecha) en max
    tip_x = pivot_x + NEEDLE_LENGTH * math.cos(angle)
    tip_y = pivot_y + NEEDLE_LENGTH * math.sin(angle)

    fig.add_shape(
        type="line", xref="paper", yref="paper",
        x0=pivot_x, y0=pivot_y, x1=tip_x, y1=tip_y,
        line=dict(color=color, width=5),
    )

    # Punta triangular, para que se lea como flecha y no como un palito.
    head_len, head_width = 0.05, 0.03
    back_x, back_y = tip_x - head_len * math.cos(angle), tip_y - head_len * math.sin(angle)
    perp = angle + math.pi / 2
    left_x, left_y = back_x + head_width * math.cos(perp), back_y + head_width * math.sin(perp)
    right_x, right_y = back_x - head_width * math.cos(perp), back_y - head_width * math.sin(perp)
    fig.add_shape(
        type="path", xref="paper", yref="paper",
        path=f"M {tip_x},{tip_y} L {left_x},{left_y} L {right_x},{right_y} Z",
        fillcolor=color, line=dict(color=color, width=0),
    )

    fig.add_shape(
        type="circle", xref="paper", yref="paper",
        x0=pivot_x - 0.02, y0=pivot_y - 0.04, x1=pivot_x + 0.02, y1=pivot_y + 0.04,
        fillcolor=color, line=dict(color=color, width=0),
    )


def _render(value, zones, height=130, number_size=18):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"color": TEXT, "size": number_size}, "valueformat": ".0f"},
        gauge={
            "shape": "angular",
            "axis": {"range": [0, 100], "visible": False},
            # Sin relleno acumulado ni línea de threshold: la aguja de
            # verdad se dibuja aparte con _add_needle (flecha desde el
            # centro), más llamativa que una barra o una línea delgada.
            "bar": {"color": "rgba(0,0,0,0)"},
            "bgcolor": BG,
            "borderwidth": 0,
            "steps": [{"range": [start, end], "color": color} for color, start, end in zones],
        },
    ))
    _add_needle(fig, value)
    fig.update_layout(
        paper_bgcolor=BG,
        font=dict(color=TEXT),
        margin=dict(l=15, r=15, t=15, b=0),
        height=height,
        autosize=True,
    )
    # responsive=True es lo que hace que el SVG se ajuste al ancho real del
    # contenedor flex en vez de usar el ancho por defecto de Plotly (700px)
    # — sin esto, los medidores se dibujan más anchos que su casilla y se
    # ven superpuestos unos con otros.
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={"displayModeBar": False, "staticPlot": True, "responsive": True},
    )


def compute_overall_score(rsi_level, macd_level, predicted_close, current_close):
    """
    Combina RSI + MACD (ya clasificados como bullish/bearish/neutral en
    dsprofeta/commentary.py) con hacia dónde apunta la predicción más
    reciente respecto al último precio real, en un puntaje -1 (bajista) a
    +1 (alcista). Es un promedio simple, no un modelo aparte — solo
    resume en un número lo que ya calculó el resto del análisis.
    """
    scores = [_LEVEL_SCORE.get(rsi_level, 0), _LEVEL_SCORE.get(macd_level, 0)]
    if predicted_close is not None and current_close:
        diff_pct = (float(predicted_close) - float(current_close)) / float(current_close)
        if diff_pct > 0.0005:
            scores.append(1)
        elif diff_pct < -0.0005:
            scores.append(-1)
        else:
            scores.append(0)
    return sum(scores) / len(scores) if scores else 0.0


def direction_dial(score, lang="es"):
    """Velocímetro de DIRECCIÓN del precio (-1 bajista a +1 alcista)."""
    T = get_translations(lang)
    position = max(0, min(100, (score + 1) / 2 * 100))
    zones = [(RED, 0, 40), (YELLOW, 40, 60), (GREEN, 60, 100)]
    if score > 0.2:
        signal = T["dsp_signal_up"]
    elif score < -0.2:
        signal = T["dsp_signal_down"]
    else:
        signal = T["dsp_signal_neutral"]
    return {"html": _render(position, zones), "signal_label": signal}
