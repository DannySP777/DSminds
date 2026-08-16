"""
scanner/financials.py

Últimos 3 balances financieros públicos trimestrales por ticker
(estado de resultados y hoja de balance), vía yfinance.
"""
import yfinance as yf
from django.core.cache import cache

FINANCIALS_TTL = 21600  # 6h — los reportes trimestrales no cambian entre visitas del mismo día

INCOME_ROWS = ["Total Revenue", "Net Income"]
BALANCE_ROWS = ["Total Assets", "Total Liabilities Net Minority Interest", "Total Equity Gross Minority Interest"]

LABELS = {
    "es": {
        "Total Revenue": "Ingresos totales",
        "Net Income": "Utilidad neta",
        "Total Assets": "Activos totales",
        "Total Liabilities Net Minority Interest": "Pasivos totales",
        "Total Equity Gross Minority Interest": "Patrimonio",
    },
    "en": {
        "Total Revenue": "Total revenue",
        "Net Income": "Net income",
        "Total Assets": "Total assets",
        "Total Liabilities Net Minority Interest": "Total liabilities",
        "Total Equity Gross Minority Interest": "Equity",
    },
}


def get_financial_statements(symbol: str, lang: str = "es") -> dict:
    lang = lang if lang in LABELS else "es"
    cache_key = f"scanner:financials:{symbol}:{lang}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compute_financial_statements(symbol, lang)
    if result["has_data"]:
        cache.set(cache_key, result, FINANCIALS_TTL)
    return result


def _compute_financial_statements(symbol: str, lang: str) -> dict:
    labels = LABELS[lang]
    empty = {"has_data": False, "quarter_labels": [], "income": {}, "balance": {}}

    try:
        ticker_obj = yf.Ticker(symbol)
        income = ticker_obj.quarterly_income_stmt
        balance = ticker_obj.quarterly_balance_sheet
    except Exception:
        return empty

    if income is None or income.empty or balance is None or balance.empty:
        return empty

    # Últimos 3 trimestres, en orden cronológico (más viejo -> más reciente)
    # para que la gráfica se lea de izquierda a derecha como progresión en el tiempo.
    quarters = list(income.columns[:3])[::-1]
    quarter_labels = [q.strftime("%b %Y") for q in quarters]

    def extract(df, rows):
        series = {}
        for row in rows:
            if row not in df.index:
                continue
            values = []
            for q in quarters:
                if q not in df.columns:
                    values.append(None)
                    continue
                v = df.loc[row, q]
                values.append(float(v) if v == v else None)  # v == v descarta NaN
            series[labels[row]] = values
        return series

    return {
        "has_data": True,
        "quarter_labels": quarter_labels,
        "income": extract(income, INCOME_ROWS),
        "balance": extract(balance, BALANCE_ROWS),
    }
