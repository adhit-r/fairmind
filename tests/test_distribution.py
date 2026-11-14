import matplotlib
matplotlib.use("Agg")

import pandas as pd
import pytest

from apps.ml.visualizations import plot_numeric_distributions as exported_plot
from apps.ml.visualizations.data_distribution import (
    plot_numeric_distributions
)


def _grid_shape(ax):
    spec = ax.get_subplotspec().get_gridspec()
    return spec.nrows, spec.ncols


def test_plot_numeric_distributions_runs():
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [10, 20, 30, 40, 50]
    })

    fig, axes = plot_numeric_distributions(df, show=False)

    assert fig is not None
    assert len(axes) == 2
    assert len(fig.axes) == 2
    assert _grid_shape(axes[0]) == (1, 2)

    # Should run without raising any exception
    fig2, _ = plot_numeric_distributions(df, show=False)
    matplotlib.pyplot.close(fig)
    matplotlib.pyplot.close(fig2)


def test_plot_numeric_distributions_invalid_input():
    with pytest.raises(TypeError):
        plot_numeric_distributions("not a dataframe")


def test_plot_numeric_distributions_empty_dataframe():
    with pytest.raises(ValueError):
        plot_numeric_distributions(pd.DataFrame())


def test_plot_numeric_distributions_missing_column():
    df = pd.DataFrame({"age": [1, 2, 3], "income": [10, 20, 30]})

    with pytest.raises(ValueError, match=r"not found") as exc_info:
        plot_numeric_distributions(df, columns=["age", "salary"], show=False)

    message = str(exc_info.value)
    assert "salary" in message
    assert "age" in message
    assert "income" in message


def test_plot_numeric_distributions_non_numeric_column():
    df = pd.DataFrame({
        "age": [1, 2, 3],
        "city": ["Delhi", "Mumbai", "Chennai"],
    })

    with pytest.raises(ValueError, match="not numeric") as exc_info:
        plot_numeric_distributions(df, columns=["age", "city"], show=False)

    assert "city" in str(exc_info.value)


def test_plot_numeric_distributions_empty_column_list():
    df = pd.DataFrame({"age": [1, 2, 3]})

    with pytest.raises(ValueError, match="at least one"):
        plot_numeric_distributions(df, columns=[], show=False)


def test_plot_numeric_distributions_string_columns_rejected():
    df = pd.DataFrame({"age": [1, 2, 3]})

    with pytest.raises(TypeError, match="sequence of column names"):
        plot_numeric_distributions(df, columns="age", show=False)


def test_plot_numeric_distributions_single_column_layout():
    df = pd.DataFrame({"age": [1, 2, 3, 4]})

    fig, axes = plot_numeric_distributions(df, columns=["age"], show=False)
    try:
        assert len(axes) == 1
        assert len(fig.axes) == 1
        assert _grid_shape(axes[0]) == (1, 1)
    finally:
        matplotlib.pyplot.close(fig)


def test_plot_numeric_distributions_two_column_layout():
    df = pd.DataFrame({
        "age": [1, 2, 3, 4],
        "income": [10, 20, 30, 40],
    })

    fig, axes = plot_numeric_distributions(df, show=False)
    try:
        assert len(axes) == 2
        assert len(fig.axes) == 2
        assert _grid_shape(axes[0]) == (1, 2)
    finally:
        matplotlib.pyplot.close(fig)


def test_plot_numeric_distributions_many_columns_layout():
    df = pd.DataFrame({f"feature_{i}": list(range(6)) for i in range(7)})

    fig, axes = plot_numeric_distributions(df, show=False)
    try:
        assert len(axes) == 7
        assert len(fig.axes) == 7
        assert _grid_shape(axes[0]) == (3, 3)
    finally:
        matplotlib.pyplot.close(fig)


def test_plot_numeric_distributions_skips_non_numeric_by_default():
    df = pd.DataFrame({
        "age": [1, 2, 3, 4],
        "city": ["a", "b", "c", "d"],
    })

    fig, axes = plot_numeric_distributions(df, show=False)
    try:
        assert len(axes) == 1
        assert len(fig.axes) == 1
    finally:
        matplotlib.pyplot.close(fig)


def test_plot_numeric_distributions_no_numeric_columns():
    df = pd.DataFrame({"city": ["a", "b", "c"]})

    with pytest.raises(ValueError, match="No numeric columns"):
        plot_numeric_distributions(df, show=False)


def test_plot_numeric_distributions_exported_from_package():
    assert exported_plot is plot_numeric_distributions


def test_plot_numeric_distributions_docstring_covers_headless_usage():
    doc = plot_numeric_distributions.__doc__
    assert "Agg" in doc
    assert "show=False" in doc
    assert "non-GUI" in doc or "CI" in doc
