##
# @file benchmark_small_plots.py
# @author Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
# @date 2025-01-13
#
# @brief This script generates plots for the benchmark_small specified in the task description.


from src.utils.plot_utils import load_and_prepare_data, enrich_df, plot_throughput, plot_success_ratio_all_implementations, plot_total_vs_successful_operations_all_implementations, explode_average_ops_per_thread
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def plot_avg_ops_per_thread(df, implementation_name, column='average_operations_per_thread'):
    df_filtered = df[
        (df['implementation_name'] == implementation_name) &
        (df['op_mix'] == '101080') &
        (df['range_type'] == 'shared') &
        (df['runtime_in_sec'] == 1) &
        (df['threads'] == 64)
    ].copy()

    df_exploded = explode_average_ops_per_thread(df_filtered, column=column)
    df_exploded = df_exploded[['index_in_array', column]]
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 6))
    ax = sns.barplot(
        data=df_exploded,
        x='index_in_array',
        y=column,
    )
    plt.title(f"Barplot of Average Operations Per Thread ({implementation_name})", fontsize=14)
    plt.xlabel("Thread Index", fontsize=12)
    plt.ylabel("Average Operations", fontsize=12)
    ax.set_xticklabels(
        [lbl.get_text() if i % 5 == 0 else "" for i, lbl in enumerate(ax.get_xticklabels())]
    )

    plt.tight_layout()
    plt.savefig(f"./plots/benchmark_avg_ops_per_thread_{implementation_name}_64threads.png")
    plt.close()

def main():
    final_df = load_and_prepare_data(base_path="./data/")
    final_df = enrich_df(final_df)

    plot_avg_ops_per_thread(final_df, "global_lock", column='average_operations_per_thread')
    plot_avg_ops_per_thread(final_df, "fine_lock", column='average_operations_per_thread')
    plot_avg_ops_per_thread(final_df, "lock_free", column='average_operations_per_thread')
    plot_throughput(final_df, "101080", "shared", 1, store=True, base_path="./plots/")
    plot_success_ratio_all_implementations(final_df, ('Inserts', 'total_inserts', 'successful_inserts'), "101080", "shared", 1, store=True, base_path="./plots/")
    plot_total_vs_successful_operations_all_implementations(final_df, ('Inserts', 'total_inserts', 'successful_inserts'), "101080", "shared", 1, store=True, base_path="./plots/")
    
   
if __name__ == "__main__":
    main()
