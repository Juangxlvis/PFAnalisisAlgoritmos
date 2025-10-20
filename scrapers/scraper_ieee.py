import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

load_dotenv()

# Configurar carpeta de descargas
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "downloads/IEE")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Configurar Chrome
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(DOWNLOAD_FOLDER),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")


def wait_for_page_load(driver, timeout=10):
    """Espera a que la página se cargue completamente"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)  # Tiempo adicional para elementos dinámicos
    except TimeoutException:
        print("⚠️ Timeout esperando la carga de la página")


def close_modal_safely(driver):
    """Cierra el modal de descarga de manera segura"""
    close_selectors = [
        "//div[contains(@class, 'modal-dialog')]//i[contains(@class,'fa-times')]",
        "//div[contains(@class, 'modal-dialog')]//button[contains(@class, 'close')]",
        "//div[contains(@class, 'modal')]//button[@aria-label='Close']",
        "//button[contains(@class, 'btn-close')]"
    ]

    for selector in close_selectors:
        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            actions = ActionChains(driver)
            actions.move_to_element(close_button).click().perform()
            print("✅ Modal cerrado")
            time.sleep(2)
            return True
        except (TimeoutException, ElementClickInterceptedException):
            continue

    # Si no se puede cerrar con click, intenta ESC
    try:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(2)
        print("✅ Modal cerrado con ESC")
        return True
    except Exception:
        print("⚠️ No se pudo cerrar el modal")
        return False


def has_next_page(driver):
    """Verifica si existe una página siguiente disponible"""
    try:
        # Buscar el botón de siguiente página
        next_selectors = [
            "//a[contains(@class, 'stats-Pagination_arrow_next')]",
            "//button[contains(@class, 'stats-Pagination_arrow_next')]",
            ".stats-Pagination_arrow_next_2",
            "//a[@aria-label='Next page']",
            "//button[@aria-label='Next page']"
        ]

        for selector in next_selectors:
            try:
                if selector.startswith("."):
                    next_element = driver.find_element(By.CLASS_NAME, selector[1:])
                elif selector.startswith("//"):
                    next_element = driver.find_element(By.XPATH, selector)
                else:
                    next_element = driver.find_element(By.CSS_SELECTOR, selector)

                # Verificar si el elemento está habilitado y es clickeable
                if next_element.is_enabled() and next_element.is_displayed():
                    # Verificar que no tenga clases de disabled
                    class_attr = next_element.get_attribute("class") or ""
                    disabled_attr = next_element.get_attribute("disabled")

                    if "disabled" not in class_attr.lower() and disabled_attr != "true":
                        return True, next_element
            except NoSuchElementException:
                continue

        return False, None
    except Exception as e:
        print(f"⚠️ Error verificando página siguiente: {e}")
        return False, None


def scrape_IEE():
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")

    SEARCH_TERM = "generative artificial intelligence"
    current_year = int(time.strftime("%Y"))
    start_year = current_year - 4 
    LOGIN_URL = f"https://ieeexplore-ieee-org.crai.referencistas.com/search/searchresult.jsp?newsearch=true&queryText={SEARCH_TERM.replace(' ', '%20')}&ranges={start_year}_{current_year}_Year"

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)
    wait_for_page_load(driver)

    # ------------------ LOGIN ------------------
    try:
        google_login_button = driver.find_element(By.ID, "btn-google")
        google_login_button.click()
        time.sleep(6)

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
        time.sleep(6)

        password_input = driver.find_element(By.NAME, "Passwd")
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)
        time.sleep(15)

        driver.switch_to.window(main_window)

    except Exception as e:
        print("❌ Error durante el login:", e)
        driver.quit()
        return

    # ------------------ ACEPTAR COOKIES ------------------
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.osano-cm-accept-all"))
        )
        button.click()
        print("✅ Cookies aceptadas")
    except TimeoutException:
        print("⚠️ Botón de cookies no encontrado (quizás ya aceptado).")

    # ------------------ SELECCIONAR 100 ------------------
    try:
        itemsPerPage = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "dropdownPerPageLabel"))
        )
        itemsPerPage.click()
        option_100 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '100')]"))
        )
        option_100.click()
        print("✅ Seleccionaste 100 elementos por página.")
        wait_for_page_load(driver)
    except Exception as e:
        print("❌ Error al seleccionar 100:", e)

    # ------------------ ITERAR PÁGINAS ------------------
    page_number = 1
    max_retries = 3

    MAX_PAGES_TO_DOWNLOAD = 10

    try:
        while page_number <= MAX_PAGES_TO_DOWNLOAD:
            print(f"📄 Procesando página {page_number}...")
            retry_count = 0
            page_success = False

            while retry_count < max_retries and not page_success:
                try:
                    # Esperar a que la página se cargue
                    wait_for_page_load(driver)

                    # Seleccionar todos los resultados
                    checkbox = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "results-actions-selectall-checkbox"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(3)

                    # Botón Export
                    export = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Export')]"))
                    )
                    export.click()
                    time.sleep(3)

                    # Pestaña Citations
                    citations_tab = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Citations')]"))
                    )
                    citations_tab.click()
                    time.sleep(2)

                    # BibTeX
                    bibtex_radio = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@for='download-bibtex']/input"))
                    )
                    if not bibtex_radio.is_selected():
                        bibtex_radio.click()
                    time.sleep(2)

                    # Citation + Abstract
                    add_abstract = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Citation and Abstract')]/input"))
                    )
                    if not add_abstract.is_selected():
                        add_abstract.click()
                    time.sleep(2)

                    # Download
                    download_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//div[contains(@class, 'modal-dialog')]//button[contains(text(), 'Download')]")
                        )
                    )
                    download_button.click()
                    print(f"✅ Página {page_number}: descarga iniciada")
                    time.sleep(10)  # Esperar a que inicie la descarga

                    page_success = True

                except (TimeoutException, ElementClickInterceptedException) as e:
                    retry_count += 1
                    print(f"⚠️ Intento {retry_count}/{max_retries} falló en página {page_number}: {e}")
                    if retry_count < max_retries:
                        time.sleep(5)
                        # Intentar cerrar cualquier modal abierto
                        close_modal_safely(driver)
                    else:
                        print(f"❌ No se pudo procesar la página {page_number} después de {max_retries} intentos")
                        break

            # Cerrar el modal
            if page_success:
                close_modal_safely(driver)

            # Verificar si hay página siguiente
            has_next, next_element = has_next_page(driver)

            if not has_next:
                print("🏁 No hay más páginas disponibles. Proceso completado.")
                break

            # Ir a la siguiente página
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", next_element)
                time.sleep(1)
                next_element.click()
                print(f"✅ Navegando a página {page_number + 1}")
                page_number += 1
                wait_for_page_load(driver)

            except Exception as e:
                print(f"❌ Error navegando a la siguiente página: {e}")
                break

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")

    print(f"📊 Proceso completado. Se procesaron {page_number} páginas.")
    driver.quit()


if __name__ == "__main__":
    scrape_IEE()