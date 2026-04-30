import pandas as pd
import os

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_FINANCIAMIENTO = os.path.join(DIR_BASE, "..", "data", "raw", "sedatu", "getfinanciamiento_nacional_20260405.csv")

def analizar_evolucion_temporal():
    print("Iniciando análisis temporal de financiamiento...")
    
    try:
        df = pd.read_csv(ARCHIVO_FINANCIAMIENTO)
        
        df_valid = df[(df['acciones'] > 0) & (df['monto'] > 0)]
        
        resumen_anual = df_valid.groupby('ano').agg(
            total_acciones=('acciones', 'sum'),
            total_monto=('monto', 'sum')
        ).reset_index()
        
        resumen_anual['monto_promedio'] = resumen_anual['total_monto'] / resumen_anual['total_acciones']
        
        resumen_anual['Monto Promedio'] = resumen_anual['monto_promedio'].apply(lambda x: f"${x:,.2f} MXN")
        resumen_anual['Total Acciones'] = resumen_anual['total_acciones'].apply(lambda x: f"{x:,.0f}")
        
        print("\nCosto Promedio de la Vivienda Financiada por Año:")
        print(resumen_anual[['ano', 'Total Acciones', 'Monto Promedio']].to_string(index=False))
        
    except Exception as e:
        print(f"Error procesando el archivo: {e}")

if __name__ == "__main__":
    analizar_evolucion_temporal()