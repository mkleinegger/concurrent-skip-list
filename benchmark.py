import os
os.environ["OMP_STACKSIZE"] = "64k"
import ctypes
import csv

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
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        directory_name = f"{self.name}/{op_mix}_{range_type}"

        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)

        for runtime in self.runtime_in_sec:
            result_file = os.path.join(result_dir, f"{runtime}s_{len(self.num_of_threads)}threads.csv")
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
                            ctypes.c_int(runtime),
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
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        directory_name = f"{self.name}/{op_mix}_{range_type}"

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
                headers = next(reader)

                for row in reader:
                    threads = int(row[0])
                    values = list(map(float, row[2:]))

                    if threads not in data:
                        data[threads] = {"sum": [0.0] * len(values), "count": 0}

                    for i, val in enumerate(values):
                        data[threads]["sum"][i] += val
                    data[threads]["count"] += 1

            with open(avg_file, mode="w", newline="") as outfile:
                writer = csv.writer(outfile)
                writer.writerow(["threads"] + headers[2:])

                for threads, stats in sorted(data.items()):
                    sums = stats["sum"]
                    cnt = stats["count"]
                    avg_list = [s / cnt for s in sums]
                    writer.writerow([threads] + avg_list)

            print(f"Averaged data written to: {avg_file}")


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
                    basedir=basedir,
                    name=lib_name,
                )

                bench.run()
                bench.write_avg_data()


if __name__ == "__main__":
    benchmark_all()

