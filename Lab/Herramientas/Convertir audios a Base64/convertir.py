import os
import base64

def codificar_recurso_universal():
    print("=======================================================")
    print("  CONVERTIDOR UNIVERSAL DE RECURSOS A BASE64 (SAGA 31) ")
    print("=======================================================\n")
    
    archivo_origen = input("Introduce el nombre completo o ruta del archivo (ej: estornudo.mp3): ").strip()
    
    if not os.path.exists(archivo_origen):
        print(f"\n[ERROR] El archivo '{archivo_origen}' no existe en esta carpeta.")
        input("\nPresiona Enter para salir...")
        return

    # Crear de forma automática la subcarpeta dentro del directorio actual
    carpeta_destino = "recursos_base64"
    os.makedirs(carpeta_destino, exist_ok=True)
    
    # Extraer el nombre base para generar el archivo de salida
    nombre_base = os.path.splitext(os.path.basename(archivo_origen))[0]
    archivo_txt_salida = os.path.join(carpeta_destino, f"codigo_{nombre_base}.txt")
    
    print(f"\n[1/2] Leyendo y cifrando '{archivo_origen}' en memoria virtual...")
    with open(archivo_origen, "rb") as f_origen:
        bytes_binarios = f_origen.read()
        cadena_base64 = base64.b64encode(bytes_binarios).decode("utf-8")
        
    print(f"[2/2] Exportando cadena de texto a la carpeta '{carpeta_destino}'...")
    with open(archivo_txt_salida, "w", encoding="utf-8") as f_salida:
        f_salida.write(cadena_base64)
        
    print("\n=======================================================")
    print("            ¡PROCESO FINALIZADO CON ÉXITO!            ")
    print("=======================================================")
    print(f"Código exportado listo en: {archivo_txt_salida}")
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    codificar_recurso_universal()

