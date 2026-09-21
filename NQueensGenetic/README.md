# N-Reinas con algoritmo genético

Aplicación en Python que resuelve el problema escalable de las N-Reinas. El índice del
vector representa la **columna** y su valor representa la **fila**; por tanto, el genotipo
es una permutación y su fenotipo siempre contiene exactamente una reina por fila y por
columna.

Por ejemplo, `[2, 4, 6, 8, 3, 1, 7, 5]` (mostrado en base 1) coloca la primera reina en
la fila 2, columna 1; la segunda en la fila 4, columna 2; etc.

## Ejecución

No requiere paquetes externos: utiliza únicamente la biblioteca estándar de Python 3.

```bash
# Interfaz gráfica, caso base
python3 main.py 8

# Interfaz con un tablero mayor
python3 main.py 50

# Ejecución por consola
python3 main.py 100 --no-gui

# Experimento reproducible y exportación de la convergencia
python3 main.py 50 --no-gui --seed 42 --history-csv resultados/n50.csv

# Comparación rápida de escalabilidad
python3 main.py --benchmark 8 50 100 --seed 42
```

Si no existe un entorno gráfico, el programa cambia automáticamente al modo consola.

## Etapas implementadas

1. **Población inicial:** genera permutaciones aleatorias de las filas `0..N-1`.
2. **Evaluación:** el costo cuenta pares de reinas que comparten diagonal en tiempo
   `O(N)`. El fitness de maximización es `1 / (1 + costo)`.
3. **Nueva población:** selecciona padres por torneo respecto al fitness, aplica cruce
   de orden OX, mutación mediante *swap* y reemplazo generacional elitista.
4. **Parada:** termina inmediatamente cuando el mejor individuo tiene costo `0`, o al
   alcanzar el límite de generaciones. La mutación se adapta durante estancamientos y
   se introducen inmigrantes aleatorios para recuperar diversidad.

OX es indispensable porque un cruce convencional puede repetir filas y romper el
genotipo de permutación.

## Interfaz

La ventana mantiene el cálculo en un hilo de trabajo para no bloquear la animación. Cada
generación produce una instantánea inmutable que permite reconstruir:

- el mejor tablero (fenotipo);
- costo, fitness, generación y tiempo;
- la gráfica de convergencia completa.

También se registra cada mutación swap aplicada. Al terminar aparecen controles para ir
al inicio, retroceder una mutación, reproducir/pausar lentamente, avanzar una mutación o
ir al resultado final. El deslizador permite saltar a cualquier paso. Debajo se muestran
completos y en base 1 los arreglos de interés:

- padre A;
- padre B;
- descendiente después de OX;
- descendiente después de la mutación swap.

El control `Mutation playback delay` permite pausas de 50 a 1500 ms y comienza en 500
ms. El tiempo reportado corresponde al algoritmo, no a la reproducción visual. El modo
consola no guarda mutaciones para evitar consumo de memoria innecesario en experimentos
grandes.

## Pruebas

```bash
python3 -m unittest discover -v
```

Las pruebas validan el costo, las permutaciones, OX, la reproducción exacta de cada swap,
la convergencia elitista y la solución reproducible del caso `N=8`.
