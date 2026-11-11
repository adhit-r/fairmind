import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Sequence, Tuple


def _subplot_shape(num_cols: int) -> Tuple[int, int]:
    """Return ``(nrows, ncols)`` for ``num_cols`` histograms.

    A single series uses one axes. Two or three series stay on one row.
    Larger feature sets use extra rows and widen to three columns, or four
    once there are more than 15 series, so the figure stays readable.
    """
    if num_cols <= 3:
        return 1, num_cols
    if num_cols == 4:
        return 2, 2
    ncols = 3 if num_cols <= 15 else 4
    nrows = (num_cols + ncols - 1) // ncols
    return nrows, ncols


def plot_numeric_distributions(
    df: pd.DataFrame,
    columns: Optional[Sequence[str]] = None,
    bins: int = 30,
    show: bool = True
) -> Tuple[plt.Figure, List[plt.Axes]]:
    """
    Plot distribution histograms for numeric columns in a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing data.
    columns : sequence of str, optional
        Specific numeric columns to plot. If None, all numeric columns are used.
        Every name must exist in ``df.columns`` and refer to a numeric column.
    bins : int, default=30
        Number of bins for the histogram.
    show : bool, default=True
        Whether to display the plot using plt.show(). Set this to False when
        no GUI is available.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The created matplotlib figure.
    axes : list of matplotlib.axes.Axes
        One axes per plotted column, in column order. Unused grid cells are
        not included.

    Raises
    ------
    TypeError
        If df is not a pandas DataFrame, or columns is a string rather than
        a sequence of column names.
    ValueError
        If the DataFrame is empty, no numeric columns are available, a
        requested column does not exist, or a requested column is not numeric.

    Notes
    -----
    Headless and CI usage
        ``show=True`` calls ``plt.show()``, which needs an interactive backend
        and a display. In CI, notebooks running as scripts, or any other
        non-GUI environment, pass ``show=False`` and select a non-interactive
        Matplotlib backend *before* importing ``matplotlib.pyplot``::

            import matplotlib
            matplotlib.use("Agg")  # must run before importing pyplot
            import pandas as pd
            from apps.ml.visualizations import plot_numeric_distributions

            fig, axes = plot_numeric_distributions(df, show=False)
            fig.savefig("distributions.png")
            plt.close(fig)

        ``Agg`` renders to files only and does not open a window. Closing the
        figure releases memory when many plots are created in one process.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()
        if not columns:
            raise ValueError("No numeric columns available for plotting.")
    else:
        if isinstance(columns, str):
            raise TypeError(
                "columns must be a sequence of column names, not a single string. "
                f"Got {columns!r}."
            )
        try:
            columns = list(columns)
        except TypeError as exc:
            raise TypeError(
                "columns must be a sequence of column names."
            ) from exc
        if not columns:
            raise ValueError("columns must contain at least one column name.")

        missing = [col for col in columns if col not in df.columns]
        if missing:
            raise ValueError(
                "Requested column(s) not found in DataFrame: "
                f"{missing}. Available columns: {list(df.columns)}."
            )

        non_numeric = [
            col for col in columns
            if not pd.api.types.is_numeric_dtype(df[col])
        ]
        if non_numeric:
            raise ValueError(
                "Requested column(s) are not numeric and cannot be plotted "
                f"as distributions: {non_numeric}. "
                "Choose numeric columns, or omit columns to plot every numeric feature."
            )

    num_cols = len(columns)
    nrows, ncols = _subplot_shape(num_cols)
    fig, axes_grid = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(6 * ncols, 4 * nrows),
        squeeze=False,
    )
    axes = axes_grid.ravel().tolist()

    for ax, col in zip(axes, columns):
        ax.hist(df[col].dropna(), bins=bins)
        ax.set_title(f"Distribution of {col}")
        ax.set_xlabel(str(col))
        ax.set_ylabel("Frequency")

    for ax in axes[num_cols:]:
        fig.delaxes(ax)

    fig.tight_layout()

    if show:
        plt.show()

    return fig, axes[:num_cols]
