import ctypes
import os
import datetime
import matplotlib.pyplot as plt

class cBenchCounters(ctypes.Structure):
    '''
    Matches the structure returned by skiplist.c for tracking operations.
    '''
    _fields_ = [
        ("adds", ctypes.c_int),
        ("rems", ctypes.c_int),
        ("cons", ctypes.c_int),
    ]

class cBenchResult(ctypes.Structure):
    '''
    Matches the structure returned by skiplist.c for benchmarking.
    '''
    _fields_ = [
        ("time", ctypes.c_float),         # Execution time in seconds
        ("counters", cBenchCounters),     # Operation counters
    ]

class Benchmark:
    '''
    Class representing a benchmark. It assumes any benchmark sweeps over some
    parameter xrange using the fixed set of inputs for every point. It simply
    averages the results over the given amount of repetitions.
    '''
    def __init__(self, bench_function, parameters,
                 repetitions_per_point, xrange, basedir, name):
        self.bench_function = bench_function
        self.parameters = parameters
        self.repetitions_per_point = repetitions_per_point
        self.xrange = xrange
        self.basedir = basedir
        self.name = name

        self.data = {}
        self.now = None

    def run(self):
        '''
        Runs the benchmark with the given parameters. Collects
        repetitions_per_point data points and writes them back to the data
        dictionary to be processed later.
        '''
        self.now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print(f"Starting Benchmark run at {self.now}")

        for x in self.xrange:
            tmp = []
            for r in range(0, self.repetitions_per_point):
                try:
                    print(f"Running benchmark function with x={x}")
                    result = self.bench_function(x, *self.parameters).time * 1000
                    print(f"Result: {result} ms")
                    tmp.append(result)
                except Exception as e:
                    print(f"Error during benchmark function call: {e}")
            self.data[x] = tmp

    def write_avg_data(self):
        '''
        Writes averages for each point measured into a dataset in the data
        folder timestamped when the run was started.
        '''
        if self.now is None:
            raise Exception("Benchmark was not run. Run before writing data.")

        try:
            os.makedirs(f"{self.basedir}/data/{self.now}/avg")
        except FileExistsError:
            pass
        with open(f"{self.basedir}/data/{self.now}/avg/{self.name}.data", "w") as datafile:
            datafile.write(f"x datapoint\n")
            for x, box in self.data.items():
                datafile.write(f"{x} {sum(box)/len(box)}\n")

    def plot_results(self):
        '''
        Plots the results of the benchmark.
        '''
        if not self.data:
            raise Exception("No data to plot. Run the benchmark first.")

        x_vals = list(self.data.keys())
        y_vals = [sum(box)/len(box) for box in self.data.values()]

        plt.figure()
        plt.plot(x_vals, y_vals, marker='o')
        plt.xlabel('Number of Operations')
        plt.ylabel('Time (ms)')
        plt.title(f'Benchmark Results: {self.name}')
        plt.grid(True)
        plt.savefig(f"{self.basedir}/data/{self.now}/avg/{self.name}.png")
        plt.show()

def benchmark():
    '''
    Requires the binary for the skip list to be compiled as a shared library.
    '''
    basedir = os.path.dirname(os.path.abspath(__file__))
    binary_path = f"{basedir}/skiplist.so"
    if not os.path.exists(binary_path):
        raise FileNotFoundError(f"Shared library not found: {binary_path}")

    binary = ctypes.CDLL(binary_path)

    # Set the result type for each skip list benchmark function
    binary.bench_add.restype = cBenchResult
    binary.bench_rem.restype = cBenchResult
    binary.bench_con.restype = cBenchResult

    # Define parameter sweeps (e.g., number of elements in the skip list)
    element_counts = [10, 100, 1000, 10000]  # X-axis for benchmarking

    # Create benchmark objects for different operations
    add_bench = Benchmark(binary.bench_add, (), 5, element_counts, basedir, "add_bench")
    rem_bench = Benchmark(binary.bench_rem, (), 5, element_counts, basedir, "rem_bench")
    con_bench = Benchmark(binary.bench_con, (), 5, element_counts, basedir, "con_bench")

    # Run and store benchmark results
    print("Running add benchmark...")
    add_bench.run()
    add_bench.write_avg_data()
    add_bench.plot_results()

    print("Running remove benchmark...")
    rem_bench.run()
    rem_bench.write_avg_data()
    rem_bench.plot_results()

    print("Running contains benchmark...")
    con_bench.run()
    con_bench.write_avg_data()
    con_bench.plot_results()

    # Run the benchmark with the specified parameters
    key_range = 100000
    operation_mixes = [(10, 10, 80), (40, 40, 20)]
    durations = [1, 5]

    for mix in operation_mixes:
        for duration in durations:
            print(f"Running benchmark with mix {mix} for {duration} seconds...")
            add_bench = Benchmark(binary.bench_add, (key_range, mix[0], mix[1], mix[2], duration), 1, [1], basedir, f"add_bench_{mix}_{duration}")
            add_bench.run()
            add_bench.write_avg_data()
            add_bench.plot_results()

            rem_bench = Benchmark(binary.bench_rem, (key_range, mix[0], mix[1], mix[2], duration), 1, [1], basedir, f"rem_bench_{mix}_{duration}")
            rem_bench.run()
            rem_bench.write_avg_data()
            rem_bench.plot_results()

            con_bench = Benchmark(binary.bench_con, (key_range, mix[0], mix[1], mix[2], duration), 1, [1], basedir, f"con_bench_{mix}_{duration}")
            con_bench.run()
            con_bench.write_avg_data()
            con_bench.plot_results()

if __name__ == "__main__":
    benchmark()