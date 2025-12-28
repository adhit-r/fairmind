import matplotlib.pyplot as plt
import pandas as pd

def plot_feature_importance(feature_names, importances):
    """
    Plot feature importance bar chart.
    """
    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)

    plt.figure(figsize=(8, 5))
    plt.barh(
        importance_df["Feature"],
        importance_df["Importance"]
    )
    plt.xlabel("Importance Score")
    plt.title("Feature Importance")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()