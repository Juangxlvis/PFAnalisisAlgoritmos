# domain/utils.py
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding
import seaborn as sns
from bibtexparser.bwriter import BibTexWriter
from fuzzywuzzy import fuzz
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
import numpy as np

def leer_bibtex(file_path):
    """
    Lee un archivo .bib y devuelve una lista de diccionarios con los datos de los artículos.
    --- VERSIÓN CON PRE-LIMPIEZA PARA SAGE ---
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        cleaned_content = ""
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("doi:") and "=" not in line:
                continue  
            cleaned_content += line

        parser = BibTexParser()
        parser.ignore_errors = True
        parser.allow_duplicate_fields = True
        parser.common_strings = True
        parser.customization = homogenize_latex_encoding
        
        bib_database = bibtexparser.loads(cleaned_content, parser=parser)
        
        if not bib_database.entries:
            print(f"Advertencia: 'leer_bibtex' no encontró entradas en {file_path} (después de limpiar).")
            
        return bib_database.entries
            
    except FileNotFoundError:
        print(f"Advertencia: No se encontró el archivo {file_path}")
        return []
    except Exception as e:
        print(f"Error crítico leyendo el archivo {file_path}: {e}")
        return []

def normalize_data(entries):
    """Normaliza los datos de los artículos a un formato estándar."""
    normalized_articles = []
    for e in entries:
        if not isinstance(e, dict):
            print(f"Omitiendo entrada no válida: {e}")
            continue
            
        normalized_articles.append({
            'title': e.get('title', 'No Title').strip().lower(),
            'author': e.get('author', 'No Author').strip().lower(),
            'year': e.get('year', '').strip(),
            'abstract': e.get('abstract', '').strip().lower(),
            'raw_data': e
        })
    return normalized_articles

def save_bibtex(filename, articles):
    """Guarda artículos en archivo BibTeX, filtrando None."""
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = [a['raw_data'] for a in articles if a is not None and 'raw_data' in a]
    
    writer = BibTexWriter()
    writer.order_entries_by = None
    writer.indent = '    '
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(writer.write(db))

def buscar_duplicados(articles):
    """Identifica artículos duplicados por título usando fuzzy matching."""
    unicos = []
    duplicados = []
    vistos = {}
    
    for article in articles:
        titulo_actual = article['title']
        if titulo_actual == 'no title':
            continue
        es_duplicado = False
        for titulo_visto in vistos.keys():
            if fuzz.ratio(titulo_actual, titulo_visto) > 90:
                duplicados.append(article)
                es_duplicado = True
                break
        if not es_duplicado:
            vistos[titulo_actual] = article
            unicos.append(article)
    return unicos, duplicados


def graficar_tiempos(mediciones, num_articles):
    """Genera gráfico de comparación de tiempos"""
    metodos = list(mediciones.keys())
    tiempos = list(mediciones.values())
    plt.figure(figsize=(12, 6))
    bars = plt.bar(metodos, tiempos)
    plt.xlabel('Método de Ordenamiento')
    plt.ylabel('Tiempo (s)')
    plt.title(f'Comparación de Tiempos ({num_articles} artículos)')
    plt.xticks(rotation=45, ha='right')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.6f}',
                 ha='center', va='bottom')
    plt.tight_layout()
    plt.show()

def extraer_abstracts_bibtex(ruta):
    """Extrae abstracts y etiquetas de un archivo .bib, versión robusta."""
    try:
        with open(ruta, 'r', encoding='utf-8') as bibtex_file:
            lines = bibtex_file.readlines()
        
        cleaned_content = ""
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("doi:") and "=" not in line:
                continue
            cleaned_content += line

        parser = BibTexParser()
        parser.ignore_errors = True
        parser.allow_duplicate_fields = True
        parser.common_strings = True
        parser.customization = homogenize_latex_encoding
        
        bib_database = bibtexparser.loads(cleaned_content, parser=parser)
    
    except Exception as e:
        print(f"Error crítico leyendo {ruta} en extraer_abstracts: {e}")
        return [], []

    abstracts = []
    etiquetas = []
    for entry in bib_database.entries:
        if not isinstance(entry, dict):
            continue
        if 'abstract' in entry:
            abstracts.append(entry['abstract'])
            keyword = entry.get('keywords', '').strip()
            if keyword:
                etiquetas.append(keyword)
            else:
                etiquetas.append(entry.get('title', 'Desconocido')[:30])
    return abstracts, etiquetas

def graficar_dendrograma_rq5(dist_matrix, labels, metodo='ward', titulo='Dendrograma'):
    condensed = squareform(dist_matrix, checks=False)
    linkage_matrix = linkage(condensed, method=metodo)
    plt.figure(figsize=(12, 6))
    dendrogram(linkage_matrix, labels=labels, leaf_rotation=90)
    plt.title(titulo)
    plt.tight_layout()
    plt.show()

def graficar_similitud(dist_matrix, etiquetas, titulo="Similitud de Abstracts - SBERT"):
    n = len(dist_matrix)
    nombres = etiquetas
    plt.figure(figsize=(12, 6))
    plt.bar(nombres, [10]*n)
    plt.xticks(rotation=90)
    plt.title(titulo)
    plt.tight_layout()
    plt.show()

def graficar_heatmap_similitud(dist_matrix):
    max_dist = np.max(dist_matrix)
    simil_matrix = 100 * (1 - dist_matrix / max_dist)
    etiquetas = [f"A{i+1}" for i in range(len(dist_matrix))]
    plt.figure(figsize=(12, 10))
    sns.heatmap(simil_matrix, xticklabels=etiquetas, yticklabels=etiquetas, cmap="viridis", annot=True, fmt=".1f")
    plt.title("Similitud entre Abstracts (%) - Basado en WMD")
    plt.xlabel("Abstract")
    plt.ylabel("Abstract")
    plt.tight_layout()
    plt.show()