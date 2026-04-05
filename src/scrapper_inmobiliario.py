from playwright.sync_api import sync_playwright, TimeoutError
import pandas as pd
import time
import random
import os
import re
from datetime import datetime

def limpiar_url(url_bruta):
    if not url_bruta or pd.isna(url_bruta): return ""
    return str(url_bruta).split('#')[0].strip()

def obtener_metadatos_estado(page, url_estado):
    try:
        page.goto(url_estado, timeout=60000)
        time.sleep(3) 
        texto_resultados = page.locator('h1, .results-count, [data-qa="search-results-title"]').inner_text()
        numeros = re.findall(r'[\d,]+', texto_resultados)
        if numeros:
            return int(numeros[0].replace(',', '')), (int(numeros[0].replace(',', '')) // 20) + 2
    except: pass
    return None, 1000

def rastreador_nacional_definitivo():
    print("🇲🇽 Iniciando Crawler Nivel 8.3: Radar de Fin de Inventario Actualizado...")
    
    estados = [
        "aguascalientes", "baja-california", "baja-california-sur", "campeche", 
        "chiapas", "chihuahua", "ciudad-de-mexico", "coahuila", "colima", 
        "durango", "estado-de-mexico", "guanajuato", "guerrero", "hidalgo", 
        "jalisco", "michoacan", "morelos", "nayarit", "nuevo-leon", "oaxaca", 
        "puebla", "queretaro", "quintana-roo", "san-luis-potosi", "sinaloa", 
        "sonora", "tabasco", "tamaulipas", "tlaxcala", "veracruz", "yucatan", 
        "zacatecas"
    ]
    
    carpeta_salida = "../data/raw/estados"
    os.makedirs(carpeta_salida, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for estado in estados:
            print(f"\n{'='*60}")
            print(f"📍 PROCESANDO: {estado.upper()}")
            
            url_base = f"https://propiedades.com/{estado}/casas-venta"
            archivo_csv = f"{carpeta_salida}/oferta_{estado}.csv"
            archivo_finalizado = f"{carpeta_salida}/.completado_{estado}"
            urls_vistas = set() 

            if os.path.exists(archivo_finalizado):
                print("✅ Estado ya completado. Saltando...")
                continue

            total_web, paginas_estimadas = obtener_metadatos_estado(page, url_base)
            
            # AUTO-MIGRADOR
            if os.path.exists(archivo_csv):
                try:
                    df_header = pd.read_csv(archivo_csv, nrows=0)
                    if 'Fecha_Consulta' not in df_header.columns:
                        archivo_legacy = f"{carpeta_salida}/oferta_{estado}_legacy.csv"
                        if os.path.exists(archivo_legacy): os.remove(archivo_legacy)
                        os.rename(archivo_csv, archivo_legacy)
                        df_viejo = pd.read_csv(archivo_legacy, engine='python', on_bad_lines='skip')
                        col_url = 'URL_Propiedad' if 'URL_Propiedad' in df_viejo.columns else 'URL'
                        if col_url in df_viejo.columns:
                            urls_vistas.update([limpiar_url(u) for u in df_viejo[col_url].dropna()])
                except: pass

            # CEREBRO DE REANUDACIÓN
            pagina_inicio = 1
            if os.path.exists(archivo_csv):
                try:
                    df_actual = pd.read_csv(archivo_csv, engine='python', on_bad_lines='skip')
                    if not df_actual.empty:
                        col_url = 'URL_Propiedad' if 'URL_Propiedad' in df_actual.columns else 'URL'
                        if col_url in df_actual.columns:
                            urls_vistas.update([limpiar_url(u) for u in df_actual[col_url].dropna()])

                        if 'Pagina_Extraida' in df_actual.columns:
                            ultima_pag = int(df_actual['Pagina_Extraida'].max())
                            pagina_inicio = max(1, ultima_pag - 5)
                            print(f"🔄 Reanudando motor desde la página: {pagina_inicio} (Incluye traslape)")
                        
                        if total_web and len(urls_vistas) >= (total_web * 0.95):
                            print("🏁 Inventario prácticamente completo. Finalizando estado.")
                            with open(archivo_finalizado, 'w') as f: f.write("OK")
                            continue
                except: pass

            # BUCLE DE EXTRACCIÓN
            timeouts_consecutivos = 0  # <--- FAILSAFE INICIALIZADO

            for num_pagina in range(pagina_inicio, paginas_estimadas + 1):
                tiempo_inicio_ciclo = time.time() 
                url = url_base if num_pagina == 1 else f"{url_base}?pagina={num_pagina}"
                fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                try:
                    page.goto(url, timeout=90000)
                    time.sleep(2) # Breve pausa para dejar que renderice el mensaje de error si existe
                    
                    if num_pagina > 1 and f"pagina={num_pagina}" not in page.url:
                        print("🏁 Redirección detectada. Fin de inventario.")
                        with open(archivo_finalizado, 'w') as f: f.write(fecha_ahora)
                        break

                    # --- NUEVO RADAR DE FIN DE INVENTARIO BASADO EN TU CAPTURA ---
                    if (page.locator('text="¡Lo sentimos!"').is_visible() or 
                        page.locator('text="Tu búsqueda no generó resultados"').is_visible() or
                        page.locator('text="No encontramos resultados"').is_visible()):
                        
                        print(f"  🏁 Fin de inventario visual detectado en la página {num_pagina}.")
                        with open(archivo_finalizado, 'w') as f: f.write(fecha_ahora)
                        break

                    page.evaluate("window.scrollBy(0, document.body.scrollHeight/2)")
                    page.wait_for_selector('section.pcom-property-card', timeout=15000)
                    tarjetas = page.query_selector_all('section.pcom-property-card')

                    datos_lote = []
                    duplicados_omitidos = 0

                    for t in tarjetas:
                        try:
                            calle_el = t.query_selector('a.pcom-property-card-body-main-info-street')
                            link_bruto = calle_el.get_attribute('href')
                            if link_bruto and not link_bruto.startswith('http'): link_bruto = "https://propiedades.com" + link_bruto
                            link_puro = limpiar_url(link_bruto)
                            
                            if link_puro in urls_vistas:
                                duplicados_omitidos += 1
                                continue 
                            urls_vistas.add(link_puro)
                            
                            precio = t.query_selector('section[class*="main-info"] > div').inner_text().strip()
                            calle = calle_el.inner_text().strip().replace('\n', ' ')
                            caract = " | ".join([am.inner_text().strip() for am in t.query_selector_all('li.amenities')])

                            datos_lote.append({
                                "Estado": estado.title(),
                                "Pagina_Extraida": num_pagina,
                                "Fecha_Consulta": fecha_ahora,
                                "Precio": precio,
                                "Ubicacion": calle,
                                "Caracteristicas": caract,
                                "URL_Propiedad": link_puro
                            })
                        except: continue

                    if datos_lote:
                        df_p = pd.DataFrame(datos_lote)
                        df_p.to_csv(archivo_csv, mode='a', index=False, header=not os.path.exists(archivo_csv), encoding='utf-8-sig')
                        
                    tiempo_procesamiento = time.time() - tiempo_inicio_ciclo
                    tiempo_espera = max(1.0, random.uniform(8.0, 12.0) - tiempo_procesamiento)
                    
                    print(f"      ✅ Pág {num_pagina}: {len(datos_lote)} nuevas | {duplicados_omitidos} repetidas.")
                    print(f"      ⏱️ T. Proc: {tiempo_procesamiento:.1f}s | Pausando {tiempo_espera:.1f}s")
                    
                    timeouts_consecutivos = 0 # Reseteamos el failsafe si hubo éxito
                    time.sleep(tiempo_espera)

                except TimeoutError:
                    timeouts_consecutivos += 1
                    print(f"  ❌ Timeout. Saltando a la siguiente... ({timeouts_consecutivos}/3)")
                    
                    # --- EL CORTOCIRCUITO ---
                    if timeouts_consecutivos >= 3:
                        print("  🛑 Demasiados Timeouts seguidos. El inventario se acabó o hay un bloqueo en la sombra.")
                        with open(archivo_finalizado, 'w') as f: f.write(fecha_ahora)
                        break # Cortamos por lo sano y pasamos al siguiente estado
                    continue
                    
                except Exception as e:
                    print(f"  ❌ Error inesperado: {e}")
                    break

        browser.close()
    print("\n🚀 Extracción finalizada a máxima eficiencia.")

if __name__ == "__main__":
    rastreador_nacional_definitivo()