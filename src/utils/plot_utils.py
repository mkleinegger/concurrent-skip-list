import os
import glob
import ast
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_and_prepare_data(base_path='data'):
    pattern = os.path.join(base_path, '**', '*_average.csv')
    csv_files = glob.glob(pattern, recursive=True)

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in the path: {base_path}")

    dfs = []
    for fpath in csv_files:
        parts = fpath.split(os.sep)

        implementation_name = parts[1]  # e.g., 'sequential', 'fine_lock'
        op_mix_range = parts[2]         # e.g., '101080_shared'
        op_mix, range_type = op_mix_range.split('_', 1) 

        filename = parts[-1]  # e.g., 'run_1s_time_averages.csv'
        base_name = filename.replace('_average.csv', '')
        splitted = base_name.split('_')

        runtime_str = splitted[0].rstrip('s')  # remove trailing 's', e.g., '1'

        try:
            runtime = int(runtime_str)
        except ValueError:
            runtime = runtime_str

        df = pd.read_csv(fpath)
        
    
        # Add contextual columns
        df['implementation_name'] = implementation_name
        df['op_mix'] = op_mix
        df['range_type'] = range_type
        df['runtime_in_sec'] = runtime

        # Drop unnecessary columns if present
        unnecessary_columns = []  # e.g., ['prefill_count', 'some_other_column']
        for col in unnecessary_columns:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

        # Sanitize the 'average_operations_per_thread' column
        if 'average_operations_per_thread' in df.columns:
            def sanitize_average_ops(x):
                if isinstance(x, str):
                    try:
                        # Safely evaluate the string to a Python literal
                        evaluated = ast.literal_eval(x)
                        # Ensure it's a list or tuple
                        if isinstance(evaluated, (list, tuple)):
                            return np.array(evaluated)
                        else:
                            return np.nan
                    except (ValueError, SyntaxError) as e:
                        return np.nan
                elif isinstance(x, (list, tuple, np.ndarray)):
                    return np.array(x)
                else:
                    return np.nan

            df['average_operations_per_thread'] = df['average_operations_per_thread'].apply(lambda x: sanitize_average_ops(x))

        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)
    return final_df

def enrich_df(df):
    df_sequential_101080 = df[(df['implementation_name'] == 'sequential') & (df['op_mix'] == "101080")].copy()
    df_sequential_101080['range_type'] = 'disjoint'

    df_sequential_404020 = df[(df['implementation_name'] == 'sequential') & (df['op_mix'] == "404020")].copy()
    df_sequential_404020['range_type'] = 'disjoint'

    # Concatenate the modified DataFrames back into final_df
    return pd.concat([df, df_sequential_404020, df_sequential_101080], ignore_index=True)

