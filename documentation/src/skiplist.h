#ifndef SKIPLIST_H
#define SKIPLIST_H

#include <stddef.h>

#define MAX_LEVEL 10 // Adjust based on your implementation

typedef struct node {
    int key;
    void *value;
    struct node *next[MAX_LEVEL];
} node_t;

typedef struct list {
    node_t *head;
    node_t *tail;
    int maxLevel;
} list_t;

// Function declarations
void init(node_t *head, node_t *tail, list_t *list);
int add(int key, void *value, list_t *list);
int rem(int key, list_t *list);
int con(int key, void **value, list_t *list);
void clean(list_t *list);
void print_skiplist(list_t *list);

#endif // SKIPLIST_H
