# 🏡 Sistema Recomendador para la Mitigación del Rezago Habitacional en México (2015-2026)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Playwright](https://img.shields.io/badge/Playwright-Web%20Scraping-green.svg)
![SEDATU/SNIIV](https://img.shields.io/badge/API-SEDATU%20%7C%20SNIIV-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-yellow.svg)

## 📌 Descripción del Proyecto
Este proyecto de **Maestría en Ciencia de Datos** aborda la desconexión crítica entre la oferta inmobiliaria privada y la demanda social efectiva en México. Mediante un enfoque de **Analítica Prescriptiva**, el sistema identifica brechas de asequibilidad y sugiere zonas óptimas para el desarrollo habitacional.

La innovación técnica reside en un **Motor Híbrido de Adquisición de Datos** que cruza el inventario institucional del Gobierno Federal con la dinámica de precios en tiempo real del mercado abierto capturada vía scraping.

---

## ⚙️ Arquitectura y Pipeline de Datos (Nivel 9)
El proyecto implementa un pipeline de datos robusto capaz de gestionar y procesar +200,000 registros:

1.  **Extracción de Demanda (CuboAPI SNIIV):** Orquestador dinámico que consume 10 endpoints oficiales (INFONAVIT, FOVISSSTE, CONAVI, INSUS, etc.). Implementa lógica de *Chunking temporal* y manejo de *snapshots* de inventario.
2.  **Extracción de Oferta (Web Scraping):** Motor de alto rendimiento desarrollado con **Playwright**, optimizado para los 32 estados de la república con:
    * Deduplicación por *hashing* de URLs en memoria RAM.
    * Sistema de reanudación automática (*Checkpointing*) basado en archivos físicos.
    * Radar dinámico para detección de fin de inventario.
3.  **Feature Engineering:** Modelado avanzado basado en los **Perímetros de Contención Urbana (PCU)**, niveles salariales en UMA y superficies de construcción.
4.  **Machine Learning:** Algoritmo de similitud vectorial (Content-Based Filtering) para detectar el "Market Fit" entre el poder adquisitivo y la oferta disponible.

---

## 📂 Estructura del Repositorio
```text
SistemaRecomendadorTesis/
│
├── docs/                    # Documentación técnica y diccionarios de datos
│   ├── REPORTE_TECNICO_SNIIV.md     # Metodología de la CuboAPI
│   └── REPORTE_TECNICO_SCRAPING.md  # Metodología del Scraper Playwright
│
├── src/                     # Código fuente (Python)
│   ├── data_extraction.py   # Orquestador Maestro de APIs SEDATU
│   ├── scraper_engine.py    # Motor de Scraping (Nivel 8.3)
│   └── data_cleaning.py     # Limpieza y homologación (EDA)
│
├── data/                    # Almacenamiento local (Ignorado en Git)
│   ├── raw/
│   │   ├── sedatu/          # 10 Datasets nacionales oficiales consolidadores
│   │   └── estados/         # Oferta privada de los 32 estados (.csv)
│
└── notebooks/               # Jupyter Notebooks para análisis exploratorio