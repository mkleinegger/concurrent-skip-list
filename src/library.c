#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <strings.h>
#include "omp.h"
#include <string.h>
#include <unistd.h>
#include <time.h>

#include "skiplist.h"

#define VERBOSE
#define INC(_c) ((_c)++)

/* These structs should match the definition in benchmark.py */
struct bench_result
{
    float time;
    long long total_operations;
    long long total_inserts;
    long long successful_inserts;
    long long total_deletes;
    long long successful_deletes;
    long long total_contains;
    long long successful_contains;
    long long operations_per_thread[64];
};

int basic_correctness_test(skiplist *list)
{
    int valid = 1;
    for (int key = 0; key < 100; key++)
    {
        valid &= con(list, key) == 0;
        valid &= add(list, key, NULL) == 1;
        valid &= con(list, key) == 1;
    }

    if (valid == 0)
    {
        printf("Basic correctness test: Inserts FAILED.\n");
        return 1;
    }

    for (int key = 0; key < 100; key += 1)
    {
        valid &= con(list, key) == 1;
        valid &= rem(list, key) == 1;
        valid &= con(list, key) == 0;
    }

    if (valid == 0)
    {
        printf("Basic correctness test: Removes FAILED.\n");
        return 1;
    }

    for (int key = 0; key < 100; key++)
    {
        valid &= con(list, key) == 0;
    }

    valid &= con(list, 999) == 0;
    if (valid == 0)
    {
        printf("Basic correctness test: Contains FAILED.\n");
        return 1;
    }

    printf("Basic correctness test: SUCCESS.\n");
    return 0;
}

long *generate_unique_keys(int start, int end, unsigned int seed)
{
    int range = end - start;
    long *keys = malloc(range * sizeof(long));
    if (!keys)
    {
        fprintf(stderr, "Memory allocation failed for unique keys.\n");
        exit(EXIT_FAILURE);
    }

    for (int i = 0; i < range; i++)
    {
        keys[i] = start + i;
    }

    srand(seed);
    for (int i = range - 1; i > 0; i--)
    {
        int j = rand() % (i + 1);
        long temp = keys[i];
        keys[i] = keys[j];
        keys[j] = temp;
    }

    return keys;
}

struct bench_result run_benchmark(
    skiplist *list,
    int runtime_in_sec,
    float i,
    float d,
    float c,
    int start_range,
    int end_range,
    int selection_strategy,
    int disjoint_range,
    int seed)
{
    double tic, toc;
    float runtime = 0.0;
    long long t_ops = 0;
    long long t_adds = 0;
    long long t_rems = 0;
    long long t_cons = 0;
    long long s_adds = 0;
    long long s_rems = 0;
    long long s_cons = 0;
    long long ops_threads[omp_get_max_threads()];

    long *unique_keys = NULL;
    int unique_key_index = 0;
    int total_unique_keys = end_range - start_range;

    if (selection_strategy == 2)
    {
        unique_keys = generate_unique_keys(start_range, end_range, seed);
    }

#pragma omp parallel shared(list, unique_keys, unique_key_index) reduction(+ : runtime, s_adds, s_rems, s_cons, t_ops, t_adds, t_rems, t_cons)
    {
        long long ops = 0;
        long long adds = 0;
        long long rems = 0;
        long long cons = 0;
        long long su_adds = 0;
        long long su_rems = 0;
        long long su_cons = 0;

        int thread_id = omp_get_thread_num();

        int start = start_range;
        int end = end_range;
        int step = (end - start) / omp_get_max_threads();
        if (disjoint_range == 1)
        {
            start = thread_id * step + start_range;
            end = (thread_id + 1) * step + start_range;
        }

        unsigned int thread_seed = seed + thread_id;
#pragma omp barrier
        long key = 0;
        tic = toc = omp_get_wtime();
        while (toc - tic < runtime_in_sec)
        {
            switch (selection_strategy)
            {
            case 0:
                key = rand_r(&thread_seed) % (end_range - start_range) + start_range;
                break;
            case 1:
                key = (key + 1) % (end_range - start_range) + start_range;
                break;
            case 2:
                key = unique_key_index++;
                if (key >= total_unique_keys)
                    break;
                key = unique_keys[key];
                break;
            }
            if (selection_strategy == 2 && key >= total_unique_keys)
            {
                break;
            }

            int r = rand_r(&thread_seed) % 100 + 1;
            if (r <= i)
            {
                if (add(list, key, NULL))
                {
                    su_adds++;
                }
                adds++;
                ops++;
            }
            else if (r <= i + d)
            {
                if (rem(list, key))
                {
                    su_rems++;
                }
                rems++;
                ops++;
            }
            else
            {
                if (con(list, key))
                {
                    su_cons++;
                }
                cons++;
                ops++;
            }
            toc = omp_get_wtime();
        }
#pragma omp barrier
        t_adds += adds;
        t_cons += cons;
        t_rems += rems;
        s_adds += su_adds;
        s_cons += su_cons;
        s_rems += su_rems;
        t_ops += ops;
        ops_threads[thread_id] = ops;
        runtime += toc - tic;
    }

    struct bench_result counters = {.time = runtime / omp_get_max_threads(),
                                    .total_operations = t_ops,
                                    .total_inserts = t_adds,
                                    .successful_inserts = s_adds,
                                    .total_deletes = t_rems,
                                    .successful_deletes = s_rems,
                                    .total_contains = t_cons,
                                    .successful_contains = s_cons};

    for (int i = 0; i < omp_get_max_threads(); i++)
    {
        counters.operations_per_thread[i] = ops_threads[i];
    }

    if (unique_keys != NULL)
        free(unique_keys);
    return counters;
}

