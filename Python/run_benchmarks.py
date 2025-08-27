
import os
import subprocess
import sys
import re
import statistics
from typing import Dict, List, Tuple
import json


# ---------------------------------------------------------------------
# Utilidades de rutas
# ---------------------------------------------------------------------

def _candidates_with_exe(paths: List[str]) -> List[str]:
    out: List[str] = []
    for p in paths:
        out.append(p)
        if not p.lower().endswith(".exe"):
            out.append(p + ".exe")
    return out

def pick_executable(candidates: List[str]) -> str:
    for p in _candidates_with_exe(candidates):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return candidates[0]


EXEC_SERIAL = pick_executable(["./zombie_serial", "./C/zombie_serial"])
EXEC_OMP    = pick_executable(["./zombie_omp", "./C/zombie_omp"])
PY_SCRIPT   = "Python/zombie_threads.py" if os.path.isfile("Python/zombie_threads.py") else "./zombie_threads.py"


# ---------------------------------------------------------------------
# Ejecucion de comandos y metricas
# ---------------------------------------------------------------------

def run_command(cmd, capture=True):
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True, check=True)
        m = re.search(r"Time\s*=\s*([\d.]+)", result.stdout)
        if m:
            return float(m.group(1)), result.stdout
        print("Warning: no se encontro 'Time =' en STDOUT de:", " ".join(cmd))
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        return 0.0, result.stdout
    except subprocess.CalledProcessError as e:
        print("Error ejecutando comando:", " ".join(cmd))
        if e.stdout: print("STDOUT:\n", e.stdout)
        if e.stderr: print("STDERR:\n", e.stderr)
        return 0.0, ""


def run_multiple_times(cmd: List[str], runs: int = 3) -> float:
    times: List[float] = []
    for _ in range(runs):
        t, _ = run_command(cmd)
        if t > 0:
            times.append(t)
    return statistics.mean(times) if times else 0.0


def calculate_metrics(time_serial: float, time_parallel: float, num_threads: int) -> Dict[str, float]:
    speedup = (time_serial / time_parallel) if time_parallel > 0 else 0.0
    efficiency = (speedup / num_threads * 100.0) if num_threads > 0 else 0.0
    return {
        "speedup": speedup,
        "efficiency": efficiency,
        "time_reduction": ((time_serial - time_parallel) / time_serial * 100.0) if time_serial > 0 else 0.0,
    }


def powers_of_two_up_to(n: int) -> List[int]:
    vals: List[int] = []
    p = 1
    while p <= n:
        vals.append(p)
        p *= 2
    if n not in vals:
        vals.append(n)
        vals = sorted(set(vals))
    return vals


# ---------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------

def benchmark_c_implementations(map_file: str, days: int, max_threads: int = 8) -> Dict:
    results: Dict = {}

    print("\n" + "=" * 80)
    print("PARTE 1: COMPARACION C SERIAL VS C PARALELO (OpenMP)")
    print("=" * 80)

    # Serial
    print("\nEjecutando version SERIAL en C (3 runs)...")
    time_serial = run_multiple_times([EXEC_SERIAL, map_file, str(days)], runs=3)
    print(f"  Tiempo promedio serial: {time_serial:.4f} s")

    results["serial"] = {"time": time_serial, "threads": 1}

    # Paralelo
    results["parallel"] = {}
    thread_counts = powers_of_two_up_to(max_threads)

    for threads in thread_counts:
        if threads > max_threads:
            continue
        print(f"\nEjecutando version PARALELA en C con {threads} threads (3 runs)...")
        time_parallel = run_multiple_times([EXEC_OMP, map_file, str(days), str(threads)], runs=3)
        print(f"  Tiempo promedio con {threads} threads: {time_parallel:.4f} s")

        metrics = calculate_metrics(time_serial, time_parallel, threads)
        results["parallel"][threads] = {
            "time": time_parallel,
            "speedup": metrics["speedup"],
            "efficiency": metrics["efficiency"],
        }

        print(f"  Speedup:    {metrics['speedup']:.2f}x")
        print(f"  Eficiencia: {metrics['efficiency']:.1f}%")

    return results


