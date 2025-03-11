import pandas as pd
import numpy as np
import geopandas as gpd

# Step 1: Load EU27 ISO3 codes
eu_countries_df = pd.read_csv(
    "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/EU_countries.csv"
)
eu_countries = eu_countries_df["ISO3"].tolist()

# Step 2: Load the WISE_UNDP dataset and filter for EU27 countries only
wise_undp_df = pd.read_csv(
    "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP.csv"
)

# Step 3: Filter for EU27 countries
wise_undp_eu27_df = wise_undp_df[wise_undp_df["ISO3"].isin(eu_countries)]

# Step 4: Check for missing data for each indicator and year
indicators = wise_undp_eu27_df["Acronym"].unique()
years = wise_undp_eu27_df["Year"].unique()

# Load population data
population_df = pd.read_csv(
    "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP_Pop.csv"
)
population_df = population_df[population_df["ISO3"].isin(eu_countries)]  # Filter for EU27

missing_data = []
valid_years = []

for indicator in indicators:
    for year in years:
        data_subset = wise_undp_eu27_df[
            (wise_undp_eu27_df["Acronym"] == indicator)
            & (wise_undp_eu27_df["Year"] == year)
        ]
        
        # Calculate total population of EU27 countries for this year
        total_eu_population = population_df[population_df["Year"] == year]["Value"].sum()
        
        # Calculate population of countries with available data
        available_population = population_df[
            (population_df["Year"] == year)
            & (population_df["ISO3"].isin(data_subset["ISO3"]))
        ]["Value"].sum()
        
        # Check if enough data is available (more than 4/5 of EU population)
        if available_population >= total_eu_population * 4 / 5:
            valid_years.append((indicator, year))
        
        # Check which countries have missing data to prepare for estimation
        countries_with_data = data_subset["ISO3"].tolist()
        missing_countries = [country for country in eu_countries if country not in countries_with_data]
        
        if missing_countries:
            for country in missing_countries:
                missing_data.append({
                    'ISO3': country,
                    'Year': year,
                    'Indicator': indicator
                })

# Step 5: Convert missing data to a DataFrame
missing_data_df = pd.DataFrame(missing_data)

# Step 6: Load the shapefile for the EU countries (to find neighbors)
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
eu_shapefile = world[world['iso_a3'].isin(eu_countries)]

# Step 7: Find neighbors for each EU country using GeoPandas
neighbors_dict = {}
for country in eu_shapefile['iso_a3']:
    neighbors = eu_shapefile[eu_shapefile.geometry.touches(eu_shapefile[eu_shapefile['iso_a3'] == country].geometry.iloc[0])]['iso_a3'].tolist()
    neighbors_dict[country] = neighbors

# Step 8: Merge population data with the UNDP dataset
wise_undp_eu27_pop_df = pd.merge(
    wise_undp_eu27_df, 
    population_df[["ISO3", "Year", "Value"]], 
    on=["ISO3", "Year"], 
    how="inner"
)
wise_undp_eu27_pop_df.rename(columns={"Value_x": "Indicator_Value", "Value_y": "Population_Value"}, inplace=True)

# Step 9: Estimate missing data using population-weighted average from neighboring countries
def estimate_missing_data(df, indicator, year, missing_data_df, neighbors_dict):
    missing_countries_year = missing_data_df[(missing_data_df['Year'] == year) & (missing_data_df['Indicator'] == indicator)]
    
    for _, row in missing_countries_year.iterrows():
        country = row['ISO3']
        if country in neighbors_dict:
            neighbors = neighbors_dict[country]
            neighbors_data = df[(df["Acronym"] == indicator) & (df["Year"] == year) & (df["ISO3"].isin(neighbors))]
            
            if len(neighbors_data) > 0:
                # Calculate population-weighted average for the neighbors
                weighted_sum = (neighbors_data["Indicator_Value"] * neighbors_data["Population_Value"]).sum()
                total_population = neighbors_data["Population_Value"].sum()
                weighted_avg = weighted_sum / total_population
                
                # Estimate the missing value based on the neighbors' weighted average
                df.loc[(df["ISO3"] == country) & (df["Year"] == year) & (df["Acronym"] == indicator), "Indicator_Value"] = weighted_avg
                
    return df

# Step 10: Estimate missing data for valid years (only for years where more than 4/5 of the population data is available)
for indicator, year in valid_years:
    wise_undp_eu27_pop_df = estimate_missing_data(wise_undp_eu27_pop_df, indicator, year, missing_data_df, neighbors_dict)

# Step 11: Calculate population-weighted average for each indicator and year
def calculate_weighted_avg(df, indicator, year):
    data_subset = df[(df["Acronym"] == indicator) & (df["Year"] == year)]
    
    # Calculate weighted sum of indicator values * population
    weighted_sum = (data_subset["Indicator_Value"] * data_subset["Population_Value"]).sum()
    
    # Calculate total population
    total_population = data_subset["Population_Value"].sum()
    
    # Calculate population-weighted average
    weighted_avg = weighted_sum / total_population
    return weighted_avg

# Step 12: Compute results
results = []
for indicator, year in valid_years:
    weighted_avg = calculate_weighted_avg(wise_undp_eu27_pop_df, indicator, year)
    results.append({"Indicator": indicator, "Year": year, "Population_Weighted_Avg": weighted_avg})

# Step 13: Save results
results_df = pd.DataFrame(results)
output_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/EU_UNDP_estimated.csv"
results_df.to_csv(output_path, index=False)

print(f"Results saved to {output_path}")