def plot_throughput(df, op_mix, range_type, runtime, store=False):
    df_filtered = df.loc[
        (df['op_mix'] == op_mix) & 
        (df['range_type'] == range_type) &
        (df['runtime_in_sec'] == runtime)
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

    plt.title(f"Throughput for op_mix={op_mix}, range={range_type}, runtime={runtime}s")
    plt.xlabel("Number of Threads")
    plt.ylabel("Throughput (ops/sec)")
    plt.legend(title="Implementation")
    plt.tight_layout()
    if store:
        os.makedirs('plots/all_impl', exist_ok=True)
        plt.savefig(f"plots/all_impl/benchmark_throughput_{op_mix}_{range_type}_{runtime}s.png")
    else:
        plt.show()


def plot_total_vs_successful_operations(df, implementation_name, op_mix, range_type, runtime_in_sec, store=False):
    filtered_df = df[
        (df['implementation_name'] == implementation_name) &
        (df['op_mix'] == op_mix) &
        (df['range_type'] == range_type) &
        (df['runtime_in_sec'] == runtime_in_sec)
    ]
    
    palette = {
        'Inserts': 'tab:blue',
        'Deletes': 'tab:orange',
        'Contains': 'tab:green'
    }
    linestyles = {
        'Total': 'solid',
        'Successful': 'dashed'
    }
    operations = {
        'Inserts': ('total_inserts', 'successful_inserts'),
        'Deletes': ('total_deletes', 'successful_deletes'),
        'Contains': ('total_contains', 'successful_contains')
    }

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 8))
    
    for operation, (total_col, success_col) in operations.items():
        sns.lineplot(
            data=filtered_df,
            x='threads',
            y=total_col,
            label=f'{operation} Total',
            color=palette[operation],
            linestyle=linestyles['Total'],
            marker='o',
            errorbar=None
        )
        
        sns.lineplot(
            data=filtered_df,
            x='threads',
            y=success_col,
            label=f'{operation} Successful',
            color=palette[operation],
            linestyle=linestyles['Successful'],
            marker='o',
            errorbar=None
        )
    
    plt.title(
        f"Total vs Successful Operations\n"
        f"Implementation: {implementation_name}, Operation Mix: {op_mix}, "
        f"Range Type: {range_type}, Runtime: {runtime_in_sec}s",
        fontsize=16,
        fontweight='bold'
    )
    
    plt.xlabel("Number of Threads", fontsize=14)
    plt.ylabel("Number of Operations", fontsize=14)
    plt.legend(title="Operation Status", fontsize=12, title_fontsize=12)
    plt.tight_layout()
    if store:
        os.makedirs(f'plots/{implementation_name}', exist_ok=True)
        plt.savefig(f"plots/{implementation_name}/benchmark_succesful-vs-total-operation_{op_mix}_{range_type}_{runtime_in_sec}s.png", dpi=300)
    else:
        plt.show()

def plot_total_vs_successful_operations_all_implementations(
    df, 
    op, 
    op_mix, 
    range_type, 
    runtime_in_sec,
    store=False
):
    filtered_df = df[
        (df['op_mix'] == op_mix) &
        (df['range_type'] == range_type) &
        (df['runtime_in_sec'] == runtime_in_sec)
    ]
    
    if filtered_df.empty:
        return
    operation_name, total_col, success_col = op
    
    implementation_names = filtered_df['implementation_name'].unique()
    num_implementations = len(implementation_names)
    
    palette = sns.color_palette(n_colors=num_implementations)
    implementation_color_map = dict(zip(implementation_names, palette))
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 8))
    
    max_total = 0
    max_success = 0
    
    for implementation in implementation_names:
        impl_df = filtered_df[filtered_df['implementation_name'] == implementation].sort_values(by='threads')
        
        if impl_df.empty:
            continue
        
        sns.lineplot(
            data=impl_df,
            x='threads',
            y=total_col,
            label=f'{implementation} - Total',
            color=implementation_color_map[implementation],
            linestyle='solid',
            marker='o'
        )
        
        current_max_total = impl_df[total_col].max()
        if current_max_total > max_total:
            max_total = current_max_total
        
        sns.lineplot(
            data=impl_df,
            x='threads',
            y=success_col,
            label=f'{implementation} - Successful',
            color=implementation_color_map[implementation],
            linestyle='dashed',
            marker='o'
        )
        
        current_max_success = impl_df[success_col].max()
        if current_max_success > max_success:
            max_success = current_max_success
    
    overall_max = max(max_total, max_success)
    y_limit = overall_max * 1.1 
    
    plt.ylim(0, y_limit)
    plt.title(
        f"Total vs Successful Operations for All Implementations\n"
        f"Operation Mix: {op_mix}, Range Type: {range_type}, Runtime: {runtime_in_sec}s",
        fontsize=18,
        fontweight='bold'
    )
    plt.xlabel("Number of Threads", fontsize=16)
    plt.ylabel("Number of Operations", fontsize=16)
    plt.legend(title="Implementation & Status", fontsize=12, title_fontsize=14, loc='upper right')
    plt.tight_layout()
    if store:
        plt.savefig(f"plots/all_impl/benchmark_all_implementations_{operation_name}_{op_mix}_{range_type}_{runtime_in_sec}s.png", dpi=300)
    else:
        plt.show()

