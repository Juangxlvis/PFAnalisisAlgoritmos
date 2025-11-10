import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from pybtex.database import parse_file
from collections import Counter
import requests
import time
from fpdf import FPDF
import plotly.express as px
from iso3166 import countries

#Configuración de rutas
RUTA_BIB = os.path.join("data", "requerimiento1", "articulos_unificados.bib")
OUTPUT_DIR = os.path.join("data", "requerimiento5")
os.makedirs(OUTPUT_DIR, exist_ok=True)

#Función aux
def leer_bibtex(archivo):
    try:
        bib_data = parse_file(archivo)
        articulos = []
        for entry in bib_data.entries.values():
            campos = entry.fields
            articulos.append({
                "title": campos.get("title", "").strip(),
                "year": campos.get("year", "").strip(),
                "doi": campos.get("doi", "").strip(),
                "author": " and ".join(str(p) for p in entry.persons.get("author", [])),
                "abstract": campos.get("abstract", "").strip(),
                "booktitle": campos.get("booktitle", "").strip(),  
                "journal": campos.get("journal", "").strip(),       
            })
        df = pd.DataFrame(articulos)

        # Fusión: preferir 'journal' si 'booktitle' está vacío
        df["fuente"] = df.apply(
            lambda r: r["booktitle"] if r["booktitle"] else r["journal"],
            axis=1
        )
        return df

    except Exception as e:
        print(f"[ERROR] No se pudo leer el BibTeX: {e}")
        return pd.DataFrame()



#FUNCIÓN PARA OBTENER PAÍS DEL PRIMER AUTOR (OpenAlex + ROR)
def obtener_pais_por_doi(doi, cache):
    
    """Obtiene el país del primer autor usando OpenAlex y ROR."""
    if not doi:
        return None
    
    if doi in cache:
        return cache[doi]

    try:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        doi = doi.replace("https://doi.org/", "").strip()
        for intento in range(3):
            try:
                r = requests.get(url, timeout=20)
                if r.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if intento == 2:
                    raise
                time.sleep(3)
        if r.status_code != 200:
            return None

        data = r.json()
        authorships = data.get("authorships", [])
        if not authorships:
            return None

        first_author = authorships[0]
        institutions = first_author.get("institutions", [])

        # Caso 1: OpenAlex ya trae el país
        if institutions:
            country = institutions[0].get("country_code")
            if country:
                try:
                    country_iso3 = countries.get(country.upper()).alpha3
                    cache[doi] = country_iso3
                    return country_iso3
                except Exception:
                    cache[doi] = country.upper()
                    return country.upper()
           
            ror_id = institutions[0].get("ror")
            if ror_id:
                ror_resp = requests.get(f"{ror_id}.json", timeout=10)
                if ror_resp.status_code == 200:
                    ror_data = ror_resp.json()
                    country = ror_data.get("country", {}).get("country_code")
                    if country:
                        return country.upper()
            cache[doi] = None
            return None

            

    except Exception as e:
        print(f"[WARN] No se pudo obtener país para DOI {doi}: {e}")
        cache[doi] = None
        return None


#FUNCIÓN PARA GENERAR EL MAPA DE CALOR
def generar_mapa_calor(df):
    """Genera un mapa mundial de calor con Plotly."""
    df_validos = df.dropna(subset=["pais"])
    if df_validos.empty:
        print("[WARN] No hay países válidos para graficar el mapa.")
        return None

    conteo = df_validos["pais"].value_counts().reset_index()
    conteo.columns = ["country", "publications"]

    # Intentar convertir a nombre completo
    def nombre_completo(iso):
        try:
            return countries.get(iso).name
        except Exception:
            return iso

    conteo["country_name"] = conteo["country"].apply(nombre_completo)

    fig = px.choropleth(
        conteo,
        locations="country",
        color="publications",
        hover_name="country_name",
        color_continuous_scale="Tealgrn",
        projection="natural earth",
        title="Mapa Mundial de Publicaciones por País del Primer Autor",
    )

    fig.update_layout(
    geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
    coloraxis_colorbar=dict(title="Cantidad de Publicaciones"),
    title=dict(x=0.5, xanchor='center', font=dict(size=16))
    )


    ruta_img = os.path.join(OUTPUT_DIR, "mapa_calor_paises.png")
    ruta_html = os.path.join(OUTPUT_DIR, "mapa_calor_paises.html")

    fig.write_image(ruta_img, scale=2)
    fig.write_html(ruta_html)
    print(f"[OK] Mapa mundial guardado en {ruta_img} y {ruta_html}")
    return ruta_img



