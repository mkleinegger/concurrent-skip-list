#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "skiplist.h"

// Function to run all tests
void run_tests() {
    printf("Running Skip List Tests...\n");

    // Test 1: Initialization
    printf("Test 1: Initialization... ");
    list_t list;
    node_t head, tail;
    init(&head, &tail, &list);
    assert(list.head == &head);
    assert(list.tail == &tail);
    assert(list.maxLevel == 0);
    for (int i = 0; i < MAX_LEVEL; i++) {
        assert(list.head->next[i] == list.tail);
    }
    printf("Passed!\n");

    // Test 2: Add elements
    printf("Test 2: Add Elements... ");
    assert(add(5, NULL, &list) == 1);
    assert(add(10, NULL, &list) == 1);
    assert(add(5, NULL, &list) == 0);
    printf("Passed!\n");

    // Test 3: Search elements
    printf("Test 3: Search Elements... ");
    void *value = NULL;
    assert(con(5, &value, &list) == 1);
    assert(con(10, &value, &list) == 1);
    assert(con(15, &value, &list) == 0);
    printf("Passed!\n");

    // Test 4: Remove elements
    printf("Test 4: Remove Elements... ");
    assert(rem(5, &list) == 1);
    assert(rem(5, &list) == 0);
    assert(rem(15, &list) == 0);
    printf("Passed!\n");

    // Test 5: Clean-up
    printf("Test 5: Clean-up... ");
    clean(&list);
    for (int i = 0; i < MAX_LEVEL; i++) {
        assert(list.head->next[i] == list.tail);
    }
    printf("Passed!\n");

    printf("Test 6: Verify Skip List Levels... ");
    assert(add(10, NULL, &list) == 1);
    assert(add(20, NULL, &list) == 1);
    assert(add(30, NULL, &list) == 1);

    // Check that head's next pointers at level 0 point to the first element
    assert(list.head->next[0] != NULL);
    assert(list.head->next[0]->key == 10);

        // Ensure skip list levels are used (basic validation)
    for (int i = 1; i < MAX_LEVEL; i++) {
        if (list.head->next[i]) {
        printf("Level %d initialized.\n", i);
    }
}
printf("Passed!\n");
}

int main() {
    // Run unit tests
    run_tests();

    // Basic functionality test
    printf("\nTesting Basic Skip List Operations...\n");
    list_t list;
    node_t head, tail;
    init(&head, &tail, &list);

    // Add elements
    add(10, NULL, &list);
    add(20, NULL, &list);

    // Search for elements
    void *value = NULL; // To store the result if found
    printf("Search 10: %d\n", con(10, &value, &list)); // Should print 1 (found)

    // Remove elements
    rem(10, &list);
    printf("Search 10 after remove: %d\n", con(10, &value, &list)); // Should print 0 (not found)

    // Clean up
    clean(&list);

    return EXIT_SUCCESS;
}

