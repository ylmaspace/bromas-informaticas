import os
import sys
import subprocess

def asegurar_libreria_grafica():
    """ Verifica de forma automática si Pillow está instalado; si no, lo descarga en silencio """
    try:
        from PIL import Image
    except ImportError:
        print("[ENTORNO] Instalando motor de conversión gráfica (Pillow) de forma interna...")
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transformar_imagen_a_ico():
    asegurar_libreria_grafica()
    from PIL import Image

    print("=======================================================")
    print("   CONVERTIDOR MULTIFORMATO A ICONO .ICO (SAGA 31)    ")
    print("=======================================================\n")
    
    # Listar imágenes disponibles en la carpeta actual para ponértelo fácil
    formatos_soportados = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.svg')
    archivos = [f for f in os.listdir('.') if f.lower().endswith(formatos_soportados)]
    
    if not archivos:
        print("[AVISO] No se encontraron archivos de imagen (.png, .jpg, .svg, etc.) en esta carpeta.")
        print("Mete la imagen que quieras transformar al lado de este script.")
        input("\nPresiona Enter para salir...")
        return
        
    print("Imágenes detectadas en el directorio:")
    for i, archivo in enumerate(archivos):
        print(f" [{i}] {archivo}")
        
    try:
        seleccion = int(input("\nSelecciona el número de la imagen a convertir: "))
        imagen_objetivo = archivos[seleccion]
    except:
        print("[ERROR] Selección no válida.")
        input("\nPresiona Enter para salir...")
        return
        
    # Crear de forma automática la subcarpeta de recursos si no existe
    carpeta_destino = "iconos_generados"
    os.makedirs(carpeta_destino, exist_ok=True)
    
    nombre_base = os.path.splitext(os.path.basename(imagen_objetivo))[0]
    ruta_ico_salida = os.path.join(carpeta_destino, f"{nombre_base}.ico")
    
    print(f"\n[1/2] Procesando canales de color y transparencias de '{imagen_objetivo}'...")
    
    try:
        # Abrimos la imagen de origen
        img = Image.open(imagen_objetivo)
        
        # Windows requiere que los archivos .ico contengan múltiples resoluciones estandarizadas
        # (16x16, 32x32, 48x48 y 256x256 píxeles) para que se vea nítido tanto en el escritorio como en barras
        tamaños_iconos = [(16, 16), (32, 32), (48, 48), (256, 256)]
        
        print(f"[2/2] Reescalando y empaquetando capas en '{carpeta_destino}'...")
        # Guardamos en formato ICO inyectando la lista de tamaños nativos de Windows
        img.save(ruta_ico_salida, format="ICO", sizes=tamaños_iconos)
        
        print("\n=======================================================")
        print("          ¡CONVERSIÓN DE ICONO COMPLETADA!             ")
        print("=======================================================")
        print(f"Archivo .ico listo para camuflajes en: {ruta_ico_salida}")
        
    except Exception as e:
        print(f"\n[ERROR EN LA CONVERSIÓN]: {str(e)}")
        print("Nota: Para archivos .svg vectoriales puros, asegúrate de que no contengan enlaces rotos externos.")
        
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    transformar_imagen_a_ico()
