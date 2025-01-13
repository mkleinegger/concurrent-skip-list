# Author: Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
# Created: 2025-01-13

NAME = library

CC = gcc
RM ?= rm -rf
MKDIR ?= mkdir -p

CFLAGS := -O3 -Wall -Wextra -fopenmp -fPIC
SRC_DIR = src
BUILD_DIR = build
DATA_DIR = data
INCLUDES = inc

SKIPLISTS = seq lockfree finelocking globallocking
LIBRARIES = $(foreach variant,$(SKIPLISTS),$(BUILD_DIR)/$(NAME)_$(variant).so)

all: create_dirs $(LIBRARIES)
	@echo "All shared libraries built."

# Create directories as a separate target to avoid conflicts
create_dirs:
	@echo "Ensuring directories exist: $(BUILD_DIR) and $(DATA_DIR)"
	$(MKDIR) $(BUILD_DIR)
	$(MKDIR) $(DATA_DIR)

# Build shared libraries for each skiplist variant
$(BUILD_DIR)/$(NAME)_seq.so: $(SRC_DIR)/skiplist_seq.c $(SRC_DIR)/library.c | $(BUILD_DIR)
	@echo "Building library: $@"
	$(CC) $(CFLAGS) -shared -o $@ $^

$(BUILD_DIR)/$(NAME)_lockfree.so: $(SRC_DIR)/skiplist_lockfree.c $(SRC_DIR)/library.c | $(BUILD_DIR)
	@echo "Building library: $@"
	$(CC) $(CFLAGS) -shared -o $@ $^ -latomic

$(BUILD_DIR)/$(NAME)_finelocking.so: $(SRC_DIR)/skiplist_finelocking.c $(SRC_DIR)/library.c | $(BUILD_DIR)
	@echo "Building library: $@"
	$(CC) $(CFLAGS) -shared -o $@ $^

$(BUILD_DIR)/$(NAME)_globallocking.so: $(SRC_DIR)/skiplist_globallocking.c $(SRC_DIR)/library.c | $(BUILD_DIR)
	@echo "Building library: $@"
	$(CC) $(CFLAGS) -shared -o $@ $^

# Run small benchmark
small-bench: all
	@echo "Running small-bench with all libraries ..."
	python benchmark_small.py

bench-global: all
	@echo "This could run a sophisticated, FULL benchmark"
	python ./benchmark.py --library library_globallocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --disjoint-range --selection-strategy 0 --basic-testing --seed 42 --basedir . --name global_lock
	python ./benchmark.py --library library_globallocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name global_lock
	python ./benchmark.py --library library_globallocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --disjoint-range --selection-strategy 0 --basic-testing --seed 42 --basedir . --name global_lock
	python ./benchmark.py --library library_globallocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name global_lock

bench-fine: all
	@echo "This could run a sophisticated, FULL benchmark"
	@echo "Plotting bench results for fine lock - 1 repetition..."
	python ./benchmark.py --library library_finelocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --disjoint-range --selection-strategy 0 --basic-testing --seed 42 --basedir . --name fine_lock
	python ./benchmark.py --library library_finelocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name fine_lock
	python ./benchmark.py --library library_finelocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --disjoint-range --selection-strategy 0 --basic-testing --seed 42 --basedir . --name fine_lock
	python ./benchmark.py --library library_finelocking.so --repetitions-per-point 3 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name fine_lock


bench-lockfree: all
	@echo "This could run a sophisticated, FULL benchmark"
	python ./benchmark.py --library library_lockfree.so --repetitions-per-point 1 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --disjoint-range --selection-strategy 0 --basic-testing --seed 42 --basedir . --name lock_free
	python ./benchmark.py --library library_lockfree.so --repetitions-per-point 1 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name lock_free
	python ./benchmark.py --library library_lockfree.so --repetitions-per-point 1 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --disjoint-range --selection-strategy 0 --basic-testing --seed 42 --basedir . --name lock_free
	python ./benchmark.py --library library_lockfree.so --repetitions-per-point 1 --num-of-threads 1 2 4 8 10 20 40 64 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name lock_free

bench-seq: all
	python ./benchmark.py --library library_seq.so --repetitions-per-point 3 --num-of-threads 1 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 40 40 20 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name sequential
	python ./benchmark.py --library library_seq.so --repetitions-per-point 3 --num-of-threads 1 --base-range 0 100000 --runtime-in-sec 1 5 --operations-mix 10 10 80 --selection-strategy 0 --basic-testing --seed 42 --basedir . --name sequential

bench-custom: all
	python ./benchmark.py --library library_finelocking.so \
        --repetitions-per-point 1 \
        --num-of-threads 1 2 4 8 10 20 40 64 \
        --base-range 0 100000 \
        --runtime-in-sec 1 5 \
        --operations-mix 40 40 20 \
        --selection-strategy 0 \
        --basic-testing \
        --seed 42 \
        --basedir . \
        --name custom_results

small-plot: 
	@echo "Plotting small-bench results ..."
	python benchmark_small_plots.py
	@echo "============================================"
	@echo "Created plots/avgplot.pdf"

report: small-plot
	@echo "Compiling report ..."
	bash -c 'cd report && pdflatex report.tex'
	@echo "============================================"
	@echo "Done"

zip:
	@zip project.zip benchmark.py benchmark_small.py benchmark_small_plots.py Makefile README src/* src/utils/* notebooks/* report/report.tex run_nebula.sh run_setup_python.sh requirements.txt

# Clean up build artifacts
clean:
	@echo "Cleaning build directory: $(BUILD_DIR), data directory: $(DATA_DIR), and libraries."
	$(RM) -Rf $(BUILD_DIR)
	$(RM) -Rf $(DATA_DIR)
	$(RM) -f $(NAME) $(NAME).so

.PHONY: all create_dirs clean small-bench
