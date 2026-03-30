# 🏡 Sistema Recomendador para la Mitigación del Rezago Habitacional en México (2015-2025)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Machine%20Learning-orange.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-lightgrey.svg)
![LaTeX](https://img.shields.io/badge/LaTeX-Academic%20Writing-green.svg)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-yellow.svg)

## 📌 Descripción del Proyecto
El mercado habitacional en México enfrenta un "Trilema" sistémico: precios al alza, elitización de la oferta y un rezago social persistente. Este proyecto de **Maestría en Ciencia de Datos** busca resolver la desconexión entre la construcción de vivienda y la demanda efectiva mediante **Analítica Prescriptiva**.

El objetivo principal es construir un **Sistema Recomendador Multicriterio** que consuma de manera automatizada grandes volúmenes de datos abiertos de las APIs del Gobierno Federal (SEDATU/SNIIV) para sugerir zonas geográficas óptimas y segmentos de vivienda prioritarios, apoyando la toma de decisiones estratégicas tanto para desarrolladores privados como para la asignación de subsidios públicos.

## ⚙️ Arquitectura y Pipeline de Datos
El proyecto está estructurado en las siguientes fases técnicas:
1. **ETL (Extracción, Transformación y Carga):** Conexión automatizada a las APIs RESTful del Cubo de Financiamientos del SNIIV (INFONAVIT, FOVISSSTE, CNBV).
2. **Feature Engineering:** Cálculo espacial de la "Brecha de Asequibilidad" cruzando el Ticket Promedio hipotecario contra los rangos salariales reales y los Perímetros de Contención Urbana (PCU).
3. **Machine Learning:** Implementación de un algoritmo de **Filtrado Basado en Contenido (Content-Based Filtering)** utilizando métricas de similitud vectorial para emitir recomendaciones territoriales.

## 📂 Estructura del Repositorio
```text
SistemaRecomendadorTesis/
│
├── protocolo/               # Documento de protocolo de tesis escrito en LaTeX
│   ├── protocolo_tesis.tex  # Código fuente del documento
│   └── referencias.bib      # Base de datos bibliográfica (Formato APA)
│
├── src/                     # Código fuente en Python
│   ├── data_extraction.py   # Scripts de conexión a las APIs del SNIIV
│   ├── data_cleaning.py     # Limpieza y transformación de JSON a DataFrames
│   └── recommender.py       # Algoritmo de recomendación con scikit-learn
│
├── notebooks/               # Jupyter Notebooks para EDA (Análisis Exploratorio)
│
├── data/                    # (Ignorado en git) Datasets crudos y procesados
│
├── .gitignore               # Reglas de exclusión para entornos virtuales y datos pesados
└── README.md                # Este archivo