struct bench_result bench(
    int num_of_threads,
    int runtime_in_sec,
    float i,
    float d,
    float c,
    int start_range,
    int end_range,
    int disjoint_range,
    int selection_strategy,
    int prefill_count,
    int basic_testing,
    int seed)
{
    skiplist *mylist = malloc(sizeof(skiplist));
    if (!mylist)
    {
        fprintf(stderr, "Memory allocation failed for skiplist.\n");
        exit(EXIT_FAILURE);
    }
    init(mylist);

    // Perform basic correctness test in a single thread
#pragma omp single
    {
        if (basic_testing == 1)
        {
            basic_correctness_test(mylist);
        }
    }

    srand(seed);
    for (int j = 0; j < prefill_count; j++)
    {
        int key;
        switch (selection_strategy)
        {
        case 0:
            key = rand() % (end_range - start_range) + start_range;
            break;
        case 1:
        case 2:
            key = j % (end_range - start_range) + start_range;
            break;
        default:
            key = rand() % (end_range - start_range) + start_range;
            break;
        }
        add(mylist, key, NULL);
    }

    struct bench_result result = {0};
    omp_set_num_threads(num_of_threads);
    {
#ifdef VERBOSE
        printf("Number of threads: %d\n", omp_get_max_threads());
#endif
        result = run_benchmark(mylist, runtime_in_sec, i, d, c, start_range, end_range, selection_strategy, disjoint_range, seed);
    }

    clean(mylist);
    free(mylist);

#ifdef VERBOSE
    printf("\nTime: %f seconds\n", result.time);
    printf("Inserting:  %llu/%llu\n",
           result.successful_inserts, result.total_inserts);
    printf("Deleting:   %llu/%llu\n",
           result.successful_deletes, result.total_deletes);
    printf("Containing: %llu/%llu\n",
           result.successful_contains, result.total_contains);
    printf("Total operations: %llu\n", result.total_operations);

    for (int i = 0; i < num_of_threads; i++)
    {
        printf("Thread %d: %llu operations\n", i, result.operations_per_thread[i]);
    }
#endif

    return result;
}

/* main is not relevant for benchmark.py but necessary when run alone for
 * testing.
 */
int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;
    bench(64, 1, 10, 10, 80, 0, 100000, 1, 0, 0, 1, 42);
}
