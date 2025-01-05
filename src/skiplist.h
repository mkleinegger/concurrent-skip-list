#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>

#define MAX_LEVEL 32
#define P 0.5
#define COUNTERS

#ifdef COUNTERS
#define INC(_c) ((_c)++)
#else
#define INC(_c)
#endif

#define FINE_LOCKING

typedef struct _node {
    long key;
    void *value;
    struct _node *next[MAX_LEVEL];

    #ifdef FINE_LOCKING
    omp_lock_t lock;
    volatile int marked;
    volatile int fullyLinked;
    int top_level;
    #endif
} skiplist_node;

typedef struct _list {
    struct _node *header;
    int max_level;

#ifdef COUNTERS
    unsigned long long adds, rems, cons;
#endif
} skiplist;

void init(skiplist* list);
void clean(skiplist *list);

int add(skiplist *list, long key, void *value);
int rem(skiplist *list, long key);
int con(skiplist *list, long key);