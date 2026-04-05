# Reporte Técnico: Extracción de Oferta Inmobiliaria (Web Scraping)

## 1. Objetivo y Alcance
Debido a la inexistencia de una API pública para portales inmobiliarios comerciales, se desarrolló un motor de extracción de datos no estructurados (*Web Scraper*) para obtener la oferta actual de viviendas en venta en los 32 estados de México. Este dataset representa el "Lado de la Oferta" en el Sistema Recomendador de la tesis.

---

## 2. Stack Tecnológico y Arquitectura
El motor de extracción fue construido con las siguientes herramientas de ingeniería:

* **Playwright (Python):** Framework de automatización de navegadores de alto nivel para manejar contenido renderizado dinámicamente (JavaScript).
* **Motor Chromium:** Navegador en modo *headful* para emular el comportamiento humano real.
* **Pandas:** Para la estructuración de datos en tiempo real y persistencia en archivos CSV.



---

## 3. Lógica de Ingeniería y Robustez
El script cuenta con mecanismos avanzados para garantizar la continuidad de la extracción masiva:

### A. Sistema de Reanudación (Checkpointing)
El motor analiza los archivos existentes antes de iniciar. Si una extracción se interrumpe (por fallo de red o energía), el script detecta la última página procesada y reanuda el trabajo con un traslape de 5 páginas para asegurar que no se pierdan propiedades nuevas publicadas durante la pausa.

### B. Deduplicación en Memoria (Hashing)
Para optimizar el almacenamiento y evitar registros redundantes, el sistema mantiene un `Set` de URLs en memoria RAM. Antes de escribir en el CSV, verifica si la propiedad ya existe, ignorando duplicados en milisegundos.

### C. Adaptabilidad Visual (Radar de Fin de Inventario)
Se implementó un sistema de detección de patrones visuales para identificar el fin del inventario. El scraper es capaz de leer mensajes dinámicos como *"¡Lo sentimos! Tu búsqueda no generó resultados"*, cerrando el estado actual y saltando al siguiente de forma automática.

### D. Evasión de Bloqueos y Ética de Extracción
* **User-Agent Spoofing:** Rotación de firmas de navegador para evitar la identificación como bot.
* **Delays Aleatorios:** Pausas de entre 8 y 12 segundos entre páginas para no saturar los servidores del portal y emular tiempos de lectura humanos.

---

## 4. Estructura del Dataset (Data Schema)
Los datos se guardan en archivos individuales por estado bajo la ruta `../data/raw/estados/`.

| Columna | Descripción | Importancia para el Modelo |
| :--- | :--- | :--- |
| **Estado** | Entidad federativa de la propiedad. | Segmentación geográfica. |
| **Pagina_Extraida** | Número de página del portal de origen. | Trazabilidad de la extracción. |
| **Fecha_Consulta** | Marca de tiempo de la extracción. | Análisis de frescura de datos. |
| **Precio** | Valor comercial listado. | Variable objetivo (Label/Target). |
| **Ubicacion** | Dirección o calle de la propiedad. | Geocodificación y análisis de zona. |
| **Caracteristicas** | Amenities (Habitaciones, Baños, m²). | Features para el algoritmo de recomendación. |
| **URL_Propiedad** | Enlace directo a la fuente. | Verificación y limpieza de datos. |

---

## 5. Notas de Implementación
* **Failsafe de Timeouts:** Tras 3 errores de carga consecutivos, el sistema marca el estado como completado o requiere intervención, evitando bucles infinitos en páginas inexistentes.
* **Normalización de Precios:** Los datos se extraen en formato bruto para ser procesados posteriormente en la fase de Limpieza de Datos (EDA), donde se eliminarán caracteres especiales y se convertirán a valores numéricos.

---

> **Estatus del Motor:** Operativo Nivel 8.3.
> **Última Actualización:** 05 de abril de 2026.
> **Autor:** Cesar Omar Miguel Gonzalez.