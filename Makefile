NAME = library

CC = gcc
RM ?= rm -rf
MKDIR ?= mkdir -p

CFLAGS := -O3 -Wall -Wextra -fopenmp -fPIC
SRC_DIR = src
BUILD_DIR = build
DATA_DIR = data
INCLUDES = inc

# Skiplist variants
SKIPLISTS = seq lockfree finelocking globallocking
LIBRARIES = $(foreach variant,$(SKIPLISTS),$(BUILD_DIR)/$(NAME)_$(variant).so)

# Default target
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
	$(CC) $(CFLAGS) -shared -o $@ $^

$(BUILD_DIR)/$(NAME)_finelocking.so: $(SRC_DIR)/skiplist_finelocking.c $(SRC_DIR)/library.c | $(BUILD_DIR)
	@echo "Building library: $@"
	$(CC) $(CFLAGS) -shared -o $@ $^

$(BUILD_DIR)/$(NAME)_globallocking.so: $(SRC_DIR)/skiplist_globallocking.c $(SRC_DIR)/library.c | $(BUILD_DIR)
	@echo "Building library: $@"
	$(CC) $(CFLAGS) -shared -o $@ $^

# Run small benchmark
small-bench: all
	@echo "Running small-bench with all libraries ..."
	python benchmark.py

bench-global: all
	@echo "This could run a sophisticated, FULL benchmark"
	@echo "Plotting bench results for global lock - 1 repetition..."
	python benchmark_globallock.py 

bench-fine: all
	@echo "This could run a sophisticated, FULL benchmark"
	@echo "Plotting bench results for fine lock - 1 repetition..."
	python benchmark_finelock.py 

bench-lockfree: all
	@echo "This could run a sophisticated, FULL benchmark"
	@echo "Plotting bench results for lock free - 1 repetition..."
	python benchmark_lockfree.py 

small-plot: 
	@echo "Plotting small-bench results ..."
	bash -c 'cd plots && pdflatex "\newcommand{\DATAPATH}{../data/$$(ls ../data/ | sort -r | head -n 1)}\input{avg_plot.tex}"'
	@echo "============================================"
	@echo "Created plots/avgplot.pdf"

report: small-plot
	@echo "Compiling report ..."
	bash -c 'cd report && pdflatex report.tex'
	@echo "============================================"
	@echo "Done"

zip:
	@zip project.zip benchmark.py benchmark_globallock.py benchmark_finelock.py benchmark_lockfree.py benchmark_seq.py Makefile README src/* plots/avg_plot.tex report/report.tex run_nebula.sh

# Clean up build artifacts
clean:
	@echo "Cleaning build directory: $(BUILD_DIR), data directory: $(DATA_DIR), and libraries."
	$(RM) -Rf $(BUILD_DIR)
	$(RM) -f $(NAME) $(NAME).so

.PHONY: all create_dirs clean small-bench
