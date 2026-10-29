# 🎙️ GUION DE EXPOSICIÓN (2 PERSONAS · 2 MINUTOS EXACTOS)
**Actividad:** Algoritmos de Búsqueda en Inteligencia Artificial aplicados a Redes WAN-IoT Sísmicas  
**Tiempo Total Estimado:** 2 minutos y 10 segundos (~65 segundos por persona)  
**Archivos de apoyo:**
- Presentación: `Presentacion_FIA_IA_Algoritmos_Busqueda.pptx` (o `.pdf`)
- Demostrador en vivo: `demo_busqueda_wan_iot.py`

---

## 👤 EXPOSITOR 1 (Diapositivas 1 a 4 · Tiempo: 1 min 05 s)
**Enfoque:** Introducción, Escenario de Red WAN-IoT y Formulación Matemática.

### 📌 Diapositiva 1 · Portada (10 segundos · `0:00 – 0:10`)
- **En pantalla:** Portada oficial con el título y nombres del equipo.
- **🗣️ Lo que dices en voz alta:**
  > "Buenos días, profesor y compañeros. Hoy les presentamos la aplicación de **algoritmos de búsqueda en Inteligencia Artificial** para optimizar el **enrutamiento de baja latencia en una red WAN-IoT sísmica** controlada por software (SDN)."

---

### 📌 Diapositiva 2 · Fase 1: Escenario de Red (18 segundos · `0:10 – 0:28`)
- **En pantalla:** Mapa de 8 routers, tecnologías de enlace (DWDM, 5G, LTE) y alerta sísmica.
- **🗣️ Lo que dices en voz alta:**
  > "Nuestra red conecta **8 routers y 12 enlaces heterogéneos** de fibra óptica, microondas 5G y respaldo LTE. El Gateway sísmico R0 debe transmitir paquetes críticos de alerta hacia el Servidor Edge-IA R7 con un **SLA estricto menor a 15 milisegundos**. Un ruteo clásico por saltos toma enlaces lentos de 24 ms que comprometen la alerta temprana, por lo que requerimos búsqueda óptima."

---

### 📌 Diapositiva 3 · Fase 2: Formulación Formal en IA (18 segundos · `0:28 – 0:46`)
- **En pantalla:** Espacio de estados, Estado Inicial S0, Prueba de Meta y 12 Enlaces.
- **🗣️ Lo que dices en voz alta:**
  > "Formulamos el problema formalmente: el **espacio de estados** son los 8 routers; el **estado inicial S0** es el Gateway R0; y la **prueba de meta** se cumple cuando el paquete arriba al Servidor R7. Las **acciones** corresponden a reenviar el paquete a través de los 12 enlaces directos bidireccionales de la red."

---

### 📌 Diapositiva 4 · Fase 2: Métricas, Heurística y Admisibilidad (19 segundos · `0:46 – 1:05`)
- **En pantalla:** Función de costo g(n), fórmula física h(n) y gráfica demostrativa de admisibilidad.
- **🗣️ Lo que dices en voz alta:**
  > "El costo acumulado g(n) es la **latencia real en milisegundos** medida por telemetría SDN. Para guiar la búsqueda, formulamos la **heurística física h(n)** dividiendo la distancia GPS en línea recta hacia la meta entre la velocidad de la luz en fibra (200 km/ms). Como ninguna señal física viaja más rápido que la luz en línea recta, h(n) nunca sobrestima el costo real: es **estrictamente admisible y consistente**."

---

### 🤝 Frase de Pase / Transición (Expositor 1 cede la palabra):
> **Expositor 1:** *"A continuación, mi compañero(a) explicará la comparativa de algoritmos, los resultados obtenidos y la traza en memoria."*

---

---

## 👤 EXPOSITOR 2 (Diapositivas 5 a 8 · Tiempo: 1 min 05 s)
**Enfoque:** Comparativa Algorítmica, Justificación Técnica, Traza A* y Conclusiones.

### 📌 Diapositiva 5 · Fase 3: Comparativa Ciega vs. Informada (18 segundos · `1:05 – 1:23`)
- **En pantalla:** Tabla comparativa visual entre BFS, UCS y A*.
- **🗣️ Lo que dices en voz alta:**
  > "Gracias. Al comparar los algoritmos: **BFS** busca por menor número de saltos y elige la ruta por LTE de 24 ms, **violando el SLA sísmico**. **UCS** sí halla la ruta óptima de 11 ms, pero necesita expandir los 8 nodos de la red. En cambio, **A\*** encuentra exactamente el mismo óptimo de **11 milisegundos**, pero explorando únicamente **4 nodos**, podando el 50% de la red."

---

### 📌 Diapositiva 6 · Fase 3: Justificación Técnica en 4 Ejes (18 segundos · `1:23 – 1:41`)
- **En pantalla:** 4 tarjetas: Memoria RAM, Variación de costos, Telemetría SDN y Optimalidad.
- **🗣️ Lo que dices en voz alta:**
  > "Elegimos **A\*** por cuatro razones clave: soporta enlaces con costos variables donde BFS falla; reduce el consumo de memoria RAM **podando ramas con f(n) > C\***; aprovecha que el controlador SDN ya conoce las coordenadas GPS y la telemetría en tiempo real; y garantiza completitud matemática y optimalidad de costo."

---

### 📌 Diapositiva 7 · Traza Paso a Paso de A* (17 segundos · `1:41 – 1:58`)
- **En pantalla:** Los 4 pasos en la cola de prioridad (R0 -> R2 -> R5 -> R7).
- **🗣️ Lo que dices en voz alta:**
  > "En la traza paso a paso observamos su eficiencia: el algoritmo arranca en R0, prioriza R2 con costo total estimado de 9.0 ms, avanza a R5 con 10.0 ms y finalmente extrae la meta R7 con **11.0 ms**. Nodos como R4 y R6 nunca llegaron a instanciarse en la memoria RAM gracias a la poda heurística."

---

### 📌 Diapositiva 8 · Fase 4: Conclusión y Cierre (12 segundos · `1:58 – 2:10`)
- **En pantalla:** Síntesis ejecutiva (-54.2% latencia, -50% procesamiento) y créditos finales.
- **🗣️ Lo que dices en voz alta:**
  > "En conclusión, A\* logra una **reducción del 54.2% en latencia** frente a la búsqueda por saltos y **ahorra el 50% de procesamiento** frente a UCS, garantizando que los paquetes sísmicos se procesen a tiempo en el Servidor Edge-IA. Muchas gracias."

---

---

## ❓ PLAN B: SI EL PROFESOR HACE PREGUNTAS O PIDE EL CÓDIGO
Si el profesor pide correr la demostración o pregunta detalles técnicos, abren la terminal y ejecutan:

```bash
python demo_busqueda_wan_iot.py
```

- **Expositor 1 (en el teclado):**
  - Presiona la tecla **`1`**: muestra cómo BFS se pinta en rojo y falla el SLA sísmico (24 ms).
  - Presiona la tecla **`3`**: muestra cómo A\* encuentra la ruta verde óptima en 11 ms podando la mitad de la red.
- **Expositor 2 (explicando en voz alta):**
  - Dice: *"En pantalla vemos en tiempo real las listas OPEN y CLOSED en RAM. Además, si hubiera un terremoto que corte un cable de fibra, por ejemplo haciendo clic en el enlace R2-R5, el controlador SDN recalcula automáticamente la mejor ruta de contingencia."*
  - Si pregunta qué pasa si no hay GPS: se presiona la tecla **`G`** para mostrar cómo A\* se degrada de forma segura a UCS ($h=0$).
