# domain/requerimiento1.py
import os
# Asegúrate de que la ruta de importación sea correcta.
# Esto asume que utils.py está en la misma carpeta 'domain'.
from .utils import leer_bibtex, normalize_data, save_bibtex, buscar_duplicados

def ejecutar_req1():
    """
    Ejecuta el proceso completo del Requerimiento 1:
    Unifica todos los archivos .bib de la carpeta 'downloads' y elimina duplicados.
    """
    # 1. Definir la carpeta principal de descargas
    # Asumimos que este script se llama desde main.py en la raíz
    downloads_folder = 'downloads'

    if not os.path.isdir(downloads_folder):
        print(f"Error: La carpeta '{downloads_folder}' no existe.")
        print("   Por favor, primero ejecuta los scrapers para descargar los archivos.")
        return

    # 2. Leer y procesar todos los archivos .bib recursivamente
    all_articles = []
    print(f"\n[INFO] Leyendo archivos de la carpeta '{downloads_folder}' y subcarpetas...")
    
    # os.walk nos permite explorar todas las subcarpetas
    for root, dirs, files in os.walk(downloads_folder):
        for file in files:
            if file.endswith('.bib'):
                file_path = os.path.join(root, file)
                try:
                    entries = leer_bibtex(file_path) # De utils.py
                    normalized_entries = normalize_data(entries) # De utils.py
                    all_articles.extend(normalized_entries)
                    print(f"  - Procesado archivo '{file_path}' con {len(normalized_entries)} artículos.")
                except Exception as e:
                    print(f"  -Error al procesar el archivo '{file_path}': {e}")
    
    if not all_articles:
        print("No se encontraron artículos válidos en la carpeta 'downloads'.")
        return

    print(f"\n[INFO] Se encontraron un total de {len(all_articles)} artículos (antes de deduplicar).")

    # 3. Buscar y separar duplicados
    print("[INFO] Buscando y eliminando duplicados por título...")
    # Usamos la función de utils.py
    articulos_unicos, articulos_duplicados = buscar_duplicados(all_articles)

    output_dir = 'data/requerimiento1'
    os.makedirs(output_dir, exist_ok=True)

    # 4. Guardar los resultados en la carpeta raíz (o en 'output/' si prefieres)
    ruta_unificados = os.path.join(output_dir, 'articulos_unificados.bib')
    ruta_duplicados = os.path.join(output_dir, 'articulos_duplicados.bib')
    
    save_bibtex(ruta_unificados, articulos_unicos)
    save_bibtex(ruta_duplicados, articulos_duplicados) 

    print("\n" + "="*40)
    print("PROCESO DE UNIFICACIÓN COMPLETADO")
    print(f"  - {len(articulos_unicos)} artículos únicos guardados en '{ruta_unificados}'")
    print(f"  - {len(articulos_duplicados)} artículos duplicados guardados en '{ruta_duplicados}'")
    print("="*40)