def plot_success_ratio_all_implementations(
    df, 
    op, 
    op_mix, 
    range_type, 
    runtime_in_sec,
    store=False
):
    filtered_df = df[
        (df['op_mix'] == op_mix) &
        (df['range_type'] == range_type) &
        (df['runtime_in_sec'] == runtime_in_sec)
    ].copy()  # Explicitly create a copy
    
    if filtered_df.empty:
        return
    
    operation_name, total_col, success_col = op
    
    filtered_df.loc[:, 'success_ratio'] = filtered_df[success_col] / filtered_df[total_col].replace(0, pd.NA)
    
    implementation_names = filtered_df['implementation_name'].unique()
    num_implementations = len(implementation_names)
    
    palette = sns.color_palette(n_colors=num_implementations)
    implementation_color_map = dict(zip(implementation_names, palette))
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 8))
    
    for implementation in implementation_names:
        impl_df = filtered_df[filtered_df['implementation_name'] == implementation].sort_values(by='threads')
        
        if impl_df.empty:
            continue
        
        sns.lineplot(
            data=impl_df,
            x='threads',
            y='success_ratio',
            label=implementation,
            color=implementation_color_map[implementation],
            linestyle='solid',
            marker='o'
        )
    
    plt.ylim(0, 1.05)  # Since ratio ranges from 0 to 1
    plt.title(
        f"Success Ratio of Operations for All Implementations\n"
        f"Operation: {operation_name}, Mix: {op_mix}, Range Type: {range_type}, Runtime: {runtime_in_sec}s",
        fontsize=18,
        fontweight='bold'
    )
    plt.xlabel("Number of Threads", fontsize=16)
    plt.ylabel("Success Ratio", fontsize=16)
    plt.legend(title="Implementation", fontsize=12, title_fontsize=14, loc='lower right')
    plt.tight_layout()
    
    if store:
        os.makedirs("plots/sucess_ratio", exist_ok=True)
        plot_filename = f"benchmark_success_ratio_{operation_name}_{op_mix}_{range_type}_{runtime_in_sec}s.png"
        plt.savefig(os.path.join("plots/sucess_ratio", plot_filename), dpi=300)
    else:
        plt.show()

def plot_speedup_vs_sequential(df, op_mix, range_type, runtime, sequential_impl='sequential', store=False):
    # Filter the DataFrame for the desired parameters
    df_filtered = df.loc[
        (df['op_mix'] == op_mix) &
        (df['range_type'] == range_type) &
        (df['runtime_in_sec'] == runtime)
    ].copy()

    # Compute throughput (ops/sec)
    df_filtered['throughput'] = df_filtered['total_operations'] / df_filtered['time']

    # Identify the sequential baseline (must exist in df for op_mix, range_type, runtime, threads=1, etc.)
    # Adjust threads=1 if your "sequential" data also uses 1 thread to measure baseline.
    df_seq = df_filtered[
        (df_filtered['implementation_name'] == sequential_impl) &
        (df_filtered['threads'] == 1)
    ]
    
    if df_seq.empty:
        raise ValueError(f"No data found for sequential implementation='{sequential_impl}' with 1 thread.")

    # Get that single throughput value
    seq_throughput = df_seq['throughput'].iloc[0]

    # Compute speedup vs sequential
    df_filtered['speedup_vs_seq'] = df_filtered['throughput'] / seq_throughput

    # Plot the speedup with respect to the number of threads
    plt.figure(figsize=(8, 6))
    sns.lineplot(
        data=df_filtered,
        x='threads',
        y='speedup_vs_seq',
        hue='implementation_name',
        marker='o',
        errorbar=None
    )

    plt.title(f"Speedup vs Sequential for op_mix={op_mix}, range={range_type}, runtime={runtime}s")
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup (relative to sequential)")
    plt.legend(title="Implementation")
    plt.tight_layout()

    if store:
        os.makedirs('plots/all_impl', exist_ok=True)
        plt.savefig(f"plots/all_impl/benchmark_speedup_vs_seq_{op_mix}_{range_type}_{runtime}s.png")
    else:
        plt.show()