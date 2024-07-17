import os
import pandas as pd
from colorama import Fore, Style, init
from tabulate import tabulate

init()

def transformar_tiempos(t):
    parts = t.split(':')
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    elif len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    else:
        return float(t)

def display_table(data, headers):
    pilotos_autoclub = ['Antonio Galdeano', 'Jose Boullosa', 'Ismael Rodríguez', 'Alejandro García'] #Lista de pilotos autoclub
    rivales = ['Carlos Cabaco', 'Alberto Fernandez', 'Sergi Morera', 'Isidro Villar', 'Fran Fuentes', 'Alonso Gonzalez'] #Lista de pilotos a vigilar
    table_data = []
    for idx, row in data.iterrows():
        nombre_piloto = row['Piloto']
        #Resaltar el nombre del piloto en azul si el piloto está en la lista de Autoclub Ensidesa
        color = Fore.LIGHTBLUE_EX if nombre_piloto in pilotos_autoclub else ''
        reset_color = Style.RESET_ALL if nombre_piloto in pilotos_autoclub else ''
        #Resaltar el nombre del piloto en amarillo si está en la lista de rivales
        if nombre_piloto in rivales:
            nombre_piloto = Fore.YELLOW + nombre_piloto + Style.RESET_ALL
        table_data.append([
            idx + 1,
            color + nombre_piloto + reset_color,
            row['Fecha'],
            row['Tiempo vuelta'],
            row['Sector 1'],
            row['Sector 2'],
            row['Sector 3'],
            row['Compuesto'],
            row['Lastre'],
            row['Restrictor'],
            #row['Rain Intensity'],
            #row['Rain Wetness'],
            #row['Rain Water']
        ])
    print(tabulate(table_data, headers=headers, tablefmt='simple', colalign=("center",)*len(headers)))

def analyze_data(input_folder, tipo_compuesto):
    all_data = []

    if not os.path.exists(input_folder):
        print(f"El directorio {input_folder} no existe.")
        return

    for filename in os.listdir(input_folder):
        if filename.endswith('.csv'):
            filepath = os.path.join(input_folder, filename)
            df = pd.read_csv(filepath)
            df['Tiempo vuelta sec'] = df['Tiempo vuelta'].apply(transformar_tiempos)
            df = df[df['Tiempo vuelta sec'] < 120]
            all_data.append(df)

    if not all_data:
        print("No se encontraron datos para procesar")
        return

    all_laps = pd.concat(all_data, ignore_index=True)
    vueltas_filtradas = all_laps[all_laps['Compuesto'] == tipo_compuesto]
    if vueltas_filtradas.empty:
        print(f"No se encontraron vueltas con el compuesto {tipo_compuesto}")
        return

    vueltas_filtradas = vueltas_filtradas.sort_values(by='Tiempo vuelta sec') #Ordenado siempre de más rápido a mas lento
    
    headers = ['Posición', 'Piloto', 'Fecha', 'Tiempo vuelta', 'Sector 1', 'Sector 2', 'Sector 3', 'Compuesto', 'Lastre', 'Restrictor']
    print("Datos para el compuesto seleccionado:")
    display_table(vueltas_filtradas.reset_index(drop=True), headers)

    while True:
        filtro_piloto = input("Introduzca el nombre del piloto para filtrar (dejar en blanco para salir, o escribe 'todos' para mostrar los datos completos): ").lower()  #Siempre tratarlo como minúscula
        if not filtro_piloto:
            break
        elif filtro_piloto == 'todos':
            print("Mostrando todos los pilotos:")
            display_table(vueltas_filtradas.reset_index(drop=True), headers)
        else:
            data_especifica_piloto = vueltas_filtradas[vueltas_filtradas['Piloto'].str.lower().str.contains(filtro_piloto, case=False, na=False)]
            if data_especifica_piloto.empty:
                print("No se encontraron vueltas para el piloto especificado")
            else:
                print("Datos para el piloto seleccionado:")
                display_table(data_especifica_piloto.reset_index(drop=True), headers)

def main():
    input_folder = 'R2'
    tipo_compuesto = input("Tipo de neumático para mostrar (C1, C2, C3, C4, C5, WET): ")

    analyze_data(input_folder, tipo_compuesto)

if __name__ == "__main__":
    main()