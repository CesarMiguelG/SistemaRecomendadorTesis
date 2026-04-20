import pandas as pd
import time
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm # Barra de progreso visual

# --- CONFIGURACIÓN DE RUTAS ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_ENTRADA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "processed", "oferta_nacional_limpia.csv"))
ARCHIVO_DICCIONARIO = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "processed", "diccionario_ubicaciones.csv"))
ARCHIVO_FINAL = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def preparar_direccion(ubicacion, estado):
    """Construye la dirección de búsqueda."""
    if pd.isna(ubicacion) or str(ubicacion).strip() == "":
        return None
    # Limpiamos textos como "#s/n" o "#000" que confunden al geocoder
    ubi_limpia = str(ubicacion).split('#')[0].strip()
    return f"{ubi_limpia}, {str(estado).strip()}, México"

def paso_1_crear_diccionario():
    """Extrae solo las ubicaciones ÚNICAS de los 220k registros."""
    print("🔍 Analizando el dataset para encontrar ubicaciones únicas...")
    df_maestro = pd.read_csv(ARCHIVO_ENTRADA)
    
    # Crear columna de búsqueda
    df_maestro['Query_Geo'] = df_maestro.apply(lambda row: preparar_direccion(row['Ubicacion'], row['Estado']), axis=1)
    
    # Extraer valores únicos
    ubicaciones_unicas = df_maestro['Query_Geo'].dropna().unique()
    print(f"📊 De {len(df_maestro):,} registros, solo hay {len(ubicaciones_unicas):,} ubicaciones únicas.")
    
    # Crear o cargar diccionario
    if os.path.exists(ARCHIVO_DICCIONARIO):
        df_diccionario = pd.read_csv(ARCHIVO_DICCIONARIO)
        print(f"🔄 Diccionario existente cargado con {len(df_diccionario):,} registros.")
    else:
        df_diccionario = pd.DataFrame({'Query_Geo': ubicaciones_unicas, 'Latitud': None, 'Longitud': None})
        df_diccionario.to_csv(ARCHIVO_DICCIONARIO, index=False)
        print("💾 Nuevo diccionario de ubicaciones creado.")
        
    return df_maestro, df_diccionario

def paso_2_geocodificar_diccionario(df_diccionario):
    """Geocodifica SOLO las direcciones únicas faltantes."""
    # Filtrar las que aún no tienen coordenadas
    df_pendientes = df_diccionario[df_diccionario['Latitud'].isna()].copy()
    total_pendientes = len(df_pendientes)
    
    if total_pendientes == 0:
        print("✅ El diccionario está 100% geocodificado.")
        return df_diccionario
        
    print(f"🚀 Iniciando geocodificación de {total_pendientes:,} ubicaciones únicas...")
    
    # Configurar Geocodificador
    geolocator = Nominatim(user_agent="Tesis_Recomendador_Vivienda_Mx_V2")
    geocode_con_pausa = RateLimiter(geolocator.geocode, min_delay_seconds=1.1, error_wait_seconds=5.0)
    
    # Habilitar barra de progreso para Pandas
    tqdm.pandas(desc="Geocodificando")
    
    # Función auxiliar para manejar la respuesta
    def obtener_coordenadas(query):
        try:
            loc = geocode_con_pausa(query)
            if loc:
                return pd.Series([loc.latitude, loc.longitude])
        except:
            time.sleep(2) # Pausa extra por error de red
        return pd.Series([None, None])

    # Aplicar la geocodificación con barra de progreso
    # NOTA: Para no perder progreso si falla, guardaremos cada 100 iteraciones
    lote_size = 100
    for i in range(0, total_pendientes, lote_size):
        lote = df_pendientes.iloc[i:i+lote_size]
        
        # Geocodificar el lote
        lote[['Latitud_nueva', 'Longitud_nueva']] = lote['Query_Geo'].progress_apply(obtener_coordenadas)
        
        # Actualizar el diccionario principal en memoria
        for idx, row in lote.iterrows():
            if pd.notna(row['Latitud_nueva']):
                df_diccionario.at[idx, 'Latitud'] = row['Latitud_nueva']
                df_diccionario.at[idx, 'Longitud'] = row['Longitud_nueva']
                
        # Guardar checkpoint en disco
        df_diccionario.to_csv(ARCHIVO_DICCIONARIO, index=False)
        print(f"💾 Checkpoint guardado: Lote {i//lote_size + 1} completado.")

    return df_diccionario

def paso_3_ensamblar_dataset_final(df_maestro, df_diccionario):
    """Une las coordenadas del diccionario a los 220k registros originales."""
    print("🧩 Ensamblando el dataset final (Join Espacial Vectorizado)...")
    
    # Hacer un Left Join: A cada registro maestro le pegamos su Lat/Lon según su Query_Geo
    df_final = pd.merge(
        df_maestro,
        df_diccionario[['Query_Geo', 'Latitud', 'Longitud']],
        on='Query_Geo',
        how='left'
    )
    
    # Limpiar columna auxiliar
    df_final.drop(columns=['Query_Geo'], inplace=True)
    
    # Guardar resultado
    df_final.to_csv(ARCHIVO_FINAL, index=False, encoding='utf-8-sig')
    
    exito = df_final['Latitud'].notna().sum()
    print(f"🎉 Proceso Terminado!")
    print(f"📊 Total de registros: {len(df_final):,}")
    print(f"📍 Coordenadas asignadas: {exito:,} ({(exito/len(df_final))*100:.1f}%)")
    print(f"💾 Archivo final listo en: {ARCHIVO_FINAL}")

if __name__ == "__main__":
    df_m, df_dict = paso_1_crear_diccionario()
    df_dict_actualizado = paso_2_geocodificar_diccionario(df_dict)
    paso_3_ensamblar_dataset_final(df_m, df_dict_actualizado)