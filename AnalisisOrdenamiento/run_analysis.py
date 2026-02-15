import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

# Ensure the paths are correct for the imports
import sys
sys.path.append('.')

from sort.bubble_sort import bubble_sort
from sort.insertion_sort import insertion_sort
from sort.quicksort import quicksort

# Set theme
sns.set_theme(style="whitegrid")

def measure_time(S, sort_function):
    S_copy = S.copy()
    start_time = time.perf_counter_ns()
    sort_function(S_copy)
    end_time = time.perf_counter_ns()
    return end_time - start_time

def benchmark_algorithms(sizes, trials=10):
    results = []
    for n in sizes:
        print(f"Processing n={n}...")
        for _ in range(trials):
            S = [random.randint(0, n) for _ in range(n)]
            results.append({
                'n': n,
                'Bubble Sort': measure_time(S, bubble_sort),
                'Insertion Sort': measure_time(S, insertion_sort),
                'Quicksort': measure_time(S, quicksort)
            })
    return pd.DataFrame(results)

# Run benchmark
sizes = [10, 50, 100, 250, 500, 750, 1000]
df_raw = benchmark_algorithms(sizes, trials=10)

# Stats
df_stats = df_raw.groupby('n').agg(['mean', 'std']).reset_index()
df_stats.columns = ['n', 'bubble_mean', 'bubble_std', 'insertion_mean', 'insertion_std', 'quicksort_mean', 'quicksort_std']

# Plot 1: Complexity
plt.figure(figsize=(12, 6))
for algo in ['Bubble Sort', 'Insertion Sort', 'Quicksort']:
    mean_col = algo.lower().split()[0] + '_mean'
    std_col = algo.lower().split()[0] + '_std'
    plt.errorbar(df_stats['n'], df_stats[mean_col], yerr=df_stats[std_col], 
                 label=algo, fmt='-o', capsize=5, alpha=0.8)
plt.title('Complejidad Experimental (Tiempo vs n)')
plt.xlabel('Tamaño de Entrada (n)')
plt.ylabel('Tiempo de Ejecución (ns)')
plt.legend()
plt.yscale('log')
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.savefig('complexity_plot.png')
plt.close()

# Regressions
def perform_regression(df, formula, algo_name):
    mod = smf.ols(formula=formula, data=df)
    res = mod.fit()
    return res

res_bubble = perform_regression(df_raw, 'Q("Bubble Sort") ~ np.power(n, 2)', "Bubble Sort")
res_insertion = perform_regression(df_raw, 'Q("Insertion Sort") ~ np.power(n, 2)', "Insertion Sort")
res_quick = perform_regression(df_raw, 'Q("Quicksort") ~ n:np.log2(n)', "Quicksort")

# Plot 2: Regressions
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
sm.graphics.plot_fit(res_bubble, "np.power(n, 2)", ax=axes[0])
axes[0].set_title(r"Bubble Sort (Ajuste $n^2$)")
sm.graphics.plot_fit(res_insertion, "np.power(n, 2)", ax=axes[1])
axes[1].set_title(r"Insertion Sort (Ajuste $n^2$)")
sm.graphics.plot_fit(res_quick, "n:np.log2(n)", ax=axes[2])
axes[2].set_title(r"Quicksort (Ajuste $n \log n$)")
plt.tight_layout()
plt.savefig('regression_plot.png')
plt.close()

print("Analysis finished. Images saved as complexity_plot.png and regression_plot.png.")
