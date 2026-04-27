import pandas as pd
import numpy as np
import re
import os

# --- RUTAS DE ARCHIVOS ---
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_MAESTRO = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_limpia.csv"))
PATH_GEONAMES = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "external", "MX.txt"))
PATH_FINAL = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))
PATH_ERRORES = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "geocodificacion_errores.csv"))

def normalizar_texto_mejorado(texto):
    if pd.isna(texto): return ""
    a,b = 'áéíóúüñ','aeiouun'
    trans = str.maketrans(a,b)
    t = str(texto).lower().translate(trans).replace("-", " ").strip()
    if t == "distrito federal": t = "ciudad de mexico"
    return t

def extraer_cp_mejorado(u):
    if pd.isna(u): return None
    t = str(u).lower()
    patron = re.search(r'(?:c\.?p\.?|codigo postal)\s*:?\s*(\d{5})', t)
    if patron: return patron.group(1)
    
    todos = re.findall(r'\b(\d{5})\b', t)
    if todos: return todos[-1]
    return None

def ejecucion_maxima_precision():
    print(f"\n{'='*70}\n🚀 GEO-VALIDADOR MAX (DOBLE MOTOR: CP + MUNICIPIO)\n{'='*70}")
    
    # 1. Cargar GeoNames
    columnas_geonames = ['c1', 'postal_code', 'c3', 'admin_name1', 'c5', 'admin_name2', 'c7', 'c8', 'c9', 'latitude', 'longitude', 'c12']
    df_geo = pd.read_csv(PATH_GEONAMES, sep='\t', names=columnas_geonames, dtype={'postal_code': str})
    
    df_geo = df_geo[['postal_code', 'admin_name1', 'admin_name2', 'latitude', 'longitude']]
    df_geo.columns = ['cp_ref', 'Estado_Geo', 'Municipio_Geo', 'Latitud', 'Longitud']
    
    df_geo['Edo_Norm'] = df_geo['Estado_Geo'].apply(normalizar_texto_mejorado)
    df_geo['Mun_Norm'] = df_geo['Municipio_Geo'].apply(normalizar_texto_mejorado)

    # DICCIONARIO 1: Por CP
    dict_cp = df_geo.drop_duplicates(subset=['cp_ref']).drop(columns=['Edo_Norm', 'Mun_Norm'])
    
    # DICCIONARIO 2: Por Municipio
    dict_mun = df_geo.groupby(['Edo_Norm', 'Mun_Norm']).agg({
        'Latitud': 'mean', 
        'Longitud': 'mean', 
        'Municipio_Geo': 'first'
    }).reset_index()

    # 2. Cargar Dataset Maestro
    df_tesis = pd.read_csv(PATH_MAESTRO)
    df_tesis['cp_extraido'] = df_tesis['Ubicacion'].apply(extraer_cp_mejorado)
    df_tesis['Edo_Norm'] = df_tesis['Estado'].apply(normalizar_texto_mejorado)
    
    # 3. Fase 1: Cruce por Código Postal
    print("🧩 Fase 1: Geolocalizando por Código Postal...")
    df_merged = pd.merge(df_tesis, dict_cp, left_on='cp_extraido', right_on='cp_ref', how='left')
    
    # 4. Validar Fase 1
    def es_valido_cp(row):
        if pd.isna(row['Latitud']): return False
        edo_geo = normalizar_texto_mejorado(row['Estado_Geo'])
        return row['Edo_Norm'] in edo_geo or edo_geo in row['Edo_Norm']

    df_merged['Valido_CP'] = df_merged.apply(es_valido_cp, axis=1)

    # 5. Fase 2: Rescate por Municipio para los que fallaron
    print("🚑 Fase 2: Activando Rescate por Municipio (Fallback)...")
    
    def rescatar_por_municipio(row):
        if row['Valido_CP']: return row
        
        ubicacion_limpia = normalizar_texto_mejorado(row['Ubicacion'])
        muns_del_estado = dict_mun[dict_mun['Edo_Norm'] == row['Edo_Norm']]
        
        nombres_mun = muns_del_estado['Mun_Norm'].tolist()
        nombres_mun.sort(key=len, reverse=True)
        
        for mun_nombre in nombres_mun:
            patron = r'\b' + re.escape(mun_nombre) + r'\b'
            if re.search(patron, ubicacion_limpia):
                datos_rescatados = muns_del_estado[muns_del_estado['Mun_Norm'] == mun_nombre].iloc[0]
                row['Latitud'] = datos_rescatados['Latitud']
                row['Longitud'] = datos_rescatados['Longitud']
                row['Municipio_Geo'] = datos_rescatados['Municipio_Geo']
                row['Rescatado'] = True
                return row
        return row

    df_merged['Rescatado'] = False
    df_final = df_merged.apply(rescatar_por_municipio, axis=1)

    # 6. Estadísticas Finales
    exito_cp = df_final['Valido_CP'].sum()
    exito_mun = df_final['Rescatado'].sum()
    totales_validos = exito_cp + exito_mun
    errores_absolutos = len(df_tesis) - totales_validos
    
    print(f"\n{'='*40}")
    print(f"📊 RESULTADOS DE GEOCODIFICACIÓN")
    print(f"✅ Válidos por Código Postal: {exito_cp:,}")
    print(f"🚑 Rescatados por Municipio : {exito_mun:,}")
    print(f"🏆 Dataset Final            : {totales_validos:,} ({totales_validos/len(df_tesis):.2%})")
    print(f"❌ Errores irrecuperables   : {errores_absolutos:,}")
    print(f"{'='*40}")

    # 7. SEPARAR, LIMPIAR Y GUARDAR
    columnas_limpiar = ['cp_extraido', 'cp_ref', 'Estado_Geo', 'Edo_Norm', 'Mun_Norm', 'Valido_CP', 'Rescatado']
    columnas_existentes = [c for c in columnas_limpiar if c in df_final.columns]
    
    # 7a. Guardar el Dataset Limpio para Machine Learning
    df_dataset_limpio = df_final[df_final['Latitud'].notna()].copy()
    df_dataset_limpio.drop(columns=columnas_existentes).to_csv(PATH_FINAL, index=False, encoding='utf-8-sig')
    
    # 7b. Guardar el Reporte de Errores
    df_errores = df_final[df_final['Latitud'].isna()].copy()
    if not df_errores.empty:
        df_errores['Diagnostico'] = "FALLO_TOTAL: CP inválido y Municipio no mencionado en la ubicación"
        columnas_revision = ['Diagnostico', 'cp_extraido', 'Estado', 'Ubicacion', 'Precio_MXN']
        columnas_disponibles = [c for c in columnas_revision if c in df_errores.columns]
        df_errores[columnas_disponibles].to_csv(PATH_ERRORES, index=False, encoding='utf-8-sig')

    print(f"💾 Dataset Final guardado en: {PATH_FINAL}")
    print(f"💾 Reporte de Errores guardado en: {PATH_ERRORES}")

if __name__ == "__main__":
    ejecucion_maxima_precision()