import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import skew

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_DATOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def ejecutar_eda():
    print("Iniciando generación de gráficas EDA...")
    
    df = pd.read_csv(PATH_DATOS)
    cols_numericas = ['Precio_MXN', 'Superficie_m2', 'Recamaras', 'Banos']
    df_analisis = df.dropna(subset=cols_numericas).copy()

    # Skewness
    asimetria_precio = skew(df_analisis['Precio_MXN'])
    asimetria_superficie = skew(df_analisis['Superficie_m2'])
    print(f"Skewness - Precio: {asimetria_precio:.2f} | Superficie: {asimetria_superficie:.2f}")

    # Distribución y Log1p
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(df_analisis['Precio_MXN'], bins=50, kde=True, ax=axes[0], color='steelblue')
    axes[0].set_title('Distribución Original (Precio_MXN)')
    
    df_analisis['Precio_Log'] = np.log1p(df_analisis['Precio_MXN'])
    sns.histplot(df_analisis['Precio_Log'], bins=50, kde=True, ax=axes[1], color='seagreen')
    axes[1].set_title('Distribución Normalizada (Log1p)')
    plt.tight_layout()
    plt.savefig(os.path.join(DIR_BASE, "..", "data", "eda_1_distribucion_precio.png"), dpi=300)

    # Outliers (Regla IQR)
    Q1 = df_analisis['Precio_MXN'].quantile(0.25)
    Q3 = df_analisis['Precio_MXN'].quantile(0.75)
    IQR = Q3 - Q1
    limite_superior = Q3 + 1.5 * IQR
    
    outliers = df_analisis[df_analisis['Precio_MXN'] > limite_superior]
    pct_outliers = (len(outliers) / len(df_analisis)) * 100
    print(f"Límite IQR: ${limite_superior:,.2f} | Outliers: {len(outliers)} ({pct_outliers:.2f}%)")

    plt.figure(figsize=(10, 4))
    sns.boxplot(x=df_analisis['Precio_MXN'], color='lightcoral')
    plt.title('Dispersión y Valores Atípicos del Precio')
    plt.tight_layout()
    plt.savefig(os.path.join(DIR_BASE, "..", "data", "eda_2_outliers_boxplot.png"), dpi=300)

    # Matriz de Correlación
    matriz_corr = df_analisis[cols_numericas].corr()
    print("Generando matriz de correlación...")
    
    plt.figure(figsize=(7, 5))
    mask = np.triu(np.ones_like(matriz_corr, dtype=bool))
    sns.heatmap(matriz_corr, mask=mask, annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Matriz de Correlación')
    plt.tight_layout()
    plt.savefig(os.path.join(DIR_BASE, "..", "data", "eda_3_matriz_correlacion.png"), dpi=300)

    # Mapa de calor
    df_muestra_mapa = df_analisis.sample(n=min(50000, len(df_analisis)), random_state=42)
    
    plt.figure(figsize=(10, 7))
    sns.scatterplot(
        x=df_muestra_mapa['Longitud'], 
        y=df_muestra_mapa['Latitud'], 
        hue=df_muestra_mapa['Precio_Log'], 
        palette='magma', 
        s=15, 
        alpha=0.7,
        edgecolor=None
    )
    plt.title('Distribución Espacial de la Oferta (Log Precio)')
    plt.legend(title='Log(Precio)', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(DIR_BASE, "..", "data", "eda_4_mapa_plusvalia.png"), dpi=300)

    print("Proceso finalizado.")

if __name__ == "__main__":
    ejecutar_eda()