def benchmark_c_vs_python(map_file: str, days: int, threads: int) -> Dict:
    print("\n" + "=" * 80)
    print(f"PARTE 2: COMPARACION C PARALELO VS PYTHON PARALELO ({threads} threads)")
    print("=" * 80)

    # C paralelo
    print(f"\nEjecutando C paralelo con {threads} threads (3 runs)...")
    time_c = run_multiple_times([EXEC_OMP, map_file, str(days), str(threads)], runs=3)
    print(f"  Tiempo promedio C: {time_c:.4f} s")

    # Python paralelo (mismo interprete)
    print(f"\nEjecutando Python paralelo con {threads} threads (3 runs)...")
    time_python = run_multiple_times([sys.executable, PY_SCRIPT, map_file, str(days), str(threads)], runs=3)
    print(f"  Tiempo promedio Python: {time_python:.4f} s")

    # Ventaja de C sobre Python (cuantas veces es mas rapido C)
    c_over_python = (time_python / time_c) if time_c > 0 else 0.0
    time_reduction_vs_python = ((time_python - time_c) / time_python * 100.0) if time_python > 0 else 0.0

    print(f"\nC es {c_over_python:.2f}x mas rapido que Python")
    print(f"Reduccion de tiempo usando C: {time_reduction_vs_python:.1f}%")

    return {
        "c_parallel": time_c,
        "python_parallel": time_python,
        "speedup_c_over_python": c_over_python,
        "time_reduction_vs_python": time_reduction_vs_python,
    }


# ---------------------------------------------------------------------
# Reporte y graficos
# ---------------------------------------------------------------------

def generate_plots(results_c: Dict, results_cross: Dict, output_prefix: str) -> None:
    try:
        import matplotlib.pyplot as plt

        # Grafico 1: Speedup y eficiencia vs threads
        threads = sorted(results_c["parallel"].keys())
        speedups = [results_c["parallel"][t]["speedup"] for t in threads]
        efficiencies = [results_c["parallel"][t]["efficiency"] for t in threads]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.plot(threads, speedups, "o-", label="Speedup real")
        ax1.plot(threads, threads, "--", label="Speedup ideal (y = x)")
        ax1.set_xlabel("Numero de threads")
        ax1.set_ylabel("Speedup")
        ax1.set_title("Speedup: C Serial vs C Paralelo")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.plot(threads, efficiencies, "o-", label="Eficiencia")
        ax2.axhline(y=100, linestyle="--", label="100%")
        ax2.set_xlabel("Numero de threads")
        ax2.set_ylabel("Eficiencia (%)")
        ax2.set_title("Eficiencia del paralelismo")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{output_prefix}_speedup_efficiency.png", dpi=150)
        print(f"\nGrafico guardado: {output_prefix}_speedup_efficiency.png")
        plt.close()

        # Grafico 2: C vs Python
        fig, ax = plt.subplots(figsize=(8, 6))
        languages = ["C paralelo", "Python paralelo"]
        times = [results_cross["c_parallel"], results_cross["python_parallel"]]
        bars = ax.bar(languages, times)
        ax.set_ylabel("Tiempo (s)")
        ax.set_title("Comparacion de rendimiento: C vs Python")
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height(), f"{t:.2f}s",
                    ha="center", va="bottom")
        ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_c_vs_python.png", dpi=150)
        print(f"Grafico guardado: {output_prefix}_c_vs_python.png")
        plt.close()

    except ImportError:
        print("\nmatplotlib no instalado. Omitiendo generacion de graficos.")
        print("Instalar con: pip install matplotlib")


