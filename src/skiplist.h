/**
 * @file skip_list.h
 * @author Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
 * @date 2025-01-13
 *
 * @brief This file defines the necessary structs and methods for the skiplist.
 *  Different implementations of the skiplist are controlled via #define statements,
 *  which are specified in the corresponding implementation files and activated through
 *  the linking process during compilation.
 */

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
#elif defined(LOCK_FREE)
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

/**
 * @brief Initializes a skiplist structure.
 *
 * @param list Pointer to the skiplist to initialize.
 */
void init(skiplist *list);

/**
 * @brief Cleans up a skiplist structure, freeing allocated memory.
 *
 * @param list Pointer to the skiplist to clean.
 */
void clean(skiplist *list);

/**
 * @brief Inserts a key-value pair into the skiplist.
 *
 * @param list Pointer to the skiplist.
 * @param key The key to insert.
 * @param value Pointer to the value associated with the key.
 *
 * @return 1 if the insertion was successful, 0 if the key already exists.
 */
int add(skiplist *list, long key, void *value);

/**
 * @brief Removes a key from the skiplist.
 *
 * @param list Pointer to the skiplist.
 * @param key The key to remove.
 *
 * @return 1 if the removal was successful, 0 if the key was not found.
 */
int rem(skiplist *list, long key);

/**
 * @brief Checks if a key exists in the skiplist.
 *
 * @param list Pointer to the skiplist.
 * @param key The key to check.
 *
 * @return 1 if the key is found, 0 otherwise.
 */
int con(skiplist *list, long key);