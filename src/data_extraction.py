import requests
import pandas as pd
import os
from datetime import datetime
import time

class SEDATU_API:
    def __init__(self):
        self.base_url = "https://sniiv.sedatu.gob.mx/api/CuboAPI/"
        
        directorio_script = os.path.dirname(os.path.abspath(__file__))
        ruta_salida = os.path.join(directorio_script, "..", "data", "raw", "sedatu")
        self.output_dir = os.path.normpath(ruta_salida)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

    def descargar_bloque(self, endpoint, param_tiempo, dimensiones):
        # param_tiempo será "2015,2017" para flujos o "2025,12" para inventario
        url = f"{self.base_url}{endpoint}/{param_tiempo}/00/000/{dimensiones}"
        
        try:
            inicio = time.time()
            res = requests.get(url, headers=self.headers, timeout=90)
            
            if res.status_code == 200:
                datos = res.json()
                if datos:
                    df = pd.DataFrame(datos)
                    print(f"      ✅ [{param_tiempo}] -> {len(df)} registros ({time.time()-inicio:.1f}s)")
                    return df
                else:
                    print(f"      ⚠️ [{param_tiempo}] -> JSON Vacío (Sin datos en este periodo)")
                    return None
            else:
                print(f"      ❌ [{param_tiempo}] -> Error del servidor: {res.status_code}")
                return None
        except Exception as e:
            print(f"      ❌ [{param_tiempo}] -> Error de conexión: {e}")
            return None

def extraccion_oficial_sedatu():
    print("🇲🇽 Iniciando Extracción Total SNIIV (Adaptada para Inventario Snapshot)...")
    api = SEDATU_API()
    
    cubos = {
        "GetFinanciamiento": "anio,estado,municipio,organismo,modalidad",
        "GetCONAVI":         "anio,estado,municipio,modalidad,linea_apoyo",
        "GetFOVISSSTE":      "anio,estado,municipio,modalidad,esquema",
        "GetINFONAVIT":      "anio,estado,municipio,modalidad,linea_credito",
        "GetCNBV":           "anio,estado,municipio,modalidad,segmento",
        "GetInsus":          "anio,estado,municipio,rango_edad,genero",
        "GetRegistro":       "anio,estado,municipio,pcu,tipo_vivienda",
        "GetInventario":     "estado,municipio,pcu,avance_obra,tipo_vivienda", 
        "GetVerificacion":   "anio,estado,municipio,pcu,tipo_vivienda",
        "GetProduccion":     "anio,estado,municipio,pcu,tipo_vivienda"
    }
    
    bloques_flujo = ["2015,2017", "2018,2020", "2021,2023", "2024,2026"]
    
    # Generamos la lista de "fotos" para el inventario: Diciembre de 2015 a 2025, y Marzo de 2026
    bloques_snapshot = [f"{anio},12" for anio in range(2015, 2026)] + ["2026,3"]
    
    for endpoint, dimensiones in cubos.items():
        print(f"\n{'='*65}")
        print(f"📡 EXTRACCIÓN: {endpoint}")
        print(f"   Variables: {dimensiones}")
        print(f"{'='*65}")
        
        datos_totales = []
        
        # Lógica inteligente para decidir qué parámetros de tiempo enviar
        parametros_tiempo = bloques_snapshot if endpoint == "GetInventario" else bloques_flujo
        
        for p_tiempo in parametros_tiempo:
            df_bloque = api.descargar_bloque(endpoint, p_tiempo, dimensiones)
            
            if df_bloque is not None:
                # Si el cubo no devolvió columna temporal (como el inventario), se la inyectamos
                if 'año' not in df_bloque.columns and 'anio' not in df_bloque.columns:
                    df_bloque['periodo_reporte'] = p_tiempo
                datos_totales.append(df_bloque)
                
            time.sleep(2.5) 
            
        if datos_totales:
            print(f"\n🔄 Consolidando base de datos para {endpoint}...")
            df_final = pd.concat(datos_totales, ignore_index=True)
            
            df_final.columns = [col.lower().replace(' ', '_').replace('ñ', 'n') for col in df_final.columns]
            
            fecha_str = datetime.now().strftime("%Y%m%d")
            archivo_salida = os.path.join(api.output_dir, f"{endpoint.lower()}_nacional_{fecha_str}.csv")
            
            df_final.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
            print(f"💾 Guardado Exitoso: {len(df_final)} registros en '{archivo_salida}'.")
        else:
            print(f"🛑 Error crítico: No se lograron extraer datos para {endpoint}.")

if __name__ == "__main__":
    extraccion_oficial_sedatu()