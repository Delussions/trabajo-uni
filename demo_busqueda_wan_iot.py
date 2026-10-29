#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Inteligencia Artificial | Unidad: Algoritmos de Búsqueda
Demostración Interactiva en Vivo: Búsqueda Ciega (BFS / UCS) vs. Informada (A*)
Escenario: Enrutamiento SDN de Baja Latencia en Red WAN-IoT Sísmica -> Edge-IA
================================================================================

Ejecución:
    python demo_busqueda_wan_iot.py

Atajos de teclado durante la exposición:
    [1]       -> Simular BFS (Búsqueda Ciega por Saltos)
    [2]       -> Simular UCS (Búsqueda Ciega por Costo Uniforme g(n))
    [3]       -> Simular A*  (Búsqueda Informada f(n) = g(n) + h(n))
    [Espacio] -> Pausar / Reanudar animación paso a paso
    [Derecha] -> Avanzar un paso manualmente
    [Izq.]    -> Retroceder un paso
    [G]       -> Activar / Desactivar GPS h(n) (demuestra respaldo limpio a UCS)
    [R]       -> Restaurar todos los enlaces de la red
    Clic en cualquier enlace del mapa -> Simular caída o activación de enlace
"""

import sys
import math
import heapq
from collections import deque

# Asegurar salida UTF-8 limpia en terminales de Windows (PowerShell / CMD / VS Code)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# 1. DEFINICIÓN DEL ESCENARIO DE RED WAN-IoT Y FORMULACIÓN FORMAL EN IA
# ==============================================================================

SLA_MAX_MS = 15.0          # Límite estricto de latencia para alerta sísmica (ms)
VEL_LUZ_FIBRA = 200.0      # Velocidad de propagación óptica en fibra (km/ms)

# Espacio de Estados S = {R0, ..., R7} con coordenadas GPS reales (km) e IPs
NODOS_RED = {
    "R0": {"nombre": "GW-IoT Sísmico",   "rol": "ORIGEN (S0)",  "ip": "10.0.0.1",  "gps": (0.0, 0.0)},
    "R1": {"nombre": "RTR-Norte",        "rol": "Router WAN",   "ip": "10.0.1.1",  "gps": (400.0, 450.0)},
    "R2": {"nombre": "RTR-Costa",        "rol": "Router WAN",   "ip": "10.0.2.1",  "gps": (500.0, -150.0)},
    "R3": {"nombre": "RTR-Oeste",        "rol": "Router WAN",   "ip": "10.0.3.1",  "gps": (-300.0, -350.0)},
    "R4": {"nombre": "RTR-Sierra",       "rol": "Router WAN",   "ip": "10.0.4.1",  "gps": (950.0, 400.0)},
    "R5": {"nombre": "RTR-Centro",       "rol": "Router WAN",   "ip": "10.0.5.1",  "gps": (1000.0, -100.0)},
    "R6": {"nombre": "RTR-Sur",          "rol": "Router WAN",   "ip": "10.0.6.1",  "gps": (750.0, -550.0)},
    "R7": {"nombre": "Servidor Edge-IA", "rol": "META (CNN-1D)","ip": "10.0.7.10", "gps": (1600.0, 0.0)},
}

# 12 Enlaces Directos Bidireccionales: (Nodo_A, Nodo_B, Latencia_TWAMP_ms, Tecnología)
ENLACES_BASE = [
    ("R0", "R1", 5.0,  "5G"),
    ("R0", "R2", 3.5,  "DWDM"),
    ("R0", "R3", 3.0,  "Fibra"),
    ("R1", "R2", 3.5,  "Metro"),
    ("R1", "R4", 4.5,  "5G"),
    ("R1", "R7", 19.0, "LTE"),
    ("R2", "R3", 4.5,  "Regional"),
    ("R2", "R5", 3.5,  "DWDM"),
    ("R3", "R6", 5.5,  "Sub-GHz"),
    ("R4", "R7", 6.0,  "Metro"),
    ("R5", "R7", 4.0,  "DWDM"),
    ("R6", "R7", 7.5,  "Regional"),
]


class ProblemaEnrutamientoSDN:
    """
    Formulación formal de los 5 elementos de un Problema de Búsqueda en IA:
      1. Estado Inicial (S0): R0 (Gateway IoT Sísmico, IP 10.0.0.1)
      2. Prueba de Meta:      Meta(n) <=> (n = R7, Servidor Edge-IA, IP 10.0.7.10)
      3. Acciones y Modelo de Transición: T(n, Enviar(n -> m)) = m para (n, m) en E
      4. Costo de Ruta g(n):  Suma de latencias reales TWAMP en milisegundos
      5. Heurística h(n):     d_GPS(n, R7) / 200 km/ms (admisible y consistente)
    """

    def __init__(self, estado_inicial="R0", estado_meta="R7", enlaces_caidos=None, usar_gps=True):
        self.s0 = estado_inicial
        self.meta = estado_meta
        self.enlaces_caidos = set(enlaces_caidos or [])
        self.usar_gps = usar_gps
        self.adyacencia = {nid: [] for nid in NODOS_RED}

        for u, v, lat_ms, tec in ENLACES_BASE:
            par = tuple(sorted((u, v)))
            if par not in self.enlaces_caidos:
                self.adyacencia[u].append((v, lat_ms, tec))
                self.adyacencia[v].append((u, lat_ms, tec))

        for nid in self.adyacencia:
            self.adyacencia[nid].sort(key=lambda item: item[0])

    def es_meta(self, estado):
        """2b. Prueba de Meta (Goal Test): verifica llegada al Servidor Edge-IA R7."""
        return estado == self.meta

    def acciones(self, estado):
        """3. Acciones A(n): enlaces directos activos disponibles desde el router n."""
        return self.adyacencia.get(estado, [])

    def transicion(self, estado, vecino):
        """3. Modelo de Transición T(n, Enviar(n -> m)) = m."""
        return vecino

    def distancia_gps_km(self, u, v=None):
        """Distancia euclidiana en línea recta entre dos routers usando GPS (km)."""
        v = v or self.meta
        x1, y1 = NODOS_RED[u]["gps"]
        x2, y2 = NODOS_RED[v]["gps"]
        return math.hypot(x2 - x1, y2 - y1)

    def heuristica(self, estado):
        """
        5. Función Heurística Física h(n):
           Tiempo mínimo físico de propagación óptica en línea recta hacia R7.
           Si falla el GPS (usar_gps=False), retorna h(n) = 0 (degrada limpiamente a UCS).
        """
        if not self.usar_gps or estado == self.meta:
            return 0.0
        d_km = self.distancia_gps_km(estado, self.meta)
        return math.floor((d_km / VEL_LUZ_FIBRA) * 10.0) / 10.0


# ==============================================================================
# 2. ALGORITMOS DE BÚSQUEDA: CIEGA (BFS y UCS) VS. INFORMADA (A*)
# ==============================================================================

def calcular_latencia_ruta(problema, ruta):
    """Suma la latencia real extremo a extremo (ms) de cualquier ruta."""
    if not ruta or len(ruta) < 2:
        return 0.0
    total = 0.0
    for i in range(len(ruta) - 1):
        u, v = ruta[i], ruta[i + 1]
        for vec, costo, _ in problema.acciones(u):
            if vec == v:
                total += costo
                break
    return round(total, 2)


def busqueda_bfs(problema):
    """
    BÚSQUEDA CIEGA EN ANCHURA (BFS):
    Explora por niveles (mínimo número de saltos) mediante una cola FIFO,
    ignorando las latencias reales en milisegundos.
    """
    cola = deque([(problema.s0, [problema.s0], 0)])
    visitados_ram = {problema.s0}
    ruta_conocida = {problema.s0: [problema.s0]}
    saltos_conocidos = {problema.s0: 0}
    expandidos = []
    pasos = []

    while cola:
        actual, ruta, saltos = cola.popleft()
        expandidos.append(actual)
        g_real = calcular_latencia_ruta(problema, ruta)
        es_fin = problema.es_meta(actual)

        nuevos = []
        if not es_fin:
            for vecino, _, _ in problema.acciones(actual):
                if vecino not in visitados_ram:
                    visitados_ram.add(vecino)
                    nueva_r = ruta + [vecino]
                    ruta_conocida[vecino] = nueva_r
                    saltos_conocidos[vecino] = saltos + 1
                    cola.append((vecino, nueva_r, saltos + 1))
                    nuevos.append(vecino)

        frontera_vista = [
            {"nodo": n, "etiqueta": f"{s} saltos ({calcular_latencia_ruta(problema, r):.1f} ms)",
             "g": calcular_latencia_ruta(problema, r), "h": 0.0, "f": float(s)}
            for (n, r, s) in list(cola)
        ]
        info_nodos = {
            n_ram: {
                "g": calcular_latencia_ruta(problema, ruta_conocida[n_ram]),
                "h": 0.0,
                "f": float(saltos_conocidos[n_ram]),
            }
            for n_ram in visitados_ram
        }

        msg = (f"¡META {actual} alcanzada en {saltos} saltos! Latencia real = {g_real:.1f} ms."
               if es_fin else
               f"Expande {actual} (nivel {saltos}, g={g_real:.1f} ms) -> encola {', '.join(nuevos) if nuevos else 'ninguno'}.")

        pasos.append({
            "paso": len(pasos) + 1,
            "actual": actual,
            "ruta_actual": list(ruta),
            "g": g_real,
            "h": 0.0,
            "f": float(saltos),
            "closed": list(expandidos),
            "open": frontera_vista,
            "ram_set": sorted(visitados_ram),
            "info_nodos": info_nodos,
            "es_meta": es_fin,
            "mensaje": msg,
        })

        if es_fin:
            return {
                "algoritmo": "BFS",
                "titulo": "BFS · Búsqueda Ciega por Saltos",
                "exito": True,
                "ruta": ruta,
                "saltos": len(ruta) - 1,
                "latencia_ms": g_real,
                "cumple_sla": g_real < SLA_MAX_MS,
                "nodos_expandidos": len(expandidos),
                "nodos_en_ram": len(visitados_ram),
                "orden_expansion": expandidos,
                "pasos": pasos,
            }

    return {"algoritmo": "BFS", "titulo": "BFS · Ciega por Saltos", "exito": False,
            "ruta": [], "saltos": 0, "latencia_ms": math.inf, "cumple_sla": False,
            "nodos_expandidos": len(expandidos), "nodos_en_ram": len(visitados_ram),
            "orden_expansion": expandidos, "pasos": pasos}


def _busqueda_costo_prioridad(problema, usar_heuristica=True):
    """
    Motor de Cola de Prioridad (heapq) para:
      - UCS (usar_heuristica=False): ordena por f(n) = g(n)
      - A*  (usar_heuristica=True):  ordena por f(n) = g(n) + h(n)
    """
    nombre = "A*" if usar_heuristica else "UCS"
    titulo = ("A* · Búsqueda Informada  f(n) = g(n) + h(n)"
              if usar_heuristica else
              "UCS · Búsqueda Ciega por Costo  g(n)")

    h0 = problema.heuristica(problema.s0) if usar_heuristica else 0.0
    frontera = [(round(h0, 4), 0.0, problema.s0, [problema.s0])]
    mejor_g = {problema.s0: 0.0}
    nodos_ram = {problema.s0}
    closed = []
    closed_set = set()
    pasos = []

    while frontera:
        f_act, g_act, actual, ruta = heapq.heappop(frontera)
        if actual in closed_set:
            continue

        closed.append(actual)
        closed_set.add(actual)
        h_act = round(f_act - g_act, 2)
        es_fin = problema.es_meta(actual)

        generados = []
        if not es_fin:
            for vecino, costo_enlace, _ in problema.acciones(actual):
                if vecino in closed_set:
                    continue
                nuevo_g = round(g_act + costo_enlace, 4)
                if vecino not in mejor_g or nuevo_g < mejor_g[vecino]:
                    mejor_g[vecino] = nuevo_g
                    nodos_ram.add(vecino)
                    hv = problema.heuristica(vecino) if usar_heuristica else 0.0
                    nuevo_f = round(nuevo_g + hv, 4)
                    heapq.heappush(frontera, (nuevo_f, nuevo_g, vecino, ruta + [vecino]))
                    generados.append(f"{vecino}({'f' if usar_heuristica else 'g'}={nuevo_f:.1f})")

        mejores_abiertos = {}
        for f_i, g_i, n_i, _ in frontera:
            if n_i not in closed_set and abs(g_i - mejor_g.get(n_i, -1)) < 1e-6:
                mejores_abiertos[n_i] = (f_i, g_i, round(f_i - g_i, 2))

        frontera_ordenada = sorted(mejores_abiertos.items(), key=lambda kv: (kv[1][0], kv[0]))
        frontera_vista = [
            {
                "nodo": n_i,
                "etiqueta": (f"g={g_i:.1f} + h={h_i:.1f} = {f_i:.1f} ms"
                             if usar_heuristica else f"g = {g_i:.1f} ms"),
                "g": g_i, "h": h_i, "f": f_i,
            }
            for n_i, (f_i, g_i, h_i) in frontera_ordenada
        ]

        info_nodos = {}
        for n_ram, g_val in mejor_g.items():
            hv = problema.heuristica(n_ram) if usar_heuristica else 0.0
            info_nodos[n_ram] = {"g": g_val, "h": hv, "f": round(g_val + hv, 2)}

        if es_fin:
            msg = (f"¡META {actual} extraída con óptimo garantizado! "
                   f"Latencia = {g_act:.1f} ms ({len(closed)}/8 expandidos, {len(nodos_ram)}/8 en RAM).")
        else:
            det = f"g={g_act:.1f}, h={h_act:.1f}, f={f_act:.1f} ms" if usar_heuristica else f"g={g_act:.1f} ms"
            msg = f"Extrae {actual} ({det}) -> genera {', '.join(generados) if generados else 'ninguno'}."

        pasos.append({
            "paso": len(pasos) + 1,
            "actual": actual,
            "ruta_actual": list(ruta),
            "g": g_act,
            "h": h_act,
            "f": f_act,
            "closed": list(closed),
            "open": frontera_vista,
            "ram_set": sorted(nodos_ram),
            "info_nodos": info_nodos,
            "es_meta": es_fin,
            "mensaje": msg,
        })

        if es_fin:
            return {
                "algoritmo": nombre,
                "titulo": titulo,
                "exito": True,
                "ruta": ruta,
                "saltos": len(ruta) - 1,
                "latencia_ms": round(g_act, 2),
                "cumple_sla": g_act < SLA_MAX_MS,
                "nodos_expandidos": len(closed),
                "nodos_en_ram": len(nodos_ram),
                "orden_expansion": closed,
                "pasos": pasos,
            }

    return {"algoritmo": nombre, "titulo": titulo, "exito": False,
            "ruta": [], "saltos": 0, "latencia_ms": math.inf, "cumple_sla": False,
            "nodos_expandidos": len(closed), "nodos_en_ram": len(nodos_ram),
            "orden_expansion": closed, "pasos": pasos}


def busqueda_ucs(problema):
    """BÚSQUEDA CIEGA DE COSTO UNIFORME (UCS): ordena únicamente por g(n)."""
    return _busqueda_costo_prioridad(problema, usar_heuristica=False)


def busqueda_a_estrella(problema):
    """BÚSQUEDA INFORMADA A*: ordena por f(n) = g(n) + h(n)."""
    return _busqueda_costo_prioridad(problema, usar_heuristica=True)


# ==============================================================================
# 3. VERIFICACIÓN MATEMÁTICA DE ADMISIBILIDAD Y CONSISTENCIA + REPORTE CONSOLA
# ==============================================================================

def costo_real_minimo_hacia_meta(problema, origen):
    """Calcula h*(n): costo real óptimo desde cada nodo n hasta la meta R7."""
    sub = ProblemaEnrutamientoSDN(origen, problema.meta, problema.enlaces_caidos, usar_gps=False)
    return busqueda_ucs(sub)["latencia_ms"]


def imprimir_reporte_consola():
    prob = ProblemaEnrutamientoSDN()
    sep = "=" * 86
    print(sep)
    print(" DEMOSTRACIÓN IA · ENRUTAMIENTO SDN EN RED WAN-IoT SÍSMICA (SLA < 15.0 ms)")
    print(sep)
    print(f" Estado Inicial (S0): {prob.s0} ({NODOS_RED[prob.s0]['nombre']} · IP {NODOS_RED[prob.s0]['ip']})")
    print(f" Estado Meta:         {prob.meta} ({NODOS_RED[prob.meta]['nombre']} · IP {NODOS_RED[prob.meta]['ip']})")
    print(f" Grafo G = (V, E):    {len(NODOS_RED)} Nodos | {len(ENLACES_BASE)} Enlaces Directos\n")

    print(" [1] VERIFICACIÓN DE ADMISIBILIDAD DE LA HEURÍSTICA: 0 <= h(n) <= h*(n)")
    print("-" * 86)
    print(f" {'Nodo':<6} {'Dispositivo':<20} {'Dist. GPS':>11} {'h(n) [ms]':>11} {'h*(n) Real':>12} {'¿Admisible?':>14}")
    print("-" * 86)
    todo_admisible = True
    for nid in sorted(NODOS_RED):
        dkm = prob.distancia_gps_km(nid)
        hn = prob.heuristica(nid)
        h_star = costo_real_minimo_hacia_meta(prob, nid)
        ok = (0.0 <= hn <= h_star + 1e-9)
        todo_admisible = todo_admisible and ok
        print(f" {nid:<6} {NODOS_RED[nid]['nombre']:<20} {dkm:>8.1f} km {hn:>8.1f} ms {h_star:>9.1f} ms {'SÍ (OK)' if ok else 'NO':>14}")

    arcos_consistentes = 0
    total_arcos = 0
    for u in NODOS_RED:
        for v, c_uv, _ in prob.acciones(u):
            total_arcos += 1
            if prob.heuristica(u) <= c_uv + prob.heuristica(v) + 1e-9:
                arcos_consistentes += 1
    print("-" * 86)
    print(f" Admisibilidad global: {'VERIFICADA (8/8 nodos)' if todo_admisible else 'FALLO'} | "
          f"Consistencia triangular h(n) <= c(n,m)+h(m): VERIFICADA ({arcos_consistentes}/{total_arcos} arcos)\n")

    res_bfs = busqueda_bfs(prob)
    res_ucs = busqueda_ucs(prob)
    res_ast = busqueda_a_estrella(prob)

    print(" [2] TRAZA PASO A PASO DEL ALGORITMO ELEGIDO: A* — f(n) = g(n) + h(n)")
    print("-" * 86)
    for p in res_ast["pasos"]:
        cola_txt = ", ".join(f"{it['nodo']}({it['f']:.1f})" for it in p["open"]) or "vacía"
        print(f" Paso {p['paso']}: Expande {p['actual']} [g={p['g']:.1f} + h={p['h']:.1f} = f={p['f']:.1f} ms]"
              f" | OPEN: [{cola_txt}]")
    print()

    print(" [3] TABLA COMPARATIVA EMPÍRICA: BÚSQUEDA CIEGA (BFS / UCS) VS. INFORMADA (A*)")
    print("-" * 86)
    print(f" {'Algoritmo':<14} {'Ruta Hallada':<26} {'Latencia':>10} {'SLA <15ms':>11} {'Expandidos':>12} {'Nodos RAM':>11}")
    print("-" * 86)
    for r in (res_bfs, res_ucs, res_ast):
        ruta_s = " -> ".join(r["ruta"])
        sla_s = "CUMPLE" if r["cumple_sla"] else "FALLA"
        print(f" {r['algoritmo']:<14} {ruta_s:<26} {r['latencia_ms']:>7.1f} ms {sla_s:>11} "
              f"{r['nodos_expandidos']:>8} / 8 {r['nodos_en_ram']:>7} / 8")
    print(sep + "\n")


# ==============================================================================
# 4. SIMULADOR VISUAL INTERACTIVO (TKINTER) OPTIMIZADO PARA PROYECTOR DE AULA
# ==============================================================================

def construir_ventana_simulador(maximizar=True, iniciar_autoplay=True):
    import tkinter as tk

    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    # Paleta visual idéntica a la presentación (Template Lumra)
    C_BLACK = "#121212"
    C_BAR2  = "#1E1E1E"
    C_BG    = "#EAEAEA"
    C_WHITE = "#F8F8F8"
    C_LAV   = "#D5BFF8"
    C_MINT  = "#AFE4DE"
    C_PEACH = "#F4CAA5"
    C_PINK  = "#FD91BA"
    C_GRAY  = "#777777"

    POS_NORM = {
        "R0": (0.12, 0.50),
        "R1": (0.35, 0.21),
        "R2": (0.43, 0.56),
        "R3": (0.14, 0.81),
        "R4": (0.67, 0.23),
        "R5": (0.66, 0.54),
        "R6": (0.53, 0.82),
        "R7": (0.88, 0.49),
    }

    root = tk.Tk()
    root.title("Simulador IA · Enrutamiento SDN en Red WAN-IoT (BFS vs. UCS vs. A*)")
    root.configure(bg=C_BG)
    root.geometry("1366x768")
    root.minsize(1024, 660)
    if maximizar and sys.platform.startswith("win"):
        try:
            root.state("zoomed")
        except Exception:
            pass

    state = {
        "algo": "A*",
        "usar_gps": True,
        "enlaces_caidos": set(),
        "resultados": {},
        "paso_idx": 0,
        "playing": False,
        "after_id": None,
        "packet_after_id": None,
        "packet_t": 0.52,
        "edge_hitboxes": [],
    }

    # ---------------- FILA 1: ENCABEZADO ----------------
    hdr = tk.Frame(root, bg=C_BLACK, padx=16, pady=8)
    hdr.pack(side="top", fill="x")

    tk.Label(
        hdr,
        text="SIMULADOR SDN WAN-IoT · BÚSQUEDA CIEGA (BFS / UCS) VS. INFORMADA (A*)",
        font=("Segoe UI", 16, "bold"), fg=C_WHITE, bg=C_BLACK
    ).pack(side="left")

    tk.Label(
        hdr,
        text="Origen R0 (10.0.0.1) ➔ Meta Edge-IA R7 (10.0.7.10)  |  SLA < 15.0 ms",
        font=("Segoe UI", 12, "bold"), fg=C_MINT, bg=C_BLACK
    ).pack(side="right")

    # ---------------- FILA 2: BARRA DE BOTONES GRANDES (ADAPTABLE A 1280px) ----------------
    toolbar = tk.Frame(root, bg=C_BAR2, padx=14, pady=7)
    toolbar.pack(side="top", fill="x")

    grp_alg = tk.Frame(toolbar, bg=C_BAR2)
    grp_alg.pack(side="left")

    grp_sim = tk.Frame(toolbar, bg=C_BAR2)
    grp_sim.pack(side="right")

    def make_btn(parent, txt, bg_col, fg_col, cmd):
        b = tk.Button(
            parent, text=txt, command=cmd, font=("Segoe UI", 11, "bold"),
            bg=bg_col, fg=fg_col, activebackground=bg_col, activeforeground=fg_col,
            bd=0, relief="flat", padx=12, pady=6, cursor="hand2"
        )
        b.pack(side="left", padx=4)
        return b

    # ---------------- ÁREA PRINCIPAL (MAPA IZQ + PANEL DER) ----------------
    main_area = tk.Frame(root, bg=C_BG, padx=12, pady=10)
    main_area.pack(side="top", fill="both", expand=True)
    main_area.columnconfigure(0, weight=60, uniform="cols")
    main_area.columnconfigure(1, weight=40, uniform="cols")
    main_area.rowconfigure(0, weight=1)

    left_frame = tk.Frame(main_area, bg=C_BLACK, padx=3, pady=3)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    canvas = tk.Canvas(left_frame, bg=C_WHITE, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    right_frame = tk.Frame(main_area, bg=C_BG)
    right_frame.grid(row=0, column=1, sticky="nsew")

    # Tarjeta 1: Paso Actual y KPIs
    card_step = tk.Frame(right_frame, bg=C_WHITE, highlightbackground=C_BLACK, highlightthickness=3, padx=12, pady=8)
    card_step.pack(fill="x", pady=(0, 8))

    lbl_algo_badge = tk.Label(card_step, text="A* · Búsqueda Informada", font=("Segoe UI", 13, "bold"),
                              bg=C_MINT, fg=C_BLACK, padx=8, pady=4)
    lbl_algo_badge.pack(fill="x")

    lbl_step_title = tk.Label(card_step, text="Paso 1 / 4", font=("Segoe UI", 14, "bold"),
                              bg=C_WHITE, fg=C_BLACK, anchor="w", pady=4)
    lbl_step_title.pack(fill="x")

    lbl_step_msg = tk.Label(card_step, text="", font=("Segoe UI", 12), bg=C_WHITE, fg="#1E1E1E",
                            justify="left", anchor="w", wraplength=440)
    lbl_step_msg.pack(fill="x")

    kpi_row = tk.Frame(card_step, bg=C_WHITE, pady=6)
    kpi_row.pack(fill="x")
    for c_i in range(3):
        kpi_row.columnconfigure(c_i, weight=1)

    def make_kpi(col, titulo, bg_c):
        f = tk.Frame(kpi_row, bg=bg_c, highlightbackground=C_BLACK, highlightthickness=2, padx=4, pady=5)
        f.grid(row=0, column=col, sticky="nsew", padx=3)
        tk.Label(f, text=titulo, font=("Segoe UI", 10, "bold"), bg=bg_c, fg=C_BLACK).pack()
        v = tk.Label(f, text="-", font=("Segoe UI", 16, "bold"), bg=bg_c, fg=C_BLACK)
        v.pack()
        return v

    kpi_lat = make_kpi(0, "Latencia Ruta", C_PEACH)
    kpi_exp = make_kpi(1, "Expandidos", C_LAV)
    kpi_ram = make_kpi(2, "Nodos en RAM", C_MINT)

    # Tarjeta 2: Frontera OPEN y CLOSED en RAM
    card_queue = tk.Frame(right_frame, bg=C_WHITE, highlightbackground=C_BLACK, highlightthickness=3, padx=12, pady=8)
    card_queue.pack(fill="both", expand=True, pady=(0, 8))

    tk.Label(card_queue, text="MEMORIA RAM EN VIVO · COLA OPEN Y CLOSED",
             font=("Segoe UI", 11, "bold"), bg=C_BLACK, fg=C_WHITE, padx=8, pady=4).pack(fill="x")

    lbl_closed_list = tk.Label(card_queue, text="CLOSED: -", font=("Segoe UI", 12, "bold"),
                               bg=C_WHITE, fg=C_BLACK, anchor="w", justify="left", wraplength=440, pady=5)
    lbl_closed_list.pack(fill="x")

    tk.Label(card_queue, text="Frontera OPEN (ordenada por prioridad):",
             font=("Segoe UI", 11, "bold"), bg=C_WHITE, fg="#333333", anchor="w").pack(fill="x")

    open_box = tk.Frame(card_queue, bg=C_WHITE, pady=3)
    open_box.pack(fill="both", expand=True)

    # Tarjeta 3: Tabla Comparativa Permanente
    card_cmp = tk.Frame(right_frame, bg=C_WHITE, highlightbackground=C_BLACK, highlightthickness=3, padx=10, pady=8)
    card_cmp.pack(fill="x")

    tk.Label(card_cmp, text="TABLA COMPARATIVA EN VIVO (MISMO GRAFO)",
             font=("Segoe UI", 11, "bold"), bg=C_BLACK, fg=C_WHITE, padx=8, pady=4).pack(fill="x", pady=(0, 5))

    tbl_frame = tk.Frame(card_cmp, bg=C_WHITE)
    tbl_frame.pack(fill="x")
    headers = ["Algoritmo", "Ruta", "Latencia", "SLA", "Exp.", "RAM"]
    col_weights = [2, 4, 2, 1, 1, 1]
    for ci, (htxt, cw) in enumerate(zip(headers, col_weights)):
        tbl_frame.columnconfigure(ci, weight=cw)
        tk.Label(tbl_frame, text=htxt, font=("Segoe UI", 11, "bold"), bg="#DCDCDC", fg=C_BLACK,
                 padx=4, pady=4).grid(row=0, column=ci, sticky="nsew", padx=1, pady=1)

    tbl_cells = {}
    for ri, alg_key in enumerate(["BFS", "UCS", "A*"], start=1):
        tbl_cells[alg_key] = []
        for ci in range(len(headers)):
            lbl = tk.Label(tbl_frame, text="-", font=("Segoe UI", 11, "bold"), bg=C_WHITE, fg=C_BLACK, padx=4, pady=5)
            lbl.grid(row=ri, column=ci, sticky="nsew", padx=1, pady=1)
            tbl_cells[alg_key].append(lbl)

    def ajustar_wrap(_e=None):
        rw = max(320, right_frame.winfo_width() - 36)
        lbl_step_msg.configure(wraplength=rw)
        lbl_closed_list.configure(wraplength=rw)

    right_frame.bind("<Configure>", ajustar_wrap)

    # ---------------- LÓGICA Y DIBUJO ----------------
    def cancelar_timers():
        if state["after_id"] is not None:
            root.after_cancel(state["after_id"])
            state["after_id"] = None
        if state["packet_after_id"] is not None:
            root.after_cancel(state["packet_after_id"])
            state["packet_after_id"] = None

    def recalcular_todo():
        prob = ProblemaEnrutamientoSDN(
            enlaces_caidos=state["enlaces_caidos"],
            usar_gps=state["usar_gps"]
        )
        state["prob"] = prob
        state["resultados"] = {
            "BFS": busqueda_bfs(prob),
            "UCS": busqueda_ucs(prob),
            "A*":  busqueda_a_estrella(prob),
        }
        actualizar_tabla_comparativa()

    def actualizar_tabla_comparativa():
        for alg_key in ("BFS", "UCS", "A*"):
            res = state["resultados"][alg_key]
            es_activo = (alg_key == state["algo"])
            bg_row = (C_MINT if alg_key == "A*" else (C_PEACH if alg_key == "UCS" else C_LAV)) if es_activo else "#F2F2F2"

            if res["exito"]:
                ruta_txt = "→".join(res["ruta"])
                lat_txt = f"{res['latencia_ms']:.1f} ms"
                sla_txt = "OK" if res["cumple_sla"] else "FALLA"
            else:
                ruta_txt = "Sin ruta"
                lat_txt = "∞"
                sla_txt = "FALLA"

            vals = [
                f"▶ {alg_key}" if es_activo else alg_key,
                ruta_txt,
                lat_txt,
                sla_txt,
                f"{res['nodos_expandidos']}/8",
                f"{res['nodos_en_ram']}/8",
            ]
            for ci, val in enumerate(vals):
                fg_c = "#B00020" if (ci == 3 and sla_txt == "FALLA") else C_BLACK
                tbl_cells[alg_key][ci].configure(text=val, bg=bg_row, fg=fg_c)

    def obtener_xy(nid, w, h):
        nx, ny = POS_NORM[nid]
        pad_x = 72
        top_y = 92
        bot_y = h - 78
        usable_w = max(200, w - 2 * pad_x)
        usable_h = max(200, bot_y - top_y)
        return pad_x + nx * usable_w, top_y + ny * usable_h

    def dibujar_escena():
        canvas.delete("all")
        w = max(canvas.winfo_width(), 680)
        h = max(canvas.winfo_height(), 520)

        res = state["resultados"][state["algo"]]
        pasos = res["pasos"]
        p_actual = pasos[min(state["paso_idx"], len(pasos) - 1)] if pasos else None

        for gx in range(50, w - 30, 60):
            canvas.create_line(gx, 80, gx, h - 65, fill="#ECECEC", width=1)
        for gy in range(86, h - 60, 60):
            canvas.create_line(30, gy, w - 30, gy, fill="#ECECEC", width=1)

        gps_txt = "GPS h(n) ACTIVO" if state["usar_gps"] else "SIN GPS (h=0 ➔ A* degrada a UCS)"
        canvas.create_rectangle(14, 12, w - 14, 48, fill=C_BLACK, outline=C_BLACK)
        canvas.create_text(
            w // 2, 30,
            text=f"TOPOLOGÍA WAN-IoT ({gps_txt})  ·  Clic en cualquier enlace para simular caída",
            fill=C_WHITE, font=("Segoe UI", 11, "bold")
        )

        leyendas = [
            ("Actual", C_PINK),
            ("CLOSED", C_LAV),
            ("OPEN", C_PEACH),
            ("Ruta Óptima", C_MINT),
            ("Sin Instanciar", "#E2E2E2"),
        ]
        lx = 18
        for ltxt, lcol in leyendas:
            canvas.create_oval(lx, 56, lx + 16, 72, fill=lcol, outline=C_BLACK, width=2)
            tid = canvas.create_text(lx + 21, 64, text=ltxt, anchor="w", fill=C_BLACK, font=("Segoe UI", 10, "bold"))
            bbox = canvas.bbox(tid)
            lx = (bbox[2] + 20) if bbox else (lx + 115)

        es_paso_final = bool(p_actual and p_actual["es_meta"])
        ruta_dibujo = res["ruta"] if (es_paso_final and res["exito"]) else (p_actual["ruta_actual"] if p_actual else [])
        aristas_ruta = set()
        for i in range(len(ruta_dibujo) - 1):
            aristas_ruta.add(tuple(sorted((ruta_dibujo[i], ruta_dibujo[i + 1]))))

        # Offsets limpios por enlace para evitar colisión de etiquetas
        OFFSETS_ARISTA = {
            ("R0", "R1"): (-22, -16),
            ("R0", "R2"): (0, -22),
            ("R0", "R3"): (-36, 0),
            ("R1", "R2"): (32, -4),
            ("R1", "R4"): (0, 22),
            ("R2", "R3"): (-22, -16),
            ("R2", "R5"): (0, -22),
            ("R3", "R6"): (0, 22),
            ("R4", "R7"): (28, -14),
            ("R5", "R7"): (-8, -24),
            ("R6", "R7"): (30, 14),
        }

        state["edge_hitboxes"] = []
        for u, v, lat_ms, tec in ENLACES_BASE:
            x1, y1 = obtener_xy(u, w, h)
            x2, y2 = obtener_xy(v, w, h)
            par = tuple(sorted((u, v)))
            caido = par in state["enlaces_caidos"]
            en_ruta = (par in aristas_ruta) and not caido

            if par == ("R1", "R7"):
                cx_m = (x1 + x2) / 2
                cy_m = min(y1, y2) - 110
                pts = [x1, y1, cx_m, cy_m, x2, y2]
                mx = cx_m
                my = min(y1, y2) - 50
                smooth_flag = True
            else:
                pts = [x1, y1, x2, y2]
                ox, oy = OFFSETS_ARISTA.get(par, (0, -18))
                mx, my = (x1 + x2) / 2 + ox, (y1 + y2) / 2 + oy
                smooth_flag = False

            if caido:
                canvas.create_line(*pts, fill="#CC2222", width=3, dash=(8, 6), smooth=smooth_flag)
                lbl_txt = f"✕ {lat_ms:.1f} ms"
                bg_b, fg_b = "#FFD6D6", "#990000"
            elif en_ruta:
                col_ruta = (C_MINT if res["cumple_sla"] else C_PINK) if es_paso_final else C_PEACH
                canvas.create_line(*pts, fill=C_BLACK, width=11, smooth=smooth_flag)
                canvas.create_line(*pts, fill=col_ruta, width=6, smooth=smooth_flag)
                lbl_txt = f"{lat_ms:.1f} ms ({tec})"
                bg_b, fg_b = col_ruta, C_BLACK
            else:
                canvas.create_line(*pts, fill="#686868", width=3, smooth=smooth_flag)
                lbl_txt = f"{lat_ms:.1f} ms"
                bg_b, fg_b = C_WHITE, C_BLACK

            tid = canvas.create_text(mx, my, text=lbl_txt, fill=fg_b, font=("Segoe UI", 11, "bold"))
            tb = canvas.bbox(tid)
            if tb:
                rid = canvas.create_rectangle(tb[0] - 6, tb[1] - 3, tb[2] + 6, tb[3] + 3,
                                              fill=bg_b, outline=C_BLACK, width=2)
                canvas.tag_lower(rid, tid)
                state["edge_hitboxes"].append((tb[0] - 12, tb[1] - 10, tb[2] + 12, tb[3] + 10, par))

        if es_paso_final and res["exito"] and len(res["ruta"]) >= 2:
            segs = len(res["ruta"]) - 1
            pos_f = (state["packet_t"] % 1.0) * segs
            s_idx = min(int(pos_f), segs - 1)
            frac = pos_f - s_idx
            u_p, v_p = res["ruta"][s_idx], res["ruta"][s_idx + 1]
            x1, y1 = obtener_xy(u_p, w, h)
            x2, y2 = obtener_xy(v_p, w, h)
            if tuple(sorted((u_p, v_p))) == ("R1", "R7"):
                cx_m, cy_m = (x1 + x2) / 2, min(y1, y2) - 62
                px = (1 - frac)**2 * x1 + 2 * (1 - frac) * frac * cx_m + frac**2 * x2
                py = (1 - frac)**2 * y1 + 2 * (1 - frac) * frac * cy_m + frac**2 * y2
            else:
                px = x1 + (x2 - x1) * frac
                py = y1 + (y2 - y1) * frac
            p_col = C_BLACK if res["cumple_sla"] else "#B00020"
            canvas.create_oval(px - 11, py - 11, px + 11, py + 11, fill=C_PINK, outline=p_col, width=3)

        closed_set = set(p_actual["closed"]) if p_actual else set()
        open_set = {it["nodo"] for it in p_actual["open"]} if p_actual else set()
        ram_set = set(p_actual["ram_set"]) if p_actual else set()
        nodo_act = p_actual["actual"] if p_actual else None
        info_n = p_actual["info_nodos"] if p_actual else {}

        rad_base = max(28, min(36, int(min(w, h) * 0.048)))
        for nid in NODOS_RED:
            cx, cy = obtener_xy(nid, w, h)
            rad = rad_base + (5 if nid in ("R0", "R7") else 0)

            if es_paso_final and nid in ruta_dibujo:
                fill_c = C_MINT if res["cumple_sla"] else C_PINK
            elif nid == nodo_act:
                fill_c = C_PINK
            elif nid in closed_set:
                fill_c = C_LAV
            elif nid in open_set:
                fill_c = C_PEACH
            else:
                fill_c = "#E4E4E4"

            if nid == nodo_act:
                canvas.create_oval(cx - rad - 8, cy - rad - 8, cx + rad + 8, cy + rad + 8,
                                   outline=C_BLACK, width=3, dash=(5, 3))
            elif nid in ("R0", "R7"):
                canvas.create_oval(cx - rad - 5, cy - rad - 5, cx + rad + 5, cy + rad + 5,
                                   outline=C_BLACK, width=2, dash=(4, 4))

            outline_w = 4 if (nid == nodo_act or (es_paso_final and nid in ruta_dibujo)) else 3
            dash_node = () if (nid in ram_set or not p_actual) else (4, 3)
            canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                               fill=fill_c, outline=C_BLACK, width=outline_w, dash=dash_node)

            canvas.create_text(cx, cy - (6 if nid in ("R0", "R7") else 0),
                               text=nid, fill=C_BLACK, font=("Segoe UI", 15, "bold"))
            if nid in ("R0", "R7"):
                tag_r = "ORIGEN" if nid == "R0" else "META"
                canvas.create_text(cx, cy + 14, text=tag_r, fill=C_BLACK, font=("Segoe UI", 8, "bold"))

            hn_fijo = state["prob"].heuristica(nid)
            if nid in info_n:
                d_n = info_n[nid]
                if state["algo"] == "A*":
                    b_txt = f"g={d_n['g']:.1f} | h={d_n['h']:.1f} | f={d_n['f']:.1f}"
                elif state["algo"] == "UCS":
                    b_txt = f"g={d_n['g']:.1f} ms"
                else:
                    b_txt = f"{int(d_n['f'])} saltos ({d_n['g']:.1f} ms)"
                b_bg = C_WHITE
            else:
                b_txt = f"No en RAM (h={hn_fijo:.1f})"
                b_bg = "#EFEFEF"

            # Etiqueta superior solo para R1; R4 y demás van abajo para máximo despeje visual
            by = (cy - rad - 19) if nid == "R1" else (cy + rad + 19)
            tid = canvas.create_text(cx, by, text=b_txt, fill=C_BLACK, font=("Segoe UI", 10, "bold"))
            tb = canvas.bbox(tid)
            if tb:
                rid = canvas.create_rectangle(tb[0] - 5, tb[1] - 2, tb[2] + 5, tb[3] + 2,
                                              fill=b_bg, outline=C_BLACK, width=1)
                canvas.tag_lower(rid, tid)

        banner_y1 = h - 52
        if es_paso_final and res["exito"]:
            ok_sla = res["cumple_sla"]
            b_col = C_MINT if ok_sla else C_PINK
            veredicto = "CUMPLE SLA (< 15 ms)" if ok_sla else "FALLA SLA (> 15 ms)"
            ruta_s = " ➔ ".join(res["ruta"])
            b_texto = (f"{res['algoritmo']}:  {ruta_s}   |   "
                       f"{res['latencia_ms']:.1f} ms ({veredicto})   |   "
                       f"Expandidos: {res['nodos_expandidos']}/8 · RAM: {res['nodos_en_ram']}/8")
        elif not res["exito"]:
            b_col = C_PINK
            b_texto = "RED DESCONECTADA: No existe ruta activa entre R0 y R7 (pulsa Restaurar)."
        else:
            b_col = C_PEACH
            b_texto = (f"Simulando {res['algoritmo']} — Paso {p_actual['paso']} de {len(pasos)}: "
                       f"Expandiendo {p_actual['actual']}...")

        canvas.create_rectangle(14, banner_y1, w - 14, h - 12, fill=b_col, outline=C_BLACK, width=3)
        canvas.create_text(w // 2, (banner_y1 + h - 12) // 2, text=b_texto,
                           fill=C_BLACK, font=("Segoe UI", 12, "bold"))

    def actualizar_panel_derecho():
        res = state["resultados"][state["algo"]]
        pasos = res["pasos"]
        total_p = len(pasos)
        p_act = pasos[min(state["paso_idx"], total_p - 1)] if pasos else None

        col_badge = C_MINT if state["algo"] == "A*" else (C_PEACH if state["algo"] == "UCS" else C_LAV)
        suf_gps = "" if state["usar_gps"] or state["algo"] != "A*" else "  [h=0 ➔ UCS]"
        lbl_algo_badge.configure(text=res["titulo"] + suf_gps, bg=col_badge)

        if p_act:
            lbl_step_title.configure(
                text=f"Paso {p_act['paso']} de {total_p}  ·  Nodo: {p_act['actual']} ({NODOS_RED[p_act['actual']]['nombre']})"
            )
            lbl_step_msg.configure(text=p_act["mensaje"])
            kpi_lat.configure(text=f"{p_act['g']:.1f} ms")
            kpi_exp.configure(text=f"{len(p_act['closed'])} / 8")
            kpi_ram.configure(text=f"{len(p_act['ram_set'])} / 8")
            lbl_closed_list.configure(text="CLOSED (Expandidos):  " + " ➔ ".join(p_act["closed"]))

            for child in open_box.winfo_children():
                child.destroy()

            if not p_act["open"]:
                tk.Label(open_box, text="(Cola OPEN vacía)",
                         font=("Segoe UI", 11), bg=C_WHITE, fg=C_GRAY, anchor="w").pack(fill="x", pady=4)
            else:
                for idx_q, item in enumerate(p_act["open"][:5]):
                    bg_q = C_PEACH if idx_q == 0 else "#F1F1F1"
                    pref = "Siguiente ➔ " if idx_q == 0 else f"#{idx_q + 1} · "
                    row_q = tk.Frame(open_box, bg=bg_q, highlightbackground=C_BLACK,
                                     highlightthickness=2 if idx_q == 0 else 1, padx=8, pady=4)
                    row_q.pack(fill="x", pady=2)
                    tk.Label(row_q, text=f"{pref}{item['nodo']}",
                             font=("Segoe UI", 11, "bold"), bg=bg_q, fg=C_BLACK).pack(side="left")
                    tk.Label(row_q, text=item["etiqueta"],
                             font=("Segoe UI", 11, "bold"), bg=bg_q, fg=C_BLACK).pack(side="right")
        else:
            lbl_step_title.configure(text="Sin ruta disponible")
            lbl_step_msg.configure(text="Restaura enlaces para reconectar R0 y R7.")

        actualizar_tabla_comparativa()

    def refrescar_vista():
        actualizar_panel_derecho()
        dibujar_escena()

    def animar_paquete():
        res = state["resultados"][state["algo"]]
        pasos = res["pasos"]
        if pasos and state["paso_idx"] >= len(pasos) - 1 and res["exito"]:
            state["packet_t"] = (state["packet_t"] + 0.035) % 1.0
            dibujar_escena()
            state["packet_after_id"] = root.after(55, animar_paquete)

    def tick_autoplay():
        if not state["playing"]:
            return
        res = state["resultados"][state["algo"]]
        if state["paso_idx"] < len(res["pasos"]) - 1:
            state["paso_idx"] += 1
            refrescar_vista()
            state["after_id"] = root.after(1050, tick_autoplay)
        else:
            state["playing"] = False
            btn_play.configure(text="▶ Auto-Play")
            animar_paquete()

    def seleccionar_algoritmo(alg_key, autoplay=True):
        cancelar_timers()
        state["algo"] = alg_key
        state["paso_idx"] = 0 if autoplay else max(0, len(state["resultados"][alg_key]["pasos"]) - 1)
        state["playing"] = autoplay
        btn_play.configure(text="⏸ Pausar" if autoplay else "▶ Auto-Play")
        refrescar_vista()
        if autoplay:
            state["after_id"] = root.after(950, tick_autoplay)

    def paso_siguiente():
        cancelar_timers()
        state["playing"] = False
        btn_play.configure(text="▶ Auto-Play")
        res = state["resultados"][state["algo"]]
        if state["paso_idx"] < len(res["pasos"]) - 1:
            state["paso_idx"] += 1
        refrescar_vista()
        if state["paso_idx"] >= len(res["pasos"]) - 1:
            animar_paquete()

    def paso_anterior():
        cancelar_timers()
        state["playing"] = False
        btn_play.configure(text="▶ Auto-Play")
        if state["paso_idx"] > 0:
            state["paso_idx"] -= 1
        refrescar_vista()

    def toggle_play():
        res = state["resultados"][state["algo"]]
        if state["playing"]:
            cancelar_timers()
            state["playing"] = False
            btn_play.configure(text="▶ Auto-Play")
        else:
            cancelar_timers()
            if state["paso_idx"] >= len(res["pasos"]) - 1:
                state["paso_idx"] = 0
            state["playing"] = True
            btn_play.configure(text="⏸ Pausar")
            refrescar_vista()
            state["after_id"] = root.after(950, tick_autoplay)

    def toggle_gps():
        cancelar_timers()
        state["usar_gps"] = not state["usar_gps"]
        btn_gps.configure(
            text="GPS h(n): ON" if state["usar_gps"] else "GPS h(n): OFF (UCS)",
            bg=C_MINT if state["usar_gps"] else C_PINK
        )
        recalcular_todo()
        res = state["resultados"][state["algo"]]
        state["paso_idx"] = max(0, len(res["pasos"]) - 1)
        state["playing"] = False
        btn_play.configure(text="▶ Auto-Play")
        refrescar_vista()
        animar_paquete()

    def restaurar_red():
        cancelar_timers()
        state["enlaces_caidos"].clear()
        state["usar_gps"] = True
        btn_gps.configure(text="GPS h(n): ON", bg=C_MINT)
        recalcular_todo()
        seleccionar_algoritmo("A*", autoplay=True)

    def on_canvas_click(event):
        for x1, y1, x2, y2, par in state["edge_hitboxes"]:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                cancelar_timers()
                if par in state["enlaces_caidos"]:
                    state["enlaces_caidos"].remove(par)
                else:
                    state["enlaces_caidos"].add(par)
                recalcular_todo()
                res = state["resultados"][state["algo"]]
                state["paso_idx"] = max(0, len(res["pasos"]) - 1)
                state["playing"] = False
                btn_play.configure(text="▶ Auto-Play")
                refrescar_vista()
                animar_paquete()
                break

    make_btn(grp_alg, "[1] BFS · Ciega (Saltos)", C_LAV,   C_BLACK, lambda: seleccionar_algoritmo("BFS", True))
    make_btn(grp_alg, "[2] UCS · Ciega (Costo g)", C_PEACH, C_BLACK, lambda: seleccionar_algoritmo("UCS", True))
    make_btn(grp_alg, "[3] A* · Informada (Elegido)", C_MINT, C_BLACK, lambda: seleccionar_algoritmo("A*", True))

    make_btn(grp_sim, "⏮ Paso -", "#3A3A3A", C_WHITE, paso_anterior)
    btn_play = make_btn(grp_sim, "▶ Auto-Play", C_PINK, C_BLACK, toggle_play)
    make_btn(grp_sim, "⏭ Paso +", "#3A3A3A", C_WHITE, paso_siguiente)
    btn_gps  = make_btn(grp_sim, "GPS h(n): ON", C_MINT, C_BLACK, toggle_gps)
    make_btn(grp_sim, "↺ Restaurar Red", "#3A3A3A", C_WHITE, restaurar_red)

    canvas.bind("<Configure>", lambda _e: dibujar_escena())
    canvas.bind("<Button-1>", on_canvas_click)
    root.bind("1", lambda _e: seleccionar_algoritmo("BFS", True))
    root.bind("2", lambda _e: seleccionar_algoritmo("UCS", True))
    root.bind("3", lambda _e: seleccionar_algoritmo("A*", True))
    root.bind("<Right>", lambda _e: paso_siguiente())
    root.bind("<Left>", lambda _e: paso_anterior())
    root.bind("<space>", lambda _e: toggle_play())
    root.bind("g", lambda _e: toggle_gps())
    root.bind("G", lambda _e: toggle_gps())
    root.bind("r", lambda _e: restaurar_red())
    root.bind("R", lambda _e: restaurar_red())

    recalcular_todo()
    if iniciar_autoplay:
        root.after(250, lambda: seleccionar_algoritmo("A*", autoplay=True))
    else:
        seleccionar_algoritmo("A*", autoplay=False)

    return root, state, seleccionar_algoritmo


if __name__ == "__main__":
    imprimir_reporte_consola()
    if "--cli" not in sys.argv:
        ventana, _, _ = construir_ventana_simulador(maximizar=True, iniciar_autoplay=True)
        ventana.mainloop()
