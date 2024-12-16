#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include "skiplist.h"
#include <time.h> // For timing
#include <omp.h>

// Initialize the skip list
void init(node_t *head, node_t *tail, list_t *list) {
    if (!head || !tail || !list) {
        fprintf(stderr, "Error: Invalid input to init function.\n");
        return;
    }

    list->head = head;
    list->tail = tail;
    list->maxLevel = 0;

    // Initialize head and tail nodes
    head->key = LONG_MIN;
    tail->key = LONG_MAX;
    for (int i = 0; i < MAX_LEVEL; i++) {
        head->next[i] = tail; // Head points to tail at all levels
        tail->next[i] = NULL;
    }
}

// Clean up the skip list
void clean(list_t *list) {
    node_t *curr = list->head->next[0];
    while (curr && curr != list->tail) {
        node_t *temp = curr;
        curr = curr->next[0];
        free(temp);
    }

    // Reset the list to a clean state
    for (int i = 0; i < MAX_LEVEL; i++) {
        list->head->next[i] = list->tail;
    }
    list->maxLevel = 0;
}

// Random level generator for skip list nodes
int randomLevel() {
    int level = 0;
    while ((rand() / (double)RAND_MAX) < PROBABILITY && level < MAX_LEVEL - 1) {
        level++;
    }
    return level;
}

// Add a key-value pair to the skip list
int add(long key, void *value, list_t *list) {
    node_t *preds[MAX_LEVEL];
    node_t *succs[MAX_LEVEL];
    pos(key, list, preds, succs);

    // Check if key already exists
    if (succs[0] && succs[0]->key == key) {
        return 0; // Key already exists
    }

    // Create a new node
    int level = randomLevel();
    if (level > list->maxLevel) {
        for (int i = list->maxLevel + 1; i <= level; i++) {
            preds[i] = list->head;
        }
        list->maxLevel = level;
    }

    node_t *newNode = (node_t *)calloc(1, sizeof(node_t) + MAX_LEVEL * sizeof(node_t *));
    newNode->key = key;
    newNode->value = value;

    // Update pointers
    for (int i = 0; i <= level; i++) {
        newNode->next[i] = succs[i];
        preds[i]->next[i] = newNode;
    }
    return 1;
}

// Search for a key in the skip list
int con(long key, void **value, list_t *list) {
    node_t *curr = list->head;
    for (int i = list->maxLevel; i >= 0; i--) {
        while (curr->next[i] && curr->next[i]->key < key) {
            curr = curr->next[i];
        }
    }
    curr = curr->next[0];
    if (curr && curr->key == key) {
        if (value) *value = curr->value;
        return 1; // Key found
    }
    return 0; // Key not found
}

// Remove a key from the skip list
int rem(long key, list_t *list) {
    node_t *preds[MAX_LEVEL];
    node_t *succs[MAX_LEVEL];
    pos(key, list, preds, succs);

    // Check if key exists
    if (!succs[0] || succs[0]->key != key) {
        return 0; // Key not found
    }

    // Remove the node
    node_t *target = succs[0];
    for (int i = 0; i <= list->maxLevel; i++) {
        if (preds[i]->next[i] != target) break;
        preds[i]->next[i] = target->next[i];
    }

    // Update maxLevel
    while (list->maxLevel > 0 && list->head->next[list->maxLevel] == list->tail) {
        list->maxLevel--;
    }

    free(target);
    return 1;
}

void pos(long key, list_t *list, node_t **preds, node_t **succs) {
    node_t *curr = list->head;

    for (int i = list->maxLevel; i >= 0; i--) {
        while (curr->next[i] && curr->next[i]->key < key) {
            curr = curr->next[i];
        }
        preds[i] = curr;
        succs[i] = curr->next[i];
    }
}

cBenchResult bench_add(list_t *list, int key_range, int duration) {
    cBenchResult result = {0};
    double start_time = omp_get_wtime();

    for (int i = 0; i < duration; i++) {
        long key = rand() % key_range;
        add(key, NULL, list);
    }

    double end_time = omp_get_wtime();
    result.time = end_time - start_time;
    result.counters.adds = duration;  // Count the number of add operations

    return result;
}

cBenchResult bench_rem(list_t *list, int key_range, int duration) {
    cBenchResult result = {0};
    double start_time = omp_get_wtime();

    for (int i = 0; i < duration; i++) {
        long key = rand() % key_range;
        rem(key, list);
    }

    double end_time = omp_get_wtime();
    result.time = end_time - start_time;
    result.counters.rems = duration;  // Count the number of remove operations

    return result;
}

cBenchResult bench_con(list_t *list, int key_range, int duration) {
    cBenchResult result = {0};
    double start_time = omp_get_wtime();

    for (int i = 0; i < duration; i++) {
        long key = rand() % key_range;
        con(key, NULL, list);
    }

    double end_time = omp_get_wtime();
    result.time = end_time - start_time;
    result.counters.cons = duration;  // Count the number of contains checks

    return result;
}