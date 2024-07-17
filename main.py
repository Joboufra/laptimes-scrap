import os
import requests
import argparse
import subprocess
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from modules.lap_analysis import analyze_data
from colorama import Fore
from modules.log_config import set_logger

#Config del logger
logger = set_logger('laptimes-scrap', 'app.log')

def configurar_driver():
    options = Options()
    options.headless = True
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--disable-infobars")  # Disable infobars
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def crear_directorio_para_circuito(nombre_circuito, directorio_base):
    directorio_circuito = os.path.join(directorio_base, nombre_circuito.replace(" ", "_").replace("/", "_"))
    os.makedirs(directorio_circuito, exist_ok=True)
    return directorio_circuito

def descargar_y_guardar_archivo(url, ruta_archivo):
    with requests.Session() as sesion:
        respuesta = sesion.get(url)
        if respuesta.status_code == 200:
            with open(ruta_archivo, 'wb') as archivo:
                archivo.write(respuesta.content)
        else:
            logger.error(f"Error al descargar datos de sesión {os.path.basename(ruta_archivo)}")

def descargar_json_por_circuito(driver, url_base, directorio_base, num_paginas=4):
    campeonatos = {
        "http://totalsimracing.sytes.net:8772": "TSR",
        "http://sv.lacuevaracing.es:8772": "LCV - La Cueva"
    }
    campeonato = campeonatos.get(url_base, "Desconocido")
    directorio_campeonato = os.path.join(directorio_base, campeonato)
    os.makedirs(directorio_campeonato, exist_ok=True)
    archivos_json_descargados = []

    try:
        for pagina in range(num_paginas):
            logger.info(f"Accediendo a la página: {pagina}")
            driver.get(f"{url_base}/results?page={pagina}&server=0")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "tr")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            filas = soup.find_all('tr')

            for fila in filas[1:]:
                celdas = fila.find_all('td')
                if len(celdas) > 2:
                    nombre_circuito = celdas[2].text.strip()
                    directorio_circuito = crear_directorio_para_circuito(nombre_circuito, directorio_campeonato)
                    enlace_descarga = fila.find('a', attrs={'aria-label': 'download result'})
                    if enlace_descarga:
                        url_json = urljoin(url_base, enlace_descarga['href'])
                        nombre_archivo_json = url_json.split('/')[-1]
                        ruta_archivo = os.path.join(directorio_circuito, nombre_archivo_json)

                        if not os.path.exists(ruta_archivo):
                            descargar_y_guardar_archivo(url_json, ruta_archivo)
                            archivos_json_descargados.append(ruta_archivo)
                            logger.info(f"Archivo descargado: {nombre_archivo_json}, Campeonato: {campeonato}, Circuito: {nombre_circuito}")
                        else:
                            logger.debug(f"Archivo ya existe: {nombre_archivo_json}")
                    else:
                        logger.error("No se encontró enlace de descarga en la fila.")
    except Exception as e:
        logger.error("Error durante el proceso de scraping: " + str(e))

    return archivos_json_descargados

def update_data():
    driver = configurar_driver()
    urls_base = [
        "http://totalsimracing.sytes.net:8772",
        "http://sv.lacuevaracing.es:8772",
    ]
    try:
        for url_base in urls_base:
            logger.info(f"Descargando datos desde {url_base}")
            descargar_json_por_circuito(driver, url_base, os.path.join(os.getcwd(), "data", "origin"), 3)
    finally:
        driver.quit()

def procesar_datos():
    subprocess.run(['python3', 'data.py'])

def parse_args():
    parser = argparse.ArgumentParser(description="Scrap de análisis de vueltas | Jose Boullosa")
    parser.add_argument('--update', action='store_true', help="Lanzar recolección de datos y análisis (Para tareas batch)")
    return parser.parse_args()

def main_menu(update=False):
    if update:
        logger.info("Actualización automática de datos")
        update_data()
        procesar_datos()
    else:
        print(Fore.CYAN + "\n##########################\n### Menú de navegación ###\n##########################")
        print(Fore.LIGHTMAGENTA_EX + "1. Actualizar datos")
        print(Fore.LIGHTMAGENTA_EX + "2. Analizar datos")
        choice = input(Fore.WHITE + "Introduce tu elección (1 o 2): ")

        if choice == '1':
            print(Fore.CYAN + "\n########################\n### Actualizar datos ###\n########################" + Fore.WHITE)
            update_data()
            procesar_datos()
        elif choice == '2':
            input_folder = 'R2'
            print(Fore.CYAN + "\n################################\n### Opción 2: Analizar datos ###\n################################")
            print(Fore.LIGHTMAGENTA_EX + "Escoge tu compuesto (1: C1, 2: C2, 3: C3, 4: C4, 5: C5, W: WET)")
            tyre_opt = input(Fore.WHITE + "Opción: ")
            tyre_type = {'1': 'C1', '2': 'C2', '3': 'C3', '4': 'C4', '5': 'C5', 'W': 'WET'}.get(tyre_opt, '')
            if tyre_type:
                analyze_data(input_folder, tyre_type)
            else:
                print(Fore.RED + "Opción no válida. Por favor, repite.")
                main_menu()
        else:
            print(Fore.RED + "Opción no válida. Por favor, introduce 1 o 2.")
            main_menu()

if __name__ == "__main__":
    args = parse_args()
    main_menu(update=args.update)