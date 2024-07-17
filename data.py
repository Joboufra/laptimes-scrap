import os
import json
import datetime
import time
from psycopg2 import Error
from psycopg2.extras import execute_values
from modules.log_config import set_logger
from config import get_conexion_db

# Configuración inicial del logger
logger = set_logger('laptimes-scrap', 'app.log')

# Formatear timestamps en milisegundos a 'MM:ss.mss'
def format_time(milliseconds):
    seconds, ms = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02}:{seconds:02}.{ms:03}"

# Crear el esquema y tabla si no existen
def crear_esquema_y_tabla(conn):
    try:
        with conn.cursor() as cur:
            # Verificar si el schema existe
            cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ac';")
            schema_exists = cur.fetchone()
            if not schema_exists:
                cur.execute("CREATE SCHEMA ac;")
            
            # Verificar si la tabla existe y añadir columnas si es necesario
            cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'ac' 
                AND table_name = 'tiemposvuelta'
            );
            """)
            table_exists = cur.fetchone()[0]
            if not table_exists:
                cur.execute('''
                CREATE TABLE ac.TiemposVuelta (
                    Piloto TEXT,
                    Fecha TIMESTAMP,
                    TiempoVuelta TEXT,
                    Compuesto TEXT,
                    Sector1 TEXT,
                    Sector2 TEXT,
                    Sector3 TEXT,
                    Lastre INTEGER,
                    Restrictor INTEGER,
                    Grip FLOAT,
                    Circuito TEXT,
                    Campeonato TEXT,
                    Coche TEXT,
                    Team TEXT,
                    Temp_Ambiente FLOAT,
                    Temp_Pista FLOAT,
                    UNIQUE(Piloto, Fecha, Circuito)
                )
                ''')
                conn.commit()
                logger.info("Estado tabla: Tabla creada correctamente")
            else:
                conn.commit()
                logger.debug("Estado tabla: OK")
    except Exception as e:
        logger.error(f"Error al crear esquema y tabla: {e}", exc_info=True)
        raise

# Procesar archivos en un circuito específico
def procesar_archivos_en_circuito(conn, carpeta_campeonato, carpeta_circuito, directorio_base):
    try:
        input_folder = os.path.join(directorio_base, carpeta_campeonato, carpeta_circuito)
        logger.info(f"Procesando archivos en la carpeta {input_folder}")

        with conn.cursor() as cur:
            crear_esquema_y_tabla(conn)

            # Verificar y listar archivos en el directorio
            files_in_directory = os.listdir(input_folder)
            logger.info(f"Archivos encontrados en {input_folder}: {files_in_directory}")

            # Ordenar archivos por fecha de modificación
            sorted_filenames = sorted(
                (f for f in files_in_directory if f.endswith('.json') and not f.endswith('RACE.json') and not f.endswith('QUALIFY.json')),
                key=lambda x: os.path.getmtime(os.path.join(input_folder, x))
            )

            if not sorted_filenames:
                logger.info(f"No se encontraron archivos JSON válidos en la carpeta {input_folder}")

            insert_query = '''
            INSERT INTO ac.TiemposVuelta (Piloto, Fecha, TiempoVuelta, Compuesto, Sector1, Sector2, Sector3, Lastre, Restrictor, Grip, Circuito, Campeonato, Coche, Team, Temp_Ambiente, Temp_Pista)
            VALUES %s
            ON CONFLICT (Piloto, Fecha, Circuito) DO NOTHING
            '''

            records = []
            for filename in sorted_filenames:
                filepath = os.path.join(input_folder, filename)
                logger.debug(f"Procesando archivo {filepath}")
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    track_name = data.get('TrackName', 'Unknown Track')
                    cars = {car['Driver']['Name']: (car['Model'], car['Driver']['Team']) for car in data['Cars']}
                    
                    for lap in data['Laps']:
                        try:
                            driver_name = lap['DriverName']
                            car_model, team = cars.get(driver_name, ('Unknown Car', 'Unknown Team'))
                            lap_timestamp = datetime.datetime.fromtimestamp(lap['Timestamp'])  # Convertir de segundos a datetime
                            total_lap_time_ms = lap['LapTime']
                            total_lap_time_str = format_time(total_lap_time_ms)
                            sector_times = lap['Sectors']
                            formatted_sector_times = [format_time(st) for st in sector_times]
                            grip_value = 0.00 if lap['Conditions'] is None else round(lap['Conditions']['Grip'] * 100, 2)
                            temp_ambiente = 0.00 if lap['Conditions'] is None else round(lap['Conditions']['Ambient'], 2)
                            temp_pista = 0.00 if lap['Conditions'] is None else round(lap['Conditions']['Road'], 2)
                            
                            records.append((
                                driver_name,
                                lap_timestamp,
                                total_lap_time_str,
                                lap['Tyre'],
                                formatted_sector_times[0],
                                formatted_sector_times[1],
                                formatted_sector_times[2],
                                lap['BallastKG'],
                                lap['Restrictor'],
                                grip_value,
                                track_name,
                                carpeta_campeonato,
                                car_model,
                                team,
                                temp_ambiente,
                                temp_pista
                            ))
                        except Exception as e:
                            logger.error(f"Error preparando datos de vuelta para el piloto {driver_name}: {e}", exc_info=True)

            if records:
                start_time = time.time()
                try:
                    execute_values(cur, insert_query, records)
                    conn.commit()
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    logger.info(f"Operación de inserción completada. Tiempo: {elapsed_time:.2f} segundos.")
                except Exception as e:
                    logger.error(f"Error durante la inserción en la base de datos: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Ocurrió un error al procesar archivos en el circuito {carpeta_circuito}: {e}", exc_info=True)
        raise

#Procesar archivos en todos los circuitos de un campeonato
def procesar_archivos_en_directorio(conn, carpeta_campeonato, directorio_base):
    try:
        campeonato_folder = os.path.join(directorio_base, carpeta_campeonato)
        circuitos = [d for d in os.listdir(campeonato_folder) if os.path.isdir(os.path.join(campeonato_folder, d))]
        
        for circuito in circuitos:
            procesar_archivos_en_circuito(conn, carpeta_campeonato, circuito, directorio_base)
    except Exception as e:
        logger.error(f"Ocurrió un error al procesar archivos en el campeonato {carpeta_campeonato}: {e}", exc_info=True)
        raise

# Procesar todos los datos
def procesar_datos():
    try:
        logger.info("Procesando datos")
        directorio_base = os.path.join(os.getcwd(), "data", "origin")
        carpetas_campeonatos = [d for d in os.listdir(directorio_base) if os.path.isdir(os.path.join(directorio_base, d))]
        
        conn = get_conexion_db()
        if conn is None:
            logger.error("No se pudo establecer conexión con la base de datos. Abortando proceso.")
            return
        
        for carpeta_campeonato in carpetas_campeonatos:
            procesar_archivos_en_directorio(conn, carpeta_campeonato, directorio_base)
    except Exception as e:
        logger.error(f"Ocurrió un error al procesar los datos: {e}", exc_info=True)
    finally:
        if conn is not None:
            conn.close()
            logger.info("Conexión cerrada")

if __name__ == "__main__":
    procesar_datos()
