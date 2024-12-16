#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "skiplist.h"

void run_tests() {
    printf("Running Skip List Tests...\n");

    list_t list;
    node_t head, tail;
    init(&head, &tail, &list);

    // Test 1: Initialization
    printf("Test 1: Initialization... ");
    assert(list.head == &head);
    assert(list.tail == &tail);
    assert(list.maxLevel == 0);
    for (int i = 0; i < MAX_LEVEL; i++) {
        assert(list.head->next[i] == list.tail);
    }
    printf("Passed!\n");

    // Other tests remain unchanged...
}

void clean(list_t *list) {
    node_t *current = list->head->next[0];
    node_t *next;

    while (current != list->tail) {
        next = current->next[0];
        free(current);
        current = next;
    }

    for (int i = 0; i < MAX_LEVEL; i++) {
        list->head->next[i] = list->tail;
    }
}

void print_skiplist(list_t *list) {
    for (int i = 0; i < MAX_LEVEL; i++) {
        printf("Level %d: ", i);
        node_t *current = list->head->next[i];
        while (current != list->tail) {
            printf("%d -> ", current->key);
            current = current->next[i];
        }
        printf("NULL\n");
    }
}

int main() {
    run_tests();

    // Example tests
    list_t list;
    node_t head, tail;
    init(&head, &tail, &list);

    add(10, NULL, &list);
    add(20, NULL, &list);
    void *value = NULL;
    printf("Search 10: %d\n", con(10, &value, &list));
    rem(10, &list);
    printf("Search 10 after remove: %d\n", con(10, &value, &list));

    printf("Before clean-up:\n");
    print_skiplist(&list);

    clean(&list);
    printf("After clean-up:\n");
    print_skiplist(&list);

    return 0;
}
