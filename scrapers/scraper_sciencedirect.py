# science_test_debug.py
import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "downloads", "science_direct")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(DOWNLOAD_FOLDER),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
})


def save_debug_artifacts(driver, name_prefix="debug"):
    """Solo guarda el HTML snippet para debug críticos únicamente"""
    html_path = os.path.join(DOWNLOAD_FOLDER, f"{name_prefix}_html_snippet.txt")
    try:
        html = driver.page_source
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html[:20000])  # limitado a 20k chars
        print(f"Guardado snippet de HTML en: {html_path}")
        return html_path
    except Exception as e:
        print(f"No se pudo guardar snippet HTML: {e}")
        return None


def remove_common_overlays(driver):
    scripts = [
        "document.querySelectorAll('.modal, .overlay, .modal-backdrop, .cookie-banner, [role=\"dialog\"]').forEach(e=>e.remove());",
        "document.querySelectorAll('[style*=\"z-index\"]').forEach(e=>{ if(window.getComputedStyle(e).zIndex && parseInt(window.getComputedStyle(e).zIndex) > 1000) e.style.display='none'; });",
    ]
    for s in scripts:
        try:
            driver.execute_script(s)
        except Exception:
            pass


def click_element_fallbacks(driver, elem, desc="element"):
    """Intenta varias formas de clicar un elemento WebElement."""
    try:
        elem.click()
        return True, "click()"
    except Exception:
        try:
            ActionChains(driver).move_to_element(elem).click().perform()
            return True, "ActionChains click"
        except Exception:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                driver.execute_script("arguments[0].click();", elem)
                return True, "JS click"
            except Exception:
                return False, "failed clicks"


def change_results_per_page(driver, results_count=100):
    """Cambia el número de resultados por página"""
    try:
        print(f"Intentando cambiar a {results_count} resultados por página...")

        # Buscar el dropdown o botón para cambiar resultados por página
        selectors = [
            f"//span[contains(@class, 'anchor-text') and contains(text(), '{results_count}')]",
            f"button[aria-label*='{results_count}']",
            f"a[aria-label*='{results_count}']",
            f"//option[contains(text(), '{results_count}')]",
            ".results-per-page-selector",
            ".page-size-selector",
            "[data-testid*='page-size']"
        ]

        for selector in selectors:
            try:
                if selector.startswith("//"):
                    elem = driver.find_element(By.XPATH, selector)
                else:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)

                if elem.is_displayed() and elem.is_enabled():
                    print(f"Encontrado selector de resultados con: {selector}")

                    # Hacer scroll y click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(1)

                    ok, how = click_element_fallbacks(driver, elem, f"results_{results_count}")
                    if ok:
                        print(f"Cambiado a {results_count} resultados por página")

                        # Esperar a que se recargue la página con más resultados
                        time.sleep(5)
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        time.sleep(3)
                        return True
            except Exception:
                continue

        print(f"No se pudo cambiar a {results_count} resultados por página, continuando...")
        return False

    except Exception as e:
        print(f"Error cambiando resultados por página: {e}")
        return False


