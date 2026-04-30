import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
import os

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_ENTRADA = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))
PATH_SALIDA = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "dataset_escalado.csv"))

def ejecutar_escalamiento():
    print("Iniciando normalización y escalamiento robusto...")
    df = pd.read_csv(PATH_ENTRADA)
    
    # Transformación logarítmica
    df['Precio_Log'] = np.log1p(df['Precio_MXN'])
    
    # Selección de variables estructurales
    cols_a_escalar = ['Superficie_m2', 'Recamaras', 'Banos']
    
    # Escalamiento
    scaler = RobustScaler()
    df[cols_a_escalar] = scaler.fit_transform(df[cols_a_escalar])
    
    # Exportación (se descarta Precio_MXN para evitar data leakage)
    df_final = df.drop(columns=['Precio_MXN'])
    df_final.to_csv(PATH_SALIDA, index=False, encoding='utf-8-sig')
    
    print(f"Proceso completado. Dataset guardado en: {PATH_SALIDA}")
    print("Muestra de datos escalados:")
    print(df_final[cols_a_escalar].head())

if __name__ == "__main__":
    ejecutar_escalamiento()