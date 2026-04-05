# 🗺️ Master Roadmap: Sistema Recomendador para Mitigación del Rezago Habitacional

## FASE 1: Fundamentos y Setup (Completado) 🏁
- [x] Definición del problema ("Trilema" habitacional).
- [x] Redacción del Protocolo (Antecedentes, Planteamiento, Objetivos, Marco Teórico).
- [x] Configuración de entorno local: VS Code, Git, GitHub y entorno virtual (`.venv`).
- [x] Configuración de bibliografía (APA) y compilación en LaTeX.

## FASE 2: Ingeniería de Datos (Pipeline ETL) 🛠️
*Objetivo: Consumir, limpiar y estructurar los datos crudos en un formato de alto rendimiento.*
- [ ] **Extracción (Extract):**
  - [ ] Escribir script `data_extraction.py` para conectar a las APIs del SNIIV (`requests`).
  - [ ] Manejar la paginación o límites de descarga de la API para obtener el histórico completo (2015-2025).
  - [ ] Extraer catálogos de claves (Estados, Municipios, Segmentos UMA, PCUs).
- [ ] **Transformación (Transform):**
  - [ ] Parsear las respuestas JSON y aplanarlas en DataFrames de `pandas`.
  - [ ] Limpieza de datos: Identificar y tratar valores nulos (NaN) o atípicos (outliers) en precios y subsidios.
  - [ ] Estandarización de tipos de datos: Convertir fechas a `datetime`, montos a `float`, claves a `int`.
- [ ] **Carga (Load):**
  - [ ] Guardar el dataset consolidado en formato `.parquet` o `.csv` optimizado dentro de la carpeta `/data` (asegurando que esté en el `.gitignore`).

## FASE 3: Feature Engineering y Análisis Exploratorio (EDA) 📊
*Objetivo: Crear las variables matemáticas que alimentarán al modelo y descubrir patrones ocultos.*
- [ ] Configurar un Jupyter Notebook (`exploracion_inicial.ipynb`).
- [ ] **Análisis Descriptivo:**
  - [ ] Graficar la serie de tiempo del volumen de créditos vs. el Ticket Promedio (2015-2025).
  - [ ] Mapear la contracción de la vivienda económica (m² y recámaras) frente al crecimiento residencial.
- [ ] **Feature Engineering (Creación de variables):**
  - [ ] Calcular la **"Brecha de Asequibilidad"** por municipio (Ticket Promedio / Salario Promedio).
  - [ ] Codificar variables categóricas (One-Hot Encoding para Estados y Segmentos).
  - [ ] Normalizar/Estandarizar variables numéricas (usando `MinMaxScaler` o `StandardScaler` de Scikit-learn).
  - [ ] Integrar el factor espacial: Ponderar zonas según su Perímetro de Contención Urbana (PCU).

## FASE 4: Modelado del Sistema Recomendador (Machine Learning) 🧠
*Objetivo: Traducir los datos en recomendaciones prescriptivas.*
- [ ] **Definición de Perfiles:**
  - [ ] Construir la Matriz de "Perfil de Usuario" (Representa la capacidad financiera y necesidad social de una región o grupo demográfico).
  - [ ] Construir la Matriz de "Perfil de Ítem" (Representa las características de la vivienda y su ubicación).
- [ ] **Desarrollo del Algoritmo (`recommender.py`):**
  - [ ] Implementar un modelo de **Filtrado Basado en Contenido (Content-Based Filtering)**.
  - [ ] Utilizar métricas de similitud vectorial (Ej. *Similitud del Coseno* o *Distancia Euclidiana* vía `scikit-learn`).
  - [ ] Programar la lógica multicriterio: Penalizar recomendaciones en zonas de alta segregación (fuera de PCU) y premiar zonas con alto déficit pero viabilidad económica.
- [ ] **Función de Salida (Output):**
  - [ ] Crear una función que reciba parámetros (ej. Estado: Baja California, Presupuesto Objetivo: $X) y devuelva el Top 5 de municipios y segmentos de vivienda a desarrollar.

## FASE 5: Validación y Backtesting 🧪
*Objetivo: Demostrar matemáticamente que las recomendaciones del modelo son precisas y útiles.*
- [ ] Dividir el dataset cronológicamente (Entrenar con 2015-2023, validar con 2024-2025).
- [ ] Definir métricas de evaluación para el recomendador (Ej. *Precision@K*, *Recall@K*, o Cobertura).
- [ ] Contrastar empíricamente: ¿El modelo recomienda construir donde realmente hubo éxito de absorción, o advierte contra zonas donde hubo abandono de vivienda?

## FASE 6: Despliegue e Interfaz (El "Wow Factor") 🚀 (Opcional pero recomendado)
*Objetivo: Crear un prototipo interactivo para la presentación de la tesis.*
- [ ] Instalar `Streamlit`.
- [ ] Crear un script `app.py` que levante una interfaz web local.
- [ ] Agregar *sliders* (deslizadores) para ajustar el presupuesto y menús desplegables para seleccionar el Estado.
- [ ] Mostrar las recomendaciones del modelo en un mapa interactivo (usando `folium` o `plotly`).

## FASE 7: Redacción Final de la Tesis (LaTeX) ✍️
*Objetivo: Documentar el rigor científico del proyecto.*
- [ ] **Capítulo 1 e Introducción:** Expandir el Protocolo actual.
- [ ] **Capítulo 2 - Metodología:** Explicar a detalle la arquitectura del ETL, las matemáticas de la Similitud del Coseno y las decisiones de Feature Engineering.
- [ ] **Capítulo 3 - Desarrollo y Resultados:** Mostrar visualizaciones del EDA, métricas de rendimiento del modelo y casos de uso prácticos (Ej. El contraste Tijuana vs. Tabasco).
- [ ] **Capítulo 4 - Conclusiones y Trabajo Futuro:** Reflexión sobre el impacto de la herramienta en políticas públicas.
- [ ] Compilación final, revisión de ortografía y ajuste de la bibliografía APA.

## FASE 8: Preparación para la Defensa 🎓
- [ ] Extraer las gráficas clave para la presentación.
- [ ] Diseñar diapositivas (Puede ser en PowerPoint o usando Beamer en LaTeX).
- [ ] Ensayo del flujo: Problema -> Datos -> Algoritmo -> Solución (Demo del sistema).