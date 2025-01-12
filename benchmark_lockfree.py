import os
os.environ["OMP_STACKSIZE"] = "64k"
import ctypes
import datetime
import csv
# import pandas as pd
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
        """
        Runs the benchmark with the given parameters. Writes results to a CSV
        file after each repetition for incremental updates.
        """
        implementation_name = "lock_free"
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        directory_name = f"{implementation_name}/{op_mix}_{range_type}"

        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)

        for runtime in self.runtime_in_sec:  # Iterate over runtimes
            result_file = os.path.join(result_dir, f"{runtime}s_{len(self.num_of_threads)}threads.csv")
            print(f"Saving results to: {result_file}")

            with open(result_file, mode="w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(
                    [
                        "threads",
                        "repetitions_per_point",
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
                            ctypes.c_int(runtime),  # Correctly passing runtime as an integer
                            ctypes.c_float(self.operations_mix[0]),
                            ctypes.c_float(self.operations_mix[1]),
                            ctypes.c_float(self.operations_mix[2]),
                            ctypes.c_int(self.base_range[0]),
                            ctypes.c_int(self.base_range[1]),
                            ctypes.c_int(1 if self.disjoint_range else 0),
                            ctypes.c_int(self.selection_strategy),
                            ctypes.c_int(0),
                            ctypes.c_int(1 if self.basic_testing else 0),
                            ctypes.c_int(self.seed),
                        )

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
        Incrementally processes the CSV file with benchmark results, averages data over threads,
        and writes the averages to a new CSV file without using pandas.
        """
        implementation_name = "lock_free"
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
                    threads = int(row[0])  # The first column is 'threads'
                    values = list(map(float, row[2:]))  # Convert numeric columns to float

                    if threads not in data:
                        data[threads] = {"sum": [0] * len(values), "count": 0}

                    # Incrementally add the row values to the sums
                    for i, value in enumerate(values):
                        data[threads]["sum"][i] += value
                    data[threads]["count"] += 1

            # Write averages to a new CSV file
            with open(avg_file, mode="w", newline="") as outfile:
                writer = csv.writer(outfile)
                writer.writerow(["threads"] + headers[2:])  # Write header excluding repetition column

                for threads, stats in sorted(data.items()):
                    # Calculate averages
                    averages = [s / stats["count"] for s in stats["sum"]]
                    writer.writerow([threads] + averages)

            print(f"Averaged data written to: {avg_file}")

def benchmark_lock_free():
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary = ctypes.CDLL(f"{basedir}/build/library_lockfree.so")
    binary.bench.restype = cBenchResult

    num_threads = [1, 2, 4, 8, 10, 20, 40, 64]
    # num_threads = [1, 2, 4, 8, 10, 20, 40, 64] #adjusted for 5s benching with 40 40 20 
    
    runtimes = [1, 5]  # 1 second and 5 seconds
    # runtimes = [1]  # 1 second - tested
    # runtimes = [5]  # 5 seconds - tested
    
    
    mixes = [(10, 10, 80), (40, 40, 20)]  # Operation mixes
    # mixes = [(10, 10, 80)]  # Operation mixes
    # mixes = [(40, 40, 20)]  # Operation mixes
    
    
    disjoint_types = [True, False]  # Disjoint and shared ranges
    # disjoint_types = [True]  # Disjoint and shared ranges - tested 
    # disjoint_types = [False]  # Disjoint and shared ranges - tested
    
    

    for disjoint in disjoint_types:
        for mix in mixes:
            bench = Benchmark(
                bench_function=binary.bench,
                num_of_threads=num_threads,
                runtime_in_sec=runtimes,
                operations_mix=mix,
                base_range=(0, 100000),
                disjoint_range=disjoint,
                repetitions_per_point=1,  
                selection_strategy=0,  
                basic_testing=False,  
                seed=42,
                basedir=basedir,
                name="lock_free",
            )
            bench.run()
            bench.write_avg_data()


if __name__ == "__main__":
    benchmark_lock_free()
