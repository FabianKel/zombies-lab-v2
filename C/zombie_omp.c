#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <omp.h>

static const int DI[8] = {-1, +1, 0, 0, -1, -1, +1, +1};
static const int DJ[8] = {0, 0, -1, +1, -1, +1, -1, +1};

#define AT(A, i, j, N) (A[(i) * (N) + (j)])

static inline int inside(int i, int j, int N) { return (i >= 0 && i < N && j >= 0 && j < N); }

static int read_input(FILE *f, int *N, char **grid) {
    int M; // ignored
    if (fscanf(f, "%d %d", N, &M) != 2) return 0;

    int Nloc = *N;
    *grid = (char *)malloc((size_t)Nloc * Nloc);
    if (!*grid) return 0;

    int count = 0;
    while (count < Nloc * Nloc) {
        int c = fgetc(f);
        if (c == EOF) break;
        if (c == 'H' || c == 'Z' || c == '.' || c == 'h' || c == 'z')
            (*grid)[count++] = (char)toupper(c);
    }
    return count == Nloc * Nloc;
}

static void save_grid(char *grid, int N, const char *fname) {
    FILE *out = fopen(fname, "w");
    if (!out) return;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            fputc(AT(grid, i, j, N), out);
            if (j + 1 < N) fputc(' ', out);
        }
        fputc('\n', out);
    }
    fclose(out);
}

static void simulate_step_omp(char *prev, char *next, unsigned char *mark, int N) {
#pragma omp parallel for
    for (int idx = 0; idx < N * N; idx++) mark[idx] = 0;

#pragma omp parallel for schedule(static)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (AT(prev, i, j, N) != 'Z') continue;
            for (int k = 0; k < 8; k++) {
                int ni = i + DI[k], nj = j + DJ[k];
                if (!inside(ni, nj, N)) continue;
                if (AT(prev, ni, nj, N) == 'H') {
#pragma omp atomic write
                    AT(mark, ni, nj, N) = 1;
                    break;
                }
            }
        }
    }

#pragma omp parallel for schedule(static)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            char c = AT(prev, i, j, N);
            if (c == 'Z')
                AT(next, i, j, N) = 'Z';
            else if (c == 'H')
                AT(next, i, j, N) = AT(mark, i, j, N) ? 'Z' : 'H';
            else
                AT(next, i, j, N) = '.';
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s map.txt days [threads]\n", argv[0]);
        return 1;
    }
    int days = atoi(argv[2]);
    int threads = (argc >= 4) ? atoi(argv[3]) : omp_get_max_threads();
    omp_set_num_threads(threads);

    FILE *f = fopen(argv[1], "r");
    if (!f) { perror("fopen"); return 1; }

    int N;
    char *prev;
    if (!read_input(f, &N, &prev)) {
        fprintf(stderr, "Invalid input.\n");
        return 1;
    }
    fclose(f);

    char *next = (char *)malloc((size_t)N * N);
    unsigned char *mark = (unsigned char *)malloc((size_t)N * N);

    double t0 = omp_get_wtime();
    for (int t = 0; t < days; t++) {
        simulate_step_omp(prev, next, mark, N);
        char *tmp = prev; prev = next; next = tmp;
    }
    double t1 = omp_get_wtime();

    save_grid(prev, N, "final_map.txt");

    printf("Time = %.6f\n", t1 - t0);
    printf("Cores = %d\n", threads);

    free(prev); free(next); free(mark);
    return 0;
}
