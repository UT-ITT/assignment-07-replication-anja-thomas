import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------
# Load data
# -------------------------------------------------
normal = pd.read_csv("experiment1_thomas_normal_cursor.csv")
bubble = pd.read_csv("experiment1_thomas_bubble_cursor.csv")

# Combine datasets
data = pd.concat([normal, bubble], ignore_index=True)

# Rename cursor labels (optional)
data["cursor"] = data["cursor"].replace({
    "point": "Normal Cursor",
    "bubble": "Bubble Cursor"
})

plt.style.use("ggplot")

# -------------------------------------------------
# Figure 1: Mean Movement Time by Block
# -------------------------------------------------
plt.figure(figsize=(8,5))

for cursor in data["cursor"].unique():
    subset = data[data["cursor"] == cursor]
    means = subset.groupby("block")["movement_time_s"].mean()

    plt.plot(
        means.index,
        means.values,
        marker="o",
        linewidth=2,
        label=cursor
    )

plt.xlabel("Practice Block")
plt.ylabel("Mean Movement Time (s)")
plt.title("Movement Time by Practice Block")
plt.legend()
plt.tight_layout()
plt.show()

# -------------------------------------------------
# Figure 2: Mean Movement Time vs Environment Width (Distractor Density)
# -------------------------------------------------
plt.figure(figsize=(8,5))

for cursor in data["cursor"].unique():
    subset = data[data["cursor"] == cursor]
    # Changed "D" to "EW" to match your actual CSV column
    means = subset.groupby("EW")["movement_time_s"].mean()

    plt.plot(
        means.index,
        means.values,
        marker="o",
        linewidth=2,
        label=cursor
    )

plt.xlabel("Environment Width (EW)")
plt.ylabel("Mean Movement Time (s)")
plt.title("Movement Time vs Environment Width")
plt.legend()
plt.tight_layout()
plt.show()

# -------------------------------------------------
# Figure 3: Error Rate Comparison
# -------------------------------------------------
error_rates = data.groupby("cursor")["errors"].mean()

plt.figure(figsize=(6,5))
plt.bar(error_rates.index, error_rates.values)
plt.ylabel("Mean Error Rate")
plt.title("Error Rate Comparison")
plt.tight_layout()
plt.show()

# -------------------------------------------------
# Figure 4: Overall Mean Movement Time
# -------------------------------------------------
mean_times = data.groupby("cursor")["movement_time_s"].mean()

plt.figure(figsize=(6,5))
plt.bar(mean_times.index, mean_times.values)
plt.ylabel("Mean Movement Time (s)")
plt.title("Overall Cursor Performance")
plt.tight_layout()
plt.show()

# -------------------------------------------------
# Summary Statistics
# -------------------------------------------------
summary = data.groupby("cursor").agg(
    Mean_Time=("movement_time_s", "mean"),
    Std_Time=("movement_time_s", "std"),
    Mean_Error=("errors", "mean"),
    Trials=("movement_time_s", "count")
)

print("\nSummary Statistics")
print(summary)