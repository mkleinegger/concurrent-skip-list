#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <strings.h>
#include "omp.h"

#include "skiplist.h"

#define VERBOSE

/* These structs should to match the definition in benchmark.py */
struct bench_result
{
    float time;
    unsigned long long total_inserts;
    unsigned long long successful_inserts;
    unsigned long long total_deletes;
    unsigned long long successful_deletes;
    unsigned long long total_contains;
    unsigned long long successful_contains;
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
    int seed,
    int *correctness)
{
    struct bench_result counters = {0};
    srand(seed);

    long key = 0;
    double tic, toc;

#pragma omp barrier
    tic = toc = omp_get_wtime();
    while (toc - tic < runtime_in_sec)
    {
        switch (selection_strategy)
        {
        case 0:
            key = rand() % end_range + start_range;
            break;
        case 1:
            key = (key + 1) % end_range + start_range;
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
            // avoid duplicates
            if (correctness[key] == 0)
            {
                counters.total_inserts++;
                int success = add(list, key, NULL);

                if (success)
                {
                    correctness[key] = 1;
                    counters.successful_inserts++;
                }
            }
        }
        else if (r <= i + d)
        {
            // delete
            counters.total_deletes++;
            int success = rem(list, key);

            // check for correctness
            if (success == correctness[key])
            {
                counters.successful_deletes++;
            }
            if (success)
            {
                correctness[key] = 0;
            }
        }
        else
        {
            // contains
            counters.total_contains++;
            int success = con(list, key);

            // check for correctness
            if (success == correctness[key])
            {
                counters.successful_contains++;
            }
        }
        toc = omp_get_wtime();
    }

    counters.time = toc - tic;
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
    int seed)
{
    struct bench_result result[num_of_threads];
    memset(&result, 0, sizeof(result));

    int *correctness = malloc(100000 * sizeof(int));
    memset(correctness, 0, sizeof(correctness));

    skiplist *mylist = malloc(sizeof(skiplist));
    init(mylist); // your skiplist init

    int start = start_range;
    int end = end_range;
    int step = (end - start) / num_of_threads;

    // TODO: add pre-fill items

    omp_set_num_threads(num_of_threads);
    {
#pragma omp parallel
        for (int t = 0; t < num_of_threads; t++)
        {
            if (disjoint_range == 1)
            {
                start = t * step;
                end = (t + 1) * step;
            }
            result[t] = run_benchmark(mylist, runtime_in_sec, i, d, c, start, end, selection_strategy, seed + t, correctness);
        }
    }

    clean(mylist);
    free(mylist);
    free(correctness);

    // Sum up the results
    struct bench_result result_sum = {0, 0, 0, 0, 0, 0, 0};
    for (int i = 0; i < num_of_threads; i++)
    {
        result_sum.time += result[i].time;
        result_sum.total_inserts += result[i].total_inserts;
        result_sum.successful_inserts += result[i].successful_inserts;
        result_sum.total_deletes += result[i].total_deletes;
        result_sum.successful_deletes += result[i].successful_deletes;
        result_sum.total_contains += result[i].total_contains;
        result_sum.successful_contains += result[i].successful_contains;
    }
    result_sum.time /= num_of_threads;

    // Print or return the result
#ifdef VERBOSE
    printf("\nTime: %f\n", result_sum.time);
    printf("Inserting:  %llu/%llu\n",
           result_sum.successful_inserts, result_sum.total_inserts);
    printf("Deleting:   %llu/%llu\n",
           result_sum.successful_deletes, result_sum.total_deletes);
    printf("Containing: %llu/%llu\n",
           result_sum.successful_contains, result_sum.total_contains);
#endif

    return result_sum;
}

/* main is not relevant for benchmark.py but necessary when run alone for
 * testing.
 */
int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;
    small_bench(1, 30, 10, 10, 80, 0, 100000, 0, 0, 42);
}
