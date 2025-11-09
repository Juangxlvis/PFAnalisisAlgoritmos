# domain/requerimiento2.py
import os
import numpy as np
import pandas as pd
from utils import leer_bibtex, normalize_data
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
from sentence_transformers import SentenceTransformer, util
from gensim.models import KeyedVectors

RUTA_UNIFICADOS = os.path.join('data', 'requerimiento1', 'articulos_unificados.bib')

modelo_sbert = SentenceTransformer('all-MiniLM-L6-v2')
modelo_word2vec = None

try:
    print("[INFO] Cargando modelo Word2Vec (puede tardar 1-2 minutos la primera vez)...")
    modelo_word2vec = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
    print("[OK] Modelo Word2Vec cargado correctamente.")
except Exception as e:
    print(f"[WARN] No se pudo cargar el modelo Word2Vec: {e}")

def mostrar_lista_articulos(articulos):
    """Muestra una lista numerada de artículos con título y año."""
    print("\nLISTA DE ARTÍCULOS DISPONIBLES")
    if not articulos:
        print("No se encontraron artículos.")
        return
    
    for i, articulo in enumerate(articulos):
        titulo = articulo.get('title', 'Sin Título')
        ano = articulo.get('year', 'Sin Año')
        print(f"[{i+1}] {titulo} ({ano})")

def seleccionar_articulos(articulos):
    
    articulos_seleccionados = []
    while True:
        seleccion = input("\nIngrese los números de los artículos a comparar, separados por comas (ej: 1, 5, 10): ")
        indices_seleccionados = []
        
        try:
            numeros_str = [s.strip() for s in seleccion.split(',') if s.strip() != '']
            for num_str in numeros_str:
                indice = int(num_str) - 1 
                if 0 <= indice < len(articulos):
                    indices_seleccionados.append(indice)
                else:
                    print(f"Número fuera de rango: {num_str}")
            
            if len(indices_seleccionados) < 2:
                print("Debe seleccionar al menos dos artículos para comparar.")
                continue
            
            articulos_seleccionados = [articulos[i] for i in indices_seleccionados]
            abstracts_seleccionados = [art.get('abstract', '') for art in articulos_seleccionados]
            
            print("\nArtículos seleccionados para comparar:")
            for i in indices_seleccionados:
                t = articulos[i].get('title', 'Sin Título')
                print(f"  [{i+1}] {t}")
                
            if any(not abstract for abstract in abstracts_seleccionados):
                print("\nAdvertencia: Uno o más de los artículos seleccionados no tienen abstract.")
            
            indices_reales_1based = [i+1 for i in indices_seleccionados]
            return abstracts_seleccionados, indices_reales_1based

        except ValueError:
            print("Error: Por favor, ingrese solo números separados por comas.")
        except Exception as e:
            print(f"Error inesperado: {e}")



#Funciones de simimlitud clásica

def similitud_jaccard(texto1, texto2):
    "Similitud basada en conjuntos de palabras"
    set1, set2 = set(texto1.lower().split()), set(texto2.lower().split())
    inter = len(set1 & set2)
    union = len(set1 | set2)
    return inter / union if union != 0 else 0

def similitud_coseno(texto1, texto2):
    """Similitud del coseno usando vectorización TF-IDF."""
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = vectorizer.fit_transform([texto1, texto2])
    return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]


def similitud_levenshtein(texto1, texto2):
    """Similitud normalizada usando distancia de edición de Levenshtein."""
    max_len = max(len(texto1), len(texto2))
    if max_len == 0:
        return 1.0
    distancia = levenshtein_distance(texto1, texto2)
    return 1 - distancia / max_len


def similitud_damerau(texto1, texto2):
    """Similitud basada en secuencia (considera transposiciones)."""
    matcher = SequenceMatcher(None, texto1, texto2)
    return matcher.ratio()

#Funciondes de similitud basadas en IA

def similitud_sbert(texto1, texto2):
    """Similitud usando Sentence-BERT (representaciones semánticas)."""
    emb1 = modelo_sbert.encode(texto1, convert_to_tensor=True)
    emb2 = modelo_sbert.encode(texto2, convert_to_tensor=True)
    return float(util.cos_sim(emb1, emb2)[0][0])


