# domain/requerimiento1.py
import os
# Asegúrate de que la ruta de importación sea correcta según tu estructura.
# Esta importación asume que utils.py está en la misma carpeta 'domain'.
from .utils import leer_bibtex, normalize_data, save_bibtex, buscar_duplicados

def ejecutar_req1():
    """
    Ejecuta el proceso completo del Requerimiento 1.
    """
    # 1. Pedir la ruta de la carpeta al usuario.
    folder_path = input("➡️  Ingrese la ruta de la carpeta con los archivos .bib : ")

    # 2. Validar que la ruta y la carpeta existan.
    if not os.path.isdir(folder_path):
        print(f"Error: La carpeta '{folder_path}' no existe o no es un directorio.")
        return

    # 3. Leer y procesar todos los archivos .bib de la carpeta.
    all_articles = []
    print(f"\n[INFO] Leyendo archivos de la carpeta '{folder_path}'...")
    for file in os.listdir(folder_path):
        if file.endswith('.bib'):
            file_path = os.path.join(folder_path, file)
            try:
                entries = leer_bibtex(file_path)
                normalized_entries = normalize_data(entries)
                all_articles.extend(normalized_entries)
                print(f"  - Procesado archivo '{file}' con {len(normalized_entries)} artículos.")
            except Exception as e:
                print(f"  -Error al procesar el archivo '{file}': {e}")
    
    if not all_articles:
        print("No se encontraron artículos válidos en la carpeta.")
        return

    print(f"\n[INFO] Se encontraron un total de {len(all_articles)} artículos.")

    # 4. Buscar y separar duplicados.
    print("[INFO] Buscando y eliminando duplicados por título...")
    articulos_unicos, articulos_duplicados = buscar_duplicados(all_articles)

    # 5. Guardar los resultados en los archivos de salida.
    ruta_unificados = 'articulos_unificados.bib'
    ruta_duplicados = 'articulos_duplicados.bib'
    
    save_bibtex(ruta_unificados, articulos_unicos)
    save_bibtex(ruta_duplicados, articulos_duplicados)

    print("\n" + "="*40)
    print("PROCESO COMPLETADO")
    print(f"  - {len(articulos_unicos)} artículos únicos guardados en '{ruta_unificados}'")
    print(f"  - {len(articulos_duplicados)} artículos duplicados guardados en '{ruta_duplicados}'")
    print("="*40)