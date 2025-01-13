from plot_utils import load_and_prepare_data, plot_throughput
import pandas as pd

def main():
    final_df = load_and_prepare_data()

    # Separate DataFrames for specific conditions
    df_sequential_101080 = final_df[
        (final_df['implementation_name'] == 'sequential') &
        (final_df['op_mix'] == "101080")
    ].copy()
    df_sequential_101080['range_type'] = 'disjoint'

    df_sequential_404020 = final_df[
        (final_df['implementation_name'] == 'sequential') &
        (final_df['op_mix'] == "404020")
    ].copy()
    df_sequential_404020['range_type'] = 'disjoint'

    # Concatenate the modified DataFrames back into final_df
    final_df = pd.concat([final_df, df_sequential_404020, df_sequential_101080], ignore_index=True)

    plot_throughput(final_df, '101080', 'shared', store=True)
    plot_throughput(final_df, '101080', 'disjoint', store=True)
    plot_throughput(final_df, '404020', 'shared', store=True)
    plot_throughput(final_df, '404020', 'disjoint', store=True)

if __name__ == "__main__":
    main()