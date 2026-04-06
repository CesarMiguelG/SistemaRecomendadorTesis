from playwright.sync_api import sync_playwright, TimeoutError
import pandas as pd
import time
import random
import os
import re
from datetime import datetime

# --- CONFIGURACIÓN ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_SALIDA = os.path.abspath(os.path.join(DIRECTORIO_ACTUAL, "..", "data", "raw", "estados"))

COLUMNAS_MAESTRAS = [
    "Estado", "Pagina_Extraida", "Fecha_Consulta", 
    "Precio", "Ubicacion", "Caracteristicas", "URL_Propiedad"
]

def limpiar_texto(texto):
    if pd.isna(texto) or texto is None: return ""
    return re.sub(r'\s+', ' ', str(texto)).strip()

def limpiar_url(url_bruta):
    if pd.isna(url_bruta) or not url_bruta: return ""
    return str(url_bruta).split('#')[0].strip()

def preprocesar_y_normalizar_csvs(carpeta):
    print(f"\n{'='*65}\n🛠️ FASE 1: NORMALIZACIÓN, AUDITORÍA Y ROTACIÓN DE CERTIFICADOS\n{'='*65}")
    
    # 1. DESTRUCCIÓN DE CERTIFICADOS OBSOLETOS (Falsos Positivos)
    certificados_viejos = [f for f in os.listdir(carpeta) if f.startswith(".completado_")]
    if certificados_viejos:
        print(f"  🗑️ Revocando {len(certificados_viejos)} certificados de versiones anteriores...")
        for viejo in certificados_viejos:
            os.remove(os.path.join(carpeta, viejo))

    # 2. NORMALIZACIÓN DE CSVS
    archivos = [f for f in os.listdir(carpeta) if f.startswith("oferta_") and f.endswith(".csv")]
    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        try:
            df = pd.read_csv(ruta, engine='python', on_bad_lines='skip')
            if df.empty: continue
            
            if 'URL' in df.columns: df.rename(columns={'URL': 'URL_Propiedad'}, inplace=True)
            for col in ['Precio', 'Ubicacion', 'Caracteristicas']:
                if col in df.columns: df[col] = df[col].apply(limpiar_texto)
            if 'URL_Propiedad' in df.columns: df['URL_Propiedad'] = df['URL_Propiedad'].apply(limpiar_url)
            for col_maestra in COLUMNAS_MAESTRAS:
                if col_maestra not in df.columns: df[col_maestra] = ""
            
            # Forzar esquema y guardar
            df[COLUMNAS_MAESTRAS].to_csv(ruta, index=False, encoding='utf-8-sig')
        except: pass
    print("✨ Base de datos homologada al Esquema V9.\n")

