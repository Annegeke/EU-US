import pandas as pd
import numpy as np

# Step 1: Load EU27 ISO3 codes (only ISO3 column)
eu_countries_df = pd.read_csv('/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/EU_countries.csv')
eu_countries = eu_countries_df['ISO3'].tolist()

# Step 2: Load the WISE_UNDP dataset and filter for EU27 countries only
wise_undp_df = pd.read_csv('/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP.csv')
wise_undp_eu27_df = wise_undp_df[wise_undp_df['ISO3'].isin(eu_countries)]

# Step 3: Check for missing data for each indicator and year (ensure 100% data for EU27)
indicators = wise_undp_eu27_df['Acronym'].unique()
years = wise_undp_eu27_df['Year'].unique()

valid_years = []
for indicator in indicators:
    for year in years:
        data_subset = wise_undp_eu27_df[(wise_undp_eu27_df['Acronym'] == indicator) & (wise_undp_eu27_df['Year'] == year)]
        
        # Ensure all EU27 countries have data for this indicator and year
        if len(data_subset) == len(eu_countries):  # Check if there are exactly 27 countries with data
            valid_years.append((indicator, year))

print("Valid year-indicator combinations:", valid_years)

# Step 4: Load population data and merge with WISE_UNDP dataset for EU27 countries
population_df = pd.read_csv('/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP_Pop.csv')
population_df = population_df[population_df['ISO3'].isin(eu_countries)]  # Filter for EU27 countries

# Merge population data with the UNDP dataset
wise_undp_eu27_pop_df = pd.merge(wise_undp_eu27_df, population_df[['ISO3', 'Year', 'Value']], on=['ISO3', 'Year'], how='inner')
wise_undp_eu27_pop_df.rename(columns={'Value_x': 'Indicator_Value', 'Value_y': 'Population_Value'}, inplace=True)

# Step 5: Calculate population-weighted average for each indicator and year
def calculate_weighted_avg(df, indicator, year):
    data_subset = df[(df['Acronym'] == indicator) & (df['Year'] == year)]
    
    # Calculate weighted sum of indicator values * population
    weighted_sum = (data_subset['Indicator_Value'] * data_subset['Population_Value']).sum()
    
    # Calculate total population
    total_population = data_subset['Population_Value'].sum()
    
    # Calculate population-weighted average
    weighted_avg = weighted_sum / total_population
    return weighted_avg

# Dictionary to store the results
results = []

# Calculate the weighted averages for valid year-indicator combinations
for indicator, year in valid_years:
    weighted_avg = calculate_weighted_avg(wise_undp_eu27_pop_df, indicator, year)
    results.append({
        'Indicator': indicator,
        'Year': year,
        'Population_Weighted_Avg': weighted_avg
    })

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Step 6: Save the results to a new CSV file
output_path = '/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/processed/EU_UNDP_basic.csv'
results_df.to_csv(output_path, index=False)

print(f"Results saved to {output_path}")
