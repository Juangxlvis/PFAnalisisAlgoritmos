import os
import bibtexparser
import seaborn as sns
from bibtexparser.bwriter import BibTexWriter
from fuzzywuzzy import fuzz
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
import numpy as np

def leer_bibtex(file_path):
    """Lee archivo BibTeX y devuelve entradas"""
    # Tu función original está perfecta, la dejamos.
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return bibtexparser.load(file).entries
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error leyendo el archivo {file_path}: {e}")
        return []

def normalize_data(entries):
    """Normaliza los datos de los artículos a un formato estándar."""
    normalized_articles = []
    for e in entries:
        normalized_articles.append({
            'title': e.get('title', 'No Title').strip().lower(),
            'author': e.get('author', 'No Author').strip().lower(),
            'year': e.get('year', '').strip(),
            'abstract': e.get('abstract', '').strip().lower(),
            'raw_data': e  # Guardamos la entrada original completa
        })
    return normalized_articles

def save_bibtex(filename, articles):
    """Guarda artículos en archivo BibTeX, filtrando None."""
    db = bibtexparser.bibdatabase.BibDatabase()
    # Filtrar artículos que no son None y tienen raw_data
    db.entries = [a['raw_data'] for a in articles if a is not None and 'raw_data' in a]
    
    writer = BibTexWriter()
    writer.order_entries_by = None
    writer.indent = '    ' # Usamos 4 espacios para la indentación
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(writer.write(db))

def buscar_duplicados(articles):
    """Identifica artículos duplicados por título usando fuzzy matching."""
    unicos = []
    duplicados = []
    vistos = {} # Usaremos el título como clave para eficiencia
    
    for article in articles:
        # ¡OJO! Corregimos 'titulo' a 'title' para que coincida con normalize_data
        titulo_actual = article['title']
        
        es_duplicado = False
        for titulo_visto in vistos.keys():
            # Comparamos si el título actual es muy similar a uno ya visto
            if fuzz.ratio(titulo_actual, titulo_visto) > 90: # 90% de similitud
                duplicados.append(article)
                es_duplicado = True
                break
        
        if not es_duplicado:
            vistos[titulo_actual] = article
            unicos.append(article)
            
    return unicos, duplicados

