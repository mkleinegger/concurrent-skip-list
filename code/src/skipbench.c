#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "skiplist.h"

typedef struct list_t {
    // Define your list structure here
} list_t;

typedef struct {
    list_t *list;
    int key_range;
    int seed;
    int insert_percent;
    int delete_percent;
    int contains_percent;
    int ops;
} thread_args_t;

volatile int keep_running;

void add(long key, void *value, list_t *list) {
    // Implement add function
}

void rem(long key, list_t *list) {
    // Implement remove function
}

void con(long key, void *value, list_t *list) {
    // Implement contains function
}

void *thread_func(void *arg) {
    thread_args_t *args = (thread_args_t *)arg;
    unsigned seed = args->seed + omp_get_thread_num();
    int ops = 0;

    while (keep_running) {
        int op = rand_r(&seed) % 100;
        long key = rand_r(&seed) % args->key_range;

        if (op < args->insert_percent) {
            add(key, NULL, args->list);
        } else if (op < args->insert_percent + args->delete_percent) {
            rem(key, args->list);
        } else {
            con(key, NULL, args->list);
        }
        ops++;
    }

    args->ops = ops;
    return NULL;
}

void run_benchmark_omp(list_t *list, int threads, int duration,
                       int key_range, int insert_percent, int delete_percent,
                       int contains_percent, unsigned seed) {
    unsigned long long total_ops = 0;

    double start_time = omp_get_wtime();

    // Allocate memory for thread arguments
    thread_args_t *args = malloc(threads * sizeof(thread_args_t));
    if (args == NULL) {
        fprintf(stderr, "Failed to allocate memory for thread arguments\n");
        return;
    }

    // Initialize thread arguments
    for (int i = 0; i < threads; i++) {
        args[i].list = list;
        args[i].key_range = key_range;
        args[i].seed = seed;
        args[i].insert_percent = insert_percent;
        args[i].delete_percent = delete_percent;
        args[i].contains_percent = contains_percent;
        args[i].ops = 0;
    }

    keep_running = 1;

    // Create threads
    #pragma omp parallel num_threads(threads)
    {
        thread_func(&args[omp_get_thread_num()]);
    }

    keep_running = 0;

    double end_time = omp_get_wtime();

    // Aggregate operations
    for (int i = 0; i < threads; i++) {
        total_ops += args[i].ops;
    }

    printf("Total operations: %llu\n", total_ops);
    printf("Duration: %f seconds\n", end_time - start_time);

    // Free allocated memory
    free(args);
}

void run_benchmark(int threads, int repetitions, int duration, int prefill_items,
                   int key_range, int insert_percent, int delete_percent,
                   int contains_percent, unsigned seed) {
    list_t list;
    node_t head, tail;

    init(&head, &tail, &list);

    for (int i = 0; i < prefill_items; i++) {
        add(rand() % key_range, NULL, &list);
    }

    double total_time = 0;
    unsigned long long total_ops = 0;

    for (int rep = 0; rep < repetitions; rep++) {
        double start_time = omp_get_wtime();

        run_benchmark_omp(&list, threads, duration, key_range, insert_percent, delete_percent, contains_percent, seed);

        double end_time = omp_get_wtime();
        total_time += (end_time - start_time) * 1000; // Convert to ms

        printf("Experiment %d complete.\n", rep + 1);
    }

    printf("Average time per experiment: %.2f ms\n", total_time / repetitions);
    printf("Total operations: %llu\n", total_ops);

    clean(&list);
}

void run_specific_benchmarks() {
    int threads = 1;
    int repetitions = 1;
    int prefill_items = 1000;
    unsigned seed = 42;
    int key_range = 100000;

    int operation_mixes[2][3] = {
        {10, 10, 80},
        {40, 40, 20}
    };

    for (int i = 0; i < 2; i++) {
        printf("Running benchmark with mix (%d, %d, %d) for %d seconds...\n",
               operation_mixes[i][0], operation_mixes[i][1], operation_mixes[i][2], repetitions);
        run_benchmark(threads, repetitions, 1, prefill_items, key_range,
                      operation_mixes[i][0], operation_mixes[i][1], operation_mixes[i][2], seed);
    }
}

int main() {
    run_specific_benchmarks();
    return 0;
}