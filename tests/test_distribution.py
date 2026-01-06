import pandas as pd
import pytest

from apps.backend.utils.visualization.data_distribution import (
    plot_numeric_distributions
)


def test_plot_numeric_distributions_runs():
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [10, 20, 30, 40, 50]
    })
    
    fig, axes = plot_numeric_distributions(df, show=False)

    assert fig is not None
    assert len(axes) > 0


    # Should run without raising any exception
    plot_numeric_distributions(df, show=False)


def test_plot_numeric_distributions_invalid_input():
    with pytest.raises(TypeError):
        plot_numeric_distributions("not a dataframe")


def test_plot_numeric_distributions_empty_dataframe():
    with pytest.raises(ValueError):
        plot_numeric_distributions(pd.DataFrame())
