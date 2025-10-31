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
                "abstract": campos.get("abstract", "").strip()
            })
        return pd.DataFrame(articulos)
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
    print(conteo.head())

    fig = px.choropleth(
        conteo,
        locations="country",                
        color="publications",
        hover_name="country",
        color_continuous_scale="YlGnBu",
        projection="natural earth",
        title="Mapa Mundial de Publicaciones por País del Primer Autor"
    )

    ruta = os.path.join(OUTPUT_DIR, "mapa_calor_paises.png")
    fig.write_image(ruta, scale=2)
    print(f"[OK] Mapa mundial guardado en {ruta}")
    return ruta


#FUNCIÓN PARA GENERAR LA NUBE DE PALABRAS A PARTIR DE LOS ABSTRACTS
def generar_nube_palabras(df):
    texto = " ".join(df["abstract"].dropna().tolist())
    if not texto.strip():
        print("[WARN] No hay abstracts válidos para generar la nube de palabras.")
        return None

    wc = WordCloud(width=1000, height=600, background_color="white", colormap="viridis").generate(texto)
    plt.figure(figsize=(10, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Nube de Palabras (Abstracts)", fontsize=14)
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


#FUNCIÓN PARA EXPORTAR TODO LO ANTERIOR A UN PDF
def exportar_pdf(rutas_imagenes):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for img in rutas_imagenes:
        if img and os.path.exists(img):
            pdf.add_page()
            pdf.image(img, x=10, y=30, w=180)

    ruta_pdf = os.path.join(OUTPUT_DIR, "visualizaciones_requerimiento5.pdf")
    pdf.output(ruta_pdf)
    print(f"[OK] PDF generado en {ruta_pdf}")



def ejecutar_req5():
    print("[INFO] Ejecutando Requerimiento 5 (Visualización y Exportación)...")

    df = leer_bibtex(RUTA_BIB)
    if df.empty:
        print("[ERROR] No se encontraron artículos.")
        return
    
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

    exportar_pdf([mapa, nube, linea])

    print("\nRequerimiento 5 completado exitosamente.")
    print(f"[OK] Resultados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    ejecutar_req5()
