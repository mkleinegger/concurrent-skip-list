#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <strings.h>
#include <stdbool.h>
#include <omp.h>

/* These structs should to match the definition in benchmark.py
 */
struct counters {
    int failed_turns;
    int successful_lends;
};
struct bench_result {
    float time;
    struct counters reduced_counters;
};

/* This is our example shared structure, a library for threads. Books can be
 * lent and returned via the four respective functions.
 */
struct one_thread_library {
    int art_of_multiprocessor_programming;
    int the_c_programming_language;
} library;


bool lend_herlihyshavit_luchangco_spear(struct one_thread_library* l) {
    if (l->art_of_multiprocessor_programming > 0) {
        l->art_of_multiprocessor_programming--;
        return true;
    }
    return false;
}

void return_herlihyshavit_luchangco_spear(struct one_thread_library* l) {
    l->art_of_multiprocessor_programming++;
}

bool lend_kernigham_ritchie(struct one_thread_library* l) {
    if (l->the_c_programming_language > 0) {
        l->the_c_programming_language--;
        return true;
    }
    return false;
}

void return_kernigham_ritchie(struct one_thread_library* l) {
    l->the_c_programming_language++;
}

struct counters random_bench1(struct one_thread_library* l, int times, int seed) {
    int tid = omp_get_thread_num();
    printf("Thread %d started.\n", tid);
    // Barrier to force OMP to start all threads at the same time
    #pragma omp barrier

    struct random_data rand_state;
    int choice;
    char statebuf[32];
    bzero(&rand_state, sizeof(struct random_data));
    bzero(&statebuf,   sizeof(statebuf));
    initstate_r(seed, statebuf, 32, &rand_state);

    struct counters data = {.failed_turns = 0,
                            .successful_lends = 0};

    int herlihy_shavit_luchangco_spear = 0;
    int kernigham_ritchie = 0;

    for (int i=0; i<times;) {
        // What are we reading today?
        random_r(&rand_state, &choice);

        // We can only have exclusive access to the library
        #pragma omp critical
        {
            if (choice > ((1<<30))) {
                if (lend_herlihyshavit_luchangco_spear(l)) {
                    herlihy_shavit_luchangco_spear++;
                    data.successful_lends++;
                } else if (herlihy_shavit_luchangco_spear > 0) {
                    return_herlihyshavit_luchangco_spear(l);
                    herlihy_shavit_luchangco_spear--;
                    i++;
                } else {
                    data.failed_turns++;
                }
            } else {
                if (lend_kernigham_ritchie(l)) {
                    kernigham_ritchie++;
                    data.successful_lends++;
                } else if (kernigham_ritchie > 0) {
                    return_kernigham_ritchie(l);
                    kernigham_ritchie--;
                    i++;
                } else {
                    data.failed_turns++;
                }
            }
        }
    }
    return data;
}

struct bench_result small_bench(int t, int len) {
    struct bench_result result;
    struct counters thread_data[t];
    double tic, toc;

    library.art_of_multiprocessor_programming = 20;
    library.the_c_programming_language = 20;

    omp_set_num_threads(t);
    tic = omp_get_wtime();
    {
        #pragma omp parallel for
        for (int i=0; i<t; i++) {
            thread_data[i] = random_bench1(&library, len, i);
        }
    }
    toc = omp_get_wtime();

    for (int i=0; i<t; i++) {
        result.reduced_counters.successful_lends += thread_data[i].successful_lends;
        result.reduced_counters.failed_turns     += thread_data[i].failed_turns;
    }

    result.time = (toc - tic);
    printf("LIBRARY: lending %d books on %d threads took: %fs\n",\
           len, t, toc - tic);
    printf("  with %d failed turns and %d successful lends: %f lends/s throughput\n",\
        result.reduced_counters.failed_turns,
        result.reduced_counters.successful_lends,
        result.reduced_counters.successful_lends/result.time);

    return result;
}

/* main is not relevant for benchmark.py but necessary when run alone for
 * testing.
 */
int main(int argc, char * argv[]) {
    (void) argc;
    (void) argv;
    small_bench(1, 10);
    small_bench(2, 10);
    small_bench(4, 10);
    small_bench(8, 10);
    small_bench(16, 10);
}
