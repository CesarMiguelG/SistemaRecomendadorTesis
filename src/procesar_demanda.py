import pandas as pd
import os
import numpy as np

# --- CONFIGURACIÓN DE RUTAS ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
# Ruta actualizada apuntando a sedatu
CARPETA_ENTRADA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "raw", "sedatu"))
CARPETA_SALIDA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "processed"))

os.makedirs(CARPETA_SALIDA, exist_ok=True)

ARCHIVO_FINANCIAMIENTO = os.path.join(CARPETA_ENTRADA, "getfinanciamiento_nacional_20260405.csv")
ARCHIVO_INSUS = os.path.join(CARPETA_ENTRADA, "getinsus_nacional_20260405.csv")
ARCHIVO_SALIDA = os.path.join(CARPETA_SALIDA, "demanda_municipal_consolidada.csv")

def procesar_demanda():
    print(f"\n{'='*65}\n📈 INICIANDO MOTOR DE DEMANDA (API SNIIV)\n{'='*65}")

    # 1. CARGA DE DATOS FINANCIEROS (El Dinero)
    print("⏳ Cargando histórico de financiamiento (2015-2025)...")
    try:
        df_fin = pd.read_csv(ARCHIVO_FINANCIAMIENTO, dtype={'clave_estado': str, 'clave_municipio': str})
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo en {ARCHIVO_FINANCIAMIENTO}")
        return
    
    # Limpiar datos no geolocalizados
    df_fin = df_fin[(df_fin['estado'] != 'No distribuido') & (df_fin['municipio'] != 'No distribuido')]

    # Agrupar por municipio sumando todo el dinero y acciones de la década
    demanda_muni = df_fin.groupby(['clave_estado', 'estado', 'clave_municipio', 'municipio']).agg(
        Total_Creditos=('acciones', 'sum'),
        Total_Monto_MXN=('monto', 'sum')
    ).reset_index()

    # CÁLCULO MAESTRO: Ticket Promedio
    demanda_muni['Ticket_Promedio_MXN'] = np.where(
        demanda_muni['Total_Creditos'] > 0, 
        demanda_muni['Total_Monto_MXN'] / demanda_muni['Total_Creditos'], 
        0
    )
    
    # Redondear para no tener decimales
    demanda_muni['Ticket_Promedio_MXN'] = demanda_muni['Ticket_Promedio_MXN'].round(2)
    print(f"✅ Ticket Promedio calculado para {len(demanda_muni)} municipios.")

    # 2. CARGA DE DATOS SOCIODEMOGRÁFICOS (Brecha de Género)
    print("⏳ Cargando datos sociodemográficos INSUS...")
    if os.path.exists(ARCHIVO_INSUS):
        df_insus = pd.read_csv(ARCHIVO_INSUS, dtype={'clave_estado': str, 'clave_municipio': str})
        df_insus = df_insus[(df_insus['estado'] != 'No distribuido') & (df_insus['municipio'] != 'No distribuido')]
        
        # Separar en dos DataFrames: Mujeres y Hombres
        mujeres = df_insus[df_insus['sexo'] == 'Mujer'].groupby(['clave_estado', 'clave_municipio']).agg(
            Creditos_Mujer=('acciones', 'sum')
        ).reset_index()
        
        hombres = df_insus[df_insus['sexo'] == 'Hombre'].groupby(['clave_estado', 'clave_municipio']).agg(
            Creditos_Hombre=('acciones', 'sum')
        ).reset_index()

        # Unir los datos de género a nuestra tabla principal
        demanda_muni = demanda_muni.merge(mujeres, on=['clave_estado', 'clave_municipio'], how='left')
        demanda_muni = demanda_muni.merge(hombres, on=['clave_estado', 'clave_municipio'], how='left')
        
        demanda_muni.fillna({'Creditos_Mujer': 0, 'Creditos_Hombre': 0}, inplace=True)
        
        # CÁLCULO MAESTRO 2: Porcentaje de Participación Femenina
        demanda_muni['Total_Creditos_Genero'] = demanda_muni['Creditos_Mujer'] + demanda_muni['Creditos_Hombre']
        demanda_muni['Pct_Creditos_Mujeres'] = np.where(
            demanda_muni['Total_Creditos_Genero'] > 0,
            (demanda_muni['Creditos_Mujer'] / demanda_muni['Total_Creditos_Genero']) * 100,
            0
        ).round(2)
        
        print("✅ Brecha de género calculada e integrada.")
        demanda_muni.drop(columns=['Total_Creditos_Genero'], inplace=True)
    else:
        print(f"⚠️ Archivo INSUS no encontrado en {ARCHIVO_INSUS}. Saltando módulo de género.")

    # 3. GUARDAR EL DATASET MAESTRO
    demanda_muni.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8-sig')
    print(f"\n🎉 ¡Proceso Terminado!")
    print(f"💾 Base de Demanda guardada en: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    procesar_demanda()