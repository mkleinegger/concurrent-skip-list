#!/usr/bin/env python3
import os
import ctypes
import csv
import time
import datetime
import json 

# Define the cBenchResult structure
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
        ("basic_correctness_test_success", ctypes.c_int),
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
        prefill_count,  # New parameter
        basedir,
        name,
    ):
        self.bench_function = bench_function
        self.repetitions_per_point = repetitions_per_point
        self.num_of_threads = num_of_threads
        self.base_range = base_range

        # Ensure runtime_in_sec is a list or tuple to iterate over
        if isinstance(runtime_in_sec, int):
            self.runtime_in_sec = [runtime_in_sec]
        else:
            self.runtime_in_sec = runtime_in_sec

        self.operations_mix = operations_mix
        self.disjoint_range = disjoint_range
        self.selection_strategy = selection_strategy
        self.basic_testing = basic_testing
        self.seed = seed
        self.prefill_count = prefill_count  # Store the prefill_count
        self.basedir = basedir
        self.name = name

        self.data = {}
        self.now = None

    def run(self):
        """
        Runs the benchmark and saves the results to CSV files.
        """
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        directory_name = f"{self.name}/{op_mix}_{range_type}"

        result_dir = os.path.join(self.basedir, "data", directory_name)
        os.makedirs(result_dir, exist_ok=True)

        # Timestamp for unique file naming
        self.now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        for runtime in self.runtime_in_sec:
            result_file = os.path.join(result_dir, f"run_{runtime}s_{self.now}.csv")
            print(f"Saving results to: {result_file}")

            with open(result_file, mode="w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(
                    [
                        "threads",
                        "repetition",
                        "prefill_count", 
                        "time",
                        "total_inserts",
                        "successful_inserts",
                        "total_deletes",
                        "successful_deletes",
                        "total_contains",
                        "successful_contains",
                        "total_operations",
                        "basic_correctness_test_success",
                        "operations_per_thread", 
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
                            ctypes.c_int(self.disjoint_range),
                            ctypes.c_int(self.selection_strategy),
                            ctypes.c_int(self.prefill_count),  # Use prefill_count here
                            ctypes.c_int(self.basic_testing),
                            ctypes.c_int(self.seed),
                        )

                        # Serialize operations_per_thread as a JSON string containing only relevant threads
                        ops_per_thread = json.dumps(list(result.operations_per_thread)[:t])

                        csv_writer.writerow(
                            [
                                t,
                                i,
                                self.prefill_count,  # Record prefill_count
                                result.time,
                                result.total_inserts,
                                result.successful_inserts,
                                result.total_deletes,
                                result.successful_deletes,
                                result.total_contains,
                                result.successful_contains,
                                result.total_operations,
                                result.basic_correctness_test_success,
                                ops_per_thread
                            ]
                        )
                        csvfile.flush()
                        del result

    def write_avg_data(self):
        """
        Processes the CSV files with benchmark results, averages data over
        repetitions for each thread count, and writes to new averages CSV files.
        Note: Averaging 'operations_per_thread' requires aggregating per-thread data.
        This example calculates the average operations per thread across repetitions.
        """
        op_mix = f"{int(self.operations_mix[0])}{int(self.operations_mix[1])}{int(self.operations_mix[2])}"
        range_type = "disjoint" if self.disjoint_range else "shared"
        directory_name = f"{self.name}/{op_mix}_{range_type}"

        result_dir = os.path.join(self.basedir, "data", directory_name)

        for runtime in self.runtime_in_sec:
            result_file = os.path.join(result_dir, f"run_{runtime}s_{self.now}.csv")
            avg_file = os.path.join(result_dir, f"{runtime}s_{self.now}_average.csv")

            if not os.path.exists(result_file):
                print(f"Result file does not exist: {result_file}")
                continue

            print(f"Calculating averages for: {result_file}")

            # Dictionaries to store sums and counts for averaging
            data_map = {}
            ops_thread_map = {}

            with open(result_file, mode="r") as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    threads = int(row["threads"])
                    prefill = int(row["prefill_count"])  # Read prefill_count if needed

                    if threads not in data_map:
                        # Initialize sums for numeric fields
                        data_map[threads] = {
                            "time": 0.0,
                            "total_inserts": 0,
                            "successful_inserts": 0,
                            "total_deletes": 0,
                            "successful_deletes": 0,
                            "total_contains": 0,
                            "successful_contains": 0,
                            "total_operations": 0,
                            "basic_correctness_test_success": 0
                        }
                        # Initialize sums for operations_per_thread
                        ops_thread_map[threads] = [0] * threads  # Dynamic based on threads

                    # Aggregate numeric fields
                    data_map[threads]["time"] += float(row["time"])
                    data_map[threads]["total_inserts"] += int(row["total_inserts"])
                    data_map[threads]["successful_inserts"] += int(row["successful_inserts"])
                    data_map[threads]["total_deletes"] += int(row["total_deletes"])
                    data_map[threads]["successful_deletes"] += int(row["successful_deletes"])
                    data_map[threads]["total_contains"] += int(row["total_contains"])
                    data_map[threads]["successful_contains"] += int(row["successful_contains"])
                    data_map[threads]["total_operations"] += int(row["total_operations"])
                    data_map[threads]["basic_correctness_test_success"] += int(row["basic_correctness_test_success"])

                    # Aggregate operations_per_thread
                    try:
                        ops_per_thread = json.loads(row["operations_per_thread"])
                        for idx in range(threads):
                            ops_thread_map[threads][idx] += ops_per_thread[idx]
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for thread {threads}: {e}")
                        continue
                    except IndexError as e:
                        print(f"Index error for thread {threads}: {e}")
                        continue

            # Write averages to a new CSV file
            with open(avg_file, mode="w", newline="") as outfile:
                fieldnames = [
                    "threads",
                    "prefill_count",  # Include prefill_count in averages
                    "time",
                    "total_inserts",
                    "successful_inserts",
                    "total_deletes",
                    "successful_deletes",
                    "total_contains",
                    "successful_contains",
                    "total_operations",
                    "basic_correctness_test_success",  # Added comma
                    "average_operations_per_thread",
                ]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                for threads in sorted(data_map.keys()):
                    count = self.repetitions_per_point
                    avg_data = {
                        "threads": threads,
                        "prefill_count": self.prefill_count,  # Record prefill_count
                        "time": data_map[threads]["time"] / count,
                        "total_inserts": data_map[threads]["total_inserts"] / count,
                        "successful_inserts": data_map[threads]["successful_inserts"] / count,
                        "total_deletes": data_map[threads]["total_deletes"] / count,
                        "successful_deletes": data_map[threads]["successful_deletes"] / count,
                        "total_contains": data_map[threads]["total_contains"] / count,
                        "successful_contains": data_map[threads]["successful_contains"] / count,
                        "total_operations": data_map[threads]["total_operations"] / count,
                        "basic_correctness_test_success": True if data_map[threads]["basic_correctness_test_success"] == count else False,
                        "average_operations_per_thread": json.dumps([
                            ops_thread_map[threads][idx] / count for idx in range(threads)
                        ]),
                    }
                    writer.writerow(avg_data)

            print(f"Averaged data written to: {avg_file}")

