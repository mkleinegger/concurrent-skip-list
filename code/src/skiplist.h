#ifndef SKIPLIST_H
#define SKIPLIST_H

#include <stdio.h>
#include <stdlib.h>

#define MAX_LEVEL 16
#define PROBABILITY 0.5

typedef struct _node {
    long key;
    void *value;
    struct _node *next[MAX_LEVEL];
} node_t;

typedef struct _list {
    node_t *head;
    node_t *tail;
    int maxLevel;

    #ifdef COUNTERS
    unsigned long long adds;
    unsigned long long rems;
    unsigned long long cons;
    #endif
} list_t;

typedef struct {
    int adds;  // Number of successful additions
    int rems;  // Number of successful removals
    int cons;  // Number of successful contains
} cBenchCounters;

typedef struct {
    float time;         // Total execution time in seconds
    cBenchCounters counters;  // Operation counters
} cBenchResult;


// Skip list function prototypes
void init(node_t *head, node_t *tail, list_t *list);
void clean(list_t *list);
int add(long key, void *value, list_t *list);
int rem(long key, list_t *list);
int con(long key, void **value, list_t *list);
void pos(long key, list_t *list, node_t **preds, node_t **succs);

// Benchmark prototype
cBenchResult run_benchmark(list_t *list, int prefill_count, int duration,
                           int op_mix[3], int key_range, int seed);

cBenchResult bench_add(list_t *list, int key_range, int duration);
cBenchResult bench_rem(list_t *list, int key_range, int duration);
cBenchResult bench_con(list_t *list, int key_range, int duration);



#endif // SKIPLIST_H
