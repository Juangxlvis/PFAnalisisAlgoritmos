import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import unicodedata
from itertools import combinations

# ---------------- CONFIGURACIÓN ----------------
INPUT_DIR = os.path.join("data", "requerimiento2")
OUTPUT_DIR = os.path.join("data", "requerimiento2", "reportes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

METRICAS = [
    "Jaccard",
    "Coseno_TFIDF",
    "Levenshtein",
    "Damerau",
    "SBERT",
    "Word2Vec"
]

def generar_heatmap(ruta_csv, metrica):
    """Genera un heatmap a partir del CSV de similitud (con números en los títulos)."""
    df = pd.read_csv(ruta_csv, index_col=0)

    plt.figure(figsize=(10, 8))
    sns.heatmap(df, cmap="YlGnBu", annot=True, fmt=".2f", linewidths=0.3, cbar_kws={'label': 'Similitud'})
    plt.title(f"Matriz de Similitud ({metrica})", fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()

    ruta_img = os.path.join(OUTPUT_DIR, f"heatmap_{metrica}.png")
    plt.savefig(ruta_img, dpi=300)
    plt.close()
    return ruta_img



def obtener_top_similares(df, top_n=5):
    """Devuelve los pares de artículos más similares."""
    pares = []
    for i, j in combinations(df.columns, 2):
        valor = float(df.at[i, j]) if not pd.isna(df.at[i, j]) else 0
        pares.append((i, j, valor))
    top = sorted(pares, key=lambda x: x[2], reverse=True)[:top_n]
    return pd.DataFrame(top, columns=["Artículo 1", "Artículo 2", "Similitud"])


def limpiar_texto(texto):
        """Limpia y normaliza texto para evitar errores de codificación en PDF."""
        if not isinstance(texto, str):
            texto = str(texto)
        texto = texto.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Normalizar (quita tildes y caracteres Unicode no latinos)
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        return texto.strip()

def exportar_pdf(resultados):


    """Genera un PDF con matrices, heatmaps y top 5 relaciones claras y numeradas."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=9)

    

    for metrica, data in resultados.items():
        df = data["df"]
        ruta_img = data["img"]
        top = data["top"]

        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        titulo = limpiar_texto(f"Matriz de Similitud: {metrica}")
        pdf.cell(0, 10, titulo, ln=True, align="C")
        pdf.ln(5)

    
        df.index = [limpiar_texto(idx) for idx in df.index]
        df.columns = [limpiar_texto(col) for col in df.columns]



        # Heatmap
        if os.path.exists(ruta_img):
            pdf.image(ruta_img, x=10, y=None, w=190)
            pdf.ln(8)

        # Sección de relaciones más similares
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Top 5 Relaciones Más Similares:", ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", size=9)

        articulos_numerados = {limpiar_texto(t): f"[{i+1}] {limpiar_texto(t)}" for i, t in enumerate(df.index)}


        # Escribir las 5 relaciones en formato más claro
        for _, fila in top.iterrows():
            art1 = limpiar_texto(fila["Artículo 1"])
            art2 = limpiar_texto(fila["Artículo 2"])
            sim = f"{fila['Similitud']:.3f}"
            texto = f"{art1} vs {art2} - Similitud: {sim}\n"
            texto_seguro = texto.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 6, texto_seguro)
            pdf.ln(1)

    ruta_pdf = os.path.join("data/requerimiento2/reportes", "matrices_similitud.pdf")
    pdf.output(ruta_pdf)
    print(f"[OK] PDF generado en {ruta_pdf}")


def ejecutar_req2_viz():
    print("[INFO] Generando visualización consolidada de similitudes...")
    resultados = {}

    for metrica in METRICAS:
        ruta_csv = os.path.join(INPUT_DIR, f"similitud_{metrica}.csv")
        if os.path.exists(ruta_csv):
            print(f"[OK] Procesando {metrica}...")
            df = pd.read_csv(ruta_csv, index_col=0)
            img = generar_heatmap(ruta_csv, metrica)
            top = obtener_top_similares(df)
            resultados[metrica] = {"df": df, "img": img, "top": top}
        else:
            print(f"[WARN] No se encontró {ruta_csv}")

    exportar_pdf(resultados)
    print("\nRequerimiento 2 (visualización + ranking) completado exitosamente.")


if __name__ == "__main__":
    ejecutar_req2_viz()
