import os

def generar_plantilla_base():
    print("=======================================================")
    print("      CREADOR DE PLANTILLAS PARA LESSWARES (SAGA 31)   ")
    print("=======================================================\n")
    
    print("Selecciona el tipo de broma informática que vas a programar:")
    print(" [1] Lessware de Pantalla (Efectos visuales)")
    print(" [2] Lessware de Ratón (Captura de cursor)")
    print(" [3] Lessware de Teclado (Hooks de escritura)")
    
    tipo = input("\nIntroduce tipo (1-3): ").strip()
    nombre = input("¿Qué nombre de archivo quieres ponerle? (ej: virus_loco): ").strip()
    
    if not nombre.endswith(".py"): nombre += ".py"
    
    bloque_comun = '''import os, sys, time, threading, random, math, ctypes

RUNNING = True
user32 = ctypes.windll.user32

def detector_hardware_shift():
    """ REGLA DE ORO DE SEGURIDAD BLINDADA EN SEGUNDO PLANO A 5MS """
    global RUNNING
    while RUNNING:
        if (user32.GetAsyncKeyState(0x10) & 0x8000) or (user32.GetAsyncKeyState(0xA0) & 0x8000) or (user32.GetAsyncKeyState(0xA1) & 0x8000):
            RUNNING = False
            # Aquí puedes añadir código de limpieza gráfica específico antes de morir
            os._exit(0)
        time.sleep(0.005)

# Arrancar el freno de mano de hardware de forma paralela
threading.Thread(target=detector_hardware_shift, daemon=True).start()
'''

    if tipo == "1":
        especifico = '''
# --- PLANTILLA DE PANTALLA ---
gdi32 = ctypes.windll.gdi32
width = user32.GetSystemMetrics(0)
height = user32.GetSystemMetrics(1)

hdc = user32.GetDC(0)
print("[LOG] Motor de pantalla listo. Inserta tu bucle BitBlt o FillRect aquí abajo...")

while RUNNING:
    # METER TU EFECTO AQUÍ (Ejemplo: parpadeo o deformación)
    time.sleep(0.05)

user32.ReleaseDC(0, hdc)
'''
    elif tipo == "2":
        especifico = '''
# --- PLANTILLA DE RATÓN ---
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
pt = POINT()

print("[LOG] Motor de ratón listo. Inserta tu bucle de alteración del cursor aquí abajo...")

while RUNNING:
    user32.GetCursorPos(ctypes.byref(pt))
    # METER TU TROLEO DE RATÓN AQUÍ
    time.sleep(0.1)
'''
    else:
        especifico = '''
# --- PLANTILLA DE TECLADO ---
# Nota: Para hooks globales avanzados recuerda usar SetWindowsHookExW (WH_KEYBOARD_LL = 13)
print("[LOG] Motor de teclado listo. Registrando bucle nativo de mensajes...")

# Inserta aquí tu callback y tu inyector de texto Base64
while RUNNING:
    time.sleep(1)
'''

    with open(nombre, "w", encoding="utf-8") as f:
        f.write(bloque_comun + especifico)
        
    print(f"\n[OK] Plantilla automatizada creada con éxito: {nombre}")
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    generar_plantilla_base()
