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
    ]


class SequentialBenchmark:
    def __init__(
        self,
        bench_function,
        runtime_in_sec,
        operations_mix,
        base_range,
        repetitions,
        seed,
        basedir,
        name,
    ):
        self.bench_function = bench_function
        self.runtime_in_sec = runtime_in_sec
        self.operations_mix = operations_mix
        self.base_range = base_range
        self.repetitions = repetitions
        self.seed = seed
        self.basedir = basedir
        self.name = name

    def run(self):
        implementation_name = "sequential"
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        directory_name = f"{implementation_name}/{op_mix}_random"

        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)

        for runtime in self.runtime_in_sec:
            result_file = os.path.join(result_dir, f"{runtime}s_1thread.csv")
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

                for rep in range(self.repetitions):
                    result = self.bench_function(
                        ctypes.c_int(1),  # Only 1 thread for sequential implementation
                        ctypes.c_int(runtime),
                        ctypes.c_float(self.operations_mix[0]),
                        ctypes.c_float(self.operations_mix[1]),
                        ctypes.c_float(self.operations_mix[2]),
                        ctypes.c_int(self.base_range[0]),
                        ctypes.c_int(self.base_range[1]),
                        ctypes.c_int(0),  # Random selection strategy
                        ctypes.c_int(0),  # Prefill count
                        ctypes.c_int(0),  # Basic testing
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


def benchmark_sequential():
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary = ctypes.CDLL(f"{basedir}/build/library_seq.so")
    binary.bench.restype = cBenchResult

    runtimes = [1, 5]  # 1 second and 5 seconds
    mixes = [(10, 10, 80), (40, 40, 20)]  # Operation mixes

    for mix in mixes:
        bench = SequentialBenchmark(
            bench_function=binary.bench,
            runtime_in_sec=runtimes,
            operations_mix=mix,
            base_range=(0, 100000),
            repetitions=1,  # Single repetition for each configuration
            seed=42,
            basedir=basedir,
            name="sequential",
        )
        bench.run()


if __name__ == "__main__":
    benchmark_sequential()
