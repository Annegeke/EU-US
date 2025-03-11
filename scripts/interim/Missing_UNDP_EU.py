import pandas as pd
import geopandas as gpd

# Step 1: Load EU27 ISO3 codes (only ISO3 column)
eu_countries_df = pd.read_csv(
    '/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/EU_countries.csv')
eu_countries = eu_countries_df['ISO3'].tolist()

# Step 2: Load the WISE_UNDP dataset 
wise_undp_df = pd.read_csv(
    '/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_UNDP.csv')

# Step 3: Ensure that 'Value' column is numeric (coerce errors to NaN)
wise_undp_df['Value'] = pd.to_numeric(wise_undp_df['Value'], errors='coerce')

# Step 4: Create a function to check missing data for each indicator and year
missing_data = []

# List of all years in the dataset (assuming 1990-2020 as the range for now)
all_years = list(range(1990, 2023))

# Step 5: For each indicator and year, check which countries have missing data
for indicator in wise_undp_df['Acronym'].unique():
    for year in all_years:
        # Filter the data for the current indicator and year
        data_subset = wise_undp_df[(wise_undp_df['Acronym'] == indicator) & (wise_undp_df['Year'] == year)]
        
        # Check for missing data (i.e., countries without data for this indicator-year combination)
        countries_with_data = data_subset['ISO3'].tolist()
        
        # List of missing countries for the current indicator-year
        missing_countries = [country for country in eu_countries if country not in countries_with_data]
        
        # If any countries are missing data, add to the missing_data list
        if missing_countries:
            for country in missing_countries:
                missing_data.append({
                    'ISO3': country,
                    'Year': year,
                    'Indicator': indicator
                })

# Step 6: Convert the missing data to a DataFrame
missing_data_df = pd.DataFrame(missing_data)

# Step 7: Load the shapefile for the EU countries (to find neighbors)
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Filter the world dataset for EU countries
eu_shapefile = world[world['iso_a3'].isin(eu_countries)]

# Step 8: Find neighbors for each EU country using GeoPandas
neighbors_dict = {}
for country in eu_shapefile['iso_a3']:
    neighbors = eu_shapefile[eu_shapefile.geometry.touches(eu_shapefile[eu_shapefile['iso_a3'] == country].geometry.iloc[0])]['iso_a3'].tolist()
    neighbors_dict[country] = neighbors

# Step 9: Check the neighboring countries for countries with missing data in 1990-1994
for indicator in missing_data_df['Indicator'].unique():
    for year in range(1990, 1995):  # Focusing only on 1990-1994
        # Filter the missing data for the specific year and indicator
        missing_countries_year = missing_data_df[(missing_data_df['Year'] == year) & (missing_data_df['Indicator'] == indicator)]
        
        # For each missing country in this year and indicator, print its neighbors
        for _, row in missing_countries_year.iterrows():
            country = row['ISO3']
            neighbors = neighbors_dict.get(country, [])
            print(f"Country: {country}, Year: {year}, Missing Data: Yes, Neighbors: {', '.join(neighbors)}")


# Step 10: Save the missing data summary to a CSV file
output_missing_data_path = '/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/interim/Missing_UNDP_EU.csv'
missing_data_df.to_csv(output_missing_data_path, index=False)

# Step 11: Display the missing data summary
print(f"Missing data summary saved to {output_missing_data_path}")
print(missing_data_df.head())