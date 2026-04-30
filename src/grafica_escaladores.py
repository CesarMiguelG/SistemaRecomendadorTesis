import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
import os
import warnings

warnings.filterwarnings('ignore')

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_DATOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def graficar_escaladores():
    print("Iniciando generación de gráfica de escaladores...")
    
    df = pd.read_csv(PATH_DATOS).dropna(subset=['Superficie_m2'])
    X = df[['Superficie_m2']]
    
    mm_scaler = MinMaxScaler()
    ss_scaler = StandardScaler()
    rs_scaler = RobustScaler()
    
    df['MinMax'] = mm_scaler.fit_transform(X)
    df['ZScore'] = ss_scaler.fit_transform(X)
    df['Robust'] = rs_scaler.fit_transform(X)
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 4, figsize=(22, 6))
    fig.suptitle('Impacto de Outliers en Técnicas de Escalamiento (Superficie m²)', fontsize=18, fontweight='bold', y=1.05)
    
    limite_superior_normal = X['Superficie_m2'].quantile(0.95)
    
    # 1. Original
    sns.histplot(data=df[df['Superficie_m2'] < limite_superior_normal], x='Superficie_m2', bins=50, ax=axes[0], color='#4C72B0', kde=True)
    axes[0].set_title('Original (Acotado P95)', fontweight='bold')
    axes[0].set_xlabel('Superficie (m²)')
    axes[0].set_ylabel('Frecuencia')
    
    # 2. Min-Max
    sns.histplot(data=df, x='MinMax', bins=100, ax=axes[1], color='#DD8452', kde=False)
    axes[1].set_xlim(-0.000001, 0.0001)
    axes[1].set_title('Min-Max Scaling', fontweight='bold')
    axes[1].set_xlabel('Valor Escala [0, 1]')
    
    # 3. Z-Score
    sns.histplot(data=df, x='ZScore', bins=1000, ax=axes[2], color='#55A868', kde=False)
    axes[2].set_xlim(-0.05, 0.05)
    axes[2].set_title('Z-Score (StandardScaler)', fontweight='bold')
    axes[2].set_xlabel('Desviaciones Estándar')
    
    # 4. Robust Scaling
    sns.histplot(data=df[df['Superficie_m2'] < limite_superior_normal], x='Robust', bins=50, ax=axes[3], color='#937860', kde=True)
    axes[3].set_title('Robust Scaling', fontweight='bold')
    axes[3].set_xlabel('Rango Intercuartílico (Mediana=0)')
    
    plt.tight_layout()
    ruta_img = os.path.join(DIR_BASE, "..", "data", "comparativa_escaladores_corregida.png")
    plt.savefig(ruta_img, dpi=300, bbox_inches='tight')
    print(f"Proceso finalizado. Gráfica guardada en: {ruta_img}")

if __name__ == "__main__":
    graficar_escaladores()