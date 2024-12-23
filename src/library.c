#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <strings.h>
#include "omp.h"

#include "skiplist.h"

/* These structs should to match the definition in benchmark.py */
struct counters
{
    unsigned long long total_inserts;
    unsigned long long successful_inserts;
    unsigned long long total_deletes;
    unsigned long long successful_deletes;
    unsigned long long total_contains;
    unsigned long long successful_contains;
};
struct bench_result
{
    float time;
    struct counters counters;
};

struct bench_result run_benchmark(
    skiplist *list,
    int runtime_in_sec,
    float i,
    float d,
    float c,
    int start_range,
    int end_range,
    int seed,
    int *correctness)
{
    struct bench_result data = {0}; // everything set to zero
    data.time = 0.0f;
    srand(seed);

    double tic = omp_get_wtime();
    double toc = omp_get_wtime();
    while (toc - tic < runtime_in_sec)
    {
        // pick an op: (insert, remove, contains)
        int r = rand() % 100;       // 0..99
        long key = rand() % 100000; // pick some key range, e.g. 0..9999

        if (r < 20)
        {
            if (correctness[key] == 0)
            {

                // insert
                data.counters.total_inserts++;
                int success = add(list, key, NULL);
                if (success)
                {
                    correctness[key]++;
                    data.counters.successful_inserts++;
                }
            }
        }
        else if (r < 40)
        {
            // delete
            data.counters.total_deletes++;
            int success = rem(list, key);
            if (success == correctness[key])
            {
                data.counters.successful_deletes++;
            }
            if (success)
            {
                correctness[key] = 0;
            }
        }
        else
        {
            // contains
            data.counters.total_contains++;
            int success = con(list, key);
            if (success == correctness[key])
                data.counters.successful_contains++;
        }
        toc = omp_get_wtime();
    }
    data.time = (float)(toc - tic);
    return data;
}

struct bench_result small_bench(
    int num_of_threads,
    int repetitions,
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
    memset(&result.counters, 0, sizeof(result.counters));

    int *correctness = malloc(100000 * sizeof(int));
    memset(correctness, 0, sizeof(correctness));

    skiplist *mylist = malloc(sizeof(skiplist));
    init(mylist); // your skiplist init

    run_benchmark(mylist, 1, 0.5, 0.2, 0.3, 0, 100000, 0, correctness);

    clean(mylist); // optional: free memory

    // Print or return the result
    printf("Thread=%d, times=%d, took=%.6f s\n", 0, 1, result.time);
    printf("  Inserting:  %llu/%llu\n",
           result.counters.successful_inserts, result.counters.total_inserts);
    printf("  Deleting:   %llu/%llu\n",
           result.counters.successful_deletes, result.counters.total_deletes);
    printf("  Containing: %llu/%llu\n",
           result.counters.successful_contains, result.counters.total_contains);

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