def get_current_page_number(driver):
    """Obtiene el número de la página actual con múltiples métodos"""
    try:
        # Método 1: Buscar en elementos de paginación activos
        active_selectors = [
            "li[data-page] button[aria-current='true']",
            "button[aria-current='true']",
            "li.active button",
            "li.active a",
            "[data-testid*='page'] button[aria-current='true']",
            ".pagination .active",
            ".pagination li.active",
            "button.selected",
            "a.selected"
        ]

        for selector in active_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text and text.isdigit():
                        print(f"Página actual detectada: {text} (selector: {selector})")
                        return int(text)
            except:
                continue

        # Método 2: Buscar input de página actual
        try:
            page_inputs = driver.find_elements(By.CSS_SELECTOR,
                                               "input[type='number'], .pagination-input, [aria-label*='page']")
            for page_input in page_inputs:
                value = page_input.get_attribute("value") or page_input.get_attribute("aria-label") or ""
                if value and any(char.isdigit() for char in value):
                    # Extraer números del texto
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        print(f"Página actual detectada: {numbers[0]} (input)")
                        return int(numbers[0])
        except:
            pass

        # Método 3: Buscar en la URL (más confiable)
        current_url = driver.current_url
        if "offset=" in current_url:
            import re
            match = re.search(r'offset=(\d+)', current_url)
            if match:
                offset = int(match.group(1))
                # Determinar resultados por página desde la URL
                if "show=100" in current_url:
                    results_per_page = 100
                elif "show=50" in current_url:
                    results_per_page = 50
                else:
                    results_per_page = 25  # default

                page_num = (offset // results_per_page) + 1
                print(
                    f"Página actual detectada: {page_num} (URL offset: {offset}, resultados por página: {results_per_page})")
                return page_num
        elif "page=" in current_url:
            import re
            match = re.search(r'page=(\d+)', current_url)
            if match:
                page_num = match.group(1)
                print(f"Página actual detectada: {page_num} (URL page)")
                return int(page_num)

        print("No se pudo detectar número de página, usando conteo manual")
        return 1  # Fallback

    except Exception as e:
        print(f"Error detectando página: {e}, usando 1 por defecto")
        return 1


def is_next_button_disabled(driver):
    """Verifica si el botón next está deshabilitado o no existe (última página)"""
    try:
        # Buscar el botón next específico
        next_buttons = driver.find_elements(By.XPATH,
                                            "//span[contains(@class, 'anchor-text') and contains(text(), 'next')]")

        if not next_buttons:
            print("No se encontró botón 'next' - última página")
            return True

        for next_btn in next_buttons:
            # Verificar si está deshabilitado por atributo o clase
            if not next_btn.is_enabled():
                print("Botón 'next' deshabilitado - última página")
                return True

            # Verificar clases del elemento o su padre
            classes = next_btn.get_attribute("class") or ""
            try:
                parent = next_btn.find_element(By.XPATH, "..")
                parent_classes = parent.get_attribute("class") or ""
            except:
                parent_classes = ""

            if "disabled" in classes.lower() or "disabled" in parent_classes.lower():
                print("Botón 'next' con clase disabled - última página")
                return True

        return False

    except Exception:
        return False


def go_to_next_page(driver):
    """Intenta navegar a la siguiente página"""
    try:
        # Primero verificar si estamos en la última página
        if is_next_button_disabled(driver):
            return False

        # Intentar diferentes selectores para el botón "Next"
        next_selectors = [
            "//span[contains(@class, 'anchor-text') and contains(text(), 'next')]",
            "//span[contains(@class, 'anchor-text') and contains(text(), 'Next')]",
            "button[aria-label*='Next']",
            "button[aria-label*='Siguiente']",
            ".pagination-next",
            ".next-page",
            "a[aria-label*='Next']",
            "a[aria-label*='Siguiente']",
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Siguiente')]",
            "//a[contains(text(), 'Next')]",
            "//a[contains(text(), 'Siguiente')]"
        ]

        for selector in next_selectors:
            try:
                if selector.startswith("//"):
                    next_btn = driver.find_element(By.XPATH, selector)
                else:
                    next_btn = driver.find_element(By.CSS_SELECTOR, selector)

                if next_btn.is_enabled() and next_btn.is_displayed():
                    print(f"Encontrado botón siguiente con selector: {selector}")

                    # Scroll al botón
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                    time.sleep(1)

                    ok, how = click_element_fallbacks(driver, next_btn, "next_button")
                    if ok:
                        print(f"Navegando a siguiente página usando: {selector}")

                        # Esperar a que cargue la nueva página
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        time.sleep(5)  # Esperar más tiempo para que cargue completamente

                        return True
            except Exception:
                continue

        print("No se pudo encontrar el botón de siguiente página")
        return False

    except Exception:
        return False


def select_all_articles(driver):
    """Selecciona todos los artículos de la página actual con múltiples métodos"""
    try:
        # Primero eliminar overlays que puedan estar tapando el checkbox
        remove_common_overlays(driver)
        time.sleep(1)

        # Método 1: Checkbox principal por ID (con wait)
        try:
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "select-all-results"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(1)

            # Verificar si ya está seleccionado
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
                print("Checkbox de selección clickeado (por ID)")
                time.sleep(2)

                # Verificar que se seleccionó correctamente
                if checkbox.is_selected():
                    print("Verificación: Checkbox está seleccionado")
                else:
                    print("El checkbox no se seleccionó correctamente")
            else:
                print("Checkbox ya estaba seleccionado")
            return True
        except Exception:
            pass

        # Método 2: Buscar checkbox por XPath con texto
        try:
            select_all_checkboxes = driver.find_elements(By.XPATH,
                                                         "//input[@type='checkbox' and contains(@aria-label, 'all') or contains(@title, 'all')]")
            for checkbox in select_all_checkboxes:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    time.sleep(1)

                    if not checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", checkbox)
                        print("Checkbox de selección clickeado (por aria-label/title)")
                        time.sleep(2)
                        return True
                except:
                    continue
        except:
            pass

        # Método 3: Buscar por otros selectores CSS
        checkbox_selectors = [
            "input[type='checkbox'][aria-label*='all']",
            "input[type='checkbox'][title*='all']",
            "input[type='checkbox'][data-testid*='select-all']",
            ".select-all-checkbox",
            "[data-cy*='select-all']",
            "#select-all-results",
            "input.select-all"
        ]

        for selector in checkbox_selectors:
            try:
                checkbox = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(1)

                if not checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                    print(f"Checkbox de selección clickeado (selector: {selector})")
                    time.sleep(2)
                    return True
            except:
                continue

        # Método 4: Buscar por texto y hacer click en elemento padre
        try:
            select_all_texts = driver.find_elements(By.XPATH,
                                                    "//*[contains(text(), 'Select all') or contains(text(), 'Seleccionar todo') or contains(text(), 'select all results')]")
            for elem in select_all_texts:
                try:
                    # Buscar el checkbox asociado o hacer click directo
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(1)

                    # Intentar encontrar un checkbox cercano
                    parent = elem.find_element(By.XPATH, "..")
                    checkboxes_in_parent = parent.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

                    if checkboxes_in_parent:
                        for cb in checkboxes_in_parent:
                            if not cb.is_selected():
                                driver.execute_script("arguments[0].click();", cb)
                                print("Checkbox encontrado cerca de texto 'Select all'")
                                time.sleep(2)
                                return True
                    else:
                        # Click directo en el elemento de texto
                        driver.execute_script("arguments[0].click();", elem)
                        print("Elemento de texto 'Select all' clickeado directamente")
                        time.sleep(2)
                        return True
                except:
                    continue
        except:
            pass

        return False

    except Exception:
        return False


def download_current_page(driver, page_number):
    """Descarga los artículos de la página actual"""
    try:
        print(f"Iniciando descarga para página {page_number}...")

        # Eliminar overlays por si tapan el botón
        remove_common_overlays(driver)
        time.sleep(2)

        # --- Seleccionar todos los artículos ---
        if not select_all_articles(driver):
            print("No se pudieron seleccionar los artículos, intentando continuar...")

        # --- Buscar Export ---
        export_candidates = []
        try:
            spans = driver.find_elements(By.XPATH, "//span[contains(@class,'export-all-link-text')]")
            export_candidates.extend(spans)
        except:
            pass

        try:
            spans2 = driver.find_elements(By.XPATH, "//span[contains(text(),'Export')]")
            export_candidates.extend(spans2)
        except:
            pass

        try:
            anchors = driver.find_elements(By.XPATH, "//a[contains(@class,'export') or contains(@class,'Export')]")
            export_candidates.extend(anchors)
        except:
            pass

        print(f"Encontrados {len(export_candidates)} candidatos para 'Export'.")

        export_clicked = False
        for idx, cand in enumerate(export_candidates):
            if not cand.is_displayed():
                continue

            desc = cand.tag_name + " / " + (cand.get_attribute("class") or "")[:120]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cand)
            time.sleep(0.5)

            ok, how = click_element_fallbacks(driver, cand, desc)
            print(f"  intento {idx + 1}: {desc} -> {ok} ({how})")
            time.sleep(2)

            # Verificar si apareció el menú de BibTeX
            try:
                bib = driver.find_elements(By.XPATH, "//span[contains(text(), 'Export citation to BibTeX')]")
                if bib:
                    export_clicked = True
                    print("Menú Export abierto (se detectó la opción BibTeX).")
                    break
            except:
                pass

        if not export_clicked:
            print("No logré abrir el menú Export automáticamente.")
            return False

        # --- Click en Export citation to BibTeX ---
        try:
            bib_span = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Export citation to BibTeX')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bib_span)
            time.sleep(1)

            ok, how = click_element_fallbacks(driver, bib_span, "bibtex_span")
            print(f"Intento click BibTeX -> {ok} via {how}")
            if not ok:
                raise Exception("No pude clicar BibTeX")

            print("Botón 'Export citation to BibTeX' clickeado")

            # Esperar a que se complete la descarga
            print("Esperando a que se complete la descarga...")
            time.sleep(10)

            return True

        except Exception as e:
            print(f"Error al clicar BibTeX: {e}")
            return False

    except Exception as e:
        print(f"Error en descarga de página {page_number}: {e}")
        return False


