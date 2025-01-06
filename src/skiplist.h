#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <limits.h>
#include <omp.h>

#define MAX_LEVEL 16
#define P 0.5

typedef struct _node
{
    long key;
    void *value;
    int top_level;

#ifdef FINE_LOCKING
    omp_lock_t lock;
    volatile int marked;
    volatile int fullyLinked;
    struct _node *next[MAX_LEVEL];
#elif defined(WAIT_FREE)
    _Atomic(struct _node *) next[MAX_LEVEL];
#else
    struct _node *next[MAX_LEVEL];
#endif
} skiplist_node;

typedef struct _list
{
    struct _node *header;

#ifdef GLOBAL_LOCK
    omp_lock_t lock;
#endif
} skiplist;

void init(skiplist *list);
void clean(skiplist *list);

int add(skiplist *list, long key, void *value);
int rem(skiplist *list, long key);
int con(skiplist *list, long key);