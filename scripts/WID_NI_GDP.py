import pandas as pd
import os

# Function to process the raw data and return a cleaned DataFrame
def process_data():
    # URL to the raw data
    url = "https://raw.githubusercontent.com/Annegeke/EU-US/refs/heads/main/data/raw/WID_NI_GDP.csv"

    # Step 1: Read the CSV file using the correct separator (',')
    # Skip the first row, and treat the multi-line header appropriately
    df = pd.read_csv(url, sep=",", header=1, engine="python")

    # Step 2: Clean up column names by removing unwanted newline characters and extra spaces
    df.columns = df.columns.str.replace(r'\r\n', ' ', regex=True).str.strip()

    # Step 3: Inspect the cleaned column names to ensure they're correct
    print("Cleaned column names:")
    print(df.columns)

    # Step 4: Define the column names for US and EU GDP based on the cleaned column names
    us_gdp_column = "agdpro_992_i_US Gross domestic product Total population | average income or wealth | adults | individual | Euro € | ppp | constant (2023) USA"
    eu_gdp_column = "agdpro_992_i_QY Gross domestic product Total population | average income or wealth | adults | individual | Euro € | ppp | constant (2023) European Union"

    # Step 5: Filter the data for the years 1990 to 2023 and make a copy to avoid modifying a view
    df_filtered = df[(df['Year'] >= 1990) & (df['Year'] <= 2023)].copy()

    # Step 6: Calculate the new "US=100" column using .loc[] to avoid the warning
    df_filtered.loc[:, 'US=100'] = (df_filtered[eu_gdp_column] / df_filtered[us_gdp_column]) * 100

    # Step 7: Return the filtered data with the new column
    return df_filtered

# If you want to test this file directly, you can print the processed data
if __name__ == "__main__":
    processed_data = process_data()
    print(processed_data[['Year', 'US=100']].head())  # Display a preview of the data

    # Step 8: Ensure the data/processed folder exists or create it
    processed_data_folder = "data/processed"
    os.makedirs(processed_data_folder, exist_ok=True)  # Creates folder if it doesn't exist

    # Step 9: Save the processed data to a CSV file in the data/processed folder
    processed_data_path = os.path.join(processed_data_folder, "processed_wid_gdp.csv")
    processed_data.to_csv(processed_data_path, index=False)

    # Print a success message
    print(f"Processed data saved to {processed_data_path}")