def similitud_word2vec(texto1, texto2):
    """Similitud promedio con Word2Vec (usa el modelo cargado globalmente)."""
    if modelo_word2vec is None:
        return similitud_coseno(texto1, texto2)
    
    def vector_promedio(texto):
        palabras = [w for w in texto.lower().split() if w in modelo_word2vec]
        if not palabras:
            return np.zeros(modelo_word2vec.vector_size)
        return np.mean([modelo_word2vec[w] for w in palabras], axis=0)
    
    vec1, vec2 = vector_promedio(texto1), vector_promedio(texto2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))



def ejecutar_req2():
    
    if not os.path.exists(RUTA_UNIFICADOS):
        print(f"Error: No se encuentra el archivo '{RUTA_UNIFICADOS}'.")
        print("   Por favor, ejecute la Opción 1 del menú principal primero.")
        return

    # 1. Cargar los artículos unificados
    print(f"[INFO] Cargando artículos desde '{RUTA_UNIFICADOS}'...")
    articulos = normalize_data(leer_bibtex(RUTA_UNIFICADOS))
    
    if not articulos:
        print("El archivo de artículos unificados está vacío.")
        return

    # 2. Mostrar la lista para que el usuario elija
    mostrar_lista_articulos(articulos)
    
    # 3. Obtener los abstracts seleccionados
    abstracts, indices_reales = seleccionar_articulos(articulos)
    
    if not abstracts:
        print("No se pudieron obtener los abstracts para la comparación.")
        return

    # titulos y titulos_cortos deben corresponder al orden seleccionado
    titulos = []
    for idx_1based in indices_reales:
        art = articulos[idx_1based - 1]
        titulos.append(art.get('title', f'Art_{idx_1based}')[:50])

    n = len(abstracts)

    # Diccionario para matrices de cada algoritmo
    resultados = {
        "Jaccard": np.zeros((n, n)),
        "Coseno_TFIDF": np.zeros((n, n)),
        "Levenshtein": np.zeros((n, n)),
        "Damerau": np.zeros((n, n)),
        "SBERT": np.zeros((n, n)),
        "Word2Vec": np.zeros((n, n))
    }
        
    print("\n[INFO] Calculando similitudes entre abstracts...\n")
    for i in range(n):
        for j in range(n):
            if i == j:
                for key in resultados.keys():
                    resultados[key][i, j] = 1.0
                continue
            
            a1, a2 = abstracts[i], abstracts[j]
            resultados["Jaccard"][i, j] = similitud_jaccard(a1, a2)
            resultados["Coseno_TFIDF"][i, j] = similitud_coseno(a1, a2)
            resultados["Levenshtein"][i, j] = similitud_levenshtein(a1, a2)
            resultados["Damerau"][i, j] = similitud_damerau(a1, a2)
            resultados["SBERT"][i, j] = similitud_sbert(a1, a2)
            resultados["Word2Vec"][i, j] = similitud_word2vec(a1, a2)

    os.makedirs("data/requerimiento2", exist_ok=True)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 180)
    pd.set_option('display.colheader_justify', 'center')

    # Títulos abreviados (primeras 5 palabras limpias)
    def abreviar_titulo(t):
        palabras = t.replace('{', '').replace('}', '').split()
        return ' '.join(palabras[:5]) + ('...' if len(palabras) > 5 else '')

    titulos_cortos = [abreviar_titulo(t) for t in titulos]

    for nombre, matriz in resultados.items():
        # aquí usamos indices_reales para conservar los números originales
        numeros_originales = [f"[{indices_reales[i]}] {titulos_cortos[i]}" for i in range(len(titulos_cortos))]
        df = pd.DataFrame(matriz, index=numeros_originales, columns=numeros_originales)
        print(f"\n=== MATRIZ DE SIMILITUD ({nombre}) ===")
        print(df.round(3).to_string())
        ruta_csv = os.path.join("data/requerimiento2", f"similitud_{nombre}.csv")
        df.to_csv(ruta_csv, index=True, encoding='utf-8-sig')
        print(f"[OK] Resultados guardados en: {ruta_csv}")