#FUNCIÓN PARA GENERAR LA NUBE DE PALABRAS A PARTIR DE LOS ABSTRACTS
def generar_nube_palabras(df):
    texto_abstracts = " ".join(df["abstract"].dropna().tolist())
    texto_keywords = " ".join(df["keywords"].dropna().tolist()) if "keywords" in df.columns else ""
    texto_total = (texto_abstracts + " " + texto_keywords).strip()

    if not texto_total:
        print("[WARN] No hay texto válido para generar la nube de palabras.")
        return None

    wc = WordCloud(width=1000, height=600, background_color="white", colormap="viridis").generate(texto_total)
    plt.figure(figsize=(10, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Nube de Palabras (Abstracts + Keywords)", fontsize=14)
    ruta = os.path.join(OUTPUT_DIR, "nube_palabras.png")
    plt.tight_layout()
    plt.savefig(ruta, dpi=300)
    plt.close()
    print(f"[OK] Nube de palabras guardada en {ruta}")
    return ruta

#FUNCION PARA GENERAR UNA LINEA DE TIEMPO, TNIENDO EN CUENTA LAS PUBLICACIONES POR AÑO
def generar_linea_tiempo(df):
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    conteo = df["year"].value_counts().sort_index()
    plt.figure(figsize=(10, 5))
    plt.plot(conteo.index, conteo.values, marker="o", color="steelblue")
    plt.title("Línea Temporal de Publicaciones", fontsize=14)
    plt.xlabel("Año")
    plt.ylabel("Cantidad de Publicaciones")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "linea_tiempo.png")
    plt.savefig(ruta, dpi=300)
    plt.close()
    print(f"[OK] Línea temporal guardada en {ruta}")
    return ruta

#FUNCION PARA GENERAR UNA LINEA DE TIEMPO, TNIENDO EN CUENTA LAS PUBLICACIONES POR AÑO Y LAS FUENTES
def generar_linea_tiempo_fuente(df):
    """Genera línea temporal de publicaciones por año y fuente."""
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year", "fuente"])

    conteo = df.groupby(["year", "fuente"]).size().reset_index(name="publicaciones")

    plt.figure(figsize=(16, 7))
    sns.lineplot(data=conteo, x="year", y="publicaciones", hue="fuente", marker="o")
    plt.title("Línea Temporal de Publicaciones por Año y Fuente", fontsize=13)
    plt.xlabel("Año")
    plt.ylabel("Cantidad de Publicaciones")
    plt.legend(title="Revista / Conferencia", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    ruta = os.path.join(OUTPUT_DIR, "linea_tiempo_fuente.png")
    plt.savefig(ruta, dpi=300)
    plt.close()
    print(f"[OK] Línea temporal guardada en {ruta}")
    return ruta


def generar_linea_tiempo_revista(df):
    """Genera un heatmap de publicaciones por año y revista (limitado a 15 + Otros + Sin fuente)."""
    if "booktitle" not in df.columns:
        print("[WARN] No hay campo 'booktitle' (revista o conferencia).")
        return None, None

    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Normalizar nombres de fuente
    df["booktitle"] = df["booktitle"].fillna("Sin fuente").replace("", "Sin fuente")

    # Contar ocurrencias totales por revista
    conteo_total = df["booktitle"].value_counts()

    # Tomar las 15 principales y agrupar el resto
    top_15 = conteo_total.nlargest(15).index.tolist()
    df["fuente_limpia"] = df["booktitle"].apply(lambda x: x if x in top_15 else "Otros")

    # Asignar abreviaturas
    abreviaturas = {nombre: f"F{i+3}" for i, nombre in enumerate(sorted(top_15))}
    abreviaturas["Sin fuente"] = "F1"
    abreviaturas["Otros"] = "F2"

    # Crear columna abreviada
    df["abreviatura"] = df["fuente_limpia"].map(abreviaturas)

    # Generar tabla de conteos
    conteo = df.groupby(["year", "abreviatura"]).size().reset_index(name="publicaciones")
    pivot = conteo.pivot(index="year", columns="abreviatura", values="publicaciones").fillna(0)

    # === ORDENAR COLUMNAS (F1 y F2 primero) ===
    columnas_ordenadas = ["F1", "F2"] + sorted([c for c in pivot.columns if c not in ["F1", "F2"]])
    pivot = pivot[columnas_ordenadas]

    # === HEATMAP ===
    plt.figure(figsize=(18, 7))
    sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".0f", cbar_kws={"label": "Publicaciones"})
    plt.title("LMapa de calor de Publicaciones por Año y Revista", fontsize=14)
    plt.xlabel("Revista / Conferencia (abreviada)")
    plt.ylabel("Año")
    plt.tight_layout()

    ruta_img = os.path.join(OUTPUT_DIR, "linea_tiempo_revista.png")
    plt.savefig(ruta_img, dpi=300)
    plt.close()
    print(f"[OK] Línea temporal por revista guardada en {ruta_img}")

    # === LEYENDA TXT ===
    ruta_txt = os.path.join(OUTPUT_DIR, "leyenda_revistas.txt")
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write("LEYENDA DE ABREVIATURAS (Revistas y Conferencias)\n")
        f.write("=" * 60 + "\n\n")
        for nombre, abrev in sorted(abreviaturas.items(), key=lambda x: x[1]):
            f.write(f"{abrev:<5} -> {nombre}\n")

    print(f"[OK] Leyenda de abreviaturas guardada en {ruta_txt}")
    return ruta_img, ruta_txt


#FUNCIÓN PARA EXPORTAR TODO LO ANTERIOR A UN PDF
def exportar_pdf(rutas_imagenes, ruta_txt=None):
    """Genera un PDF con todas las visualizaciones e incluye la leyenda TXT al final."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Añadir imágenes
    for img in rutas_imagenes:
        if img and os.path.exists(img):
            pdf.add_page()
            pdf.image(img, x=10, y=30, w=180)

    # Si hay archivo de texto, añadirlo como nueva página al final
    if ruta_txt and os.path.exists(ruta_txt):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Leyenda de Abreviaturas", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Courier", size=10)
        with open(ruta_txt, "r", encoding="utf-8") as f:
            for linea in f:
                pdf.multi_cell(0, 6, linea.strip())

    ruta_pdf = os.path.join(OUTPUT_DIR, "visualizaciones_requerimiento5.pdf")
    pdf.output(ruta_pdf)
    print(f"[OK] PDF generado en {ruta_pdf}")


def ejecutar_req5():
    print("[INFO] Ejecutando Requerimiento 5 (Visualización y Exportación)...")

    df = leer_bibtex(RUTA_BIB)
    if df.empty:
        print("[ERROR] No se encontraron artículos.")
        return
    
    if "fuente" in df.columns:
        top_fuentes = df["fuente"].value_counts().nlargest(15).index
        df["fuente"] = df["fuente"].apply(lambda x: x if x in top_fuentes else "Otros")

    if "booktitle" in df.columns:
        top_books = df["booktitle"].value_counts().nlargest(15).index
        df["booktitle"] = df["booktitle"].apply(lambda x: x if x in top_books else "Otros")

    
    ruta_cache = os.path.join(OUTPUT_DIR, "cache_paises.csv")
    cache = {}

    if os.path.exists(ruta_cache):
        cache_df = pd.read_csv(ruta_cache)
        cache = dict(zip(cache_df["doi"], cache_df["pais"]))

    print("[INFO] Consultando países por DOI...")
    df["pais"] = df["doi"].apply(lambda d: obtener_pais_por_doi(d, cache))
    time.sleep(1)

    cache_df = pd.DataFrame(list(cache.items()), columns=["doi", "pais"])
    cache_df.to_csv(ruta_cache, index=False)
    print(f"[OK] Cache de países guardado en {ruta_cache}")

    print("\n[INFO] Generando visualizaciones...")
    mapa = generar_mapa_calor(df)
    nube = generar_nube_palabras(df)
    linea = generar_linea_tiempo(df)
    linea_fuente = generar_linea_tiempo_fuente(df)
    linea_revista, leyenda_txt = generar_linea_tiempo_revista(df)
    exportar_pdf([mapa, nube, linea, linea_fuente, linea_revista], leyenda_txt)

    print("\nRequerimiento 5 completado exitosamente.")
    print(f"[OK] Resultados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    ejecutar_req5()
