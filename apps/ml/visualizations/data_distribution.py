import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple


def plot_numeric_distributions(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    bins: int = 30,
    show: bool = True
) -> Tuple[plt.Figure, list]:
    """
    Plot distribution histograms for numeric columns in a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing data.
    columns : list of str, optional
        Specific numeric columns to plot. If None, all numeric columns are used.
    bins : int, default=30
        Number of bins for the histogram.
    show : bool, default=True
        Whether to display the plot using plt.show().

    Returns
    -------
    fig : matplotlib.figure.Figure
        The created matplotlib figure.
    axes : list
        List of matplotlib axes objects.

    Raises
    ------
    TypeError
        If df is not a pandas DataFrame.
    ValueError
        If DataFrame is empty or contains no numeric columns.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if not columns:
        raise ValueError("No numeric columns available for plotting.")

    num_cols = len(columns)
    fig, axes = plt.subplots(
        nrows=(num_cols + 1) // 2,
        ncols=2,
        figsize=(12, 4 * ((num_cols + 1) // 2))
    )

    axes = axes.flatten()

    for idx, col in enumerate(columns):
        axes[idx].hist(df[col].dropna(), bins=bins)
        axes[idx].set_title(f"Distribution of {col}")
        axes[idx].set_xlabel(col)
        axes[idx].set_ylabel("Frequency")

    for j in range(idx + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()

    if show:
        plt.show()

    return fig, axes

