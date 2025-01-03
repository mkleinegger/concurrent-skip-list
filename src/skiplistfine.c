#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>
#include <time.h>
#include <unistd.h> // For usleep (optional)

// Define maximum level for the skip list
#define MAX_LEVEL 16
// Probability for random level generation
#define P 0.5

// Node structure
typedef struct Node {
    long key;
    void *value;
    struct Node **next;    // Array of next pointers for each level
    volatile int marked;            // 0 = not marked, 1 = marked for deletion
    volatile int fullyLinked;       // 0 = not fully linked, 1 = fully linked
    omp_lock_t lock;       // Lock for this node
} Node;

// SkipList structure
typedef struct skiplist {
    Node *head;
    Node *tail;
    int maxLevel;
} skiplist;

// Function Prototypes
void init(skiplist* list);
void clean(skiplist *list);
int add(skiplist *list, long key, void *value);
int rem(skiplist *list, long key);
int con(skiplist *list, long key);

// Helper Function Prototypes
int find(skiplist *list, long key, Node **preds, Node **succs);

// Function to create a new node
Node* createNode(long key, void *value, int level) {
    Node *node = (Node*) malloc(sizeof(Node));
    if (node == NULL) {
        perror("Failed to allocate memory for new node");
        exit(EXIT_FAILURE);
    }
    node->key = key;
    node->value = value;
    node->next = (Node**) malloc(sizeof(Node*) * (level + 1));
    if (node->next == NULL) {
        perror("Failed to allocate memory for node next pointers");
        free(node);
        exit(EXIT_FAILURE);
    }
    for(int i = 0; i <= level; i++) {
        node->next[i] = NULL;
    }
    node->marked = 0;        // Initialize as not marked
    node->fullyLinked = 0;   // Initialize as not fully linked
    omp_init_lock(&node->lock); // Initialize the node's lock
    return node;
}


// Initialize the skip list
void init(skiplist* list) {
    list->maxLevel = MAX_LEVEL;
    
    // Create head and tail sentinel nodes
    list->head = createNode(INT_MIN, NULL, list->maxLevel);
    list->tail = createNode(INT_MAX, NULL, list->maxLevel);
    
    // Initialize next pointers of head to point to tail
    for(int i = 0; i <= list->maxLevel; i++) {
        list->head->next[i] = list->tail;
    }

}

// Destroy the skip list and free memory
void clean(skiplist *list) {
    if (list == NULL) return;
    Node *node = list->head;
    while(node != NULL) {
        Node *temp = node;
        node = node->next[0];
        omp_destroy_lock(&temp->lock); // Destroy the node's lock
        free(temp->next);
        free(temp);
    }

}

// Thread-safe random level generator using rand_r
int randomLevel(unsigned int *seed) {
    int level = 0;
    while (((double) rand() / RAND_MAX) < P && level < MAX_LEVEL)
        level++;
    return level;
}

// Find function to locate predecessors and successors
int find(skiplist *list, long key, Node **preds, Node **succs) {
    int lFound = -1;
    Node *pred = list->head;
    for(int level = list->maxLevel; level >= 0; level--) {
        Node *curr = pred->next[level];
        while(curr->key < key) {
            pred = curr;
            curr = pred->next[level];
        }
        preds[level] = pred;
        succs[level] = curr;
        if(lFound == -1 && curr->key == key) {
            lFound = level;
        }
    }
    return lFound;
}

//
int add(skiplist *list, long key, void *value) {
    // Initialize thread-local seed for rand_r
    unsigned int seed = (unsigned int)(time(NULL)) ^ omp_get_thread_num();
    
    int topLevel = randomLevel(&seed);
    Node *preds[MAX_LEVEL + 1];
    Node *succs[MAX_LEVEL + 1];
    
    while (1) {
        int lFound = find(list, key, preds, succs);
        if(lFound != -1) {
            Node *nodeFound = succs[lFound];
            //omp_set_lock(&nodeFound->lock);
            if(!nodeFound->marked) { // if marked == 0
                // Wait until the node is fully linked
                while(!nodeFound->fullyLinked) {
                    //omp_unset_lock(&nodeFound->lock);
                    //omp_set_lock(&nodeFound->lock);
                }
                //omp_unset_lock(&nodeFound->lock);
                return 0; // Key already in the list
            }
            //omp_unset_lock(&nodeFound->lock);
            // Node is marked for deletion, retry
            continue;
        }
        
        // Collect all nodes to lock (preds and succs up to topLevel)
        Node *nodesToLock[2*(MAX_LEVEL+1)];
        int numNodesToLock = 0;
        nodesToLock[numNodesToLock++] = preds[0];
        for(int level = 1; level <= topLevel; level++) {
             if(preds[level]->key != preds[level-1]->key) {
                nodesToLock[numNodesToLock++] = preds[level];
            }
        }
        
        // Acquire all necessary locks in order
        for(int i = 0; i < numNodesToLock; i++) {
            omp_set_lock(&nodesToLock[i]->lock);
        }
        
        // Re-validate preds and succs
        int valid = 1;
        for(int level = 0; level <= topLevel; level++) {
            if(preds[level]->marked || succs[level]->marked || preds[level]->next[level] != succs[level]) {
                valid = 0;
                break;
            }
        }
        
        if(!valid) {
            for(int i = 0; i < numNodesToLock; i++) {
                omp_unset_lock(&nodesToLock[i]->lock);
            }
            continue; // Retry
        }
        
        // Create the new node
        Node *newNode = createNode(key, value, topLevel);

        // Insert the new node by updating next pointers
        for(int level = 0; level <= topLevel; level++) {
            newNode->next[level] = succs[level];
            preds[level]->next[level] = newNode;
        }
        newNode->fullyLinked = 1; // Linearization point
        
        // Release all acquired locks
        for(int i = 0; i < numNodesToLock; i++) {
            omp_unset_lock(&nodesToLock[i]->lock);
        }
        
        return 1; // Successfully inserted
    }
}