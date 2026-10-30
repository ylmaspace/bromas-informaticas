import os
import base64

def codificar_imagen_universal():
    print("=======================================================")
    print("  CONVERTIDOR DE IMÁGENES A BASE64 (LABORATORIO SAGA 31) ")
    print("=======================================================\n")
    
    archivo_origen = input("Introduce el nombre de la imagen con su extensión (ej: susto.png): ").strip()
    
    if not os.path.exists(archivo_origen):
        print(f"\n[ERROR] El archivo '{archivo_origen}' no se encuentra en esta carpeta.")
        input("\nPresiona Enter para salir...")
        return

    carpeta_destino = "recursos_base64"
    os.makedirs(carpeta_destino, exist_ok=True)
    
    nombre_base = os.path.splitext(os.path.basename(archivo_origen))[0]
    archivo_txt_salida = os.path.join(carpeta_destino, f"imagen_{nombre_base}.txt")
    
    print(f"\n[1/2] Cifrando estructura de píxeles de '{archivo_origen}'...")
    with open(archivo_origen, "rb") as img_f:
        cadena_base64 = base64.b64encode(img_f.read()).decode("utf-8")
        
    print(f"[2/2] Guardando cadena de texto en '{carpeta_destino}'...")
    with open(archivo_txt_salida, "w", encoding="utf-8") as txt_f:
        txt_f.write(cadena_base64)
        
    print("\n=======================================================")
    print("            ¡IMAGEN PROCESADA CON ÉXITO!              ")
    print("=======================================================")
    print(f"Código listo para incrustar en: {archivo_txt_salida}")
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    codificar_imagen_universal()