def print_results_table(results_c: Dict, results_cross: Dict) -> None:
    print("\n" + "=" * 80)
    print("TABLA DE RESULTADOS")
    print("=" * 80)

    print("\nC SERIAL VS C PARALELO:")
    print("-" * 60)
    print(f"{'Threads':<10} {'Tiempo (s)':<15} {'Speedup':<10} {'Eficiencia':<12}")
    print("-" * 60)
    print(f"{'Serial':<10} {results_c['serial']['time']:<15.4f} {'1.00':<10} {'100.0%':<12}")
    for threads in sorted(results_c["parallel"].keys()):
        data = results_c["parallel"][threads]
        print(f"{threads:<10} {data['time']:<15.4f} {data['speedup']:<10.2f} {data['efficiency']:<.1f}%")

    print("\nC PARALELO VS PYTHON PARALELO:")
    print("-" * 60)
    print(f"{'Implementacion':<20} {'Tiempo (s)':<15} {'Factor':<10}")
    print("-" * 60)
    print(f"{'C Paralelo':<20} {results_cross['c_parallel']:<15.4f} {'1.0x':<10}")
    print(f"{'Python Paralelo':<20} {results_cross['python_parallel']:<15.4f} "
          f"{results_cross['speedup_c_over_python']:<.1f}x mas lento")


def main() -> None:
    if len(sys.argv) < 4:
        print("Uso: python Python/run_benchmarks.py <map_file> <days> <max_threads>")
        sys.exit(1)

    map_file = sys.argv[1]
    days = int(sys.argv[2])
    max_threads = int(sys.argv[3])

    # Tamano estimado desde el nombre del archivo (opcional)
    map_size = "unknown"
    m = re.search(r"(\d+)", map_file)
    if m:
        map_size = m.group(1)

    print("\n" + "=" * 80)
    print("BENCHMARK DE SIMULACION DE ZOMBIES")
    print("=" * 80)
    print("\nPARAMETROS DE PRUEBA:")
    print(f"  - Archivo de mapa: {map_file}")
    print(f"  - Tamano estimado: {map_size}x{map_size}")
    print(f"  - Dias de simulacion: {days}")
    print(f"  - Threads maximos: {max_threads}")

    # Parte 1: C Serial vs C Paralelo
    results_c = benchmark_c_implementations(map_file, days, max_threads)

    # Parte 2: C Paralelo vs Python Paralelo
    results_cross = benchmark_c_vs_python(map_file, days, max_threads)

    # Parte 3: Limitaciones

    # Tabla
    print_results_table(results_c, results_cross)

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN EJECUTIVO")
    print("=" * 80)

    best_speedup = max(results_c["parallel"].values(), key=lambda x: x["speedup"])
    best_threads = [k for k, v in results_c["parallel"].items() if v["speedup"] == best_speedup["speedup"]][0]

    print("\nMEJORES RESULTADOS:")
    print(f"  - Mejor speedup en C: {best_speedup['speedup']:.2f}x con {best_threads} threads")
    print(f"  - Eficiencia maxima:  {best_speedup['efficiency']:.1f}%")
    print(f"  - C vs Python: C es {results_cross['speedup_c_over_python']:.2f}x mas rapido")

    print("\nTIEMPOS ABSOLUTOS:")
    print(f"  - C Serial: {results_c['serial']['time']:.4f} s")
    print(f"  - C Paralelo ({max_threads} threads): {results_c['parallel'].get(max_threads, {}).get('time', 'N/A')} s")
    print(f"  - Python Paralelo ({max_threads} threads): {results_cross['python_parallel']:.4f} s")

    # Guardar JSON
    output_file = f"benchmark_results_{map_size}_{days}.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "parameters": {
                    "map_file": map_file,
                    "map_size": map_size,
                    "days": days,
                    "max_threads": max_threads,
                },
                "c_benchmarks": results_c,
                "cross_language": results_cross,
            },
            f,
            indent=2,
        )
    print(f"\nResultados guardados en: {output_file}")

    # Graficos
    generate_plots(results_c, results_cross, f"benchmark_{map_size}_{days}")

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
