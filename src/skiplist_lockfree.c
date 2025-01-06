#include "skiplist_lockfree.h"
#include "skiplist.h"

void init(skiplist *list)
{
    list->header = (skiplist_node *)malloc(sizeof(skiplist_node));
    list->header->key = INT_MIN;
    list->header->value = NULL;
    list->header->top_level = MAX_LEVEL - 1;
    for (int i = 0; i < MAX_LEVEL; i++)
    {
        STORE(&list->header->next[i], NULL);
    }

    srand(42);
}

void clean(skiplist *list)
{
    skiplist_node *curr = getpointer(LOAD(&list->header->next[0]));
    while (curr)
    {
        skiplist_node *next = getpointer(LOAD(&curr->next[0]));
        free(curr);
        curr = next;
    }
    free(list->header);
    list->header = NULL;
}

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
    skiplist_node *pred = NULL, *curr = NULL, *succ = NULL;
retry:
{
    pred = list->header;
    for (int level = MAX_LEVEL - 1; level >= 0; level--)
    {
        curr = getpointer(LOAD(&pred->next[level]));
        while (1)
        {
            if (!curr)
                break;
            succ = getpointer(LOAD(&curr->next[level]));

            while (ismarked(LOAD(&curr->next[level])))
            {
                if (!CAS(&pred->next[level], &curr, succ))
                {
                    goto retry;
                }
                curr = getpointer(LOAD(&pred->next[level]));
                if (!curr)
                    break;
                succ = getpointer(LOAD(&curr->next[level]));
            }

            if (curr != NULL && curr->key < key)
            {
                pred = curr;
                curr = succ;
            }
            else
                break;
        }
        preds[level] = pred;
        succs[level] = curr;
    }
    return (curr && curr->key == key);
}
}

int con(skiplist *list, long key)
{
    skiplist_node *pred = list->header, *curr = NULL, *succ = NULL;
    for (int level = MAX_LEVEL - 1; level >= 0; level--)
    {
        curr = getpointer(LOAD(&pred->next[level]));
        while (1)
        {
            if (!curr)
                break;
            succ = getpointer(LOAD(&curr->next[level]));

            while (ismarked(LOAD(&curr->next[level])))
            {
                curr = getpointer(LOAD(&pred->next[level]));
                if (!curr)
                    break;
                succ = getpointer(LOAD(&curr->next[level]));
            }

            if (curr && curr->key < key)
            {
                pred = curr;
                curr = succ;
            }
            else
                break;
        }
    }
    return (curr && curr->key == key);
}

int add(skiplist *list, long key, void *value)
{
    int topLevel = randomLevel(P, MAX_LEVEL - 1);
    skiplist_node *preds[MAX_LEVEL], *succs[MAX_LEVEL];

    while (1)
    {
        int found = find(list, key, preds, succs);
        if (found)
            return 0;

        skiplist_node *newNode = (skiplist_node *)malloc(sizeof(skiplist_node));
        if (!newNode)
            return 0;
        newNode->key = key;
        newNode->value = value;
        newNode->top_level = topLevel;

        for (int level = 0; level <= topLevel; level++)
        {
            skiplist_node *succ = succs[level];
            STORE(&newNode->next[level], succ);
        }

        if (!CAS(&preds[0]->next[0], &succs[0], newNode))
        {
            free(newNode);
            continue;
        }

        for (int level = 1; level <= topLevel; level++)
        {
            while (1)
            {
                if (CAS(&preds[level]->next[level], &succs[level], newNode))
                {
                    break;
                }
                find(list, key, preds, succs);
            }
        }

        return 1;
    }
}

int rem(skiplist *list, long key)
{
    skiplist_node *preds[MAX_LEVEL], *succs[MAX_LEVEL];
    skiplist_node *nodeToRemove = NULL;
    int bottomLevel = 0;

    while (1)
    {
        int found = find(list, key, preds, succs);
        if (!found)
            return 0;
        nodeToRemove = getpointer(LOAD(&succs[0]));

        for (int level = nodeToRemove->top_level; level >= 1; level--)
        {
            skiplist_node *succ = getpointer(LOAD(&nodeToRemove->next[level]));
            while (!ismarked(LOAD(&nodeToRemove->next[level])))
            {
                CAS(&nodeToRemove->next[level], &succ, setmark(LOAD(&nodeToRemove->next[level])));
                succ = getpointer(LOAD(&nodeToRemove->next[level]));
            }
        }

        skiplist_node *bottomNext = getpointer(LOAD(&nodeToRemove->next[bottomLevel]));
        while (1)
        {
            int success = CAS(&nodeToRemove->next[bottomLevel], &bottomNext, setmark(bottomNext));
            bottomNext = getpointer(LOAD(&nodeToRemove->next[bottomLevel]));

            if (success)
            {
                find(list, key, preds, succs);
                return 1;
            }
            else if (ismarked(bottomNext))
            {
                return 0;
            }
        }
    }
}
