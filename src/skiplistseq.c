#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include "skiplist.h"

int randomLevel(double p, int max_level) {
    int level = 0;

    while ((rand() / (double)RAND_MAX) < p && level < max_level - 1) {
        level++;
    }

    return level;
}

int add(skiplist *list, long key, void *value) {
    skiplist_node *update[MAX_LEVEL];
    skiplist_node *node = list->header;

    for (int i = list->max_level; i >= 0; i--) {
        while (node->next[i] != NULL && node->next[i]->key < key) {
            node = node->next[i];
        }
        update[i] = node;
    }

    int level = randomLevel(P, MAX_LEVEL);
    if (level > list->max_level) {
        for (int i = list->max_level + 1; i <= level; i++) {
            update[i] = list->header;
        }
        list->max_level = level;
    }

    INC(list->adds);

    skiplist_node *new_node = malloc(sizeof(skiplist_node));
    new_node->key = key;
    new_node->value = value;

    for (int i = 0; i <= level; i++) {
        new_node->next[i] = update[i]->next[i];
        update[i]->next[i] = new_node;
    }

    return 1; // Return 1 to indicate success
}

int con(skiplist *list, long key) {
    skiplist_node *node = list->header;
    for (int i = list->max_level; i >= 0; i--) {
        while (node->next[i] != NULL && node->next[i]->key < key) {
            node = node->next[i];
        }
    }

    INC(list->cons);

    if (node->next[0] != NULL && node->next[0]->key == key) {
        return 1;
    }
    return 0;
}

int rem(skiplist *list, long key) {
    skiplist_node *update[MAX_LEVEL];
    skiplist_node *node = list->header;

    for (int i = list->max_level; i >= 0; i--) {
        while (node->next[i] != NULL && node->next[i]->key < key) {
            node = node->next[i];
        }
        update[i] = node;
    }

    node = node->next[0];
    if (node != NULL && node->key == key) {
        for (int i = 0; i <= list->max_level; i++) {
            if (update[i]->next[i] != node) {
                break;
            }
            update[i]->next[i] = node->next[i];
        }

        INC(list->rems);
        free(node);

        while (list->max_level > 0 && list->header->next[list->max_level] == NULL) {
            list->max_level--;
        }

        return 1;
    }
}

void init(skiplist *list) {
    list->header = malloc(sizeof(skiplist_node));
    list->header->key = -1;
    list->header->value = NULL;

    list->max_level = 0;
}

void clean(skiplist *list) {
    skiplist_node *node = list->header->next[0];
    while (node != NULL) {
        skiplist_node *next = node->next[0];
        free(node);
        node = next;
    }

    free(list->header);
}

int main() {
    skiplist *list = malloc(sizeof(skiplist));
    init(list);

    const int num_keys = 100000;

    srand((unsigned int)time(NULL));

    // Insert keys
    for (int i = 0; i < num_keys; i++) {
        add(list, i, NULL);
    }

    // Verify correctness of inserted keys
    for (int i = 0; i < num_keys; i++) {
        if (con(list, i) == 0) {
            printf("Key %d not found in skiplist!\n", i);
            return 1;
        }
    }

    printf("All keys verified successfully!\n");

    for (int i = 0; i < num_keys; i+=2) {
        rem(list, i);
    }

        // Verify correctness of inserted keys
    for (int i = 0; i < num_keys; i++) {
        if (i % 2 == 0 && con(list, i) == 1) {
            printf("Key %d should have been removed from skiplist!\n", i);
            return 1;
        } else if (i % 2 != 0 && con(list, i) == 0) {
            printf("Key %d not found in skiplist!\n", i);
            return 1;
        }
    }

    // Benchmark contains operation
    printf("Benchmarking contains operation...\n");
    clock_t start_time = clock();
    for (int i = 0; i < num_keys * 10; i++) {
        unsigned long key = rand() % (num_keys * 10);
        con(list, key);
    }
    clock_t end_time = clock();

    double elapsed_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
    printf("Contains benchmark completed in %.6f seconds.\n", elapsed_time);

#ifdef COUNTERS
    printf("Adds: %llu, Removes: %llu, Contains: %llu\n", list->adds, list->rems, list->cons);
#endif
    clean(list);

    return 0;
}
