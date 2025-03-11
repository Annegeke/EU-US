import pandas as pd

# File paths
eu_countries_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/EU_countries.csv"
whr_data_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/raw/WISE_WHR.csv"

# Load EU countries list
eu_countries_df = pd.read_csv(eu_countries_path)
eu_countries = eu_countries_df["ISO3"].tolist()

# Load WHR dataset 
whr_df = pd.read_csv(whr_data_path)

# Filter for EU27 countries only
whr_eu27_df = whr_df[whr_df["ISO3"].isin(eu_countries)]

# Identify unique indicators
indicators = whr_eu27_df["Acronym"].unique()

# Identify missing years per indicator
missing_data = []
for indicator in indicators:
    indicator_df = whr_eu27_df[whr_eu27_df["Acronym"] == indicator]
    years_available = indicator_df["Year"].unique()
    
    # Expected years (based on min/max years in the dataset)
    expected_years = list(range(min(years_available), max(years_available) + 1))
    
    for country in eu_countries:
        country_years = indicator_df[indicator_df["ISO3"] == country]["Year"].unique()
        missing_years = [year for year in expected_years if year not in country_years]
        
        if missing_years:
            for year in missing_years:
                missing_data.append({"ISO3": country, "Year": year, "Indicator": indicator})

# Convert to DataFrame for easy viewing
missing_data_df = pd.DataFrame(missing_data)

# Save missing data information
missing_data_path = "/Users/jansengaj/Library/CloudStorage/OneDrive-UniversiteitLeiden/Documents/5. Github/EU-US/data/interim/Missing_WHR_EU.csv"
missing_data_df.to_csv(missing_data_path, index=False)

# Print summary
print(f"Missing data saved to {missing_data_path}")
print(f"Total missing entries: {len(missing_data_df)}")
print(missing_data_df.head())