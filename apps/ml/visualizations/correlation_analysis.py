import matplotlib.pyplot as plt
import seaborn as sns

def plot_correlation_matrix(df):
    """
    Plot correlation heatmap for numerical features.
    """
    corr = df.corr(numeric_only=True)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5
    )
    plt.title("Feature Correlation Matrix")
    plt.tight_layout()
    plt.show()