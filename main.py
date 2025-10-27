# main.py
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'domain'))
sys.path.append(os.path.join(script_dir, 'scrapers'))

try:
    from requerimiento1 import ejecutar_req1
    from requerimiento2 import ejecutar_req2

    
    from scraper_sciencedirect import science_test_debug
    from scraper_ieee import scrape_IEE
    from scraper_sage import scrape_sage

except ImportError as e:
    print(f"Error fatal: No se pudo importar un módulo. Asegúrate de que los archivos están en las carpetas correctas.")
    print(f"   Detalle: {e}")
    sys.exit(1)

def mostrar_menu():

    print("\n" + "="*40)
    print("   MENÚ DE ANÁLISIS BIBLIOMÉTRICO")
    print("="*40)
    print("0. Ejecutar Scrapers (Descargar todos los datos)")
    print("1. Unificar y limpiar archivos BibTeX (Req. 1)")
    print("2. Analizar similitud de abstracts (Req. 2)")
    print("3. Analizar frecuencia de términos (Req. 3)")
    print("4. Generar dendrograma de agrupamiento (Req. 4)")
    print("5. Generar visualizaciones (Req. 5)")
    print("9. Salir del programa")
    print("-" * 40)

def main():
    """Función principal que ejecuta el menú."""
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ")

        if opcion == '0':
            print("\n[INFO] Iniciando descarga automática de todas las bases de datos...")
            print("   Esto puede tardar varios minutos.")
            try:
                print("\n--- [1/3] Ejecutando Scraper de ScienceDirect ---")
                science_test_debug()
                
                print("\n--- [2/3] Ejecutando Scraper de IEEE Xplore ---")
                scrape_IEE()
                
                print("\n--- [3/3] Ejecutando Scraper de SAGE ---")
                scrape_sage()
                
                print("\nProceso de descarga completado.")
            except Exception as e:
                print(f"ERROR durante la ejecución de los scrapers: {e}")
                print("   Asegúrate de que el archivo .env está configurado y el VPN/Proxy (CRAI) está activo.")

        elif opcion == '1':
            print("\n[INFO] Ejecutando Requerimiento 1 (Unificación)...")
            ejecutar_req1()
            print("Unificación completada.")

        elif opcion == '2':
            print("\n[INFO] Ejecutando Requerimiento 2...")
            ejecutar_req2()

        elif opcion == '3':
            print("\n[INFO] Ejecutando Requerimiento 3...")
            print("Requerimiento 3 (aún no implementado).")

        elif opcion == '4':
            print("\n[INFO] Ejecutando Requerimiento 4...")
            print("Requerimiento 4 (aún no implementado).")

        elif opcion == '5':
            print("\n[INFO] Ejecutando Requerimiento 5...")
            print("Requerimiento 5 (aún no implementado).")

        elif opcion == '9': 
            print("\nSaliendo del programa. ¡Hasta luego!")
            break
        else:
            print("\nOpción no válida. Por favor, intente de nuevo.")


if __name__ == "__main__":
    main()