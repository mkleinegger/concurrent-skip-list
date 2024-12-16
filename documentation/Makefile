NAME = skiplist

CC ?= gcc
RM ?= rm -f
MKDIR ?= mkdir -p

CFLAGS := -O3 -Wall -Wextra -fopenmp -g 

SRC_DIR = src
BUILD_DIR = build
DATA_DIR = data
INCLUDES = $(SRC_DIR)

# Object files for the skiplist implementation
OBJECTS = $(BUILD_DIR)/skiplistseq.o

# Default target
all: $(BUILD_DIR) $(NAME).so
	@echo "Built $(NAME)"

# Build directory creation
$(BUILD_DIR):
	@echo "Creating build directory: $(BUILD_DIR)"
	$(MKDIR) $(BUILD_DIR)

# Data directory creation
$(DATA_DIR):
	@echo "Creating data directory: $(DATA_DIR)"
	$(MKDIR) $(DATA_DIR)

# Compile source files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -fPIC -I$(INCLUDES) -c -o $@ $<

# Compile skipbench source file
$(BUILD_DIR)/skipbench.o: $(SRC_DIR)/skipbench.c | $(BUILD_DIR)
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -fPIC -I$(INCLUDES) -c -o $@ $<

# Build shared library
$(NAME).so: $(OBJECTS)
	@echo "Linking $(NAME) as shared library..."
	$(CC) $(CFLAGS) -fPIC -shared -o $(BUILD_DIR)/$(NAME).so $^

# Build test binary
test: $(BUILD_DIR)/test_skiplist

$(BUILD_DIR)/test_skiplist: $(SRC_DIR)/test_skiplist.c $(OBJECTS)
	@echo "Compiling test_skiplist..."
	$(CC) $(CFLAGS) -I$(INCLUDES) -o $@ $^

run-test: test
	@echo "Running test_skiplist..."
	$(BUILD_DIR)/test_skiplist

# Benchmark binary
benchmark: $(BUILD_DIR)/skipbench.o $(OBJECTS)
	@echo "Compiling benchmark..."
	$(CC) $(CFLAGS) -I$(INCLUDES) -o $(BUILD_DIR)/benchmark $^

run-benchmark: benchmark
	@echo "Running benchmark..."
	OMP_NUM_THREADS=1 $(BUILD_DIR)/benchmark 1 5 1 100 50 30 20 42 1000

# Run specific benchmarks
run-specific-benchmarks: benchmark
	@echo "Running specific benchmarks..."
	./$(BUILD_DIR)/benchmark > benchmark_output.txt

# Run Python-based small benchmark
small-bench: $(BUILD_DIR) $(NAME).so $(DATA_DIR)
	@echo "Running small-bench..."
	python3 benchmark.py

# Plotting results
small-plot: $(DATA_DIR)
	@echo "Plotting small-bench results..."
	bash -c 'cd plots && pdflatex "\newcommand{\DATAPATH}{../data/$$(ls ../data/ | sort -r | head -n 1)}\input{avg_plot.tex}"'
	@echo "============================================"
	@echo "Created plots/avgplot.pdf"

# Generate report
report: small-plot
	@echo "Compiling report..."
	bash -c 'cd report && pdflatex report.tex'
	@echo "============================================"
	@echo "Done"

# Package the project
zip:
	@zip project.zip benchmark.py Makefile README src/* plots/avg_plot.tex report/report.tex run_nebula.sh

# Clean build artifacts
clean:
	@echo "Cleaning build directory: $(BUILD_DIR) and binaries: $(NAME).so"
	$(RM) -Rf $(BUILD_DIR)
	$(RM) -f $(BUILD_DIR)/$(NAME).so

.PHONY: all clean test run-test benchmark run-benchmark run-specific-benchmarks small-bench small-plot report zip
