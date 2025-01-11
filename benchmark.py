import os
os.environ["OMP_STACKSIZE"] = "64k"
import ctypes
import datetime
import csv
import time
import concurrent.futures

class cBenchResult(ctypes.Structure):
    _fields_ = [
        ("time", ctypes.c_float),
        ("total_operations", ctypes.c_longlong),
        ("total_inserts", ctypes.c_longlong),
        ("successful_inserts", ctypes.c_longlong),
        ("total_deletes", ctypes.c_longlong),
        ("successful_deletes", ctypes.c_longlong),
        ("total_contains", ctypes.c_longlong),
        ("successful_contains", ctypes.c_longlong),
        ("operations_per_thread", ctypes.c_longlong * 64),
    ]


class Benchmark:
    """
    Class representing a benchmark. It sweeps over certain parameters and writes
    results to CSV, then can produce average data.
    """
    def __init__(
        self,
        bench_function,
        repetitions_per_point,
        num_of_threads,
        base_range,
        runtime_in_sec,
        operations_mix,
        disjoint_range,
        selection_strategy,
        basic_testing,
        seed,
        basedir,
        name,
    ):
        self.bench_function = bench_function
        self.repetitions_per_point = repetitions_per_point
        self.num_of_threads = num_of_threads
        self.base_range = base_range

        # Ensure runtime_in_sec is a list (for easy iteration)
        if isinstance(runtime_in_sec, int):
            self.runtime_in_sec = [runtime_in_sec]
        else:
            self.runtime_in_sec = runtime_in_sec

        self.operations_mix = operations_mix
        self.disjoint_range = disjoint_range
        self.selection_strategy = selection_strategy
        self.basic_testing = basic_testing
        self.seed = seed
        self.basedir = basedir
        self.name = name

    def run(self):
        """
        Runs the benchmark for the given parameters and writes results to CSV.
        """
        # You can change this to something dynamic, or keep it as self.name
        # for simpler folder naming.
        implementation_name = self.name

        # E.g., "101080" for (10,10,80)
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        # "disjoint" or "shared"
        range_type = "disjoint" if self.disjoint_range else "shared"
        # e.g., data/lock_free/101080_shared
        directory_name = f"{implementation_name}/{op_mix}_{range_type}"

        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)

        for runtime in self.runtime_in_sec:
            # Example CSV filename: "1s_8threads.csv"
            result_file = os.path.join(result_dir, f"{runtime}s_{len(self.num_of_threads)}threads.csv")
            print(f"Saving results to: {result_file}")

            with open(result_file, mode="w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)

                # Write header
                csv_writer.writerow(
                    [
                        "threads",
                        "repetition",
                        "time",
                        "total_inserts",
                        "successful_inserts",
                        "total_deletes",
                        "successful_deletes",
                        "total_contains",
                        "successful_contains",
                        "total_operations",
                    ]
                )

                for t in self.num_of_threads:
                    for i in range(self.repetitions_per_point):
                        result = self.bench_function(
                            ctypes.c_int(t),
                            ctypes.c_int(runtime),
                            ctypes.c_float(self.operations_mix[0]),
                            ctypes.c_float(self.operations_mix[1]),
                            ctypes.c_float(self.operations_mix[2]),
                            ctypes.c_int(self.base_range[0]),
                            ctypes.c_int(self.base_range[1]),
                            ctypes.c_int(1 if self.disjoint_range else 0),
                            ctypes.c_int(self.selection_strategy),
                            ctypes.c_int(0),  # prefill, if any
                            ctypes.c_int(1 if self.basic_testing else 0),
                            ctypes.c_int(self.seed),
                        )
                        # Write one row per run
                        csv_writer.writerow(
                            [
                                t,
                                i,
                                result.time,
                                result.total_inserts,
                                result.successful_inserts,
                                result.total_deletes,
                                result.successful_deletes,
                                result.total_contains,
                                result.successful_contains,
                                result.total_operations,
                            ]
                        )
                        csvfile.flush()
                        del result

    def write_avg_data(self):
        """
        Reads the CSV, computes averages over the repetitions, and writes out
        an "averages" CSV in the same directory.
        """
        implementation_name = self.name
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        directory_name = f"{implementation_name}/{op_mix}_{range_type}"

        result_dir = os.path.join(self.basedir, "data", directory_name)

        for runtime in self.runtime_in_sec:
            result_file = os.path.join(result_dir, f"{runtime}s_{len(self.num_of_threads)}threads.csv")
            avg_file = os.path.join(result_dir, f"{runtime}s_{len(self.num_of_threads)}threads_averages.csv")

            if not os.path.exists(result_file):
                print(f"Result file does not exist: {result_file}")
                continue

            print(f"Calculating averages for: {result_file}")

            data = {}

            with open(result_file, mode="r") as infile:
                reader = csv.reader(infile)
                headers = next(reader)  # skip header

                for row in reader:
                    threads = int(row[0])    # The first column is 'threads'
                    # row[1] is repetition, skip or keep if you want
                    # Convert numeric columns from row[2:] onward
                    values = list(map(float, row[2:]))

                    if threads not in data:
                        data[threads] = {"sum": [0.0] * len(values), "count": 0}

                    # Accumulate sums
                    for i, val in enumerate(values):
                        data[threads]["sum"][i] += val
                    data[threads]["count"] += 1

            # Write the averaged result to a new CSV
            with open(avg_file, mode="w", newline="") as outfile:
                writer = csv.writer(outfile)
                # Write a new header
                writer.writerow(["threads"] + headers[2:])

                for threads, stats in sorted(data.items()):
                    sums = stats["sum"]
                    cnt = stats["count"]
                    avg_list = [s / cnt for s in sums]
                    writer.writerow([threads] + avg_list)

            print(f"Averaged data written to: {avg_file}")


def benchmark_all_implementations():
    """
    Example function to benchmark four different libraries:

    1) Sequential
    2) Fine-lock
    3) Lock-free
    4) Coarse-lock (or any other)

    Each library is tested with:
        threads = [1, 2, 4, 8, 10, 20, 40, 64]
        runtime_in_sec = [1, 5]
        operations_mix = (10, 10, 80) and (40, 40, 20)
        disjoint_range = [True, False]
        repetitions_per_point = 1

    Feel free to remove or reduce these if it's too many test combinations.
    """

    basedir = os.path.dirname(os.path.abspath(__file__))
    
    # Libraries to test: name -> filename in build directory
    implementations = {
        "sequential": "library_seq.so",
        "fine_lock":  "library_finelocking.so",
        "lock_free":  "library_lockfree.so",
        "global_lock":"library_globallocking.so",
    }

    # Common parameter sets for all:
    # num_threads = [1, 2, 4, 8, 10, 20, 40, 64]
    num_threads = [1]
    
    runtimes = [1]
    mixes = [(10, 10, 80)]
    disjoint_types = [False]  # shared vs disjoint
    repetitions = 1
    base_range = (0, 100000)
    selection_strategy = 0  # random
    seed = 42
    basic_testing = False

    # For each library, run all combos of (disjoint_type, operations_mix)
    for lib_name, lib_file in implementations.items():
        # Load the shared object
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
                    num_of_threads=num_threads,
                    base_range=base_range,
                    runtime_in_sec=runtimes,
                    operations_mix=op_mix,
                    disjoint_range=disjoint,
                    selection_strategy=selection_strategy,
                    basic_testing=basic_testing,
                    seed=seed,
                    repetitions_per_point=repetitions,
                    basedir=basedir,
                    name=lib_name,  # So the CSV paths reflect this implementation
                )

                # Run the benchmark & write average data
                bench.run()
                bench.write_avg_data()


if __name__ == "__main__":
    benchmark_all_implementations()
