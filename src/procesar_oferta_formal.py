import pandas as pd
import os

# --- CONFIGURACIÓN DE RUTAS ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_ENTRADA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "raw", "sedatu"))
CARPETA_SALIDA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "processed"))

ARCHIVO_INVENTARIO = os.path.join(CARPETA_ENTRADA, "getinventario_nacional_20260405.csv")
ARCHIVO_PRODUCCION = os.path.join(CARPETA_ENTRADA, "getproduccion_nacional_20260405.csv")
ARCHIVO_SALIDA = os.path.join(CARPETA_SALIDA, "oferta_formal_pcu.csv")

def procesar_oferta_formal():
    print(f"\n{'='*65}\n🏗️ INICIANDO MOTOR DE COMPETENCIA FORMAL (INVENTARIO Y PRODUCCIÓN)\n{'='*65}")

    # 1. CARGA DE INVENTARIO (Viviendas en proceso / Obra)
    print("⏳ Cargando inventario en proceso...")
    try:
        df_inv = pd.read_csv(ARCHIVO_INVENTARIO, engine='python', on_bad_lines='skip')
        # Agrupar por Estado, Municipio y PCU
        inv_agrupado = df_inv.groupby(['estado', 'municipio', 'pcu'])['viviendas'].sum().reset_index()
        inv_agrupado.rename(columns={'viviendas': 'Viviendas_En_Proceso'}, inplace=True)
    except Exception as e:
        print(f"❌ Error leyendo Inventario: {e}")
        return

    # 2. CARGA DE PRODUCCIÓN (Viviendas Terminadas)
    print("⏳ Cargando producción histórica terminada...")
    try:
        # Aquí puedes filtrar por años recientes si lo deseas (ej. df_prod[df_prod['ano'] >= 2020])
        df_prod = pd.read_csv(ARCHIVO_PRODUCCION, engine='python', on_bad_lines='skip')
        prod_agrupado = df_prod.groupby(['estado', 'municipio', 'pcu'])['viviendas'].sum().reset_index()
        prod_agrupado.rename(columns={'viviendas': 'Viviendas_Terminadas'}, inplace=True)
    except Exception as e:
        print(f"❌ Error leyendo Producción: {e}")
        return

    # 3. FUSIÓN DE AMBOS MUNDOS (Outer Join para no perder polígonos)
    print("🧩 Fusionando bases de datos...")
    df_formal = pd.merge(inv_agrupado, prod_agrupado, on=['estado', 'municipio', 'pcu'], how='outer')
    
    # Llenar nulos con 0 (Ej. Zonas donde hay producción pero no inventario nuevo)
    df_formal.fillna({'Viviendas_En_Proceso': 0, 'Viviendas_Terminadas': 0}, inplace=True)
    
    # CÁLCULO MAESTRO: Densidad de Competencia
    df_formal['Total_Competencia_Formal'] = df_formal['Viviendas_En_Proceso'] + df_formal['Viviendas_Terminadas']

    # 4. LIMPIEZA PARA EL JOIN FUTURO
    print("🧹 Estandarizando textos para cruce espacial...")
    # Convertimos todo a mayúsculas y quitamos espacios extra para que cruce perfecto con tu Web Scraping
    for col in ['estado', 'municipio', 'pcu']:
        if col in df_formal.columns:
            df_formal[col] = df_formal[col].astype(str).str.strip().str.upper()

    # 5. GUARDAR RESULTADO
    df_formal.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8-sig')
    print(f"✅ Proceso terminado exitosamente.")
    print(f"💾 Archivo de Competencia Formal guardado en: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    procesar_oferta_formal()