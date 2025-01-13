import argparse
import os
import ctypes

from src.utils.bench_utils import cBenchResult, Benchmark

def main():
    """
    Parse command-line arguments and run the benchmark accordingly.
    """
    parser = argparse.ArgumentParser(description="Run the benchmark with command-line parameters.")
    parser.add_argument(
        "--library",
        type=str,
        default="library_globallocking.so",
        help="Path to the shared library to test (e.g., library_globallocking.so)."
    )
    parser.add_argument(
        "--repetitions-per-point",
        type=int,
        default=1,
        help="Number of repetitions per point.",
    )
    parser.add_argument(
        "--num-of-threads",
        type=int,
        nargs="+",
        default=[1],
        help="List of thread counts to test, e.g. --num-of-threads 1 2 4 8.",
    )
    parser.add_argument(
        "--base-range",
        type=int,
        nargs=2,
        default=[0, 100000],
        help="Lower and upper bound for the key range, e.g. --base-range 0 100000.",
    )
    parser.add_argument(
        "--runtime-in-sec",
        type=int,
        nargs="+",
        default=[1, 5],
        help="List of run times in seconds, e.g. --runtime-in-sec 1 5.",
    )
    parser.add_argument(
        "--operations-mix",
        type=float,
        nargs=3,
        default=[10, 10, 80],
        help="(Insert%, Delete%, Contains%), e.g. --operations-mix 40 40 20.",
    )
    parser.add_argument(
        "--disjoint-range",
        action="store_true",
        help="Use disjoint range if set; otherwise shared range.",
    )
    parser.add_argument(
        "--selection-strategy",
        type=int,
        default=0,
        help="Selection strategy (0 => random).",
    )
    parser.add_argument(
        "--basic-testing",
        action="store_true",
        help="Enable basic testing if set.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )
    parser.add_argument(
        "--prefill-count",  # New argument
        type=int,
        default=0,
        help="Number of items to prefill before benchmarking, e.g., --prefill-count 1000.",
    )
    parser.add_argument(
        "--basedir",
        type=str,
        default=".",
        help="Base directory for data output.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="bench",
        help="Name for this benchmark run.",
    )

    args = parser.parse_args()

    # Load the shared library
    this_dir = os.path.dirname(os.path.abspath(__file__))
    lib_path = os.path.join(this_dir, "build", args.library)
    if not os.path.exists(lib_path):
        raise FileNotFoundError(f"Shared library not found at: {lib_path}")
    binary = ctypes.CDLL(lib_path)
    binary.bench.restype = cBenchResult

    # Create the benchmark object with parsed arguments
    bench = Benchmark(
        bench_function=binary.bench,
        repetitions_per_point=args.repetitions_per_point,
        num_of_threads=args.num_of_threads,
        base_range=args.base_range,
        runtime_in_sec=args.runtime_in_sec,
        operations_mix=args.operations_mix,
        disjoint_range=args.disjoint_range,
        selection_strategy=args.selection_strategy,
        basic_testing=args.basic_testing,
        seed=args.seed,
        prefill_count=args.prefill_count,  # Pass prefill_count
        basedir=args.basedir,
        name=args.name,
    )

    # Run and write averages
    bench.run()
    bench.write_avg_data()


if __name__ == "__main__":
    main()