def science_test_debug():
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")

    current_year = int(time.strftime("%Y"))
    start_year = current_year - 4

    SEARCH_TERM = "generative artificial intelligence"
    LOGIN_URL = f"https://www-sciencedirect-com.crai.referencistas.com/search?qs={SEARCH_TERM.replace(' ', '%20')}&date={start_year}-{current_year}&show=100"
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)
    time.sleep(5)

    try:
        # --- LOGIN ---
        google_login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "btn-google"))
        )
        google_login_button.click()
        time.sleep(4)

        main_window = driver.current_window_handle
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                break

        email_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "identifierId")))
        email_input.send_keys(EMAIL)
        email_input.send_keys(Keys.RETURN)
        time.sleep(3)

        password_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "Passwd")))
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)
        time.sleep(10)

        driver.switch_to.window(main_window)
        print("Login completado, procediendo a descarga de todas las páginas.")

        # Asegurarse de que la página ha cargado bien
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # --- CAMBIAR A 100 RESULTADOS POR PÁGINA ---
        change_results_per_page(driver, 100)

        MAX_PAGES_TO_DOWNLOAD = 1
        
        downloaded_pages = 0
        manual_page_counter = 1

        while downloaded_pages < MAX_PAGES_TO_DOWNLOAD:
            current_page = manual_page_counter
            
            print(f"\n{'=' * 50}")
            print(f"PROCESANDO PÁGINA {current_page}...")
            print(f"{'=' * 50}")
            
            if download_current_page(driver, current_page):
                downloaded_pages += 1
                print(f"Página {current_page} descargada exitosamente.")
            else:
                print(f"Fallo al descargar la página {current_page}. Deteniendo.")
                break
            
            manual_page_counter += 1
            if downloaded_pages >= MAX_PAGES_TO_DOWNLOAD:
                print(f"Límite de {MAX_PAGES_TO_DOWNLOAD} páginas alcanzado. Proceso completado.")
                break

            print("Intentando navegar a la siguiente página...")
            if not go_to_next_page(driver):
                print("No hay más páginas disponibles. Proceso completado.")
                break
            
            time.sleep(3)

        print(f"\nPROCESO COMPLETADO")
        print(f"Total de páginas descargadas: {downloaded_pages}")

        final_files = os.listdir(DOWNLOAD_FOLDER)
        bib_final = [f for f in final_files if f.endswith('.bib') or 'bibtex' in f.lower()]
        other_files = [f for f in final_files if f not in bib_final]
        print(f"Total de archivos BibTeX descargados: {len(bib_final)}")
        if bib_final:
            print("Archivos BibTeX:")
            for bib_file in sorted(bib_final):
                print(f"   - {bib_file}")

    except Exception as e:
        print(f"Error inesperado en test debug: {e}")
        save_debug_artifacts(driver, "unexpected_error")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    science_test_debug()