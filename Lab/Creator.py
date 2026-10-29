import os
import re
import ast
import sys
import json
import shutil
import hashlib
import tempfile
import importlib.util
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".creator_lab.json")

# ──────────────────────────────────────────────────────────────────────────
#  REGLAS DE SEGURIDAD
#  Cada regla: (id, nombre, nivel, patrón regex, mensaje)
#  nivel: "ERROR" = incumple una regla importante, "AVISO" = revisar.
#  NINGUNA detiene la compilación: solo informan. Edita/añade las tuyas aquí.
# ──────────────────────────────────────────────────────────────────────────
REGLAS_PATRON = [
    ("persistencia", "Sin persistencia", "ERROR",
     r"CurrentVersion[\\/]+Run|winreg|Start Menu.{0,30}Startup|schtasks|RunOnce",
     "Parece que intenta arrancar solo con el sistema (registro / inicio / tareas programadas)."),
    ("destructivo", "Sin acciones destructivas", "ERROR",
     r"shutil\.rmtree|os\.(remove|unlink|rmdir)\b|send2trash|cipher\s*/w|\bdel\s+/[fsq]|\bformat\s+[a-zA-Z]:",
     "Borra archivos o carpetas."),
    ("apagado", "No apaga / reinicia / mata procesos", "ERROR",
     r"shutdown|taskkill|ExitWindowsEx|os\.kill\(",
     "Puede apagar, reiniciar o matar procesos."),
    ("bloqueo", "No bloquea el sistema", "ERROR",
     r"BlockInput|DisableTaskMgr|DisableLockWorkstation|taskmgr|explorer\.exe",
     "Intenta bloquear la entrada, el administrador de tareas o el escritorio."),
    ("red", "Sin conexiones de red", "AVISO",
     r"^\s*(import|from)\s+(socket|requests|urllib|http\.client|smtplib|ftplib|paramiko|websocket)",
     "Importa módulos de red."),
    ("externo", "Sin ejecución de comandos externos", "AVISO",
     r"\bsubprocess\b|os\.system|os\.popen|\beval\(|\bexec\(",
     "Ejecuta comandos o código dinámico."),
    ("ocultar", "No se oculta", "AVISO",
     r"SW_HIDE|FreeConsole|ShowWindow\(.*,\s*0\s*\)",
     "Oculta ventanas o consola."),
]

EXIT_RE = r"sys\.exit|os\._exit|\bexit\(|\bquit\(|\.destroy\(|\.quit\(|TerminateProcess|ExitProcess"
GLOBAL_HOOK_RE = r"GetAsyncKeyState|GetKeyState|keyboard\.|pynput|SetWindowsHookEx"
FOCUS_RE = r"-fullscreen|-topmost|overrideredirect"


def _linea(codigo, pos):
    return codigo.count("\n", 0, pos) + 1


def _es_comentario(codigo, pos):
    ini = codigo.rfind("\n", 0, pos) + 1
    return codigo[ini:pos].lstrip().startswith("#") or codigo[ini:].lstrip().startswith("#")


