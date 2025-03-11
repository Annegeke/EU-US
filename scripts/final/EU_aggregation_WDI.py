import pandas as pd
import numpy as np
import geopandas as gpd

# File paths
eu_countries_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/EU_countries.csv"
wdi_data_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WDI_Governance.csv"
population_data_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP_Pop.csv"

# Load EU countries
eu_countries_df = pd.read_csv(eu_countries_path)
eu_countries = eu_countries_df["ISO3"].tolist()

# Load WDI Governance dataset
wdi_df = pd.read_csv(wdi_data_path)

# Reshape WDI data to long format
wdi_df_long = wdi_df.melt(id_vars=["Country Name", "Country Code", "Series Name", "Series Code"], 
                           var_name="Year", value_name="Value")
wdi_df_long["Year"] = wdi_df_long["Year"].str.extract(r'(\d{4})').astype(int)

# Handle the WDI file where missing values are represented by '..'
wdi_df_long['Value'] = wdi_df_long['Value'].replace('..', np.nan)  # Replace '..' with NaN
wdi_df_long['Value'] = pd.to_numeric(wdi_df_long['Value'], errors='coerce')  # Convert to numeric

# Load population data
population_df = pd.read_csv(population_data_path)
population_df = population_df[population_df["ISO3"].isin(eu_countries)]

# Rename and convert population values
population_df = population_df.rename(columns={"Value": "Population_Value"})

# Convert from millions to absolute numbers
population_df["Population_Value"] *= 1e6  

# Merge WDI data with population data
wdi_eu27_df = pd.merge(wdi_df_long, population_df, left_on=["Country Code", "Year"], right_on=["ISO3", "Year"], how="inner")

# Identify unique indicators and years
indicators = wdi_eu27_df["Series Code"].unique()
years = wdi_eu27_df["Year"].unique()

# Compute valid years based on 4/5 of total EU population
valid_years = []
missing_data = []

# Calculate total EU population per year
total_population_per_year = population_df.groupby("Year")["Population_Value"].sum()

for indicator in indicators:
    for year in years:
        # Filter data for specific indicator and year
        data_subset = wdi_eu27_df[(wdi_eu27_df["Series Code"] == indicator) & (wdi_eu27_df["Year"] == year)]
        
        reported_population = data_subset["Population_Value"].sum()
        total_population = total_population_per_year.get(year, 0)
        
        # Check if 4/5 of the total EU population is reported
        if reported_population >= total_population * 4 / 5:
            valid_years.append((indicator, year))
        
        # Track missing countries (where the value is NaN for a given country)
        missing_countries = [c for c in eu_countries if c not in data_subset[data_subset["Value"].notna()]["Country Code"].tolist()]
        for country in missing_countries:
            missing_data.append({"ISO3": country, "Year": year, "Indicator": indicator})

missing_data_df = pd.DataFrame(missing_data)
output_path_missing = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/interim/Missing_WDI_gov.csv"
missing_data_df.to_csv(output_path_missing, index=False)

# Create a neighbor dictionary for each country in the EU (for the missing data estimation)
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
eu_shapefile = world[world["iso_a3"].isin(eu_countries)]

neighbors_dict = {}
for country in eu_shapefile["iso_a3"]:
    neighbors = eu_shapefile[eu_shapefile.geometry.touches(eu_shapefile[eu_shapefile["iso_a3"] == country].geometry.iloc[0])]["iso_a3"].tolist()
    neighbors_dict[country] = neighbors

# Function to estimate missing data based on neighboring countries
def estimate_missing_data(df, indicator, year, missing_data_df, neighbors_dict):
    missing_countries_year = missing_data_df[(missing_data_df['Year'] == year) & (missing_data_df['Indicator'] == indicator)]
    for _, row in missing_countries_year.iterrows():
        country = row['ISO3']
        if country in neighbors_dict:
            neighbors = neighbors_dict[country]
            neighbors_data = df[(df["Series Code"] == indicator) & (df["Year"] == year) & (df["Country Code"].isin(neighbors))]
            if len(neighbors_data) > 0:
                # Population-weighted average of neighboring countries
                weighted_sum = (neighbors_data["Value"] * neighbors_data["Population_Value"]).sum()
                total_population = neighbors_data["Population_Value"].sum()
                weighted_avg = weighted_sum / total_population
                # Assign estimated value
                df.loc[(df["Country Code"] == country) & (df["Year"] == year) & (df["Series Code"] == indicator), "Value"] = weighted_avg
    return df

# Apply missing data estimation for valid years
for indicator, year in valid_years:
    wdi_eu27_df = estimate_missing_data(wdi_eu27_df, indicator, year, missing_data_df, neighbors_dict)

# Compute population-weighted averages per indicator and year
def calculate_weighted_avg(df, indicator, year):
    data_subset = df[(df["Series Code"] == indicator) & (df["Year"] == year)]
    weighted_sum = (data_subset["Value"] * data_subset["Population_Value"]).sum()
    total_population = data_subset["Population_Value"].sum()
    weighted_avg = weighted_sum / total_population
    return weighted_avg

# Calculate and store the results
results = []
for indicator, year in valid_years:
    weighted_avg = calculate_weighted_avg(wdi_eu27_df, indicator, year)
    results.append({"Indicator": indicator, "Year": year, "Population_Weighted_Avg": weighted_avg})

# Save results to CSV
output_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/EU_WDI_estimated.csv"
results_df = pd.DataFrame(results)
results_df.to_csv(output_path, index=False)

print(f"Results saved to {output_path}")
