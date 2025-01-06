#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>
#include <time.h>
#include <stdatomic.h>

#define WAIT_FREE

#define UNMARK_MASK ~1
#define MARK_BIT 0x0000000000001

#define getpointer(_markedpointer) ((skiplist_node *)(((long)_markedpointer) & UNMARK_MASK))
#define ismarked(_markedpointer) ((((long)_markedpointer) & MARK_BIT) != 0x0)
#define setmark(_markedpointer) ((skiplist_node *)(((long)_markedpointer) | MARK_BIT))

#define LOAD(_a) atomic_load_explicit(_a, memory_order_acquire)
#define STORE(_a, _e) atomic_store_explicit(_a, _e, memory_order_release)
#define CAS(_a, _e, _d) atomic_compare_exchange_strong_explicit(_a, _e, _d, memory_order_acq_rel, memory_order_acquire)
