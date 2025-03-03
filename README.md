# Concurrent Skiplist Project

## Overview

This project implements and benchmarks different skiplist variants for concurrent multiprocessor systems. The results of the benchmarks are visualized through plots and compiled into a report.

## Directory Structure

```plaintext
.
├── Makefile               # Automates tasks like compiling, running benchmarks, and generating plots
├── README.md              # Documentation for the project
├── benchmark.py           # Main benchmarking script
├── benchmark_small.py     # Benchmark script for smaller test cases
├── benchmark_small_plots.py # Generates plots for small benchmarks
├── data/*                 # Contains benchmark results in organized directories
├── notebooks/             # Jupyter notebooks for visualizations
│   └── plots.ipynb        # Interactive analysis and plot generation
├── plots/*                # Generated plots from the benchmark scripts
├── report/                # Contains the LaTeX source for the generated report
│   └── report.tex         # Main LaTeX file
├── requirements.txt       # Python dependencies for the project
├── run_nebula.sh          # Script to run benchmarks on Nebula
├── run_setup_python.sh    # Script to set up a python environment
└── src/*                  # Source code for the skiplist and utilities
```

## How to Run the Project

### 1. Run Benchmarks

To generate benchmark data, use the provided scripts included in the Makefile:

    make bench-seq
    make bench-global
    make bench-fine
    make bench-lockfree

Using those commands in combination with slurm on nebula should produce all results

### 2. Generate Report

If you want to generate a small sample using our small benchmark, you need to do the following:

1. Set $USERNAME in `run_nebula.sh` to your username on the nebula system
3. Run `make zip`
2. Run `bash run_nebula.sh project.zip small-bench`
3. Run `make small-plot`
4. Run `make report`

This should allow to generate the necessary report. If your python environment does not have all necessary requierements, we either provide those within `./requirements.txt` to install into your environment or create and use a new environment with `run_setup_python.sh`. However for later approach you need to activate it first!

### 3. Generate Plots
To generate all Plots possibly found in the Report, simply use this created environment as a Jupyter kernel to run the notebook `./notebook/plots.ipynb`, which generates all plots.

## Additional Information
To reproduce the graphs we inkluded the gathered data from our runs under the `./data`, such that it can be looked at and used for reproduction purposes.