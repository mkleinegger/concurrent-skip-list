import os
import ctypes
import datetime
import csv

# Set environment for OpenMP stack size
os.environ["OMP_STACKSIZE"] = "64k"


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

    def get_directory_name(self):
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        return f"{self.name.replace(' ', '_')}/{op_mix}_{range_type}_selection_{self.selection_strategy}"

    def run(self):
        directory_name = self.get_directory_name()
        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)
        result_file = os.path.join(result_dir, f"{self.runtime_in_sec}s_{len(self.num_of_threads)}threads_config.csv")

        print(f"Saving results to: {result_file}")

        with open(result_file, mode="w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
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
                    del result

    def write_avg_data(self):
        directory_name = self.get_directory_name()
        result_dir = os.path.join(self.basedir, "data", directory_name)
        result_file = os.path.join(result_dir, f"{self.runtime_in_sec}s_{len(self.num_of_threads)}threads.csv")
        avg_file = os.path.join(result_dir, f"{self.runtime_in_sec}s_{len(self.num_of_threads)}threads_averages.csv")

        if not os.path.exists(result_file):
            raise Exception(f"Result file does not exist: {result_file}")

        data = {}

        with open(result_file, mode="r") as infile:
            reader = csv.reader(infile)
            headers = next(reader)

            for row in reader:
                threads = int(row[0])
                values = list(map(float, row[2:]))

                if threads not in data:
                    data[threads] = {"sum": [0] * len(values), "count": 0}

                for i, value in enumerate(values):
                    data[threads]["sum"][i] += value
                data[threads]["count"] += 1

        with open(avg_file, mode="w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["threads"] + headers[2:])

            for threads, stats in sorted(data.items()):
                averages = [s / stats["count"] for s in stats["sum"]]
                writer.writerow([threads] + averages)

        print(f"Averaged data written to: {avg_file}")


def benchmark_all():
    """
    Run benchmarks with multiple runtime configurations.
    """
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary = ctypes.CDLL(f"{basedir}/build/library_finelocking.so")
    binary.bench.restype = cBenchResult

    num_threads = [1, 2, 4, 8, 10, 20, 40, 64]
    runtimes = [1, 5]  # Add 1 and 5 seconds as runtime options
    operation_mixes = [(40, 40, 20), (10, 10, 80)]  # Two operation mixes
    disjoint_options = [False, True]  # Shared and disjoint ranges
    selection_strategies = [0]  # Random, successive, unique

    for runtime in runtimes:
        for op_mix in operation_mixes:
            for disjoint in disjoint_options:
                for strategy in selection_strategies:
                    bench = Benchmark(
                        bench_function=binary.bench,
                        num_of_threads=num_threads,
                        base_range=(0, 100000),
                        runtime_in_sec=runtime,
                        operations_mix=op_mix,
                        disjoint_range=disjoint,
                        selection_strategy=strategy,
                        seed=42,
                        repetitions_per_point=1,
                        basic_testing=False,
                        basedir=basedir,
                        name=f"finelocking_{runtime}s",
                    )
                    bench.run()
                    bench.write_avg_data()

    # Add benchmarks for the lock-free skip list
    binary2 = ctypes.CDLL(f"{basedir}/build/library_lockfree.so")
    binary2.bench.restype = cBenchResult

    for runtime in runtimes:
        for op_mix in operation_mixes:
            for disjoint in disjoint_options:
                for strategy in selection_strategies:
                    bench = Benchmark(
                        bench_function=binary2.bench,
                        num_of_threads=num_threads,
                        base_range=(0, 100000),
                        runtime_in_sec=runtime,
                        operations_mix=op_mix,
                        disjoint_range=disjoint,
                        selection_strategy=strategy,
                        seed=42,
                        repetitions_per_point=1,
                        basic_testing=False,
                        basedir=basedir,
                        name=f"lockfree_{runtime}s",
                    )
                    bench.run()
                    bench.write_avg_data()

if __name__ == "__main__":
    benchmark_all()