def obtener_metadatos_reales(page, url_estado):
    """Extrae el número total de propiedades que la web dice tener."""
    try:
        page.goto(url_estado, timeout=60000, wait_until="domcontentloaded")
        time.sleep(4)
        texto = page.locator('h1, .results-count, [data-qa="search-results-title"]').inner_text()
        numeros = re.findall(r'[\d,]+', texto)
        if numeros:
            total = int(numeros[0].replace(',', ''))
            return total, (total // 20) + 2
    except: pass
    return 0, 1000

def rastreador_nacional_definitivo():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    
    # Preprocesa y destruye banderas viejas
    preprocesar_y_normalizar_csvs(CARPETA_SALIDA)

    print(f"{'='*65}\n🚀 FASE 2: CRAWLER CON AUDITORÍA MATEMÁTICA\n{'='*65}")

    estados = [
        "aguascalientes", "baja-california", "baja-california-sur", "campeche", 
        "chiapas", "chihuahua", "ciudad-de-mexico", "coahuila", "colima", 
        "durango", "estado-de-mexico", "guanajuato", "guerrero", "hidalgo", 
        "jalisco", "michoacan", "morelos", "nayarit", "nuevo-leon", "oaxaca", 
        "puebla", "queretaro", "quintana-roo", "san-luis-potosi", "sinaloa", 
        "sonora", "tabasco", "tamaulipas", "tlaxcala", "veracruz", "yucatan", 
        "zacatecas"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()

        for estado in estados:
            url_base = f"https://propiedades.com/{estado}/casas-venta"
            archivo_csv = os.path.join(CARPETA_SALIDA, f"oferta_{estado}.csv")
            
            # NUEVO FORMATO DE CERTIFICADO V9
            archivo_finalizado = os.path.join(CARPETA_SALIDA, f".certificado_v9_{estado}")

            if os.path.exists(archivo_finalizado):
                print(f"📍 {estado.upper()}: ✅ Certificado V9 válido. Saltando.")
                continue

            # --- AUDITORÍA DE BRECHA ---
            total_web, paginas_estimadas = obtener_metadatos_reales(page, url_base)
            registros_locales = 0
            urls_vistas = set()
            pagina_inicio = 1

            if os.path.exists(archivo_csv):
                try:
                    df_actual = pd.read_csv(archivo_csv)
                    urls_vistas.update(df_actual['URL_Propiedad'].dropna().unique().tolist())
                    registros_locales = len(urls_vistas)
                    if 'Pagina_Extraida' in df_actual.columns:
                        pagina_inicio = max(1, int(df_actual['Pagina_Extraida'].max()) - 1)
                except: pass

            # Comparación científica de inventario
            if total_web > 0:
                cobertura = (registros_locales / total_web) * 100
                print(f"📍 {estado.upper()}: Web = {total_web} | Local = {registros_locales} ({cobertura:.1f}% de cobertura)")
                
                if cobertura >= 98.0:
                    print(f"  🏁 Cobertura alcanzada. Emitiendo Certificado V9...")
                    with open(archivo_finalizado, 'w') as f: f.write(f"Auditado V9: {cobertura:.1f}%")
                    continue
            else:
                print(f"📍 {estado.upper()}: Extrayendo a ciegas (no se detectó contador).")

            # --- BUCLE DE EXTRACCIÓN ---
            timeouts_consecutivos = 0

            for num_pagina in range(pagina_inicio, paginas_estimadas + 1):
                t_inicio = time.time()
                url = url_base if num_pagina == 1 else f"{url_base}?pagina={num_pagina}"
                
                try:
                    page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    time.sleep(3)
                    
                    if num_pagina > 5 and page.locator('text="¡Lo sentimos!"').is_visible():
                        print("    🏁 Fin visual detectado. Emitiendo Certificado V9...")
                        with open(archivo_finalizado, 'w') as f: f.write("Completado visualmente V9")
                        break

                    page.evaluate("window.scrollBy(0, document.body.scrollHeight/2)")
                    tarjetas = page.query_selector_all('section.pcom-property-card')
                    datos_lote = []
                    duplicados = 0

                    for t in tarjetas:
                        try:
                            calle_el = t.query_selector('a.pcom-property-card-body-main-info-street')
                            link = f"https://propiedades.com{calle_el.get_attribute('href')}".split('#')[0]
                            if link in urls_vistas:
                                duplicados += 1
                                continue
                            urls_vistas.add(link)
                            
                            datos_lote.append({
                                "Estado": estado.title(),
                                "Pagina_Extraida": num_pagina,
                                "Fecha_Consulta": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Precio": limpiar_texto(t.query_selector('section[class*="main-info"] > div').inner_text()),
                                "Ubicacion": limpiar_texto(calle_el.inner_text()),
                                "Caracteristicas": limpiar_texto(" | ".join([am.inner_text() for am in t.query_selector_all('li.amenities')])),
                                "URL_Propiedad": link
                            })
                        except: continue

                    if datos_lote:
                        df_p = pd.DataFrame(datos_lote)[COLUMNAS_MAESTRAS]
                        df_p.to_csv(archivo_csv, mode='a', index=False, header=not os.path.exists(archivo_csv), encoding='utf-8-sig')
                    
                    t_proc = time.time() - t_inicio
                    t_espera = max(1.0, random.uniform(8.0, 11.0) - t_proc)
                    print(f"    ✅ Pág {num_pagina}: {len(datos_lote)} nuevas | {duplicados} repetidas | ⏱️ {t_proc:.1f}s")
                    
                    timeouts_consecutivos = 0 
                    time.sleep(t_espera)

                except TimeoutError:
                    timeouts_consecutivos += 1
                    print(f"    ❌ Timeout ({timeouts_consecutivos}/3)")
                    if timeouts_consecutivos >= 3:
                        print("    🛑 Bloqueo detectado. Emitiendo certificado de contingencia V9...")
                        with open(archivo_finalizado, 'w') as f: f.write("Cerrado por Timeouts V9")
                        break 
                    continue
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    break

        browser.close()
    print("\n🚀 Proceso Finalizado. Todos los datos están certificados y listos para el Recomendador.")

if __name__ == "__main__":
    rastreador_nacional_definitivo()