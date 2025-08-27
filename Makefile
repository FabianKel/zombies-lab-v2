# Makefile para compilacion y pruebas (Windows/MSYS o WSL)
CC       = gcc
CFLAGS   = -O2 -Wall
OMPFLAGS = -fopenmp

CDIR   = C
PYDIR  = Python

# Ejecutables (en Windows gcc genera .exe automaticamente si el nombre lo tiene)
GEN_MAP       = gen_map.exe
ZOMBIE_SERIAL = zombie_serial.exe
ZOMBIE_OMP    = zombie_omp.exe

# Parametros
MAP_SIZE ?= 1500
DAYS     ?= 150
THREADS  ?= 8

# Archivos de salida
MAP_FILE     = test_map_$(MAP_SIZE).txt
RESULTS_FILE = results_$(MAP_SIZE)_$(DAYS).txt

# Python (se puede sobreescribir: make ... PYTHON="py -3")
PYTHON ?= python3

# ------------------------------------------------------------

all: $(GEN_MAP) $(ZOMBIE_SERIAL) $(ZOMBIE_OMP)

$(GEN_MAP): $(CDIR)/helpers.c
	$(CC) $(CFLAGS) -o $@ $<

$(ZOMBIE_SERIAL): $(CDIR)/zombie_serial.c
	$(CC) $(CFLAGS) -o $@ $<

$(ZOMBIE_OMP): $(CDIR)/zombie_omp.c
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $<

# Generar mapa de prueba (usa stdout del generador)
generate_map: $(GEN_MAP)
	./$(GEN_MAP) $(MAP_SIZE) > $(MAP_FILE)
	@echo "Mapa generado: $(MAP_FILE) ($(MAP_SIZE)x$(MAP_SIZE))"

# C serial
run_serial: $(ZOMBIE_SERIAL) generate_map
	@echo "\n=== Ejecutando version SERIAL en C ==="
	@./$(ZOMBIE_SERIAL) $(MAP_FILE) $(DAYS)

# C paralelo OpenMP
run_parallel: $(ZOMBIE_OMP) generate_map
	@echo "\n=== Ejecutando version PARALELA en C ==="
	@./$(ZOMBIE_OMP) $(MAP_FILE) $(DAYS) $(THREADS)

# Python multithreading
run_python: generate_map
	@echo "\n=== Ejecutando version PARALELA en Python ==="
	@$(PYTHON) $(PYDIR)/zombie_threads.py $(MAP_FILE) $(DAYS) $(THREADS)

# Benchmark completo (no regeneres mapa aparte)
benchmark: all generate_map
	@echo "Iniciando benchmark completo..."
	@$(PYTHON) $(PYDIR)/run_benchmarks.py $(MAP_FILE) $(DAYS) $(THREADS) > $(RESULTS_FILE)
	@echo "Resultados guardados en: $(RESULTS_FILE)"
	@cat $(RESULTS_FILE)

clean:
	rm -f $(GEN_MAP) $(ZOMBIE_SERIAL) $(ZOMBIE_OMP) *.o
	rm -f test_map_*.txt final_map.txt
	rm -f results_*.txt
	rm -f *.png *.json

.PHONY: all generate_map run_serial run_parallel run_python benchmark clean
