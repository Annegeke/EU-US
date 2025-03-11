import pandas as pd
import numpy as np
import geopandas as gpd

# File paths
eu_countries_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/EU_countries.csv"
whr_data_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_WHR.csv"
population_data_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP_Pop.csv"

# Step 1: Load EU countries list
eu_countries_df = pd.read_csv(eu_countries_path)
eu_countries = eu_countries_df["ISO3"].tolist()

# Step 2: Load WISE_WHR dataset and filter for EU27 countries only
whr_df = pd.read_csv(whr_data_path)  
whr_eu27_df = whr_df[whr_df["ISO3"].isin(eu_countries)]

# Step 3: Identify unique indicators and years
indicators = whr_eu27_df["Acronym"].unique()
years = whr_eu27_df["Year"].unique()

# Step 4: Check for missing data per indicator and year, ensuring 4/5 threshold
missing_data = []
valid_years = []
for indicator in indicators:
    for year in years:
        data_subset = whr_eu27_df[(whr_eu27_df["Acronym"] == indicator) & (whr_eu27_df["Year"] == year)]
        
        # Check if enough data is available (>= 80% of EU countries)
        if len(data_subset) >= len(eu_countries) * 4 / 5:
            valid_years.append((indicator, year))
        
        # Identify missing countries
        countries_with_data = data_subset["ISO3"].tolist()
        missing_countries = [country for country in eu_countries if country not in countries_with_data]
        
        if missing_countries:
            for country in missing_countries:
                missing_data.append({"ISO3": country, "Year": year, "Indicator": indicator})

# Convert missing data to DataFrame
missing_data_df = pd.DataFrame(missing_data)

# Step 5: Load world shapefile and find neighboring countries
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
eu_shapefile = world[world["iso_a3"].isin(eu_countries)]

# Identify neighboring countries
neighbors_dict = {}
for country in eu_shapefile["iso_a3"]:
    neighbors = eu_shapefile[eu_shapefile.geometry.touches(eu_shapefile[eu_shapefile["iso_a3"] == country].geometry.iloc[0])]["iso_a3"].tolist()
    neighbors_dict[country] = neighbors

# Step 6: Load population data and merge with WHR dataset
population_df = pd.read_csv(population_data_path)
population_df = population_df[population_df["ISO3"].isin(eu_countries)]

# Merge population data with WHR dataset
whr_eu27_pop_df = pd.merge(
    whr_eu27_df, 
    population_df[["ISO3", "Year", "Value"]], 
    on=["ISO3", "Year"], 
    how="inner"
)
whr_eu27_pop_df.rename(columns={"Value_x": "WHR_Value", "Value_y": "Population_Value"}, inplace=True)

# Step 7: Estimate missing data only for valid years
def estimate_missing_data(df, indicator, year, missing_data_df, neighbors_dict):
    missing_countries_year = missing_data_df[(missing_data_df['Year'] == year) & (missing_data_df['Indicator'] == indicator)]
    
    for _, row in missing_countries_year.iterrows():
        country = row['ISO3']
        if country in neighbors_dict:
            neighbors = neighbors_dict[country]
            neighbors_data = df[(df["Acronym"] == indicator) & (df["Year"] == year) & (df["ISO3"].isin(neighbors))]
            
            if len(neighbors_data) > 0:
                # Population-weighted average of neighboring countries
                weighted_sum = (neighbors_data["WHR_Value"] * neighbors_data["Population_Value"]).sum()
                total_population = neighbors_data["Population_Value"].sum()
                weighted_avg = weighted_sum / total_population
                
                # Assign estimated value
                df.loc[(df["ISO3"] == country) & (df["Year"] == year) & (df["Acronym"] == indicator), "WHR_Value"] = weighted_avg
                
    return df

# Apply missing data estimation only for valid years
for indicator, year in valid_years:
    whr_eu27_pop_df = estimate_missing_data(whr_eu27_pop_df, indicator, year, missing_data_df, neighbors_dict)

# Step 8: Compute population-weighted averages per indicator and year (only for valid years)
def calculate_weighted_avg(df, indicator, year):
    data_subset = df[(df["Acronym"] == indicator) & (df["Year"] == year)]
    
    # Weighted sum of indicator values * population
    weighted_sum = (data_subset["WHR_Value"] * data_subset["Population_Value"]).sum()
    
    # Total population
    total_population = data_subset["Population_Value"].sum()
    
    # Compute weighted average
    weighted_avg = weighted_sum / total_population
    return weighted_avg

# Compute results
results = []
for indicator, year in valid_years:
    weighted_avg = calculate_weighted_avg(whr_eu27_pop_df, indicator, year)
    results.append({"Indicator": indicator, "Year": year, "Population_Weighted_Avg": weighted_avg})

# Step 9: Save results
output_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/EU_WHR_estimated.csv"
results_df = pd.DataFrame(results)
results_df.to_csv(output_path, index=False)

print(f"Results saved to {output_path}")
