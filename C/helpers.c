#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <size>\n", argv[0]);
        fprintf(stderr, "Generates a size x size map with random distribution\n");
        return 1;
    }

    int N = atoi(argv[1]);
    if (N <= 0) {
        fprintf(stderr, "Size must be positive\n");
        return 1;
    }

    srand((unsigned)time(NULL));

    printf("%d %d\n", N, N);

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            int r = rand() % 100;
            char cell = (r < 60) ? 'H' : (r < 65 ? 'Z' : '.');
            printf("%c", cell);
            if (j < N - 1) printf(" ");
        }
        printf("\n");
    }
    return 0;
}
