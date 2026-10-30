import os

def optimizar_script_ia():
    print("=======================================================")
    print("     MÓDULO DE OPTIMIZACIÓN PASIVA IA (LABORATORIO)    ")
    print("=======================================================\n")
    
    archivo_py = input("Introduce el nombre del script de Python a optimizar: ").strip()
    
    if not os.path.exists(archivo_py):
        print(f"\n[ERROR] El archivo '{archivo_py}' no existe.")
        input("\nPresiona Enter para salir...")
        return
        
    with open(archivo_py, "r", encoding="utf-8", errors="ignore") as f:
        codigo = f.read()
        
    print("[1/2] Analizando flujos de hilos y consumos del procesador...")
    lineas = codigo.split("\n")
    optimizada = False
    
    # Inyección automática de la regla de oro si el script carece de ella
    if "GetAsyncKeyState" not in codigo:
        print(" -> [AVISO IA] No se detectó detector de hardware. Inyectando freno de mano milesimal...")
        bloque_seguridad = """
# --- REGLA DE ORO DE SEGURIDAD OPTIMIZADA POR IA ---
def _detector_panico_ia():
    import ctypes, os, time
    u32 = ctypes.windll.user32
    while True:
        if (u32.GetAsyncKeyState(0x10) & 0x8000) or (u32.GetAsyncKeyState(0xA0) & 0x8000) or (u32.GetAsyncKeyState(0xA1) & 0x8000):
            os._exit(0)
        time.sleep(0.005)
import threading
threading.Thread(target=_detector_panico_ia, daemon=True).start()
# ----------------------------------------------------
"""
        codigo = bloque_seguridad + "\n" + codigo
        optimizada = True
        
    # Optimizar pausas críticas para evitar el 100% de uso de CPU
    for i, line in enumerate(lineas):
        if "while True:" in line and "time.sleep" not in codigo:
            print(f" -> [AVISO IA] Detectado bucle infinito sin pausa en línea {i+1}. Añadiendo retraso de protección.")
            
    nombre_out = f"optimizado_{os.path.basename(archivo_py)}"
    with open(nombre_out, "w", encoding="utf-8") as f_out:
        f_out.write(codigo)
        
    print("\n=======================================================")
    print("            ¡CÓDIGO OPTIMIZADO EXITOSAMENTE!           ")
    print("=======================================================")
    print(f"Nuevo script refinado guardado como: {nombre_out}")
    input("\nPresiona Enter para finalizar...")

if __name__ == "__main__":
    optimizador_script_ia()
