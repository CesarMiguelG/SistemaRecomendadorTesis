import pandas as pd
import os

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_SEDATU = r"C:\SegundoSemestre\Proyecto Aplicado\tesis_final\SistemaRecomendadorTesis\data\raw\sedatu"

ARCHIVO_FINANCIAMIENTO = os.path.join(PATH_SEDATU, "getfinanciamiento_nacional_20260405.csv")
ARCHIVO_REGISTRO = os.path.join(PATH_SEDATU, "getregistro_nacional_20260405.csv")

def analizar_umbrales_oficiales():
    print("Iniciando análisis de umbrales SNIIV/SEDATU...")
    
    # 1. Análisis de Registro (RUV)
    print("Procesando Registro (RUV)...")
    try:
        df_reg = pd.read_csv(ARCHIVO_REGISTRO, encoding='utf-8')
        cols_segmento = [c for c in df_reg.columns if 'segmento' in c.lower() or 'valor' in c.lower()]
        
        if cols_segmento:
            col_seg = cols_segmento[0]
            print(f"Segmentación basada en: {col_seg}")
            dist_reg = df_reg[col_seg].value_counts(normalize=True) * 100
            print(dist_reg.round(2))
        else:
            print(f"Columnas disponibles: {list(df_reg.columns)}")
    except Exception as e:
        print(f"Error procesando Registro: {e}")

    # 2. Análisis de Financiamiento
    print("\nProcesando Financiamientos...")
    try:
        df_fin = pd.read_csv(ARCHIVO_FINANCIAMIENTO, encoding='utf-8')
        
        cols_monto = [c for c in df_fin.columns if 'monto' in c.lower()]
        cols_segmento_fin = [c for c in df_fin.columns if 'segmento' in c.lower() or 'valor' in c.lower() or 'linea' in c.lower()]
        
        if cols_monto and cols_segmento_fin:
            col_m = cols_monto[0]
            col_s = cols_segmento_fin[0]
            
            df_analisis = df_fin.dropna(subset=[col_m, col_s])
            resumen = df_analisis.groupby(col_s)[col_m].agg(['count', 'mean', 'min', 'max']).round(2)
            
            resumen['mean_MXN'] = resumen['mean'].apply(lambda x: f"${x:,.2f}")
            print(f"Resumen por '{col_s}' y '{col_m}':")
            print(resumen[['count', 'mean_MXN']])
        else:
            print("No se detectaron columnas exactas de segmentación/monto. Muestra:")
            print(df_fin.head(2))
            
    except Exception as e:
        print(f"Error procesando Financiamiento: {e}")

if __name__ == "__main__":
    analizar_umbrales_oficiales()