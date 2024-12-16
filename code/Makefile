NAME = skiplist

CC ?= gcc
RM ?= @rm
MKDIR ?= @mkdir

CFLAGS := -O3 -Wall -Wextra -fopenmp -g -DCOUNTERS


SRC_DIR = src
BUILD_DIR = build
DATA_DIR = data
INCLUDES = $(SRC_DIR)

# Object files for the skiplist implementation and benchmark
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

# # Build shared library
# $(NAME).so: $(OBJECTS)
# 	@echo "Linking $(NAME) as shared library..."
# 	$(CC) $(CFLAGS) -fPIC -shared -o $(BUILD_DIR)/$(NAME).so $^

$(NAME).so: $(OBJECTS)
	@echo "Linking $(NAME) as shared library..."
	$(CC) $(CFLAGS) -fPIC -shared -o $(BUILD_DIR)/$(NAME).so $^
	@cp $(BUILD_DIR)/$(NAME).so .  # Copy to the current directory


# Build test binary
test: $(BUILD_DIR)/test_skiplist

$(BUILD_DIR)/test_skiplist: $(SRC_DIR)/test_skiplist.c $(OBJECTS)
	@echo "Compiling test_skiplist..."
	$(CC) $(CFLAGS) -I$(INCLUDES) -o $@ $^

run-test: test
	@echo "Running test_skiplist..."
	$(BUILD_DIR)/test_skiplist

# # Benchmark binary
# benchmark: $(BUILD_DIR)/benchmark.o $(OBJECTS)
# 	@echo "Compiling benchmark..."
# 	$(CC) $(CFLAGS) -I$(INCLUDES) -o $(BUILD_DIR)/benchmark $^

# $(BUILD_DIR)/benchmark.o: $(SRC_DIR)/benchmark.c | $(BUILD_DIR)
# 	@echo "Compiling $<"
# 	$(CC) $(CFLAGS) -fPIC -I$(INCLUDES) -c -o $@ $<

# run-benchmark: benchmark
# 	@echo "Running benchmark..."
# 	$(BUILD_DIR)/benchmark 5 1000 10000 50 30 20 42

small-bench: $(BUILD_DIR) $(NAME).so $(DATA_DIR)
	@echo "Running small-bench ..."
	@python benchmark.py


skipbench: $(BUILD_DIR)/skipbench.o $(OBJECTS)
	@echo "Compiling skipbench..."
	$(CC) $(CFLAGS) -I$(INCLUDES) -o $(BUILD_DIR)/skipbench $^

$(BUILD_DIR)/skipbench.o: $(SRC_DIR)/skipbench.c | $(BUILD_DIR)
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -fPIC -I$(INCLUDES) -c -o $@ $<

run-skipbench: skipbench
	@echo "Running skipbench..."
	$(BUILD_DIR)/skipbench 4 3 5 1000 50 30 20 42 100000

# Clean build artifacts
clean:
	@echo "Cleaning build directory: $(BUILD_DIR) and binaries: $(NAME).so"
	$(RM) -Rf $(BUILD_DIR)
	$(RM) -f $(BUILD_DIR)/$(NAME).so

