import pandas as pd
import re
import os
import glob

# --- CONFIGURACIÓN DE RUTAS ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
# Suponiendo que este script está en /src y los datos en /data/raw/estados
CARPETA_ENTRADA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "raw", "estados"))
CARPETA_SALIDA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "processed"))

# Aseguramos que exista la carpeta de salida
os.makedirs(CARPETA_SALIDA, exist_ok=True)

# Tipo de cambio fijo para propiedades en USD (Ajustar según contexto de tesis)
TIPO_CAMBIO_USD = 20.0 

def limpiar_precio(texto):
    """Extrae el valor numérico del precio y convierte USD a MXN."""
    if pd.isna(texto) or not isinstance(texto, str):
        return None
    
    texto = texto.upper()
    # Extraer solo los números y comas
    numeros = re.findall(r'[\d,]+', texto)
    
    if not numeros:
        return None
        
    valor = float(numeros[0].replace(',', ''))
    
    # Si detectamos que está en dólares, aplicamos el tipo de cambio
    if 'USD' in texto:
        valor = valor * TIPO_CAMBIO_USD
        
    return valor

def extraer_caracteristica(texto, patron):
    """Extrae un número basado en una palabra clave (Recámaras, Baños, m2)."""
    if pd.isna(texto) or not isinstance(texto, str):
        return None
    
    # Busca el número justo antes de la palabra clave
    match = re.search(patron, texto, re.IGNORECASE)
    if match:
        # Reemplazar comas si las hay (ej. "1,200 m2") y convertir a float
        return float(match.group(1).replace(',', ''))
    return None

def procesar_inventario_nacional():
    print(f"🧹 Iniciando Laboratorio de Curación de Datos...")
    
    # 1. Encontrar todos los CSVs de estados
    patron_archivos = os.path.join(CARPETA_ENTRADA, "oferta_*.csv")
    archivos_csv = glob.glob(patron_archivos)
    
    if not archivos_csv:
        print("❌ No se encontraron archivos CSV en la carpeta de entrada.")
        return
    
    print(f"📂 Encontrados {len(archivos_csv)} archivos estatales. Consolidando...")
    
    # 2. Leer y concatenar todos en un solo DataFrame gigante
    lista_dfs = []
    for archivo in archivos_csv:
        try:
            df_temp = pd.read_csv(archivo, engine='python', on_bad_lines='skip')
            lista_dfs.append(df_temp)
        except Exception as e:
            print(f"  ⚠️ Error leyendo {os.path.basename(archivo)}: {e}")
            
    df_maestro = pd.concat(lista_dfs, ignore_index=True)
    total_original = len(df_maestro)
    print(f"📊 Registros crudos totales: {total_original:,}")

    # 3. APLICAR TRANSFORMACIONES (Feature Engineering)
    print("⚙️ Transformando variables de texto a numéricas...")
    
    # Limpieza de Precio
    df_maestro['Precio_MXN'] = df_maestro['Precio'].apply(limpiar_precio)
    
    # Extracción con RegEx
    # Explicación de la RegEx: (\d+[\d,]*)\s* significa "Atrapa los números (y comas) antes de..."
    df_maestro['Recamaras'] = df_maestro['Caracteristicas'].apply(
        lambda x: extraer_caracteristica(x, r'(\d+[\d,]*)\s*(?:Recámara|Recámaras|Recamara|Recamaras)')
    )
    df_maestro['Banos'] = df_maestro['Caracteristicas'].apply(
        lambda x: extraer_caracteristica(x, r'(\d+[\d,]*)\s*(?:Baño|Baños|Bano|Banos)')
    )
    df_maestro['Superficie_m2'] = df_maestro['Caracteristicas'].apply(
        lambda x: extraer_caracteristica(x, r'(\d+[\d,]*)\s*m\s*2')
    )

    # 4. FILTRADO Y SANIDAD DE DATOS
    print("🚿 Limpiando datos atípicos (Outliers) y nulos críticos...")
    
    # Eliminar filas donde no pudimos extraer el precio (son inservibles para el modelo)
    df_limpio = df_maestro.dropna(subset=['Precio_MXN'])
    
    # Filtros de Sentido Común (Domain Knowledge)
    # Por ejemplo: Descartar casas menores a $150,000 MXN (probablemente sean terrenos o errores)
    # y casas con más de 20 recámaras o menos de 20 m2.
    df_limpio = df_limpio[
        (df_limpio['Precio_MXN'] >= 150000) & 
        (df_limpio['Precio_MXN'] <= 150000000) # Límite superior razonable
    ]
    
    # 5. SELECCIÓN FINAL DE COLUMNAS
    columnas_finales = [
        'Estado', 'Ubicacion', 'Precio_MXN', 
        'Recamaras', 'Banos', 'Superficie_m2', 
        'URL_Propiedad'
    ]
    df_final = df_limpio[columnas_finales].copy()
    
    total_limpio = len(df_final)
    porcentaje_retenido = (total_limpio / total_original) * 100
    
    print(f"✅ Limpieza finalizada.")
    print(f"📉 Registros válidos retenidos: {total_limpio:,} ({porcentaje_retenido:.1f}% del total crudo).")
    
    # 6. GUARDAR RESULTADO
    ruta_salida = os.path.join(CARPETA_SALIDA, "oferta_nacional_limpia.csv")
    df_final.to_csv(ruta_salida, index=False, encoding='utf-8-sig')
    print(f"💾 Archivo maestro guardado en: {ruta_salida}")

if __name__ == "__main__":
    procesar_inventario_nacional()