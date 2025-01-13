import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import seaborn as sns
import ast

def load_and_prepare_data(base_path='data'):
    pattern = os.path.join(base_path, '**', '*_averages.csv')
    csv_files = glob.glob(pattern, recursive=True)

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in the path: {base_path}")

    dfs = []
    for fpath in csv_files:
        parts = fpath.split(os.sep)

        if len(parts) < 3:
            print(f"Skipping file due to unexpected path structure: {fpath}")
            continue

        implementation_name = parts[1]  # e.g., 'sequential', 'fine_lock'
        op_mix_range = parts[2]          # e.g., '101080_shared'

        # Split 'op_mix_range' into 'op_mix' and 'range_type'
        if '_' not in op_mix_range:
            print(f"Skipping file due to unexpected op_mix_range format: {op_mix_range}")
            continue
        op_mix, range_type = op_mix_range.split('_', 1)  # split only on the first '_'

        filename = parts[-1]  # e.g., '1s_8threads_averages.csv'
        base_name = filename.replace('_averages.csv', '')
        splitted = base_name.split('_')

        if len(splitted) < 2:
            print(f"Skipping file due to unexpected filename format: {filename}")
            continue

        runtime_str = splitted[0].rstrip('s')  # remove trailing 's', e.g., '1'
        num_threads_str = splitted[1].replace('threads', '')  # remove 'threads', e.g., '8'

        try:
            runtime = int(runtime_str)
        except ValueError:
            print(f"Runtime conversion failed for value: {runtime_str} in file: {fpath}")
            runtime = runtime_str  # Keep as string if conversion fails

        # Read the CSV file
        try:
            df = pd.read_csv(fpath)
        except Exception as e:
            print(f"Failed to read CSV file: {fpath}. Error: {e}")
            continue

        # Add contextual columns
        df['implementation_name'] = implementation_name
        df['op_mix'] = op_mix
        df['range_type'] = range_type
        df['runtime_in_sec'] = runtime

        # Handle the 'threads' column
        if 'threads' in df.columns:
            if len(df['threads'].unique()) == 1:
                csv_threads = df['threads'].unique()[0]
                try:
                    filename_threads = int(num_threads_str)
                    if csv_threads != filename_threads:
                        print(f"Mismatch in threads for file: {fpath}. CSV: {csv_threads}, Filename: {num_threads_str}")
                except ValueError:
                    print(f"Invalid thread count in filename: {num_threads_str} for file: {fpath}")
        else:
            # If 'threads' column is missing in CSV, use extracted value
            try:
                df['threads'] = int(num_threads_str)
            except ValueError:
                print(f"Threads conversion failed for value: {num_threads_str} in file: {fpath}")
                df['threads'] = num_threads_str  # Keep as string if conversion fails

        # Drop unnecessary columns if present
        # Define columns to drop (if any)
        unnecessary_columns = []  # e.g., ['prefill_count', 'some_other_column']
        for col in unnecessary_columns:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

        # Sanitize the 'average_operations_per_thread' column
        if 'average_operations_per_thread' in df.columns:
            def sanitize_average_ops(x, fpath):
                if isinstance(x, str):
                    try:
                        # Safely evaluate the string to a Python literal
                        evaluated = ast.literal_eval(x)
                        # Ensure it's a list or tuple
                        if isinstance(evaluated, (list, tuple)):
                            return np.array(evaluated)
                        else:
                            print(f"Unexpected type after evaluation in file: {fpath}. Expected list or tuple, got {type(evaluated)}.")
                            return np.nan
                    except (ValueError, SyntaxError) as e:
                        print(f"Failed to parse 'average_operations_per_thread' in file: {fpath}. Error: {e}")
                        return np.nan
                elif isinstance(x, (list, tuple, np.ndarray)):
                    return np.array(x)
                else:
                    print(f"Unexpected data type in 'average_operations_per_thread' in file: {fpath}. Got {type(x)}.")
                    return np.nan

            df['average_operations_per_thread'] = df['average_operations_per_thread'].apply(
                lambda x: sanitize_average_ops(x, fpath)
            )

            # Optionally, drop rows where 'average_operations_per_thread' couldn't be parsed
            initial_len = len(df)
            df = df.dropna(subset=['average_operations_per_thread'])
            dropped_len = initial_len - len(df)
            if dropped_len > 0:
                print(f"Dropped {dropped_len} rows due to parsing errors in 'average_operations_per_thread' for file: {fpath}")

        dfs.append(df)

    if not dfs:
        raise ValueError("No valid data frames were created from the CSV files.")

    # Concatenate all DataFrames into a final DataFrame
    final_df = pd.concat(dfs, ignore_index=True)

    return final_df

def plot_throughput(df, op_mix, range_type, store=False):
    df_filtered = df.loc[
        (df['op_mix'] == op_mix) & 
        (df['range_type'] == range_type)
    ].copy()

    df_filtered['throughput'] = df_filtered['total_operations'] / df_filtered['time']

    plt.figure(figsize=(8, 6))
    sns.lineplot(
        data=df_filtered, 
        x='threads', 
        y='throughput', 
        hue='implementation_name', 
        marker='o',
        errorbar=None
    )

    plt.title(f"Throughput for op_mix={op_mix}, range={range_type}")
    plt.xlabel("Number of Threads")
    plt.ylabel("Throughput (ops/sec)")
    plt.legend(title="Implementation")
    plt.tight_layout()
    if store:
        plt.savefig(f"plots/throughput_{op_mix}_{range_type}.png", dpi=300)
    else:
        plt.show()

