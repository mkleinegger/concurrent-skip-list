import ctypes
import os
import datetime


class cBenchResult(ctypes.Structure):
    """
    This has to match the returned struct in library.c
    """

    _fields_ = [
        ("time", ctypes.c_float),
        ("total_inserts", ctypes.c_ulonglong),
        ("successful_inserts", ctypes.c_ulonglong),
        ("total_deletes", ctypes.c_ulonglong),
        ("successful_deletes", ctypes.c_ulonglong),
        ("total_contains", ctypes.c_ulonglong),
        ("successful_contains", ctypes.c_ulonglong),
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
        self.seed = seed
        self.basedir = basedir
        self.name = name

        self.data = {}
        self.now = None

    def run(self):
        """
        Runs the benchmark with the given parameters. Collects
        repetitions_per_point data points and writes them back to the data
        dictionary to be processed later.
        """
        self.now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print(f"Starting Benchmark run at {self.now}")

        for t in self.num_of_threads:
            tmp = []
            for _ in range(0, self.repetitions_per_point):
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
                    ctypes.c_int(self.seed),
                )

                tmp.append(
                    {
                        "time": result.time,
                        "total_inserts": result.total_inserts,
                        "successful_inserts": result.successful_inserts,
                        "total_deletes": result.total_deletes,
                        "successful_deletes": result.successful_deletes,
                        "total_contains": result.total_contains,
                        "successful_contains": result.successful_contains,
                    }
                )

            self.data[t] = tmp

    def write_avg_data(self):
        """
        Writes averages for each point measured into a dataset in the data
        folder timestamped when the run was started.
        """
        if self.now is None:
            raise Exception("Benchmark was not run. Run before writing data.")

        # Create directory if it doesn't exist
        avg_dir = f"{self.basedir}/data/{self.now}/avg"
        os.makedirs(avg_dir, exist_ok=True)

        # Open file for writing
        with open(f"{avg_dir}/{self.name}.data", "w") as datafile:
            datafile.write(
                "threads time total_inserts successful_inserts total_deletes successful_deletes total_contains successful_contains\n"
            )
            for x, box in self.data.items():
                # Calculate averages for each metric
                avg_time = sum([entry["time"] for entry in box]) / len(box)
                avg_total_inserts = sum(
                    [entry["total_inserts"] for entry in box]
                ) / len(box)
                avg_successful_inserts = sum(
                    [entry["successful_inserts"] for entry in box]
                ) / len(box)
                avg_total_deletes = sum(
                    [entry["total_deletes"] for entry in box]
                ) / len(box)
                avg_successful_deletes = sum(
                    [entry["successful_deletes"] for entry in box]
                ) / len(box)
                avg_total_contains = sum(
                    [entry["total_contains"] for entry in box]
                ) / len(box)
                avg_successful_contains = sum(
                    [entry["successful_contains"] for entry in box]
                ) / len(box)

                # Write averages as a single row
                datafile.write(
                    f"{x} {avg_time} {avg_total_inserts} {avg_successful_inserts} "
                    f"{avg_total_deletes} {avg_successful_deletes} {avg_total_contains} {avg_successful_contains}\n"
                )


def benchmark():
    """
    Requires the binary to also be present as a shared library.
    """
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary = ctypes.CDLL(f"{basedir}/library.so")
    # Set the result type for each benchmark function
    binary.small_bench.restype = cBenchResult

    num_threads = [1]  # ,2,4,8,16]#,32,64,128,256]

    smallbench = Benchmark(
        bench_function=binary.small_bench,
        num_of_threads=num_threads,
        base_range=(0, 100000),
        runtime_in_sec=1,
        operations_mix=(10, 10, 80),
        disjoint_range=False,
        selection_strategy=0,
        seed=42,
        repetitions_per_point=10,
        basedir=basedir,
        name="smallbench_10",
    )

    smallbench.run()
    smallbench.write_avg_data()


if __name__ == "__main__":
    benchmark()
