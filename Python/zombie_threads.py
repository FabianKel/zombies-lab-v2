#!/usr/bin/env python3
import sys
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import cpu_count

DI = [-1, +1, 0, 0, -1, -1, +1, +1]
DJ = [ 0,  0, -1, +1, -1, +1, -1, +1]

def inside(i, j, N):
    return 0 <= i < N and 0 <= j < N

def read_input(filename):
    with open(filename, "r") as f:
        header = f.readline().strip()
        parts = header.split()
        if len(parts) < 2:
            raise ValueError("Invalid header")
        N = int(parts[0])  # M se ignora

        data = []
        for _ in range(N):
            line = f.readline()
            if not line:
                break
            for tok in line.strip().split():  # tokens separados por espacios
                c = tok.upper()
                if c in ("H", "Z", "."):
                    data.append(c)

        if len(data) != N * N:
            raise ValueError(f"Invalid input: expected {N*N} cells, got {len(data)}")

    grid = np.array(data, dtype="<U1").reshape(N, N)
    return N, grid



def save_grid(grid, fname):
    with open(fname, "w") as f:
        for row in grid:
            f.write(" ".join(row) + "\n")

def process_row(i, prev, N):
    """Marca infecciones en la fila i (multithreading)."""
    marks = np.zeros(N, dtype=np.uint8)
    row = prev[i]
    for j, c in enumerate(row):
        if c != 'Z':
            continue
        for k in range(8):
            ni, nj = i + DI[k], j + DJ[k]
            if inside(ni, nj, N) and prev[ni, nj] == 'H':
                marks[nj] = 1  # marcar humano infectado
                break
    return i, marks

def simulate_step_threads(prev, N, executor, workers):
    mark = np.zeros((N, N), dtype=np.uint8)

    # lanzar tareas por fila
    futures = [executor.submit(process_row, i, prev, N) for i in range(N)]
    for fut in as_completed(futures):
        i, row_marks = fut.result()
        mark[i] = row_marks

    # construir siguiente grilla (secuencial; también puede dividirse)
    next_grid = np.full((N, N), '.', dtype='<U1')
    for i in range(N):
        for j in range(N):
            c = prev[i, j]
            if c == 'Z':
                next_grid[i, j] = 'Z'
            elif c == 'H':
                next_grid[i, j] = 'Z' if mark[i, j] else 'H'
            else:
                next_grid[i, j] = '.'
    return next_grid

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} map.txt days [threads]")
        sys.exit(1)

    mapfile = sys.argv[1]
    days = int(sys.argv[2])
    threads = int(sys.argv[3]) if len(sys.argv) >= 4 else (cpu_count() or 4)

    N, grid = read_input(mapfile)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads) as ex:
        for _ in range(days):
            grid = simulate_step_threads(grid, N, ex, threads)
    t1 = time.perf_counter()

    save_grid(grid, "final_map.txt")
    print(f"Time = {t1 - t0:.6f}")
    print(f"Cores = {threads}")

if __name__ == "__main__":
    main()
