"""
scanner/scatter.py

Datos de la pantalla principal del Smart Scanner: los tres grupos de
acciones (penny < 2 USD, medium de 2 a 100 USD, monster = las mejores
del mercado) y las tres "lentes" de la gráfica de dispersión:

1. Momentum y fuerza relativa (swing/tendencia):
   X = fuerza relativa vs. S&P 500, Y = RSI(14).
2. Tendencia vs. riesgo (enfoque equilibrado):
   X = distancia a la media de 200 días, Y = Sharpe de ~6 meses.
3. Crecimiento vs. rentabilidad (largo plazo, fundamental):
   X = crecimiento estimado de EPS, Y = ROE.

El tamaño de cada burbuja es el volumen relativo (liquidez del día).
Todo sale de la última fila de ScanResult de cada grupo — no hay red en
cada visita: lo llena el scan diario (scan_universe). Las métricas que
Yahoo no trae para una acción (o que faltan en filas anteriores a estas
columnas) quedan en None y esa burbuja simplemente no aparece en la
lente que las necesita (ver static/js/scanner-scatter.js).
"""
from .models import ScanResult
from .services import build_all_group_summaries

# Orden de las pestañas: de menor a mayor precio/tamaño.
GROUP_ORDER = (ScanResult.GROUP_PENNY, ScanResult.GROUP_STANDARD, ScanResult.GROUP_MONSTER)
DEFAULT_GROUP = ScanResult.GROUP_MONSTER

MODE_IDS = ("momentum", "trend", "fundamental")
DEFAULT_MODE = "momentum"


def _num(value):
    return None if value is None else float(value)


def _point(result):
    """Un ScanResult como diccionario liviano para el navegador. Claves
    cortas a propósito: son ~60 puntos por carga, pero se repiten a diario."""
    return {
        "s": result.ticker.symbol,
        "n": result.ticker.name or "",
        "p": _num(result.price),
        "sc": _num(result.score),
        "rk": result.momentum_rank,
        "rs": _num(result.relative_strength),
        "rsi": _num(result.rsi),
        "d200": result.distance_ma200_pct,
        "sh": _num(result.sharpe_ratio),
        "eg": _num(result.eps_growth),
        "roe": _num(result.roe),
        "rv": _num(result.relative_volume),
        "r3": _num(result.return_3m),
        "up": result.target_upside_pct,
        "mc": result.market_cap_display or "",
    }


def build_scanner_groups(lang="es"):
    """{group: {"date", "results" (ScanResult, por ranking), "points" (dicts),
    "summary" (texto + agregados)}} para los tres grupos."""
    summaries = build_all_group_summaries(lang)
    groups = {}
    for group in GROUP_ORDER:
        latest = (
            ScanResult.objects.filter(group=group, ticker__is_active=True)
            .order_by("-date").values_list("date", flat=True).first()
        )
        results = []
        if latest:
            results = list(
                ScanResult.objects.select_related("ticker")
                .filter(group=group, date=latest, ticker__is_active=True)
                .order_by("momentum_rank", "-score")
            )
        groups[group] = {
            "date": latest,
            "results": results,
            "points": [_point(r) for r in results],
            "summary": summaries[group],
        }
    return groups


def _quads(T, mode):
    """Los cuatro cuadrantes de una lente: nombre corto + qué significa."""
    return {
        q: {
            "where": T[f"scan_quad_{q}"],
            "name": T[f"scan_{mode}_q_{q}_name"],
            "desc": T[f"scan_{mode}_q_{q}_desc"],
        }
        for q in ("tl", "tr", "bl", "br")
    }


# Ejemplo guiado de cada lente: empresas inventadas (nombre corto para el mini
# mapa, cuadrante donde caen y su posición en % dentro del mini mapa) y los
# términos que esa lente usa. Los textos salen de config/translations.py
# (scan_ex_<lente>_<n>_name/_text, scan_term_<id>_name/_def).
EXAMPLES = {
    "momentum": {
        "items": [("1", "Alfa", "tr", 78, 22), ("2", "Beta", "bl", 24, 76)],
        "terms": ("sp500", "rsi"),
    },
    "trend": {
        "items": [("1", "Gamma", "tr", 76, 22), ("2", "Delta", "bl", 24, 76)],
        "terms": ("ma200", "sharpe"),
    },
    "fundamental": {
        "items": [("1", "Alfa", "br", 78, 78), ("2", "Beta", "tl", 22, 22), ("3", "Gamma", "tr", 78, 22)],
        "terms": ("eps", "roe"),
    },
}
GLOSSARY_TERMS = ("share", "groups", "volrel", "quadrant", "score")


