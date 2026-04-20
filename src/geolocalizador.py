import pandas as pd
import re
import os
import sys

# --- RUTAS DE ARCHIVOS ---
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_MAESTRO = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_limpia.csv"))
PATH_GEONAMES = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "external", "MX.txt"))
PATH_FINAL = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def extraer_cp(u):
    if pd.isna(u): return None
    match = re.search(r'\b(\d{5})\b', str(u))
    return match.group(1) if match else None

def normalizar_texto(texto):
    """Limpia tildes y caracteres para comparar estados correctamente."""
    if pd.isna(texto): return ""
    a,b = 'áéíóúüñ','aeiouun'
    trans = str.maketrans(a,b)
    return str(texto).lower().translate(trans).strip()

def ejecucion_turbo_validada():
    print(f"\n{'='*70}\n🚀 GEO-VALIDADOR TURBO (OFFLINE)\n{'='*70}")
    
    # 1. Cargar el Diccionario de Coordenadas (MX.txt)
    print("📖 Cargando MX.txt de GeoNames...")
    # Columnas: 1:CP, 3:Estado, 5:Municipio, 9:Latitud, 10:Longitud
    df_geo = pd.read_csv(PATH_GEONAMES, sep='\t', header=None, dtype={1: str})
    df_geo = df_geo[[1, 3, 5, 9, 10]]
    df_geo.columns = ['cp_ref', 'Estado_Geo', 'Municipio_Geo', 'Latitud', 'Longitud']
    
    # Nos quedamos con un solo CP para evitar duplicados en el merge
    df_geo = df_geo.drop_duplicates(subset=['cp_ref'])

    # 2. Cargar tu Dataset de la Tesis
    print("📖 Cargando dataset maestro...")
    df_tesis = pd.read_csv(PATH_MAESTRO)
    
    # 3. Extraer CP de los anuncios
    print("🧹 Extrayendo códigos postales...")
    df_tesis['cp_extraido'] = df_tesis['Ubicacion'].apply(extraer_cp)
    
    # 4. CRUCE MASIVO (Merge)
    print("🧩 Realizando cruce de datos...")
    df_merged = pd.merge(
        df_tesis, 
        df_geo, 
        left_on='cp_extraido', 
        right_on='cp_ref', 
        how='left'
    )
    
    # 5. VALIDACIÓN DE SEGURIDAD (Estado vs Estado)
    print("🛡️  Validando coincidencia de Estados...")
    
    # Creamos una máscara de validación
    # Comparamos el estado que tú tienes con el que Geonames dice que pertenece ese CP
    df_merged['Edo_Match'] = df_merged.apply(
        lambda r: normalizar_texto(r['Estado']) in normalizar_texto(r['Estado_Geo']) 
        if pd.notna(r['Estado_Geo']) else False, axis=1
    )

    # 6. Separar Datos Válidos de Errores
    df_final = df_merged[df_merged['Edo_Match'] == True].copy()
    errores = df_merged[df_merged['Edo_Match'] == False].copy()

    # 7. Reporte de Calidad para la Tesis
    total = len(df_tesis)
    validos = len(df_final)
    fallas_cp = df_merged['Latitud'].isna().sum()
    fallas_edo = len(errores) - fallas_cp
    
    print(f"\n{'='*40}")
    print(f"📊 RESULTADOS DE CALIDAD GEOGRÁFICA")
    print(f"✅ Registros Válidos: {validos:,} ({validos/total:.1%})")
    print(f"❌ CP no encontrado: {fallas_cp:,}")
    print(f"⚠️ Estado no coincide: {fallas_edo:,} (CPs de otros estados)")
    print(f"{'='*40}")

    # 8. Limpieza final y guardado
    # Mantenemos las columnas de Municipio_Geo para tu modelo
    columnas_a_quitar = ['cp_extraido', 'cp_ref', 'Edo_Match', 'Estado_Geo']
    df_final.drop(columns=columnas_a_quitar).to_csv(PATH_FINAL, index=False, encoding='utf-8-sig')
    
    print(f"💾 Dataset Blindado guardado en: {PATH_FINAL}")

if __name__ == "__main__":
    ejecucion_turbo_validada()