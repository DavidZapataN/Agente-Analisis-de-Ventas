import os, pandas as pd, plotly.express as px

def to_df(rows, cols): return pd.DataFrame(rows, columns=cols)

def render_table(rows, cols):
    df = to_df(rows, cols)
    return df.head(20).to_string(index=False)

def render_chart(rows, cols):
    df = to_df(rows, cols)
    # Heurística simple
    if "fecha" in df.columns and len(df.columns) >= 2:
        y = next((c for c in df.columns if c != "fecha"), df.columns[-1])
        fig = px.line(df, x="fecha", y=y, markers=True)
    else:
        y = next((c for c in df.columns if df[c].dtype != "object" and c != "id"), df.columns[-1])
        x = next((c for c in df.columns if c != y), df.columns[0])
        fig = px.bar(df, x=x, y=y)
    fig.show(); return "Gráfico mostrado."

def save_file(rows, cols, name="resultado", kind="csv"):
    os.makedirs("exports", exist_ok=True)
    df = to_df(rows, cols)
    path = f"exports/{name}.{'csv' if kind=='csv' else 'xlsx'}"
    (df.to_csv if kind=="csv" else df.to_excel)(path, index=False)
    return path