def verificar_reglas(codigo, noconsole):
    """Devuelve lista de (nivel, texto). Niveles: OK, AVISO, ERROR."""
    res = []

    # 0. Sintaxis
    try:
        arbol = ast.parse(codigo)
    except SyntaxError as e:
        arbol = None
        res.append(("ERROR", f"Error de sintaxis en la línea {e.lineno}: {e.msg} (el .exe fallará al abrirse)."))

    # Texto sin líneas comentadas
    sin_coment = "\n".join(l for l in codigo.splitlines() if not l.lstrip().startswith("#"))

    # 1. Pánico por Shift (regla principal)
    tiene_shift = re.search(r"(?i)shift", sin_coment) is not None
    hook_global = re.search(GLOBAL_HOOK_RE, sin_coment) is not None
    bind_tk = re.search(r"\.bind(_all)?\(", sin_coment) is not None
    salida = re.search(EXIT_RE, sin_coment) is not None
    ventana_fija = re.search(FOCUS_RE, sin_coment) is not None

    if not tiene_shift:
        res.append(("ERROR", "PÁNICO SHIFT: no se encuentra ninguna tecla Shift en el código."))
    else:
        res.append(("OK", "PÁNICO SHIFT: se detecta referencia a la tecla Shift."))
        if not salida:
            res.append(("AVISO", "PÁNICO SHIFT: no veo ninguna salida (sys.exit / os._exit / destroy...). "
                                 "¿Realmente cierra el programa?"))
        if not hook_global and bind_tk:
            res.append(("AVISO", "PÁNICO SHIFT: solo veo .bind() de Tkinter, que funciona únicamente "
                                 "con la ventana enfocada. Mejor GetAsyncKeyState / keyboard / pynput."))
        if not hook_global and not bind_tk:
            res.append(("AVISO", "PÁNICO SHIFT: se menciona Shift pero no veo cómo se detecta la pulsación."))

    if ventana_fija and not hook_global:
        res.append(("AVISO", "Ventana pantalla completa/siempre encima sin detección GLOBAL de teclado: "
                             "si pierde el foco, el pánico podría no funcionar."))
    if noconsole and not tiene_shift:
        res.append(("ERROR", "Se compilará SIN consola y sin pánico Shift: quedaría invisible y sin salida fácil."))

    # 2. Reglas por patrón
    for _id, nombre, nivel, patron, msg in REGLAS_PATRON:
        hallazgos = [m for m in re.finditer(patron, codigo, re.MULTILINE)
                     if not _es_comentario(codigo, m.start())]
        if hallazgos:
            lineas = sorted({_linea(codigo, m.start()) for m in hallazgos})
            res.append((nivel, f"{nombre}: {msg} (línea(s): {', '.join(map(str, lineas[:8]))})"))
        else:
            res.append(("OK", f"{nombre}."))

    # 3. Bucles infinitos sin salida (AST)
    if arbol is not None:
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.While) and isinstance(nodo.test, ast.Constant) and nodo.test.value is True:
                tiene_salida = False
                for sub in ast.walk(nodo):
                    if isinstance(sub, (ast.Break, ast.Return)):
                        tiene_salida = True
                    elif isinstance(sub, ast.Call):
                        f = sub.func
                        nom = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                        if nom in ("exit", "_exit", "quit", "destroy"):
                            tiene_salida = True
                if not tiene_salida:
                    res.append(("AVISO", f"Bucle 'while True' sin break/return/exit (línea {nodo.lineno})."))

    return res


def sanitizar_nombre(nombre):
    nombre = re.sub(r'[<>:"/\\|?*]', "", nombre.strip())
    if nombre.lower().endswith(".exe"):
        nombre = nombre[:-4]
    return nombre.strip(" .")


class SuperCompiladorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Creator Lab - Compilador con verificación de seguridad")
        self.root.geometry("820x860")
        self.root.minsize(760, 760)

        self.ruta_archivo = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.nombre_exe = tk.StringVar()
        self.icono = tk.StringVar()
        self.onefile_var = tk.BooleanVar(value=True)
        self.noconsole_var = tk.BooleanVar(value=True)
        self.abrir_var = tk.BooleanVar(value=True)
        self.informe_var = tk.BooleanVar(value=True)

        self.cargar_config()
        self.crear_componentes()
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    # ── Config ────────────────────────────────────────────────────────────
    def cargar_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                c = json.load(f)
            self.dest_dir.set(c.get("dest_dir", ""))
            self.onefile_var.set(c.get("onefile", True))
            self.noconsole_var.set(c.get("noconsole", True))
            self.abrir_var.set(c.get("abrir", True))
            self.informe_var.set(c.get("informe", True))
            self.icono.set(c.get("icono", ""))
        except Exception:
            pass

    def guardar_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "dest_dir": self.dest_dir.get(),
                    "onefile": self.onefile_var.get(),
                    "noconsole": self.noconsole_var.get(),
                    "abrir": self.abrir_var.get(),
                    "informe": self.informe_var.get(),
                    "icono": self.icono.get(),
                }, f, indent=2)
        except Exception:
            pass

    def al_cerrar(self):
        self.guardar_config()
        self.root.destroy()

    # ── Interfaz ──────────────────────────────────────────────────────────
    def crear_componentes(self):
        b = ("Arial", 10, "bold")

        # Origen
        tk.Label(self.root, text="Opción A: seleccionar archivo existente (.py / .txt):", font=b)\
            .pack(anchor="w", padx=20, pady=(12, 2))
        fa = tk.Frame(self.root); fa.pack(fill="x", padx=20, pady=3)
        tk.Entry(fa, textvariable=self.ruta_archivo).pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Button(fa, text="Buscar...", command=self.buscar_archivo).pack(side="right")

        tk.Label(self.root, text="Opción B: o pega el código Python aquí:", font=b)\
            .pack(anchor="w", padx=20, pady=(8, 2))
        self.editor_codigo = scrolledtext.ScrolledText(
            self.root, height=9, bg="#1E1E1E", fg="#D4D4D4",
            font=("Consolas", 10), insertbackground="white")
        self.editor_codigo.pack(fill="x", padx=20, pady=3)

        # Destino y nombre
        marco = tk.LabelFrame(self.root, text=" Salida ", font=b)
        marco.pack(fill="x", padx=20, pady=8)
        marco.columnconfigure(1, weight=1)

        tk.Label(marco, text="Carpeta destino:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        tk.Entry(marco, textvariable=self.dest_dir).grid(row=0, column=1, sticky="we", padx=4)
        tk.Button(marco, text="Examinar...", command=self.elegir_destino).grid(row=0, column=2, padx=8)

        tk.Label(marco, text="Nombre del .exe:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        tk.Entry(marco, textvariable=self.nombre_exe).grid(row=1, column=1, sticky="we", padx=4)
        tk.Label(marco, text="(sin .exe)", fg="gray").grid(row=1, column=2, sticky="w", padx=8)

        tk.Label(marco, text="Icono (.ico):").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        tk.Entry(marco, textvariable=self.icono).grid(row=2, column=1, sticky="we", padx=4)
        tk.Button(marco, text="Elegir...", command=self.elegir_icono).grid(row=2, column=2, padx=8)

        tk.Label(marco, text="Dejar vacío = junto al archivo origen (o carpeta actual si pegas código).",
                 fg="gray", font=("Arial", 8)).grid(row=3, column=0, columnspan=3, sticky="w", padx=8)

        # Opciones
        fo = tk.Frame(self.root); fo.pack(fill="x", padx=20)
        tk.Checkbutton(fo, text="Un solo archivo (--onefile)", variable=self.onefile_var).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(fo, text="Sin consola (--noconsole)", variable=self.noconsole_var).grid(row=0, column=1, sticky="w", padx=20)
        tk.Checkbutton(fo, text="Abrir carpeta al terminar", variable=self.abrir_var).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(fo, text="Guardar informe de seguridad (.txt)", variable=self.informe_var).grid(row=1, column=1, sticky="w", padx=20)

        # Consola
        tk.Label(self.root, text="Salida de depuración y estado:", font=b)\
            .pack(anchor="w", padx=20, pady=(8, 2))
        self.consola = scrolledtext.ScrolledText(self.root, height=12, bg="black", fg="lightgreen", font=("Consolas", 9))
        self.consola.pack(fill="both", expand=True, padx=20, pady=3)
        self.consola.tag_config("ERROR", foreground="#FF5555")
        self.consola.tag_config("AVISO", foreground="#FFD24D")
        self.consola.tag_config("OK", foreground="#55FF88")
        self.consola.tag_config("INFO", foreground="lightgreen")

        # Botones
        fb = tk.Frame(self.root); fb.pack(fill="x", padx=20, pady=12)
        self.btn_verificar = tk.Button(fb, text="Solo verificar reglas", font=("Arial", 10, "bold"),
                                       bg="#2D6CDF", fg="white", command=self.solo_verificar)
        self.btn_verificar.pack(side="left", padx=(0, 10), ipady=6)
        self.btn_compilar = tk.Button(fb, text="VERIFICAR Y CREAR EXE", font=("Arial", 11, "bold"),
                                      bg="#107C41", fg="white", command=self.iniciar_proceso_hilo)
        self.btn_compilar.pack(side="left", expand=True, fill="x", ipady=6)

    # ── Utilidades UI ─────────────────────────────────────────────────────
    def ui(self, fn):
        self.root.after(0, fn)

    def log(self, texto, nivel="INFO"):
        def _l():
            self.consola.insert(tk.END, texto + "\n", nivel)
            self.consola.see(tk.END)
        self.ui(_l)

    def set_botones(self, activos):
        estado = "normal" if activos else "disabled"
        def _s():
            self.btn_compilar.config(state=estado,
                                     text="VERIFICAR Y CREAR EXE" if activos else "Procesando de forma aislada...")
            self.btn_verificar.config(state=estado)
        self.ui(_s)

    def buscar_archivo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Scripts de Python o Texto", "*.py *.txt")])
        if archivo:
            self.ruta_archivo.set(archivo)
            self.editor_codigo.delete("1.0", tk.END)
            if not self.nombre_exe.get().strip():
                self.nombre_exe.set(os.path.splitext(os.path.basename(archivo))[0])

    def elegir_destino(self):
        d = filedialog.askdirectory(title="Carpeta donde guardar el .exe")
        if d:
            self.dest_dir.set(d)

    def elegir_icono(self):
        f = filedialog.askopenfilename(filetypes=[("Icono", "*.ico")])
        if f:
            self.icono.set(f)

    # ── Lectura del código ────────────────────────────────────────────────
    @staticmethod
    def leer_archivo(ruta):
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(ruta, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError("No se pudo leer el archivo con ninguna codificación conocida.")

    def snapshot(self):
        """Lee todos los valores de la interfaz (hilo principal)."""
        return {
            "pegado": self.editor_codigo.get("1.0", tk.END).strip(),
            "archivo": self.ruta_archivo.get().strip(),
            "dest": self.dest_dir.get().strip(),
            "nombre": self.nombre_exe.get().strip(),
            "icono": self.icono.get().strip(),
            "onefile": self.onefile_var.get(),
            "noconsole": self.noconsole_var.get(),
            "abrir": self.abrir_var.get(),
            "informe": self.informe_var.get(),
        }

    def obtener_codigo(self, o):
        if o["pegado"]:
            return o["pegado"], "broma_automatica", os.getcwd()
        base = os.path.splitext(os.path.basename(o["archivo"]))[0]
        return self.leer_archivo(o["archivo"]), base, os.path.dirname(o["archivo"])

    # ── Verificación ──────────────────────────────────────────────────────
    def ejecutar_verificacion(self, codigo, noconsole):
        self.log("─── VERIFICACIÓN DE REGLAS ───", "INFO")
        res = verificar_reglas(codigo, noconsole)
        for nivel, texto in res:
            icono = {"OK": "[ OK ]", "AVISO": "[AVISO]", "ERROR": "[ERROR]"}[nivel]
            self.log(f" {icono} {texto}", nivel)
        errores = sum(1 for n, _ in res if n == "ERROR")
        avisos = sum(1 for n, _ in res if n == "AVISO")
        self.log(f"Resumen: {errores} regla(s) incumplida(s), {avisos} aviso(s). "
                 f"(Solo informativo: no se detiene el proceso)", "ERROR" if errores else ("AVISO" if avisos else "OK"))
        return res, errores, avisos

    def solo_verificar(self):
        o = self.snapshot()
        if not o["archivo"] and not o["pegado"]:
            messagebox.showerror("Error", "Selecciona un archivo (A) o pega código (B).")
            return
        self.consola.delete("1.0", tk.END)
        try:
            codigo, _, _ = self.obtener_codigo(o)
        except Exception as e:
            self.log(f"[ERROR] No se pudo leer el origen: {e}", "ERROR")
            return
        self.ejecutar_verificacion(codigo, o["noconsole"])

    # ── Compilación ───────────────────────────────────────────────────────
    def iniciar_proceso_hilo(self):
        o = self.snapshot()
        if not o["archivo"] and not o["pegado"]:
            messagebox.showerror("Error", "Debes seleccionar un archivo (A) o pegar código válido (B).")
            return
        self.guardar_config()
        self.set_botones(False)
        self.consola.delete("1.0", tk.END)
        threading.Thread(target=self.proceso_aislado_limpio, args=(o,), daemon=True).start()

    @staticmethod
    def asegurar_pyinstaller(log):
        if importlib.util.find_spec("PyInstaller") is None:
            log("    Instalando PyInstaller (primera vez)...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def proceso_aislado_limpio(self, o):
        dir_temporal = None
        resultado = None
        errores = avisos = 0
        informe = []
        try:
            codigo, nombre_base, dir_defecto = self.obtener_codigo(o)

            # Destino y nombre
            directorio_destino = o["dest"] or dir_defecto
            os.makedirs(directorio_destino, exist_ok=True)
            nombre = sanitizar_nombre(o["nombre"]) or nombre_base

            self.log(f"[1/5] Verificando reglas de seguridad...")
            res, errores, avisos = self.ejecutar_verificacion(codigo, o["noconsole"])
            informe = res
            if errores or avisos:
                self.log("      >> Se continúa igualmente con la compilación.", "AVISO")

            dir_temporal = tempfile.mkdtemp(prefix="py_isolated_comp_")
            self.log("[2/5] Preparando entorno aislado y comprobando PyInstaller...")
            self.asegurar_pyinstaller(self.log)

            script = os.path.join(dir_temporal, f"{nombre}.py")
            with open(script, "w", encoding="utf-8") as f:
                f.write(codigo)

            comando = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                       "--name", nombre,
                       "--distpath", os.path.join(dir_temporal, "out_dist"),
                       "--workpath", os.path.join(dir_temporal, "out_work"),
                       "--specpath", dir_temporal]
            if o["onefile"]:
                comando.append("--onefile")
            if o["noconsole"]:
                comando.append("--noconsole")
            if o["icono"] and os.path.isfile(o["icono"]):
                comando += ["--icon", o["icono"]]
            elif o["icono"]:
                self.log("[AVISO] El icono indicado no existe; se ignora.", "AVISO")
            comando.append(script)

            self.log("[3/5] Ejecutando PyInstaller en el directorio temporal...")
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(comando, cwd=dir_temporal, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1,
                                    creationflags=flags)
            ultimas = []
            for linea in proc.stdout:
                ultimas.append(linea.rstrip())
                ultimas = ultimas[-15:]
                if any(x in linea for x in ["INFO:", "Building", "completed", "ERROR"]):
                    self.log(f" -> {linea.strip()}")
            proc.wait()

            if o["onefile"]:
                generado = os.path.join(dir_temporal, "out_dist", f"{nombre}.exe")
            else:
                generado = os.path.join(dir_temporal, "out_dist", nombre)

            if proc.returncode == 0 and os.path.exists(generado):
                self.log("[4/5] Moviendo el resultado a la carpeta de destino...")
                final = os.path.join(directorio_destino, os.path.basename(generado))
                if os.path.isdir(final):
                    shutil.rmtree(final)
                elif os.path.exists(final):
                    os.remove(final)
                shutil.move(generado, final)
                resultado = final

                if os.path.isfile(final):
                    h = hashlib.sha256()
                    with open(final, "rb") as f:
                        for bloque in iter(lambda: f.read(1 << 20), b""):
                            h.update(bloque)
                    tam = os.path.getsize(final) / (1024 * 1024)
                    self.log(f"      Tamaño: {tam:.1f} MB | SHA-256: {h.hexdigest()}")
                    informe.append(("OK", f"SHA-256 del exe: {h.hexdigest()}"))

                if o["informe"]:
                    ruta_inf = os.path.join(directorio_destino, f"{nombre}_informe.txt")
                    with open(ruta_inf, "w", encoding="utf-8") as f:
                        f.write(f"Informe Creator Lab - {datetime.now():%Y-%m-%d %H:%M:%S}\n")
                        f.write(f"Ejecutable: {final}\n\n")
                        for nivel, texto in informe:
                            f.write(f"[{nivel}] {texto}\n")
                    self.log(f"      Informe guardado: {ruta_inf}")
            else:
                self.log("\n[ERROR] El empaquetado falló. Últimas líneas:", "ERROR")
                for l in ultimas:
                    self.log(f"   {l}", "ERROR")

        except Exception as e:
            self.log(f"\n[ERROR CRÍTICO]: {e}", "ERROR")
        finally:
            if dir_temporal:
                self.log("[5/5] Limpiando directorios transitorios...")
                shutil.rmtree(dir_temporal, ignore_errors=True)

        if resultado:
            self.log("\n¡PROCESO FINALIZADO CON ÉXITO!", "OK")
            self.log(f"Resultado: {resultado}", "OK")
            extra = ""
            if errores or avisos:
                extra = f"\n\n⚠ Verificación: {errores} regla(s) incumplida(s) y {avisos} aviso(s). Revisa la consola."
            carpeta = os.path.dirname(resultado)
            self.ui(lambda: messagebox.showinfo("Completado", f"Creado en:\n{resultado}{extra}"))
            if o["abrir"] and os.name == "nt":
                try:
                    os.startfile(carpeta)
                except Exception:
                    pass
        else:
            self.ui(lambda: messagebox.showerror("Error", "Hubo un fallo en la generación del ejecutable."))

        self.set_botones(True)


if __name__ == "__main__":
    root = tk.Tk()
    app = SuperCompiladorApp(root)
    root.mainloop()
