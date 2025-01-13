import argparse
import os
import ctypes

from src.utils.bench_utils import cBenchResult, Benchmark

def benchmark_all():
    basedir = os.path.dirname(os.path.abspath(__file__))

    implementations = {
        "sequential": "library_seq.so",
        "fine_lock": "library_finelocking.so",
        "lock_free": "library_lockfree.so",
        "global_lock": "library_globallocking.so",
    }

    num_threads_by_impl = {
        "sequential": [1],
        "fine_lock": [1, 2, 4, 8, 10, 20, 40, 64],
        "lock_free": [1, 2, 4, 8, 10, 20, 40, 64],
        "global_lock": [1, 2, 4, 8, 10, 20, 40, 64],
    }

    runtimes = [1]
    mixes = [(10, 10, 80)]
    disjoint_types = [False]
    repetitions = 1
    base_range = (0, 100000)
    selection_strategy = 0
    prefill_count = 0
    seed = 42
    basic_testing = True

    for lib_name, lib_file in implementations.items():
        lib_path = os.path.join(basedir, "build", lib_file)
        if not os.path.exists(lib_path):
            print(f"Warning: library not found: {lib_path}")
            continue

        binary = ctypes.CDLL(lib_path)
        binary.bench.restype = cBenchResult

        for disjoint in disjoint_types:
            for op_mix in mixes:
                bench = Benchmark(
                    bench_function=binary.bench,
                    num_of_threads=num_threads_by_impl[lib_name],
                    base_range=base_range,
                    runtime_in_sec=runtimes,
                    operations_mix=op_mix,
                    disjoint_range=disjoint,
                    selection_strategy=selection_strategy,
                    basic_testing=basic_testing,
                    seed=seed,
                    repetitions_per_point=repetitions,
                    prefill_count=prefill_count,
                    basedir=basedir,
                    name=lib_name,
                )

                bench.run()
                bench.write_avg_data()


if __name__ == "__main__":
    benchmark_all()

