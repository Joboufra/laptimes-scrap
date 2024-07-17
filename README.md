# laptimes-scrap

Libs en uso

* selenium
* webdriver_manager
* beautifulsoup4
* tabulate
* boto3

Parte del proyecto "Lap Analysis". Este componente realizará el web scrapping de las 2 webs objetivo, de las cuales extraemos los .json de los tiempos por vuelta y los preparamos para añadirlos a nuestra base de datos. 

Al ser en formato script y aceptando parámetros para determinadas acciones, este proceso es automatizable de forma sencilla a través de una tarea CRON que lance el programa de forma correcta.

También incluye una pequeña opción de análisis de los datos recogidos
