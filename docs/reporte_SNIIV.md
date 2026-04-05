# Reporte Técnico: Extracción Masiva de Datos de Vivienda (SNIIV / SEDATU)

## 1. Arquitectura de la Fuente de Datos
La extracción se realizó consumiendo la **CuboAPI** oficial del Sistema Nacional de Información e Indicadores de Vivienda (SNIIV). A diferencia de una API REST convencional, esta funciona bajo una lógica de **Cubos OLAP (Online Analytical Processing)**.



### Reglas Técnicas de la API:
* **Estructura de la URL:** `.../Get[Cubo]/[Rango_Fechas]/[Edo]/[Mpio]/[Dimensiones]`
* **Limitación de Agrupación:** La API permite un máximo de **5 dimensiones** (columnas) por petición.
* **Métricas Automáticas:** Las variables de valor (**acciones**, **monto**, **viviendas**) no se solicitan en la URL; el servidor las calcula y anexa automáticamente según las dimensiones de agrupación elegidas.

---

## 2. Metodología de Extracción (ETL)
Para garantizar la integridad de los datos y evitar bloqueos o tiempos de espera infinitos (*Timeouts*), se implementaron tres estrategias de ingeniería de datos:

### A. Chunking Temporal (Segmentación)
Debido a la carga computacional en el servidor gubernamental, se dividieron las peticiones en bloques de años o meses. Esto redujo el tamaño del *payload* de respuesta y aseguró una tasa de éxito del 100% en las conexiones.

### B. Diferenciación de Flujo vs. Stock (Snapshot)
Se identificaron dos comportamientos distintos en los cubos de datos:
* **Cubos de Flujo (Financiamientos, Registro, etc.):** Datos acumulados en rangos de tiempo (`Año_Inicio, Año_Fin`).
* **Cubos de Stock (Inventario):** Fotografías del estado actual en un momento específico. Se programó para extraer el cierre de cada año (`Año, Mes_12`) para capturar la "foto" del inventario disponible.

### C. Sistema de Escudo (Headers)
Se implementó una rotación de **User-Agent** para emular un navegador estándar (Chrome en Windows) y evitar que los *firewalls* institucionales clasificaran la petición como un ataque de denegación de servicio (DDoS).

---

## 3. Inventario de Datos Descargados
Se generaron **10 datasets nacionales** en formato CSV, consolidados para el periodo 2015-2026.

| Endpoint (Cubo) | Descripción del Dato | Dimensiones Clave Extraídas |
| :--- | :--- | :--- |
| **GetFinanciamiento** | Créditos otorgados (Demanda Real) | Organismo, Modalidad, Estado, Municipio |
| **GetCONAVI** | Subsidios federales directos | Línea de Apoyo, Modalidad, Municipio |
| **GetFOVISSSTE** | Créditos para trabajadores del Estado | Esquema de Crédito, Modalidad, Municipio |
| **GetINFONAVIT** | Créditos del instituto de los trabajadores | Línea de Crédito, Modalidad, Municipio |
| **GetCNBV** | Créditos hipotecarios de banca comercial | Segmento de valor, Modalidad, Municipio |
| **GetInsus** | Regularización de suelo sustentable | Rango de Edad, Género, Municipio |
| **GetRegistro** | Oferta proyectada en conjuntos habitacionales | PCU, Tipo Vivienda, Municipio |
| **GetInventario** | Viviendas en construcción/terminadas | PCU, Avance de Obra, Tipo Vivienda |
| **GetVerificacion** | Viviendas validadas físicamente | PCU, Superficie, Recámaras, Municipio |
| **GetProduccion** | Viviendas producidas y registradas | Tipo de Vivienda, PCU, Municipio |

---

## 4. Hallazgos de Limpieza (Data Cleaning Notes)
Durante el proceso de extracción, se detectaron las siguientes particularidades críticas para el análisis de datos:

1.  **Evolución del Esquema (CONAVI):** Los datos de CONAVI previos a 2018 no contienen la dimensión `linea_apoyo`, reflejando el cambio histórico en las reglas de operación de los programas federales.
2.  **Perímetros de Contención Urbana (PCU):** Los datos de `Inventario`, `Producción` y `Registro` incluyen la variable **PCU (U1, U2, U3)**. Esta será utilizada como el *feature* principal para medir la calidad de la ubicación urbana en el Sistema Recomendador.
3.  **Normalización de Nombres:** Los encabezados de las columnas fueron normalizados a minúsculas, eliminando espacios y caracteres especiales para asegurar la compatibilidad con librerías de Machine Learning en Python.

---

> **Estatus del Proyecto:** Extracción completa.
> **Fecha de cierre de datos:** 05 de abril de 2026.
> **Autor:** Cesar Omar Miguel Gonzalez.