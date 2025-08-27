#!/bin/bash
set -e

# Compile
gcc zombie_serial.c -O2 -o zombie_serial
gcc zombie_omp.c -O2 -fopenmp -o zombie_omp

DAYS=20
THREADS=8

# Run serial
SERIAL_OUTPUT=$(./zombie_serial map.txt $DAYS)
SERIAL_TIME=$(echo "$SERIAL_OUTPUT" | grep "Time" | awk '{print $3}')
echo "Serial:"
echo "$SERIAL_OUTPUT"

# Run parallel
PARALLEL_OUTPUT=$(./zombie_omp map.txt $DAYS $THREADS)
PARALLEL_TIME=$(echo "$PARALLEL_OUTPUT" | grep "Time" | awk '{print $3}')
CORES=$(echo "$PARALLEL_OUTPUT" | grep "Cores" | awk '{print $3}')
echo "Parallel:"
echo "$PARALLEL_OUTPUT"

# Speedup & efficiency
SPEEDUP=$(echo "$SERIAL_TIME / $PARALLEL_TIME" | bc -l)
EFFICIENCY=$(echo "$SPEEDUP / $CORES" | bc -l)

echo "========== RESULTS =========="
echo "Serial Time   = $SERIAL_TIME"
echo "Parallel Time = $PARALLEL_TIME"
echo "Cores         = $CORES"
echo "Speedup       = $SPEEDUP"
echo "Efficiency    = $EFFICIENCY"
