import pandas as pd

# File paths
EU_UNDP_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/EU_UNDP_estimated.csv"
US_UNDP_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP.csv"
EU_WHR_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/EU_WHR_estimated.csv"
US_WHR_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_WHR.csv"
WID_GDP_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WID_NI_GDP.csv"
OUTPUT_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/INDEX_EU_US.csv"

# Load and process UNDP data
EU_UNDP = pd.read_csv(EU_UNDP_FILE)
EU_UNDP = EU_UNDP[EU_UNDP["Indicator"] == "UNDP-HDI"][["Year", "Population_Weighted_Avg"]]
EU_UNDP.rename(columns={"Population_Weighted_Avg": "HDI_EU"}, inplace=True)

US_UNDP = pd.read_csv(US_UNDP_FILE)
US_UNDP = US_UNDP[(US_UNDP["ISO3"] == "USA") & (US_UNDP["Acronym"] == "UNDP-HDI")][["Year", "Value"]]
US_UNDP.rename(columns={"Value": "HDI_US"}, inplace=True)

# Load and process WHR data
EU_WHR = pd.read_csv(EU_WHR_FILE)
EU_WHR = EU_WHR[EU_WHR["Indicator"] == "WHR-LS"][["Year", "Population_Weighted_Avg"]]
EU_WHR.rename(columns={"Population_Weighted_Avg": "LS_EU"}, inplace=True)

US_WHR = pd.read_csv(US_WHR_FILE)
US_WHR = US_WHR[(US_WHR["ISO3"] == "USA") & (US_WHR["Acronym"] == "WHR-LS")][["Year", "Value"]]
US_WHR.rename(columns={"Value": "LS_US"}, inplace=True)

# Load and process GDP data
WID_GDP = pd.read_csv(WID_GDP_FILE, skiprows=1)
WID_GDP = WID_GDP.iloc[:, [1, -2, -1]]  # Keep Year and last two columns
WID_GDP.columns = ["Year", "GDPpc_US", "GDPpc_EU"]
WID_GDP = WID_GDP[WID_GDP["Year"] >= 1990]

# Create a DataFrame with all years from 1990
all_years_df = pd.DataFrame({"Year": range(1990, 2025)})  # Adjust to the maximum year in your dataset

# Merge datasets with all years
EU_UNDP = all_years_df.merge(EU_UNDP, on="Year", how="left")
US_UNDP = all_years_df.merge(US_UNDP, on="Year", how="left")
EU_WHR = all_years_df.merge(EU_WHR, on="Year", how="left")
US_WHR = all_years_df.merge(US_WHR, on="Year", how="left")
WID_GDP = all_years_df.merge(WID_GDP, on="Year", how="left")

# Merge the datasets together
merged_df = EU_UNDP.merge(US_UNDP, on="Year", how="inner")
merged_df = merged_df.merge(EU_WHR, on="Year", how="inner")
merged_df = merged_df.merge(US_WHR, on="Year", how="inner")
merged_df = merged_df.merge(WID_GDP, on="Year", how="inner")

# Compute indices
merged_df["Index_HDI"] = (merged_df["HDI_EU"] / merged_df["HDI_US"]) * 100
merged_df["Index_LS"] = (merged_df["LS_EU"] / merged_df["LS_US"]) * 100
merged_df["Index_GDPpc"] = (merged_df["GDPpc_EU"] / merged_df["GDPpc_US"]) * 100

# Save to CSV
merged_df.to_csv(OUTPUT_FILE, index=False)

print("INDEX_EU_US.csv successfully created")

# Step 6: Create figure of indices 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl

# File path
INPUT_FILE = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/INDEX_EU_US2.csv"

# Load data
df = pd.read_csv(INPUT_FILE)

# Set font to Roboto
mpl.rcParams['font.family'] = 'Roboto'  # This sets the default font to Roboto
mpl.rcParams['axes.titlesize'] = 18  # Title size
mpl.rcParams['axes.labelsize'] = 16  # Axis labels size
mpl.rcParams['legend.fontsize'] = 14  # Legend font size

# Set style for a clean, modern design with a white background and light gridlines
sns.set_theme(style="whitegrid", rc={
    "grid.linestyle": "-",  # solid gridlines
    "grid.color": "#f0f0f0",  # very light grey
    "axes.facecolor": "white", 
    "figure.facecolor": "white"  # Ensures the background is white
})

plt.figure(figsize=(10, 6))

# Custom colors for a softer, cleaner design
colors = {
    "Index_HDI": "#80C0D6",   # Blue
    "Index_LS": "#f5b865",    # Orange
    "Index_GDPpc": "#ced660"  # Green
}

# Plot lines with Seaborn
sns.lineplot(data=df, x="Year", y="Index_HDI", label="HDI", color=colors["Index_HDI"], linewidth=2)
sns.lineplot(data=df, x="Year", y="Index_LS", label="Life Satisfaction", color=colors["Index_LS"], linewidth=2)
sns.lineplot(data=df, x="Year", y="Index_GDPpc", label="GDP per Capita", color=colors["Index_GDPpc"], linewidth=2)

# Set x-axis to start from 1990 and y-axis to go until 110
plt.xlim(1990, 2023)
plt.ylim(0, 110)  # Set the y-axis to go until 110

# Add a darker grey line at y = 100
plt.axhline(y=100, color="#7f7f7f", linestyle="-", linewidth=1)  # Dark grey line at y=100

# Formatting
plt.xlabel("Year", fontsize=16)
plt.ylabel("Index (US = 100)", fontsize=16)
plt.title("EU Performance Relative to US (US=100)", fontsize=18, fontweight="bold")

# Customizing legend
plt.legend(frameon=False, loc="best")

# Improve tick readability
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)

# Remove the top and right spines (box around the graph)
sns.despine(top=True, right=True)

# Ensure only the x-axis line remains visible (bottom spine)
plt.gca().spines['bottom'].set_linewidth(1)

# Remove vertical gridlines (show only horizontal gridlines)
plt.grid(axis='x')

# Save as high-resolution PNG
plt.savefig("/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/paper/visuals/EU_US_Index_Graph.png", dpi=300, bbox_inches="tight")

# Show the plot
plt.show()
