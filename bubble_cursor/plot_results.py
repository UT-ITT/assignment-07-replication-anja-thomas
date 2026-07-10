import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load the data safely
file_name = "experiment1_bubble_cursor_data.csv"
if not os.path.exists(file_name):
    print(f"Error: Could not find '{file_name}' in the current folder.")
    exit()

df = pd.read_csv(file_name)

# 2. Configure aesthetic style
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# --- PLOT 1: Movement Time vs Effective Width (Crowding) ---
# This shows the core power of the Bubble Cursor
sns.lineplot(
    data=df, 
    x="EffectiveWidth", 
    y="MovementTime", 
    marker="o", 
    linewidth=2.5, 
    errorbar="ci", # Adds a shaded confidence interval band
    ax=axes[0],
    color="#2b7bba"
)
axes[0].set_title("How Crowding Affects Movement Time\n(Smaller Effective Width = More Crowded)", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Effective Width / Distractor Spacing (Pixels)", fontsize=11)
axes[0].set_ylabel("Average Movement Time (Seconds)", fontsize=11)
axes[0].set_xticks([32, 64, 96])

# --- PLOT 2: Movement Time by Distance (Amplitude) & Target Size ---
# This tracks classic Fitts' Law behaviors
sns.barplot(
    data=df,
    x="Amplitude",
    y="MovementTime",
    hue="Width",
    palette="Blues_d",
    ax=axes[1]
)
axes[1].set_title("Movement Time by Distance (Amplitude) & Target Size\n(Larger Amplitude = Further Distance)", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Amplitude / Distance (Pixels)", fontsize=11)
axes[1].set_ylabel("Average Movement Time (Seconds)", fontsize=11)
axes[1].legend(title="Target Physical Width")

# 3. Clean layout math and save out to an image
plt.tight_layout()
output_image = "bubble_cursor_performance.png"
plt.savefig(output_image, dpi=300)

print(f"Success! Charts generated and saved cleanly as '{output_image}'")
plt.show()