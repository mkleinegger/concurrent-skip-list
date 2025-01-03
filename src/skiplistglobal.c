#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "skiplist.h"

// Define a global lock
omp_lock_t lock;

int randomLevel(double p, int max_level)
{
    int level = 0;

    while ((rand() / (double)RAND_MAX) < p && level < max_level - 1)
    {
        level++;
    }

    return level;
}

int add(skiplist *list, long key, void *value)
{
    omp_set_lock(&lock); // Acquire lock
    skiplist_node *update[MAX_LEVEL];
    skiplist_node *node = list->header;

    for (int i = list->max_level; i >= 0; i--)
    {
        while (node->next[i] != NULL && node->next[i]->key < key)
        {
            node = node->next[i];
        }
        update[i] = node;
    }

    if (node->next[0] != NULL && node->next[0]->key == key)
    {
        omp_unset_lock(&lock);
        return 0;
    }

    int level = randomLevel(P, MAX_LEVEL);
    if (level > list->max_level)
    {
        for (int i = list->max_level + 1; i <= level; i++)
        {
            update[i] = list->header;
        }
        list->max_level = level;
    }

    skiplist_node *new_node = malloc(sizeof(skiplist_node));
    if (!new_node) {
        omp_unset_lock(&lock);
        return -1;
    }
    new_node->key = key;
    new_node->value = value;

    for (int i = 0; i <= level; i++)
    {
        new_node->next[i] = update[i]->next[i];
        update[i]->next[i] = new_node;
    }

    INC(list->adds);

    omp_unset_lock(&lock); // Release lock
    return 1;              // Return 1 to indicate success
}

int con(skiplist *list, long key)
{
    omp_set_lock(&lock); // Acquire lock
    int success = 0;
    skiplist_node *node = list->header;
    for (int i = list->max_level; i >= 0; i--)
    {
        while (node->next[i] != NULL && node->next[i]->key < key)
        {
            node = node->next[i];
        }
    }

    if (node->next[0] != NULL && node->next[0]->key == key)
    {
        INC(list->cons);
        success = 1;
    }
    omp_unset_lock(&lock); // Release lock
    return success;
}

int rem(skiplist *list, long key)
{
    omp_set_lock(&lock); // Acquire lock
    skiplist_node *update[MAX_LEVEL];
    skiplist_node *node = list->header;

    for (int i = list->max_level; i >= 0; i--)
    {
        while (node->next[i] != NULL && node->next[i]->key < key)
        {
            node = node->next[i];
        }
        update[i] = node;
    }

    node = node->next[0];
    if (node != NULL && node->key == key)
    {
        for (int i = 0; i <= list->max_level; i++)
        {
            if (update[i]->next[i] != node)
            {
                break;
            }
            update[i]->next[i] = node->next[i];
        }

        free(node);
        INC(list->rems);

        while (list->max_level > 0 && list->header->next[list->max_level] == NULL)
        {
            list->max_level--;
        }
        omp_unset_lock(&lock); // Release lock
        return 1;
    }
    omp_unset_lock(&lock); // Release lock
    return 0;
}

void init(skiplist *list)
{
    list->header = malloc(sizeof(skiplist_node));
    list->header->key = -1;
    list->header->value = NULL;
    list->max_level = 0;

    for (int i = 0; i < MAX_LEVEL; i++)
    {
        list->header->next[i] = NULL;
    }

    omp_init_lock(&lock);
}

void clean(skiplist *list)
{
    skiplist_node *node = list->header->next[0];
    while (node != NULL)
    {
        skiplist_node *next = node->next[0];
        free(node);
        node = next;
    }

    free(list->header);
    omp_destroy_lock(&lock);

#ifdef COUNTERS
    list->adds = 0;
    list->cons = 0;
    list->rems = 0;
#endif
}
