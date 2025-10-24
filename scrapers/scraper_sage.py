import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

# Cargar variables de entorno
load_dotenv()

# Configurar carpeta de descargas
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "downloads/sage")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Configurar opciones de Chrome
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(DOWNLOAD_FOLDER),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")


def scrape_sage():
    """Extrae artículos de SAGE, descarga citas en formato BibTeX y recorre varias páginas."""

    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")

    if not EMAIL or not PASSWORD:
        print("❌ Error: Variables de entorno EMAIL y PASSWORD no están configuradas.")
        return

    SEARCH_TERM = "generative artificial intelligence"
    current_year = int(time.strftime("%Y"))
    start_year = current_year - 4 

    LOGIN_URL = f"https://journals-sagepub-com.crai.referencistas.com/action/doSearch?AllField={SEARCH_TERM.replace(' ', '+')}&startPage=1&target=default&content=articlesChapters&pageSize=100&AfterYear={start_year}&BeforeYear={current_year}"
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(LOGIN_URL)
        time.sleep(3)

        # ------------------ LOGIN ------------------
        try:
            google_login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btn-google"))
            )
            google_login_button.click()
            time.sleep(3)

            main_window = driver.current_window_handle
            for handle in driver.window_handles:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    break

            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_input.send_keys(EMAIL)
            email_input.send_keys(Keys.RETURN)
            time.sleep(2)

            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_input.send_keys(PASSWORD)
            password_input.send_keys(Keys.RETURN)
            time.sleep(5)

            if len(driver.window_handles) > 1:
                driver.switch_to.window(main_window)

            time.sleep(10)
            print("Login exitoso")
        except Exception as e:
            print(f"Error durante el inicio de sesión: {e}")
            driver.quit()
            return

        # ------------------ ACEPTAR COOKIES ------------------
        try:
            aceptCookies = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept Non-Essential Cookies')]"))
            )
            aceptCookies.click()
            print("Cookies aceptadas")
            time.sleep(2)
        except:
            print("Botón de cookies no encontrado o ya aceptado.")

        MAX_PAGES_TO_DOWNLOAD = 2

        # ------------------ ITERAR PÁGINAS ------------------
        for page in range(1, MAX_PAGES_TO_DOWNLOAD+1):
            print(f"Procesando página {page}")

            time.sleep(5)

            try:
                checkbox = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "action-bar-select-all"))
                )
                driver.execute_script("arguments[0].scrollIntoView();", checkbox)
                driver.execute_script("arguments[0].click();", checkbox)
                print(f"Página {page}: artículos seleccionados")
                time.sleep(3)
            except Exception as e:
                print(f"Error al seleccionar resultados en página {page}: {e}")
                continue

            try:
                export_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'export-citation')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView();", export_button)
                ActionChains(driver).move_to_element(export_button).click().perform()
                print("Botón Export clickeado")
                time.sleep(10)
            except Exception as e:
                print(f"Error en exportación: {e}")
                continue

            try:
                citation_dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "citation-format"))
                )
                select = Select(citation_dropdown)
                select.select_by_value("bibtex")
                print("Formato BibTeX seleccionado")
                time.sleep(5)
            except Exception as e:
                print(f"Error al seleccionar BibTeX: {e}")
                continue

            try:
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download citation')]"))
                ).click()
                print("Descarga iniciada")
                time.sleep(8)
            except Exception as e:
                print(f"Error al hacer clic en Download: {e}")
                continue

            try:
                close_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@alt, 'close')]"))
                )
                close_button.click()
                print("Diálogo de exportación cerrado")
                time.sleep(2)
            except:
                print("No se pudo cerrar el diálogo, continuando...")

            if page == MAX_PAGES_TO_DOWNLOAD:
                print(f"Límite de {MAX_PAGES_TO_DOWNLOAD} páginas alcanzado.")
                break

            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'page-item__arrow--next')]/a"))
                )
                ActionChains(driver).move_to_element(next_button).click().perform()
                print(f"Navegando a la página {page + 1}")
                time.sleep(5)
            except:
                print("No hay más páginas disponibles.")
                break

    except Exception as e:
        print(f"Error general: {e}")
    finally:
        print("Finalizando extractor SAGE...")
        driver.quit()


if __name__ == "__main__":
    scrape_sage()