/**
 * @file skiplist_finelocking.h
 * @author Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
 * @date 2025-01-13
 *
 * @brief This file imports the necessary libraries for the skiplist using a
 *  lazy fine-grained locking approach.
 */

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>
#include <time.h>

#define FINE_LOCKING