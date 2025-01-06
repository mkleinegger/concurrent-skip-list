#include "skiplist.h"

void init(skiplist *list)
{
    list->header = malloc(sizeof(skiplist_node));
    list->header->key = INT_MIN;
    list->header->value = NULL;
    list->header->top_level = MAX_LEVEL - 1;

    for (int i = 0; i < MAX_LEVEL; i++)
    {
        list->header->next[i] = NULL;
    }
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

    for (int i = MAX_LEVEL - 1; i >= 0; i--)
    {
        while (node->next[i] != NULL && node->next[i]->key < key)
        {
            node = node->next[i];
        }
        update[i] = node;
    }

    if (node->next[0] != NULL && node->next[0]->key == key)
    {
        return 0;
    }

    int topLevel = randomLevel(P, MAX_LEVEL);
    skiplist_node *new_node = malloc(sizeof(skiplist_node));
    new_node->key = key;
    new_node->value = value;
    new_node->top_level = topLevel;

    for (int i = 0; i <= topLevel; i++)
    {
        new_node->next[i] = update[i]->next[i];
        update[i]->next[i] = new_node;
    }

    return 1;
}

int rem(skiplist *list, long key)
{
    skiplist_node *update[MAX_LEVEL];
    skiplist_node *node = list->header;

    for (int i = MAX_LEVEL - 1; i >= 0; i--)
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
        for (int i = 0; i <= node->top_level; i++)
        {
            if (update[i]->next[i] != node)
            {
                break;
            }
            update[i]->next[i] = node->next[i];
        }

        free(node);
        return 1;
    }
    return 0;
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

    return node->next[0] != NULL && node->next[0]->key == key;
}