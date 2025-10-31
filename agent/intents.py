def classify_intent(text: str):
    t = text.lower()
    out = {"format": "table", "chart": None, "file": None}
    if "gráfico" in t or "grafico" in t: out["format"] = "chart"
    if "csv" in t or "excel" in t or "archivo" in t:
        out["format"] = "file"; out["file"] = "csv" if "csv" in t else "xlsx"
    return out
