import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
import os

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.1)

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_DATOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def ejecutar_comparacion():
    print("Iniciando comparativa de algoritmos de escalamiento...")
    
    df = pd.read_csv(PATH_DATOS)
    df_clean = df.dropna(subset=['Superficie_m2']).copy()
    X = df_clean[['Superficie_m2']]
    
    scalers = {
        'Original': None,
        'Min-Max Scaling': MinMaxScaler(),
        'Z-Score (StandardScaler)': StandardScaler(),
        'Robust Scaling': RobustScaler()
    }
    
    resultados = {'Original': X['Superficie_m2'].values}
    
    for nombre, scaler in scalers.items():
        if scaler is not None:
            resultados[nombre] = scaler.fit_transform(X).flatten()

    df_resultados = pd.DataFrame(resultados)
    
    print("\nEstadísticas descriptivas post-escalamiento (Superficie_m2):")
    print("-" * 50)
    for col in df_resultados.columns:
        desc = df_resultados[col].describe()
        print(f"Método: {col}")
        print(f"  Mínimo: {desc['min']:.6f} | Máximo: {desc['max']:.6f}")
        print(f"  Media:  {desc['mean']:.6f} | Mediana: {desc['50%']:.6f}")
        print(f"  Std:    {desc['std']:.6f}")
        print("-" * 50)

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    fig.suptitle('Impacto de Outliers en Técnicas de Escalamiento (Superficie m²)')
    
    for ax, col in zip(axes, df_resultados.columns):
        p95 = np.percentile(df_resultados[col].dropna(), 95)
        p05 = np.percentile(df_resultados[col].dropna(), 5)
        
        # Usamos histogramas acotados para evitar el colapso visual del KDE con outliers extremos
        sns.histplot(data=df_resultados, x=col, ax=ax, bins=50, kde=True, 
                     color='indigo' if col == 'Robust Scaling' else 'steelblue')
        
        ax.set_title(col)
        ax.set_xlim(p05, p95)
        ax.set_xlabel('Valor')
        ax.set_ylabel('Frecuencia')
    
    plt.tight_layout()
    ruta_img = os.path.join(DIR_BASE, "..", "data", "comparativa_escaladores.png")
    plt.savefig(ruta_img, dpi=300, bbox_inches='tight')
    print(f"\nProceso finalizado. Gráfica guardada en: {ruta_img}")

if __name__ == "__main__":
    ejecutar_comparacion()