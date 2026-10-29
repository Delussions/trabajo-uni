# 🛰️ Enrutamiento SDN de Baja Latencia en Red WAN-IoT Sísmica
### Algoritmos de Búsqueda en Inteligencia Artificial: Ciega (BFS / UCS) vs. Informada (A*)
**Asignatura:** Fundamentos de Inteligencia Artificial (FIA)  
**Entorno de Ejecución:** Python 3.10+ (Librería estándar `tkinter`, sin dependencias externas `pip`)

---

## 📌 Descripción del Proyecto

Este repositorio contiene la solución completa de la actividad práctica de **Fundamentos de Inteligencia Artificial**, modelando y resolviendo el problema de **enrutamiento óptimo en una red WAN-IoT de alerta temprana sísmica** hacia un Servidor Edge-IA que ejecuta una red neuronal (CNN-1D) para la clasificación de ondas sísmicas P.

El controlador SDN debe seleccionar la ruta que minimice la latencia total acumulada garantizando un **SLA estricto menor a 15.0 milisegundos**, comparando formal y empíricamente los algoritmos:
- **BFS (Búsqueda en Anchura / Saltos):** Falla el SLA al elegir enlaces LTE saturados (24.0 ms).
- **UCS (Costo Uniforme / Dijkstra):** Encuentra la ruta óptima de 11.0 ms pero expande el 100% de la red (8/8 nodos).
- **A\* (Búsqueda Informada $f = g + h$):** Encuentra la ruta óptima de **11.0 ms** con **-50% de nodos expandidos** (4/8) y **-25% de huella en RAM** (6/8), gracias a una heurística física admisible y consistente basada en coordenadas GPS.

---

## 📂 Contenido del Repositorio

| Archivo | Descripción |
| :--- | :--- |
| **`demo_busqueda_wan_iot.py`** | Aplicación visual e interactiva en Python (`tkinter`) que simula la red, anima los paquetes, muestra las colas `OPEN`/`CLOSED` en vivo y permite simular caídas de fibra óptica con un clic. |
| **`Presentacion_FIA_IA_Algoritmos_Busqueda.pptx`** | Presentación oficial en PowerPoint (8 diapositivas, diseño Lumra, tipografías `Lora` y `Poppins` incrustadas, fórmulas en alta resolución y notas del orador). |
| **`Presentacion_FIA_IA_Algoritmos_Busqueda.pdf`** | Versión de la presentación exportada en PDF de alta fidelidad, lista para proyectar o entregar. |
| **`GUION_EXPOSICION_2_PERSONAS.md`** | Guion de exposición cronometrado a 2 minutos exactos (~65 s por persona), con el parlamento literal por diapositiva y frases de transición. |
| **`Actividad_y_Rubrica_FIA_IA.pdf`** | Documento oficial con las instrucciones y la rúbrica de evaluación de la actividad universitaria. |

---

## 🚀 Cómo Ejecutar el Demostrador Gráfico

El software no requiere instalar ningún paquete externo (`pip`), funciona de forma nativa en cualquier instalación de Python 3:

```bash
python demo_busqueda_wan_iot.py
```

### Controles Interactivos en Vivo:
- **`1`**: Ejecuta **BFS** (muestra la falla del SLA en rojo con 24.0 ms).
- **`2`**: Ejecuta **UCS** (halla el óptimo de 11.0 ms pero expande los 8 nodos).
- **`3`**: Ejecuta **A\*** (halla el óptimo de 11.0 ms podando la mitad de la red).
- **`Espacio` / `Auto-Play`**: Reproduce la animación del paquete y la expansión paso a paso.
- **`Paso +` / `Paso -`**: Avanza o retrocede nodo por nodo en la cola de prioridad.
- **Clic sobre cualquier enlace**: Corta el cable de fibra óptica para ver en tiempo real cómo el controlador SDN recalcula la ruta de contingencia.
- **`G`**: Alterna la heurística GPS para demostrar cómo $A^*$ se degrada a $UCS$ ($h=0$).

---

## 📐 Formulación Formal en Inteligencia Artificial

- **Espacio de Estados ($S$):** $S = \{R_0, R_1, R_2, R_3, R_4, R_5, R_6, R_7\}$.
- **Estado Inicial ($S_0$):** $R_0$ (Gateway IoT Sísmico, IP `10.0.0.1`).
- **Prueba de Meta:** $\mathrm{Meta}(n) \iff (n = R_7)$ (Servidor Edge-IA, IP `10.0.7.10`).
- **Función de Costo $g(n)$:** Latencia real acumulada en milisegundos (`ms`) medida por telemetría TWAMP:
  $$g(n) = \sum_{(u,v) \in \text{ruta}} c(u,v)$$
- **Función Heurística $h(n)$:** Retardo físico mínimo de propagación óptica en línea recta hacia $R_7$:
  $$h(n) = \left\lfloor \frac{d_{\text{GPS}}(n, R_7)}{200\text{ km/ms}} \right\rfloor_{0.1\text{ ms}}$$
  - **Admisibilidad:** $0 \le h(n) \le h^*(n)$ verificado en los 8 nodos.
  - **Consistencia:** $h(n) \le c(n,m) + h(m)$ verificado en los 24 arcos dirigidos.

---

## 📊 Resultados Comparativos

| Algoritmo | Tipo de Búsqueda | Ruta Obtenida | Latencia | SLA (< 15 ms) | Nodos Expandidos | Nodos en RAM |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **BFS** | Ciega (Saltos) | $R_0 \to R_1 \to R_7$ | 24.0 ms | ❌ **FALLA** | 6 / 8 (75%) | 8 / 8 (100%) |
| **UCS** | Ciega (Costo $g$) | $R_0 \to R_2 \to R_5 \to R_7$ | 11.0 ms | ✅ **CUMPLE** | 8 / 8 (100%) | 8 / 8 (100%) |
| **A\*** | Informada ($g + h$) | $R_0 \to R_2 \to R_5 \to R_7$ | 11.0 ms | ✅ **CUMPLE** | **4 / 8 (50%)** | **6 / 8 (75%)** |
