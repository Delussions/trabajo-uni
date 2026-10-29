import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import heapq

# ------------------------------------------------------------------
# SIMULADOR DE RED WAN-IoT SÍSMICA: BÚSQUEDA CIEGA (BFS/UCS) VS. A*
# ------------------------------------------------------------------

class SimuladorRedWANIoT:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Simulador de Red WAN-IoT Sísmica - Búsqueda BFS, UCS y A*")
        self.ventana.geometry("1150x760")
        self.ventana.minsize(900, 650)
        self.ventana.configure(bg="#eef3f8")

        # Posiciones de los 8 routers en el canvas (acorde a la presentación)
        self.posiciones = {
            "R0": (110, 270),
            "R1": (350, 110),
            "R2": (380, 270),
            "R3": (350, 430),
            "R4": (670, 110),
            "R5": (670, 270),
            "R6": (670, 430),
            "R7": (960, 270)
        }

        # Grafo original: 8 nodos y 12 enlaces con su costo real g(n) en milisegundos (ms)
        self.red_original = {
            "R0": [("R1", 5.0), ("R2", 3.5), ("R3", 3.0)],
            "R1": [("R0", 5.0), ("R2", 3.5), ("R4", 4.5), ("R7", 19.0)],
            "R2": [("R0", 3.5), ("R1", 3.5), ("R3", 4.5), ("R5", 3.5)],
            "R3": [("R0", 3.0), ("R2", 4.5), ("R6", 5.5)],
            "R4": [("R1", 4.5), ("R7", 6.0)],
            "R5": [("R2", 3.5), ("R7", 4.0)],
            "R6": [("R3", 5.5), ("R7", 7.5)],
            "R7": [("R1", 19.0), ("R4", 6.0), ("R5", 4.0), ("R6", 7.5)]
        }

        # Heurística h(n): retardo mínimo físico por GPS hacia la meta R7 (en ms)
        self.heuristica = {
            "R0": 8.0,
            "R1": 6.4,
            "R2": 5.5,
            "R3": 9.6,
            "R4": 3.8,
            "R5": 3.0,
            "R6": 5.0,
            "R7": 0.0
        }

        self.red = {
            nodo: vecinos.copy()
            for nodo, vecinos in self.red_original.items()
        }

        self.sla_max = 15.0  # Límite estricto de latencia para la alerta sísmica (ms)
        self.origen = "R0"
        self.destino = "R7"
        self.enlaces_averiados = set()
        self.ruta = []
        self.visitados = set()

        self.crear_interfaz()
        self.dibujar_grafo()

    def crear_interfaz(self):
        # Título principal
        titulo = tk.Label(
            self.ventana,
            text="SIMULADOR WAN-IoT SÍSMICO - BÚSQUEDA CIEGA (BFS / UCS) VS. INFORMADA (A*)",
            font=("Arial", 16, "bold"),
            bg="#17365d",
            fg="white",
            pady=14
        )
        titulo.pack(fill="x")

        # Panel superior de controles (Origen, Destino y Fallas)
        controles_frame = tk.Frame(self.ventana, bg="#eef3f8")
        controles_frame.pack(pady=10)

        tk.Label(controles_frame, text="Origen (S0):", font=("Arial", 10, "bold"), bg="#eef3f8", fg="#17365d").pack(side="left", padx=5)
        self.combo_origen = ttk.Combobox(controles_frame, values=list(self.posiciones.keys()), width=5, state="readonly")
        self.combo_origen.set(self.origen)
        self.combo_origen.pack(side="left", padx=5)
        self.combo_origen.bind("<<ComboboxSelected>>", self.actualizar_origen_destino)

        tk.Label(controles_frame, text="Destino (Meta):", font=("Arial", 10, "bold"), bg="#eef3f8", fg="#17365d").pack(side="left", padx=15)
        self.combo_destino = ttk.Combobox(controles_frame, values=list(self.posiciones.keys()), width=5, state="readonly")
        self.combo_destino.set(self.destino)
        self.combo_destino.pack(side="left", padx=5)
        self.combo_destino.bind("<<ComboboxSelected>>", self.actualizar_origen_destino)

        tk.Label(controles_frame, text="Enlace a romper/restaurar:", font=("Arial", 10, "bold"), bg="#eef3f8", fg="#17365d").pack(side="left", padx=20)

        # Obtener lista de los 12 enlaces únicos posibles
        todos_enlaces = []
        vistos = set()
        for nodo, vecinos in self.red_original.items():
            for v, _ in vecinos:
                par = tuple(sorted((nodo, v)))
                if par not in vistos:
                    vistos.add(par)
                    todos_enlaces.append(f"{par[0]} - {par[1]}")

        self.combo_enlaces = ttk.Combobox(controles_frame, values=todos_enlaces, width=12, state="readonly")
        if todos_enlaces:
            self.combo_enlaces.set("R2 - R5")
        self.combo_enlaces.pack(side="left", padx=5)

        # Área principal de dibujo (Canvas)
        self.canvas = tk.Canvas(
            self.ventana,
            bg="white",
            highlightthickness=1,
            highlightbackground="#cbd5e1"
        )
        self.canvas.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        # Panel inferior de botones de acción
        panel_botones = tk.Frame(self.ventana, bg="#eef3f8")
        panel_botones.pack(pady=10)

        botones = [
            ("Buscar Ruta BFS (Saltos)", self.buscar_ruta_bfs, "#2563eb"),
            ("Buscar Ruta UCS (Costo g)", lambda: self.buscar_ruta_costo(usar_heuristica=False), "#0284c7"),
            ("Buscar Ruta A* (g + h)", lambda: self.buscar_ruta_costo(usar_heuristica=True), "#16a34a"),
            ("Simular Falla de Enlace", self.simular_falla, "#dc2626"),
            ("Restaurar Enlace", self.restaurar_enlace, "#0f766e"),
            ("Reiniciar Todo", self.reiniciar, "#475569")
        ]

        for texto, funcion, color in botones:
            tk.Button(
                panel_botones,
                text=texto,
                command=funcion,
                font=("Arial", 10, "bold"),
                bg=color,
                fg="white",
                activeforeground="white",
                activebackground=color,
                relief="flat",
                padx=12,
                pady=8,
                cursor="hand2"
            ).pack(side="left", padx=6)

        # Mensajes y resultados
        self.resultado = tk.Label(
            self.ventana,
            text="Estado: Red WAN-IoT lista (SLA < 15.0 ms). Selecciona un algoritmo (BFS, UCS o A*) para comparar.",
            font=("Arial", 11, "bold"),
            bg="#eef3f8",
            fg="#17365d",
            wraplength=1080,
            justify="center"
        )
        self.resultado.pack(pady=(2, 2))

        leyenda = tk.Label(
            self.ventana,
            text="Gris: Enlace activo (costo g en ms)  |  Verde: Ruta encontrada  |  Rojo punteado: Enlace averiado  |  Naranja: Nodos expandidos",
            font=("Arial", 9),
            bg="#eef3f8",
            fg="#475569"
        )
        leyenda.pack(pady=(0, 10))

    def actualizar_origen_destino(self, event=None):
        self.origen = self.combo_origen.get()
        self.destino = self.combo_destino.get()
        self.ruta = []
        self.visitados = set()
        self.dibujar_grafo()
        self.resultado.config(
            text=f"Origen cambiado a [{self.origen}] y Destino a [{self.destino}]. Red lista.",
            fg="#17365d"
        )

    def calcular_latencia(self, ruta):
        total = 0.0
        for i in range(len(ruta) - 1):
            u, v = ruta[i], ruta[i + 1]
            for vecino, peso in self.red[u]:
                if vecino == v:
                    total += peso
                    break
        return total

    def dibujar_grafo(self):
        self.canvas.delete("all")
        enlaces_dibujados = set()

        # Dibujar conexiones (aristas)
        for nodo, vecinos in self.red_original.items():
            for vecino, peso in vecinos:
                enlace = tuple(sorted((nodo, vecino)))

                if enlace in enlaces_dibujados:
                    continue
                enlaces_dibujados.add(enlace)

                x1, y1 = self.posiciones[nodo]
                x2, y2 = self.posiciones[vecino]

                # Determinar estilos de línea
                if enlace in self.enlaces_averiados:
                    color = "#dc2626"
                    ancho = 4
                    estilo = (8, 5)
                elif (
                    self.ruta
                    and nodo in self.ruta
                    and vecino in self.ruta
                    and abs(self.ruta.index(nodo) - self.ruta.index(vecino)) == 1
                ):
                    color = "#16a34a"
                    ancho = 5
                    estilo = ()
                else:
                    color = "#94a3b8"
                    ancho = 2
                    estilo = ()

                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=ancho,
                    dash=estilo
                )

                # Etiqueta central del enlace (latencia en ms)
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_rectangle(
                    mx - 24, my - 10,
                    mx + 24, my + 10,
                    fill="white",
                    outline=""
                )
                self.canvas.create_text(
                    mx, my,
                    text="X" if enlace in self.enlaces_averiados else f"{peso} ms",
                    fill=color,
                    font=("Arial", 8, "bold")
                )

        # Dibujar nodos (routers)
        for nodo, (x, y) in self.posiciones.items():
            if nodo == self.origen:
                color = "#0891b2"
                etiqueta = "ORIGEN"
            elif nodo == self.destino:
                color = "#7c3aed"
                etiqueta = "META"
            elif nodo in self.visitados:
                color = "#f59e0b"
                etiqueta = "VISITADO"
            else:
                color = "#2563eb"
                etiqueta = ""

            radio = 26
            self.canvas.create_oval(
                x - radio, y - radio,
                x + radio, y + radio,
                fill=color,
                outline="white",
                width=3
            )

            self.canvas.create_text(
                x, y,
                text=nodo,
                fill="white",
                font=("Arial", 13, "bold")
            )

            # Mostrar heurística h(n) arriba del nodo
            h_val = self.heuristica.get(nodo, 0.0)
            self.canvas.create_text(
                x, y - 36,
                text=f"h={h_val} ms",
                fill="#475569",
                font=("Arial", 8, "bold")
            )

            if etiqueta:
                self.canvas.create_text(
                    x, y + 38,
                    text=etiqueta,
                    fill=color,
                    font=("Arial", 8, "bold")
                )

    def buscar_ruta_bfs(self):
        if self.origen == self.destino:
            messagebox.showwarning("Advertencia", "El nodo de origen y el destino no pueden ser el mismo.")
            return

        # Algoritmo BFS estándar (búsqueda ciega por número de saltos)
        cola = deque([self.origen])
        visitados_ram = {self.origen}
        padre = {self.origen: None}
        orden = []

        while cola:
            actual = cola.popleft()
            orden.append(actual)

            if actual == self.destino:
                break

            for vecino, _ in self.red[actual]:
                if vecino not in visitados_ram:
                    visitados_ram.add(vecino)
                    padre[vecino] = actual
                    cola.append(vecino)

        self.visitados = set(orden)

        if self.destino not in padre:
            self.ruta = []
            self.dibujar_grafo()
            self.resultado.config(
                text=f"¡Atención! No existe ruta disponible entre {self.origen} y {self.destino}.",
                fg="#dc2626"
            )
            return

        # Reconstruir camino
        ruta = []
        actual = self.destino
        while actual is not None:
            ruta.append(actual)
            actual = padre[actual]

        self.ruta = list(reversed(ruta))
        saltos = len(self.ruta) - 1
        latencia = self.calcular_latencia(self.ruta)
        estado_sla = "CUMPLE SLA" if latencia < self.sla_max else "FALLA SLA (> 15 ms)"
        color_texto = "#15803d" if latencia < self.sla_max else "#dc2626"

        self.dibujar_grafo()
        self.resultado.config(
            text=(
                f"[BFS] Ruta: {' -> '.join(self.ruta)} ({saltos} saltos)  |  "
                f"Latencia: {latencia:.1f} ms [{estado_sla}]  |  "
                f"Expandidos: {len(orden)}/8 ({' -> '.join(orden)})  |  RAM: {len(visitados_ram)}/8"
            ),
            fg=color_texto
        )

    def buscar_ruta_costo(self, usar_heuristica=True):
        if self.origen == self.destino:
            messagebox.showwarning("Advertencia", "El nodo de origen y el destino no pueden ser el mismo.")
            return

        nombre_alg = "A*" if usar_heuristica else "UCS"
        h_ini = self.heuristica.get(self.origen, 0.0) if (usar_heuristica and self.destino == "R7") else 0.0

        # Cola de prioridad: (f(n), g(n), nodo)
        cola = [(h_ini, 0.0, self.origen)]
        expandidos = set()
        costo_g = {self.origen: 0.0}
        padre = {self.origen: None}
        orden = []

        while cola:
            f_actual, g_actual, actual = heapq.heappop(cola)

            if actual in expandidos:
                continue

            expandidos.add(actual)
            orden.append(actual)

            if actual == self.destino:
                break

            for vecino, peso in self.red[actual]:
                nuevo_g = g_actual + peso
                if vecino not in costo_g or nuevo_g < costo_g[vecino]:
                    costo_g[vecino] = nuevo_g
                    padre[vecino] = actual
                    h_vecino = self.heuristica.get(vecino, 0.0) if (usar_heuristica and self.destino == "R7") else 0.0
                    f_vecino = nuevo_g + h_vecino
                    heapq.heappush(cola, (f_vecino, nuevo_g, vecino))

        self.visitados = set(orden)

        if self.destino not in expandidos:
            self.ruta = []
            self.dibujar_grafo()
            self.resultado.config(
                text=f"¡Atención! No existe ruta disponible entre {self.origen} y {self.destino}.",
                fg="#dc2626"
            )
            return

        # Reconstruir camino
        ruta = []
        actual = self.destino
        while actual is not None:
            ruta.append(actual)
            actual = padre[actual]

        self.ruta = list(reversed(ruta))
        latencia = costo_g[self.destino]
        estado_sla = "CUMPLE SLA" if latencia < self.sla_max else "FALLA SLA (> 15 ms)"
        color_texto = "#15803d" if latencia < self.sla_max else "#dc2626"

        self.dibujar_grafo()
        self.resultado.config(
            text=(
                f"[{nombre_alg}] Ruta óptima: {' -> '.join(self.ruta)}  |  "
                f"Latencia: {latencia:.1f} ms [{estado_sla}]  |  "
                f"Expandidos: {len(orden)}/8 ({' -> '.join(orden)})  |  RAM: {len(costo_g)}/8"
            ),
            fg=color_texto
        )

    def simular_falla(self):
        seleccion = self.combo_enlaces.get()
        if not seleccion:
            return

        n1, n2 = seleccion.split(" - ")
        enlace = tuple(sorted((n1, n2)))

        if enlace in self.enlaces_averiados:
            self.resultado.config(text=f"El enlace {n1}-{n2} ya se encuentra averiado.", fg="#dc2626")
            return

        # Desconectar en el grafo activo
        self.red[n1] = [(v, p) for v, p in self.red[n1] if v != n2]
        self.red[n2] = [(v, p) for v, p in self.red[n2] if v != n1]

        self.enlaces_averiados.add(enlace)
        self.ruta = []
        self.visitados = set()

        self.dibujar_grafo()
        self.resultado.config(
            text=f"¡Falla simulada! Enlace {n1}-{n2} fuera de servicio. Pulsa un botón de búsqueda para recalcular.",
            fg="#dc2626"
        )

    def restaurar_enlace(self):
        seleccion = self.combo_enlaces.get()
        if not seleccion:
            return

        n1, n2 = seleccion.split(" - ")
        enlace = tuple(sorted((n1, n2)))

        if enlace not in self.enlaces_averiados:
            self.resultado.config(text=f"El enlace {n1}-{n2} ya está activo.", fg="#0f766e")
            return

        # Restaurar conexiones desde el grafo original
        for v, p in self.red_original[n1]:
            if v == n2:
                self.red[n1].append((n2, p))
                self.red[n2].append((n1, p))
                break

        self.enlaces_averiados.remove(enlace)
        self.ruta = []
        self.visitados = set()

        self.dibujar_grafo()
        self.resultado.config(
            text=f"Enlace {n1}-{n2} restaurado exitosamente.",
            fg="#0f766e"
        )

    def reiniciar(self):
        self.red = {
            nodo: vecinos.copy()
            for nodo, vecinos in self.red_original.items()
        }
        self.enlaces_averiados.clear()
        self.ruta = []
        self.visitados = set()
        self.dibujar_grafo()
        self.resultado.config(
            text="Simulación reiniciada. Todos los enlaces están activos.",
            fg="#17365d"
        )


# Iniciar la aplicación
if __name__ == "__main__":
    ventana = tk.Tk()
    app = SimuladorRedWANIoT(ventana)
    ventana.mainloop()
