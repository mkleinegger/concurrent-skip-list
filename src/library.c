#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <strings.h>
#include "omp.h"
#include <string.h>

#include "skiplist.h"

#define VERBOSE
#define COUNTERS

/* These structs should to match the definition in benchmark.py */
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
};

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
    float time = 0.0;
    long long t_ops = 0;
    long long t_adds = 0;
    long long t_rems = 0;
    long long t_cons = 0;
    long long s_adds = 0;
    long long s_rems = 0;
    long long s_cons = 0;

#pragma omp parallel shared(list) reduction(+ : time, s_adds, s_rems, s_cons, t_ops, t_adds, t_rems, t_cons)
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
            start = thread_id * step;
            end = (thread_id + 1) * step;
        }

        srand(seed + thread_id);
#pragma omp barrier
        long key = 0;
        tic = toc = omp_get_wtime();
        while(toc - tic < runtime_in_sec)
        {
            switch (selection_strategy)
            {
            case 0:
                key = rand() % end + start;
                break;
            case 1:
                key = (key + 1) % end + start;
                break;
            case 2:
                // TODO: unique random numbers
                break;
            default:
                break;
            }

            int r = rand() % 100 + 1;
            if (r <= i)
            {
                if (add(list, key, NULL))
                {
                    INC(su_adds);
                }
                INC(adds);
                INC(ops);
            }
            else if (r <= i + d)
            {
                // if (rem(list, key))
                // {
                //     INC(su_rems);
                // }
                // INC(ops);
                // INC(rems);
            }
            else
            {
                // if (con(list, key))
                // {
                //     INC(su_cons);
                // }
                // INC(ops);
                // INC(cons);
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
        time += toc - tic;
    }

    struct bench_result counters = {.time = time / omp_get_max_threads(),
                                    .total_operations = t_ops,
                                    .total_inserts = t_adds,
                                    .successful_inserts = s_adds,
                                    .total_deletes = t_rems,
                                    .successful_deletes = s_rems,
                                    .total_contains = t_cons,
                                    .successful_contains = s_cons};
    return counters;
}

struct bench_result small_bench(
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
    int seed)
{
    skiplist *mylist = malloc(sizeof(skiplist));
    init(mylist); // your skiplist init

    // Pre-fill items based on the selection strategy
    for (int j = 0; j < prefill_count; j++)
    {
        int key;
        switch (selection_strategy)
        {
        case 0:
            key = rand() % end_range + start_range;
            break;
        case 1:
            key = j % end_range + start_range;
            break;
        case 2:
            // Generate unique random numbers
            key = j;
            break;
        default:
            key = rand() % end_range + start_range;
            break;
        }
        add(mylist, key, NULL);
    }
    struct bench_result result = {0, 0, 0, 0, 0, 0, 0};
    omp_set_num_threads(num_of_threads);
    {
        printf("Number of threads: %d\n", omp_get_max_threads());
        result = run_benchmark(mylist, runtime_in_sec, i, d, c, start_range, end_range, selection_strategy, 0, seed);
    }

    clean(mylist);
    free(mylist);

    // Print or return the result
#ifdef VERBOSE
    printf("\nTime: %f\n", result.time);
    printf("Inserting:  %llu/%llu\n",
           result.successful_inserts, result.total_inserts);
    printf("Deleting:   %llu/%llu\n",
           result.successful_deletes, result.total_deletes);
    printf("Containing: %llu/%llu\n",
           result.successful_contains, result.total_contains);
    printf("Total operations: %llu\n", result.total_operations);
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
    small_bench(40, 1, 100, 0, 0, 0, 100000, 0, 1, 0, 42);
}
