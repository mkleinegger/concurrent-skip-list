#include <stdio.h>
#include "skiplist.h"

int main() {
    node_t head, tail;
    list_t list;

    // Initialize skip list
    init(&head, &tail, &list);

    // Test adding keys
    if (add(10, NULL, &list)) {
        printf("Added 10 successfully.\n");
    } else {
        printf("Failed to add 10.\n");
    }

    if (add(20, NULL, &list)) {
        printf("Added 20 successfully.\n");
    } else {
        printf("Failed to add 20.\n");
    }

    clean(&list);
    return 0;
}
