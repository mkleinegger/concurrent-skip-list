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
    unsigned long long successful_contains;};

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
    struct bench_result counters = {0, 0, 0, 0, 0, 0, 0};
    srand(seed);

    long key = 0;
    double tic, toc;
    tic = toc = omp_get_wtime();
    while (toc - tic < runtime_in_sec)
    {
        switch (selection_strategy)
        {
        case 0:
            key = rand() % end_range + start_range;
            break;
        case 1:
            key++;
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
    struct bench_result result;
    memset(&result, 0, sizeof(result));

    int *correctness = malloc(100000 * sizeof(int));
    memset(correctness, 0, sizeof(correctness));

    skiplist *mylist = malloc(sizeof(skiplist));
    init(mylist); // your skiplist init

    result = run_benchmark(mylist, runtime_in_sec, i, d, c, start_range, end_range, selection_strategy, seed, correctness);
    
    clean(mylist);

#ifdef VERBOSE
    // Print or return the result
    printf("\nInserting:  %llu/%llu\n",
           result.successful_inserts, result.total_inserts);
    printf("Deleting:   %llu/%llu\n",
           result.successful_deletes, result.total_deletes);
    printf("Containing: %llu/%llu\n",
           result.successful_contains, result.total_contains);
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
}
