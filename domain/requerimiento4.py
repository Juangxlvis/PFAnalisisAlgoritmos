import os
import re
import string
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import pdist, squareform

#Configuración de rutas
RUTA_BIB = os.path.join("data", "requerimiento1", "articulos_unificados.bib")
OUTPUT_DIR = os.path.join("data", "requerimiento4")
os.makedirs(OUTPUT_DIR, exist_ok=True)


#Funciones auxiliares
def limpiar_texto(texto):
    """Normaliza texto eliminando signos, números y espacios extra."""
    texto = texto.lower()
    texto = re.sub(r"http\S+|www\S+", "", texto)
    texto = texto.translate(str.maketrans("", "", string.punctuation))
    texto = re.sub(r"\d+", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def leer_abstracts(file_path):
    """Lee y limpia los abstracts desde un archivo .bib."""
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encuentra el archivo: {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        contenido = f.read()
    abstracts = re.findall(r"abstract\s*=\s*[{](.*?)[}]", contenido, re.DOTALL)
    abstracts = [limpiar_texto(a) for a in abstracts if a.strip()]
    return abstracts


# TF-IDF + PCA + MATRIZ DE DISTANCIAS
def calcular_distancias_con_pca(abstracts, n_componentes=50):
    """Genera TF-IDF, reduce dimensionalidad con PCA y calcula matriz de distancias."""
    print(f"[INFO] Vectorizando {len(abstracts)} abstracts con TF-IDF...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf = vectorizer.fit_transform(abstracts).toarray()

    print(f"[INFO] Reducción de dimensionalidad a {n_componentes} componentes con PCA...")
    pca = PCA(n_components=min(n_componentes, tfidf.shape[1]))
    reducidos = pca.fit_transform(tfidf)

    # Cálculo de distancia basada en coseno
    dist = 1 - np.dot(reducidos, reducidos.T) / (
        np.linalg.norm(reducidos, axis=1)[:, None] * np.linalg.norm(reducidos, axis=1)
    )

    return dist


# Función para graficar el dendograma
def graficar_dendrograma(distancias, metodo, nombres=None, max_muestras=80):
    """Genera un dendrograma legible incluso con miles de abstracts."""
    print(f"[INFO] Generando dendrograma con método: {metodo}")

    # Si hay muchos abstracts, tomamos una muestra representativa para visualizar
    if distancias.shape[0] > max_muestras:
        print(f"[WARN] Hay {distancias.shape[0]} abstracts. Mostrando solo los primeros {max_muestras} para visualización.")
        distancias = distancias[:max_muestras, :max_muestras]
        nombres = nombres[:max_muestras] if nombres else [f"Art{i+1}" for i in range(max_muestras)]

    condensed_dist = squareform(distancias, checks=False)
    linkage_matrix = linkage(condensed_dist, method=metodo)

    plt.figure(figsize=(12, 6))
    dendrogram(linkage_matrix, labels=nombres, leaf_rotation=90, leaf_font_size=8, color_threshold=0.7)
    plt.title(f"Dendrograma de Clustering Jerárquico ({metodo.capitalize()} linkage, PCA)")
    plt.xlabel("Abstracts agrupados (muestra)")
    plt.ylabel("Distancia")
    plt.tight_layout()

    output_path = os.path.join(OUTPUT_DIR, f"dendrograma_{metodo}_pca.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[OK] Dendrograma guardado en: {output_path}")
    

def ejecutar_req4():
    print("[INFO] Ejecutando Requerimiento 4 (Clustering Jerárquico con PCA)...")

    abstracts = leer_abstracts(RUTA_BIB)
    if not abstracts:
        print("[ERROR] No se encontraron abstracts válidos.")
        return

    distancias = calcular_distancias_con_pca(abstracts, n_componentes=50)
    nombres = [f"Art{i+1}" for i in range(len(abstracts))]

    for metodo in ["single", "complete", "average"]:
        graficar_dendrograma(distancias, metodo, nombres)

    print("\n[INFO] Requerimiento 4 completado exitosamente")
    print(f"[OK] Dendrogramas generados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    ejecutar_req4()