def _term(T, term_id):
    return {"name": T[f"scan_term_{term_id}_name"], "def": T[f"scan_term_{term_id}_def"]}


def _example(T, mode, x_label, y_label):
    cfg = EXAMPLES[mode]
    return {
        "title": T["scan_ex_title"],
        "intro": T[f"scan_ex_{mode}_intro"],
        "outro": T[f"scan_ex_{mode}_outro"],
        "caption": T["scan_ex_map_caption"].format(x=x_label, y=y_label),
        "items": [
            {
                "name": T[f"scan_ex_{mode}_{n}_name"], "text": T[f"scan_ex_{mode}_{n}_text"],
                "short": short, "quad": quad, "x": x, "y": y, "quad_name": T[f"scan_{mode}_q_{quad}_name"],
            }
            for n, short, quad, x, y in cfg["items"]
        ],
        "terms": [_term(T, t) for t in cfg["terms"]],
    }


def scanner_guide(T):
    """Guía para quien nunca vio un gráfico de este tipo: 5 pasos + glosario."""
    return {
        "steps": [{"title": T[f"scan_step{n}_title"], "text": T[f"scan_step{n}_text"]} for n in range(1, 6)],
        "glossary": [_term(T, t) for t in GLOSSARY_TERMS],
    }


def scatter_modes(T):
    """Configuración de las tres lentes (textos ya traducidos). `mid` es la
    línea de referencia de cada eje: el cuadrante superior derecho, más allá
    de ambas líneas, es el "cuadrante ganador"; los otros tres se leen como
    combinaciones de fuerte/débil en cada eje."""
    return [
        {
            "id": "momentum",
            "title": T["scan_mode_momentum"], "tag": T["scan_mode_momentum_tag"],
            "x": {"key": "rs", "label": T["scan_axis_rs"], "desc": T["scan_momentum_x_desc"], "mid": 0, "unit": " pp"},
            "y": {"key": "rsi", "label": T["scan_axis_rsi"], "desc": T["scan_momentum_y_desc"], "mid": 50, "unit": ""},
            "quads": _quads(T, "momentum"),
            "example": _example(T, "momentum", T["scan_axis_rs"], T["scan_axis_rsi"]),
        },
        {
            "id": "trend",
            "title": T["scan_mode_trend"], "tag": T["scan_mode_trend_tag"],
            "x": {"key": "d200", "label": T["scan_axis_d200"], "desc": T["scan_trend_x_desc"], "mid": 0, "unit": "%"},
            "y": {"key": "sh", "label": T["scan_axis_sharpe"], "desc": T["scan_trend_y_desc"], "mid": 0, "unit": ""},
            "quads": _quads(T, "trend"),
            "example": _example(T, "trend", T["scan_axis_d200"], T["scan_axis_sharpe"]),
        },
        {
            "id": "fundamental",
            "title": T["scan_mode_fundamental"], "tag": T["scan_mode_fundamental_tag"],
            "x": {"key": "eg", "label": T["scan_axis_eps"], "desc": T["scan_fundamental_x_desc"], "mid": 10, "unit": "%"},
            "y": {"key": "roe", "label": T["scan_axis_roe"], "desc": T["scan_fundamental_y_desc"], "mid": 15, "unit": "%"},
            "quads": _quads(T, "fundamental"),
            "example": _example(T, "fundamental", T["scan_axis_eps"], T["scan_axis_roe"]),
        },
    ]


def scatter_i18n(T):
    return {
        "price": T["scan_tip_price"], "score": T["scan_tip_score"], "rvol": T["scan_tip_rvol"],
        "offScale": T["scan_tip_off_scale"], "winner": T["scan_winner_label"],
        "candidates": T["scan_candidates"], "noCandidates": T["scan_no_candidates"],
        "missing": T["scan_missing_points"], "emptyGroup": T["scan_group_empty"],
        "noData": T["scan_mode_no_data"],
    }
