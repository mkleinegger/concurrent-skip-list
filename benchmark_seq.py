import os
os.environ["OMP_STACKSIZE"] = "64k"
import ctypes
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
    Class representing a benchmark. It assumes any benchmark sweeps over some
    parameter xrange using the fixed set of inputs for every point. It simply
    averages the results over the given amount of repetitions.
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

        # Make sure runtime_in_sec is a list or tuple to iterate over
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

        self.data = {}
        self.now = None

    def run(self):
        # In this example, we are assuming a "sequential" implementation
        implementation_name = "sequential"
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        directory_name = f"{implementation_name}/{op_mix}_random"

        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)

        # Only running with one thread for sequential, per your requirement
        for runtime in self.runtime_in_sec:
            result_file = os.path.join(result_dir, f"{runtime}s_{self.num_of_threads[0]}thread.csv")
            print(f"Saving results to: {result_file}")

            with open(result_file, mode="w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(
                    [
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

                # Use self.repetitions_per_point to control the number of repetitions
                for rep in range(self.repetitions_per_point):
                    result = self.bench_function(
                        ctypes.c_int(self.num_of_threads[0]),   # e.g., 1 thread for sequential
                        ctypes.c_int(runtime),
                        ctypes.c_float(self.operations_mix[0]),
                        ctypes.c_float(self.operations_mix[1]),
                        ctypes.c_float(self.operations_mix[2]),
                        ctypes.c_int(self.base_range[0]),
                        ctypes.c_int(self.base_range[1]),
                        ctypes.c_int(self.selection_strategy),   # e.g., 0 => random selection
                        ctypes.c_int(0),                         # prefill count (adjust if needed)
                        ctypes.c_int(self.basic_testing),         # pass your bool as int
                        ctypes.c_int(self.seed),
                    )

                    csv_writer.writerow(
                        [
                            rep,
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
        Incrementally processes the CSV file with benchmark results, averages data over threads,
        and writes the averages to a new CSV file without using pandas.
        """
        # This part is meant to be an example of "fine_lock" or any other
        # implementation name you might be analyzing. Adjust as you wish.
        implementation_name = "sequential"

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

            # Dictionary to store sums and counts for averaging
            data = {}

            with open(result_file, mode="r") as infile:
                reader = csv.reader(infile)
                headers = next(reader)  # Read the header

                for row in reader:
                    # The first column might differ depending on how you wrote the CSV
                    # In this example we assume 'threads' is in column[0]
                    threads = int(row[0])
                    # Convert numeric columns to float (skipping the 'repetition' column if needed)
                    values = list(map(float, row[2:]))

                    if threads not in data:
                        data[threads] = {"sum": [0] * len(values), "count": 0}

                    # Incrementally add the row values to the sums
                    for i, value in enumerate(values):
                        data[threads]["sum"][i] += value
                    data[threads]["count"] += 1

            # Write averages to a new CSV file
            with open(avg_file, mode="w", newline="") as outfile:
                writer = csv.writer(outfile)
                # Write header excluding the first columns as appropriate
                writer.writerow(["threads"] + headers[2:])

                for threads, stats in sorted(data.items()):
                    # Calculate averages
                    averages = [s / stats["count"] for s in stats["sum"]]
                    writer.writerow([threads] + averages)

            print(f"Averaged data written to: {avg_file}")


def benchmark():
    """
    Requires the binary to also be present as a shared library.
    Demonstrates runs with:
    - 1 thread
    - random selection from base key range [0..100000]
    - operation mixes (10,10,80) and (40,40,20)
    - run times 1s and 5s
    """
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary = ctypes.CDLL(f"{basedir}/build/library_seq.so")
    # Set the result type for each benchmark function
    binary.bench.restype = cBenchResult

    # We only run with 1 thread (per your requirement)
    num_threads = [1]

    # Example: run for 1s and 5s
    run_times = [1, 5]

    # First benchmark: operations mix = (40, 40, 20)
    bench = Benchmark(
        bench_function=binary.bench,
        repetitions_per_point=1,      # e.g., run each point once
        num_of_threads=num_threads,
        base_range=(0, 100000),
        runtime_in_sec=run_times,
        operations_mix=(40, 40, 20),
        disjoint_range=False,
        selection_strategy=0,         # 0 => random
        basic_testing=True,           # pass True or 1
        seed=42,
        basedir=basedir,
        name="bench_seq",
    )
    bench.run()
    bench.write_avg_data()

    # Second benchmark: operations mix = (10, 10, 80)
    bench2 = Benchmark(
        bench_function=binary.bench,
        repetitions_per_point=1,
        num_of_threads=num_threads,
        base_range=(0, 100000),
        runtime_in_sec=run_times,
        operations_mix=(10, 10, 80),
        disjoint_range=False,
        selection_strategy=0,  # 0 => random
        basic_testing=True,
        seed=42,
        basedir=basedir,
        name="bench_seq",
    )
    bench2.run()
    bench2.write_avg_data()


if __name__ == "__main__":
    benchmark()
