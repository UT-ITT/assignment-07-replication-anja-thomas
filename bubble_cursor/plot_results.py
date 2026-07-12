import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==========================================
# 1. Load and Prepare the Data
# ==========================================

# Load your specific CSV files
df_normal = pd.read_csv("experiment2_thomas_normal_cursor.csv")
df_bubble = pd.read_csv("experiment2_thomas_bubble_cursor.csv")

# Combine the datasets into one DataFrame
df = pd.concat([df_normal, df_bubble], ignore_index=True)

# ==========================================
# 2. Calculate Derived Variables
# ==========================================
# The Fitts' Law Index of Difficulty (ID) is calculated differently depending on the cursor type.
# For the normal cursor: ID = log2(A/W + 1)
# For the bubble cursor: ID = log2(A/EW + 1)
# Since you have the EW_ratio (EW/W), we can calculate EW as (EW_ratio * W)

def calculate_id(row):
    # Check if this row is for the normal cursor (case-insensitive check)
    if 'normal' in str(row['cursor']).lower():
        return np.log2((row['A'] / row['W']) + 1)
    else:
        # Calculate Effective Width (EW) for the bubble cursor
        effective_width = row['EW_ratio'] * row['W']
        return np.log2((row['A'] / effective_width) + 1)

# Apply the ID calculation to the dataframe
df['ID'] = df.apply(calculate_id, axis=1)

# Set global plotting style
sns.set_theme(style="whitegrid")
# Standardize cursor names in case they differ slightly in the CSV, or just rely on the palette mapping
colors = {c: '#8B0000' if 'normal' in str(c).lower() else '#2E8B57' for c in df['cursor'].unique()}

# ==========================================
# 3. Generate Replicated Figures
# ==========================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# --- Plot 1: Movement Time by EW/W (Replicates Figure 10) ---
sns.pointplot(
    data=df, 
    x='EW_ratio', 
    y='movement_time_s', 
    hue='cursor', 
    ax=axes[0],
    palette=colors,
    markers=['s', 'd'],
    errorbar=None
)
axes[0].set_title('Movement Time by EW/W Ratio')
axes[0].set_xlabel('EW / W')
axes[0].set_ylabel('Movement Time (seconds)')

# --- Plot 2: Movement Time by Density (Replicates Figure 11) ---
sns.pointplot(
    data=df, 
    x='D', 
    y='movement_time_s', 
    hue='cursor', 
    ax=axes[1],
    palette=colors,
    markers=['s', 'd'],
    errorbar=None
)
axes[1].set_title('Movement Time by Distracter Density')
axes[1].set_xlabel('Intermediate Target Density (D)')
axes[1].set_ylabel('Movement Time (seconds)')

# --- Plot 3: Movement Time by Index of Difficulty (Replicates Figure 13) ---
sns.scatterplot(
    data=df, 
    x='ID', 
    y='movement_time_s', 
    hue='cursor', 
    ax=axes[2],
    palette=colors,
    alpha=0.6,
    s=60
)

# Add linear regression lines for Fitts' Law for each cursor type
for cursor_name in df['cursor'].unique():
    is_normal = 'normal' in str(cursor_name).lower()
    sns.regplot(
        data=df[df['cursor'] == cursor_name], 
        x='ID', 
        y='movement_time_s', 
        ax=axes[2], 
        scatter=False, 
        color='#8B0000' if is_normal else '#2E8B57',
        line_kws={'label': f'{cursor_name} Fit', 'linestyle': '-' if is_normal else '--'}
    )

axes[2].set_title('Movement Time by Index of Difficulty (Fitts\' Law)')
axes[2].set_xlabel('Index of Difficulty (bits)')
axes[2].set_ylabel('Movement Time (seconds)')
axes[2].legend()

# Adjust layout and display
plt.tight_layout()
plt.show()