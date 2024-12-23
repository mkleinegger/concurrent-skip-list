#include <stdio.h>
#include <stdlib.h>
#include "skiplist.h"

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
    new_node->key = key;
    new_node->value = value;

    for (int i = 0; i <= level; i++)
    {
        new_node->next[i] = update[i]->next[i];
        update[i]->next[i] = new_node;
    }

    INC(list->adds);

    return 1; // Return 1 to indicate success
}

int con(skiplist *list, long key)
{
    int success = 0;
    skiplist_node *node = list->header;
    for (int i = list->max_level; i >= 0; i--)
    {
        while (node->next[i] != NULL && node->next[i]->key < key)
        {
            node = node->next[i];
        }
    }

    INC(list->cons);

    if (node->next[0] != NULL && node->next[0]->key == key)
    {
        success = 1;
    }
    return success;
}

int rem(skiplist *list, long key)
{
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

        INC(list->rems);
        free(node);

        while (list->max_level > 0 && list->header->next[list->max_level] == NULL)
        {
            list->max_level--;
        }
        return 1;
    }
    return 0;
}

void init(skiplist *list)
{
    list->header = malloc(sizeof(skiplist_node));
    list->header->key = -1;
    list->header->value = NULL;

    list->max_level = 0;
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
}