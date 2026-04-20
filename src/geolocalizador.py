import pandas as pd
import time
import os
import sys
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm

# --- CONFIGURACIÓN DE RUTAS ---
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_RAW = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_limpia.csv"))
PATH_OLD_GEO = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geocodificada.csv"))
PATH_DICT = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "diccionario_ubicaciones.csv"))
PATH_FINAL = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

# --- PARÁMETROS ---
LOTE_GUARDADO = 20
DELAY_API = 1.2

def verificar_permisos_y_archivos():
    """Verifica la existencia de archivos y si tenemos permiso de escritura."""
    print(f"\n{'='*70}\n🛡️  VERIFICACIÓN DE SEGURIDAD Y PERMISOS\n{'='*70}")
    
    # 1. Verificar archivo base
    if not os.path.exists(PATH_RAW):
        print(f"❌ ERROR CRÍTICO: No se encuentra el archivo maestro: {PATH_RAW}")
        sys.exit(1)
    
    # 2. Verificar permisos de escritura en la carpeta
    directorio = os.path.dirname(PATH_DICT)
    if not os.access(directorio, os.W_OK):
        print(f"❌ ERROR DE PERMISOS: No tengo permiso para escribir en la carpeta: {directorio}")
        sys.exit(1)

    # 3. Verificar si el archivo está bloqueado por otro programa (Excel)
    if os.path.exists(PATH_DICT):
        try:
            with open(PATH_DICT, 'a'): pass
            print("✅ Permisos de escritura confirmados.")
        except IOError:
            print("❌ ERROR: El archivo 'diccionario_ubicaciones.csv' está bloqueado (¿Está abierto en Excel?)")
            sys.exit(1)

def auditoria_inicial():
    verificar_permisos_y_archivos()
    
    df_m = pd.read_csv(PATH_RAW)
    # Limpieza rápida de ruidos en direcciones
    df_m['Query_Geo'] = df_m.apply(lambda r: f"{str(r['Ubicacion']).split('#')[0].strip()}, {str(r['Estado']).strip()}, México", axis=1)
    uni_maestro = set(df_m['Query_Geo'].dropna().unique())
    
    base_datos = {}
    
    # Intentar recuperar datos de archivos previos
    for path in [PATH_OLD_GEO, PATH_DICT]:
        if os.path.exists(path):
            print(f"🔍 Recuperando datos de: {os.path.basename(path)}")
            try:
                df_recup = pd.read_csv(path)
                # Si es el archivo viejo, hay que generar la llave Query_Geo
                if 'Query_Geo' not in df_recup.columns:
                    df_recup['Query_Geo'] = df_recup.apply(lambda r: f"{str(r['Ubicacion']).split('#')[0].strip()}, {str(r['Estado']).strip()}, México", axis=1)
                
                # Extraer solo lo que tiene coordenadas válidas
                for _, r in df_recup.dropna(subset=['Latitud', 'Longitud']).iterrows():
                    base_datos[r['Query_Geo']] = (r['Latitud'], r['Longitud'])
            except: continue

    final_dict_data = [{'Query_Geo': q, 'Latitud': base_datos.get(q, (None, None))[0], 
                        'Longitud': base_datos.get(q, (None, None))[1]} for q in uni_maestro]
    
    df_trabajo = pd.DataFrame(final_dict_data)
    df_trabajo.to_csv(PATH_DICT, index=False)
    print(f"✅ Auditoría lista. Registros recuperados: {df_trabajo['Latitud'].notna().sum():,}")
    return df_m, df_trabajo

def motor_geocodificacion(df_dict):
    print(f"\n{'='*70}\n🚀 PROCESANDO CON VERIFICACIÓN DE ESCRITURA ACTIVA\n{'='*70}")
    
    pendientes = df_dict[df_dict['Latitud'].isna()].index.tolist()
    if not pendientes: return df_dict

    geolocator = Nominatim(user_agent="Cesar_Tesis_Master_Final")
    service = RateLimiter(geolocator.geocode, min_delay_seconds=DELAY_API, error_wait_seconds=10.0)

    pbar = tqdm(total=len(pendientes), desc="📍 Geocodificando")
    cambios_sin_guardar = 0
    ultima_fecha_mod = os.path.getmtime(PATH_DICT)

    try:
        for idx in pendientes:
            query = df_dict.at[idx, 'Query_Geo']
            try:
                res = service(query)
                if res:
                    df_dict.at[idx, 'Latitud'] = res.latitude
                    df_dict.at[idx, 'Longitud'] = res.longitude
                    cambios_sin_guardar += 1
            except Exception as e:
                if "429" in str(e): time.sleep(30)
                else: df_dict.at[idx, 'Latitud'], df_dict.at[idx, 'Longitud'] = 0.0, 0.0
            
            pbar.update(1)
            
            # --- GUARDADO Y VERIFICACIÓN ---
            if cambios_sin_guardar >= LOTE_GUARDADO:
                try:
                    df_dict.to_csv(PATH_DICT, index=False)
                    # VERIFICAR SI EL ARCHIVO REALMENTE SE ESCRIBIÓ
                    nueva_fecha = os.path.getmtime(PATH_DICT)
                    if nueva_fecha > ultima_fecha_mod:
                        pbar.set_postfix({"Disco": "✅ Escrito"})
                        ultima_fecha_mod = nueva_fecha
                        cambios_sin_guardar = 0
                    else:
                        print("\n⚠️ ALERTA: El archivo no se actualizó en disco. Revisando permisos...")
                except Exception as e:
                    print(f"\n❌ ERROR DE ESCRITURA: {e}. ¿Cerraste Excel?")
                    sys.exit(1)

    except KeyboardInterrupt: print("\n👋 Pausa segura.")
    finally:
        df_dict.to_csv(PATH_DICT, index=False)
        pbar.close()
    return df_dict

def ensamblaje_final(df_m, df_d):
    print(f"\n{'='*70}\n🧩 ENSAMBLAJE FINAL\n{'='*70}")
    mapa_lat = dict(zip(df_d['Query_Geo'], df_d['Latitud']))
    mapa_lon = dict(zip(df_d['Query_Geo'], df_d['Longitud']))
    df_m['Latitud'] = df_m['Query_Geo'].map(mapa_lat)
    df_m['Longitud'] = df_m['Query_Geo'].map(mapa_lon)
    df_m.drop(columns=['Query_Geo']).to_csv(PATH_FINAL, index=False, encoding='utf-8-sig')
    print(f"🎉 ¡Dataset Master listo! Ubicación: {PATH_FINAL}")

if __name__ == "__main__":
    maestro, diccionario = auditoria_inicial()
    diccionario_final = motor_geocodificacion(diccionario)
    ensamblaje_final(maestro, diccionario_final)