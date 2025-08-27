#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void generate_map(int n, int m, const char *filename) {
    if (n <= 0 || m <= 0) {
        printf("Invalid dimensions: n and m must be positive integers.\n");
        return;
    }

    FILE *file = fopen(filename, "w");
    if (file == NULL) {
        perror("Error opening file");
        return;
    }

    fprintf(file, "%d %d\n", n, m);

    srand(time(NULL));

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < m; j++) {
            int rand_val = rand() % 100;
            char c;
            if (rand_val < 10) {
                c = 'h';
            } else if (rand_val < 20) {
                c = 'z';
            } else {
                c = '.';
            }

            fprintf(file, "%c", c);

            if (j < m - 1) {
                fprintf(file, " ");
            }
        }
        fprintf(file, "\n");
    }

    fclose(file);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Uso: %s <dimension>\n", argv[0]);
        return 1;
    }
    int dimension = atoi(argv[1]);

    if (dimension <= 0) {
        printf("La dimensión debe de ser un integer positivo.\n");
        return 1;
    }

    const char *output_filename = "map.txt";

    generate_map(dimension, dimension, output_filename);

    printf("Mapa de dimensiones %dx%d generado y guardado en '%s'\n", dimension, dimension, output_filename);

    return 0;
}
