/**
 * @file skiplist_finelocking.c
 * @author Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
 * @date 2025-01-13
 *
 * @brief This file implements the skiplist using a lazy fine-grained locking approach.
 */

#include "skiplist_finelocking.h"
#include "skiplist.h"

void init(skiplist *list)
{
    list->header = (skiplist_node *)malloc(sizeof(skiplist_node));
    list->header->key = INT_MIN;
    list->header->value = NULL;
    list->header->marked = 0;
    list->header->fullyLinked = 1;
    list->header->top_level = MAX_LEVEL - 1;
    omp_init_lock(&list->header->lock);

    for (int i = 0; i < MAX_LEVEL; i++)
    {
        list->header->next[i] = NULL;
    }
}

void clean(skiplist *list)
{
    if (!list)
        return;

    skiplist_node *node = list->header;

    while (node != NULL)
    {
        skiplist_node *temp = node;
        node = node->next[0];
        if (temp != NULL)
        {
            omp_destroy_lock(&temp->lock);
            free(temp);
        }
    }

    list->header = NULL;
}

int find(skiplist *list, long key, skiplist_node **preds, skiplist_node **succs);

int randomLevel(double p, int max_level)
{
    int level = 0;
    while ((rand() / (double)RAND_MAX) < p && level < max_level)
    {
        level++;
    }
    return level;
}

int find(skiplist *list, long key, skiplist_node **preds, skiplist_node **succs)
{
    int lFound = -1;
    skiplist_node *pred = list->header;
    for (int level = MAX_LEVEL - 1; level >= 0; level--)
    {
        skiplist_node *curr = pred->next[level];
        while (curr != NULL && curr->key < key)
        {
            pred = curr;
            curr = pred->next[level];
        }
        if (lFound == -1 && curr != NULL && curr->key == key)
        {
            lFound = level;
        }
        preds[level] = pred;
        succs[level] = curr;
    }
    return lFound;
}

int add(skiplist *list, long key, void *value)
{
    int topLevel = randomLevel(P, MAX_LEVEL - 1);
    skiplist_node *preds[MAX_LEVEL];
    skiplist_node *succs[MAX_LEVEL];

    while (1)
    {
        int lFound = find(list, key, preds, succs);
        if (lFound != -1)
        {
            skiplist_node *nodeFound = succs[lFound];
            if (!nodeFound->marked)
            {
                while (!nodeFound->fullyLinked)
                {
                }
                return 0;
            }
            continue;
        }

        skiplist_node *nodesToLock[MAX_LEVEL];
        int numNodesToLock = 0;
        nodesToLock[numNodesToLock++] = preds[0];
        for (int level = 1; level <= topLevel; level++)
        {
            if (preds[level]->key != preds[level - 1]->key)
            {
                nodesToLock[numNodesToLock++] = preds[level];
            }
        }

        for (int i = 0; i < numNodesToLock; i++)
        {
            omp_set_lock(&nodesToLock[i]->lock);
        }

        int valid = 1;
        for (int level = 0; level <= topLevel && valid; level++)
        {
            valid = preds[level]->marked == 0 && (succs[level] == NULL || succs[level]->marked == 0) && preds[level]->next[level] == succs[level];
        }

        if (!valid)
        {
            for (int i = 0; i < numNodesToLock; i++)
            {
                omp_unset_lock(&nodesToLock[i]->lock);
            }
            continue;
        }

        skiplist_node *new_node = (skiplist_node *)malloc(sizeof(skiplist_node));
        if (!new_node)
        {
            for (int i = 0; i < numNodesToLock; i++)
            {
                omp_unset_lock(&nodesToLock[i]->lock);
            }
            return -1;
        }
        new_node->key = key;
        new_node->value = value;
        new_node->marked = 0;
        new_node->fullyLinked = 0;
        new_node->top_level = topLevel;
        omp_init_lock(&new_node->lock);
        for (int i = 0; i < MAX_LEVEL; i++)
        {
            new_node->next[i] = NULL;
        }

        for (int level = 0; level <= topLevel; level++)
        {
            new_node->next[level] = succs[level];
            preds[level]->next[level] = new_node;
        }

        new_node->fullyLinked = 1; // Linearization point

        for (int i = 0; i < numNodesToLock; i++)
        {
            omp_unset_lock(&nodesToLock[i]->lock);
        }

        return 1;
    }
}

int con(skiplist *list, long key)
{
    skiplist_node *node = list->header;
    for (int i = MAX_LEVEL - 1; i >= 0; i--)
    {
        while (node->next[i] != NULL && node->next[i]->key < key)
        {
            node = node->next[i];
        }
    }

    return node->next[0] != NULL &&
           node->next[0]->key == key &&
           node->next[0]->fullyLinked == 1 &&
           node->next[0]->marked == 0;
}

int rem(skiplist *list, long key)
{
    int isMarked = 0;
    int topLevel = -1;
    skiplist_node *preds[MAX_LEVEL];
    skiplist_node *succs[MAX_LEVEL];

    while (1)
    {
        int lFound = find(list, key, preds, succs);
        if (lFound == -1)
        {
            return 0;
        }

        skiplist_node *victim = succs[lFound];
        if (isMarked == 1 || (victim->fullyLinked == 1 && victim->marked == 0 && victim->top_level == lFound))
        {
            if (isMarked == 0)
            {
                topLevel = victim->top_level;
                omp_set_lock(&victim->lock);
                if (victim->marked == 1)
                {
                    omp_unset_lock(&victim->lock);
                    return 0;
                }
                victim->marked = 1;
                isMarked = 1;
            }

            skiplist_node *nodesToLock[MAX_LEVEL];
            int numNodesToLock = 0;
            nodesToLock[numNodesToLock++] = preds[0];
            for (int level = 1; level <= victim->top_level; level++)
            {
                if (preds[level]->key != preds[level - 1]->key)
                {
                    nodesToLock[numNodesToLock++] = preds[level];
                }
            }
            for (int i = 0; i < numNodesToLock; i++)
            {
                omp_set_lock(&nodesToLock[i]->lock);
            }

            int valid = 1;
            for (int level = 0; level <= topLevel && valid; level++)
            {
                valid = preds[level]->marked == 0 && preds[level]->next[level] == victim;
            }

            if (!valid)
            {
                for (int i = 0; i < numNodesToLock; i++)
                {
                    omp_unset_lock(&nodesToLock[i]->lock);
                }
                omp_unset_lock(&victim->lock);
                continue;
            }

            for (int level = 0; level <= topLevel; level++)
            {
                preds[level]->next[level] = victim->next[level];
            }

            for (int i = 0; i < numNodesToLock; i++)
            {
                omp_unset_lock(&nodesToLock[i]->lock);
            }
            omp_unset_lock(&victim->lock);

            return 1;
        }
        return 0;
    }
}