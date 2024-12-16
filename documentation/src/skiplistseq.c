#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>
#include "skiplist.h"

#define COUNTERS

// Constructor for the skip list
void init(node_t *head, node_t *tail, list_t *list) {
    list->head = head;
    list->tail = tail;
    list->maxLevel = 0; // Maximum level starts at 0

    list->head->key = LONG_MIN; 
    list->tail->key = LONG_MAX;

    for (int i = 0; i < MAX_LEVEL; i++) { // Initialize all levels to point to the tail
        list->head->next[i] = list->tail;
    }

#ifdef COUNTERS
    list->adds = 0;
    list->rems = 0;
    list->cons = 0;
#endif
}

// Destructor for the skip list
void clean(list_t *list) {
    node_t *curr = list->head->next[0];
    while (curr != list->tail) {
        node_t *temp = curr;
        curr = curr->next[0];
        free(temp);
    }

    for (int i = 0; i < MAX_LEVEL; i++) {
        list->head->next[i] = list->tail;
    }
}

// Random level generator
int randomLevel() {
    int level = 0;
    while ((rand() / (double)RAND_MAX) < PROBABILITY && level < MAX_LEVEL - 1) {
        level++;
    }
    return level;
}

// Position of a key in the skip list
void pos(long key, list_t *list, node_t *preds[], node_t *succs[]) {
    node_t *curr = list->head;
    for (int level = list->maxLevel; level >= 0; level--) {
        while (curr->next[level] && curr->next[level]->key < key) {
            curr = curr->next[level];
        }
        preds[level] = curr;
        succs[level] = curr->next[level];
    }
}

// Add a key to the skip list
int add(long key, void *value, list_t *list) {
    node_t *preds[MAX_LEVEL];
    node_t *succs[MAX_LEVEL];
    pos(key, list, preds, succs);

    if (succs[0] && succs[0]->key == key) {
        return 0; // Key already exists
    }

    int level = randomLevel();
    if (level > list->maxLevel) {
        for (int i = list->maxLevel + 1; i <= level; i++) {
            preds[i] = list->head;
        }
        list->maxLevel = level;
    }

    node_t *newNode = (node_t *)calloc(1, sizeof(node_t));
    newNode->key = key;
    newNode->value = value;

    for (int i = 0; i <= level; i++) {
        newNode->next[i] = succs[i];
        preds[i]->next[i] = newNode;
    }

#ifdef COUNTERS
    list->adds++;
#endif

    return 1; // Successfully added
}

// Remove a key from the skip list
int rem(long key, list_t *list) {
    node_t *preds[MAX_LEVEL];
    node_t *succs[MAX_LEVEL];
    pos(key, list, preds, succs);

    if (!succs[0] || succs[0]->key != key) {
        return 0; // Key not found
    }

    node_t *nodeToRemove = succs[0];
    for (int i = 0; i <= list->maxLevel; i++) {
        if (preds[i]->next[i] == nodeToRemove) {
            preds[i]->next[i] = nodeToRemove->next[i];
        }
    }

    while (list->maxLevel > 0 && list->head->next[list->maxLevel] == list->tail) {
        list->maxLevel--;
    }

    free(nodeToRemove);

#ifdef COUNTERS
    list->rems++;
#endif

    return 1; // Successfully removed
}

// Check if a key is in the skip list
int con(long key, void **value, list_t *list) {
    node_t *curr = list->head;
    for (int level = list->maxLevel; level >= 0; level--) {
        while (curr->next[level] && curr->next[level]->key < key) {
            curr = curr->next[level];
        }
    }

    curr = curr->next[0];
    if (curr && curr->key == key) {
        if (value) {
            *value = curr->value;
        }

#ifdef COUNTERS
        list->cons++;
#endif

        return 1; // Key found
    }

    return 0; // Key not found
}
