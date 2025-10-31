import os
import re
import string
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

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
    texto = texto.lower()
    texto = re.sub(r"http\S+|www\S+", "", texto)
    texto = texto.translate(str.maketrans("", "", string.punctuation))
    texto = re.sub(r"\d+", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def leer_abstracts(file_path):
    """Lee los abstracts del archivo BibTeX."""
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encuentra el archivo: {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        contenido = f.read()
    abstracts = re.findall(r"abstract\s*=\s*[{](.*?)[}]", contenido, re.DOTALL)
    abstracts = [limpiar_texto(a) for a in abstracts]
    return abstracts


#funcion para contar la frecuencia de las palabras clave
def contar_frecuencia_claves(abstracts):
    """Cuenta la frecuencia de aparición de las palabras asociadas."""
    conteo = Counter()
    for abs in abstracts:
        for clave in PALABRAS_CLAVE:
            if clave in abs:
                conteo[clave] += abs.count(clave)
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
    print(df_freq)

    print("\n=== 15 NUEVAS PALABRAS RELEVANTES (TF-IDF) ===")
    df_tfidf = pd.DataFrame(nuevas_palabras, columns=["Palabra", "Peso TF-IDF"])
    print(df_tfidf)

    # Guardar en CSV
    df_freq.to_csv(os.path.join(OUTPUT_DIR, "frecuencia_palabras_clave.csv"), index=False)
    df_tfidf.to_csv(os.path.join(OUTPUT_DIR, "palabras_relevantes_tfidf.csv"), index=False)

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


# ---------------------------------------------
# EJECUCIÓN DIRECTA (debug)
# ---------------------------------------------
if __name__ == "__main__":
    ejecutar_req3()
