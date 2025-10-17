# main.py
import os
from domain.requerimiento1 import ejecutar_req1

def mostrar_menu():
    """Muestra el menú de opciones en la consola."""
    print("\n" + "="*40)
    print("   MENÚ DE ANÁLISIS BIBLIOMÉTRICO")
    print("="*40)
    print("1. Unificar y limpiar archivos BibTeX (Requerimiento 1)")
    print("2. Analizar similitud de abstracts (Requerimiento 2)")
    print("3. Analizar frecuencia de términos (Requerimiento 3)")
    print("4. Generar dendrograma de agrupamiento (Requerimiento 4)")
    print("5. Generar visualizaciones (Requerimiento 5)")
    print("0. Salir del programa")
    print("-" * 40)

def main():
    """Función principal que ejecuta el menú."""
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            print("\n[INFO] Ejecutando Requerimiento 1...")
            ejecutar_req1()
            print("Requerimiento 1 (aún no implementado).")

        elif opcion == '2':
            print("\n[INFO] Ejecutando Requerimiento 2...")
            print("Requerimiento 2 (aún no implementado).")

        elif opcion == '3':
            print("\n[INFO] Ejecutando Requerimiento 3...")
            print("Requerimiento 3 (aún no implementado).")

        elif opcion == '4':
            print("\n[INFO] Ejecutando Requerimiento 4...")
            # Este es el que ya lograste ejecutar antes.
            # ejecutar_req4()
            print("Requerimiento 4 (aún no implementado).")

        elif opcion == '5':
            print("\n[INFO] Ejecutando Requerimiento 5...")
            print("Requerimiento 5 (aún no implementado).")

        elif opcion == '0':
            print("\nSaliendo del programa. ¡Hasta luego!")
            break
        else:
            print("\nOpción no válida. Por favor, intente de nuevo.")

if __name__ == "__main__":
    main()