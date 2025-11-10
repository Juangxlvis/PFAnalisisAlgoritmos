import os
import re
import string
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
from utils import leer_bibtex, normalize_data

#Configuración de las rutas
RUTA_BIB = os.path.join("data", "requerimiento1", "articulos_unificados.bib")
OUTPUT_DIR = os.path.join("data", "requerimiento3")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Palabras asociadas a las categorias
PALABRAS_CLAVE = [
    "generative models",
    "prompting",
    "machine learning",
    "multimodality",
    "fine-tuning",
    "training data",
    "algorithmic bias",
    "explainability",
    "transparency",
    "ethics",
    "privacy",
    "personalization",
    "human-ai interaction",
    "ai literacy",
    "co-creation"
]


#FUnciones auxiliares
def limpiar_texto(texto):
    """Limpieza básica del texto: minúsculas, sin signos ni números."""
    texto = texto.replace("-", " ")
    texto = texto.lower()
    texto = re.sub(r"http\S+|www\S+", "", texto)
    puntuacion_a_quitar = string.punctuation.replace("-", "")
    texto = texto.translate(str.maketrans("", "", puntuacion_a_quitar))
    texto = re.sub(r"\d+", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def leer_abstracts(file_path):
    """Lee los abstracts del archivo BibTeX."""
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encuentra el archivo: {file_path}")
        return []
    try:
        articulos = normalize_data(leer_bibtex(file_path))
        abstracts = [limpiar_texto(art['abstract']) for art in articulos if art.get('abstract')]
        return abstracts
    except Exception as e:
        print(f"[ERROR] Falló al leer los abstracts con utils: {e}")
        return []


#funcion para contar la frecuencia de las palabras clave
def contar_frecuencia_claves(abstracts):
    """Cuenta la frecuencia de aparición de las palabras asociadas."""
    conteo = Counter()
    claves_limpias = {original: limpiar_texto(original) for original in PALABRAS_CLAVE}
    for abs in abstracts:
        for clave_original, clave_limpia in claves_limpias.items():
            if clave_limpia in abs:
                conteo[clave_original] += abs.count(clave_limpia)
    return conteo


#Extracción automatica de palabras
def extraer_palabras_tfidf(abstracts, top_n=15):
    """Extrae las palabras más relevantes usando TF-IDF."""
    vectorizer = TfidfVectorizer(stop_words='english', max_features=2000)
    X = vectorizer.fit_transform(abstracts)
    tfidf_prom = X.mean(axis=0).A1
    vocabulario = vectorizer.get_feature_names_out()
    ranking = sorted(zip(vocabulario, tfidf_prom), key=lambda x: x[1], reverse=True)
    return ranking[:top_n]


#Función para guardar y mostrar los resultados
def mostrar_resultados(frecuencia, nuevas_palabras):

    print("\n=== FRECUENCIA DE PALABRAS CLAVE (Categoría: Generative AI in Education) ===")
    df_freq = pd.DataFrame(frecuencia.items(), columns=["Palabra", "Frecuencia"]).sort_values(by="Frecuencia", ascending=False)
    palabras_encontradas = set(df_freq["Palabra"])
    palabras_faltantes = [k for k in PALABRAS_CLAVE if k not in palabras_encontradas]
    if palabras_faltantes:
        df_faltantes = pd.DataFrame({"Palabra": palabras_faltantes, "Frecuencia": [0]*len(palabras_faltantes)})
        df_freq = pd.concat([df_freq, df_faltantes], ignore_index=True)
        
    df_freq.index = range(1, len(df_freq) + 1)
    print(df_freq.to_string())

    print("\n=== 15 NUEVAS PALABRAS RELEVANTES (TF-IDF) ===")
    df_tfidf = pd.DataFrame(nuevas_palabras, columns=["Palabra", "Peso TF-IDF"])
    df_tfidf.index = range(1, len(df_tfidf) + 1)
    print(df_tfidf)

    # Guardar en CSV
    df_freq.to_csv(os.path.join(OUTPUT_DIR, "frecuencia_palabras_clave.csv"), index=False)
    df_tfidf.to_csv(os.path.join(OUTPUT_DIR, "palabras_relevantes_tfidf.csv"), index=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_freq, x="Frecuencia", y="Palabra", hue="Palabra", palette="YlGnBu", dodge=False, legend=False)
    plt.title("Frecuencia de Palabras Clave - Generative AI in Education", fontsize=12)
    plt.xlabel("Frecuencia de aparición")
    plt.ylabel("Palabra clave")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "grafico_frecuencia_palabras.png"), dpi=300)
    plt.close()

    # ======= GRÁFICO 2: Palabras más relevantes por TF-IDF =======
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_tfidf, x="Palabra", y="Peso TF-IDF", hue="Palabra", palette="viridis", dodge=False, legend=False)
    plt.title("Top 15 Palabras Más Relevantes (TF-IDF)", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Palabra")
    plt.ylabel("Peso TF-IDF promedio")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "grafico_tfidf.png"), dpi=300)
    plt.close()

    print(f"\n[OK] Resultados guardados en '{OUTPUT_DIR}'")


def ejecutar_req3():
    print("[INFO] Ejecutando Requerimiento 3: Frecuencia de términos...")
    
    abstracts = leer_abstracts(RUTA_BIB)
    if not abstracts:
        print("[ERROR] No se encontraron abstracts válidos.")
        return

    # Frecuencia de palabras clave predefinidas
    frecuencia = contar_frecuencia_claves(abstracts)

    # Nuevas palabras relevantes con TF-IDF
    nuevas_palabras = extraer_palabras_tfidf(abstracts)

    # Mostrar y guardar
    mostrar_resultados(frecuencia, nuevas_palabras)
    print("\n[INFO] Requerimiento 3 completado exitosamente")


if __name__ == "__main__":
    ejecutar_req3()
