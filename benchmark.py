import os
os.environ["OMP_STACKSIZE"] = "16k"
import ctypes
import datetime
import csv
# import pandas as pd
import time

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
        self.now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print(f"Starting Benchmark run at {self.now}")

        # Create directory for results
        result_dir = f"{self.basedir}/data/{self.now}/results"
        os.makedirs(result_dir, exist_ok=True)

        # Open CSV file for appending results
        result_file = f"{result_dir}/{self.name}.csv"
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
                #time.sleep(5)
                for i in range(0, self.repetitions_per_point):
                    result = self.bench_function(
                        ctypes.c_int(t),
                        ctypes.c_int(self.runtime_in_sec),
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

                    # Write the result of the current repetition as a row
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
                    csvfile.flush()  # Ensure data is written immediately

    def write_avg_data(self):
        """
        Incrementally processes the CSV file with benchmark results, averages data over threads,
        and writes the averages to a new CSV file without using pandas.
        """
        if self.now is None:
            raise Exception("Benchmark was not run. Run before writing data.")

        # Paths for result and averaged data
        result_file = f"{self.basedir}/data/{self.now}/results/{self.name}.csv"
        avg_dir = f"{self.basedir}/data/{self.now}/avg"
        os.makedirs(avg_dir, exist_ok=True)
        avg_file = f"{avg_dir}/{self.name}_averages.csv"

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



def benchmark():
    """
    Requires the binary to also be present as a shared library.
    """
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary = ctypes.CDLL(f"{basedir}/build/library_globallocking.so")
    # Set the result type for each benchmark function
    binary.bench.restype = cBenchResult

    num_threads = [1, 2, 4, 8, 10, 20, 40, 64]

    bench = Benchmark(
        bench_function=binary.bench,
        num_of_threads=num_threads,
        base_range=(0, 100000),
        runtime_in_sec=1,
        operations_mix=(40, 40, 20),
        disjoint_range=False,
        selection_strategy=1,
        seed=42,
        repetitions_per_point=1,
        basic_testing=True,
        basedir=basedir,
        name="bench",
    )

    bench.run()
    bench.write_avg_data()

    bench2 = Benchmark(
        bench_function=binary.bench,
        num_of_threads=num_threads,
        base_range=(0, 100000),
        runtime_in_sec=1,
        operations_mix=(10, 10, 80),
        disjoint_range=False,
        selection_strategy=1,
        seed=42,
        repetitions_per_point=1,
        basic_testing=True,
        basedir=basedir,
        name="bench",
    )

    bench2.run()
    bench2.write_avg_data()


if __name__ == "__main__":
    benchmark()
