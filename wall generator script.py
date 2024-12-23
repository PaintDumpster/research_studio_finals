import pandas as pd
import random
import json
import os

import requests
import geopandas as gpd

# Load your data into a DataFrame (assuming you have a CSV file with lat/lon columns)
df = pd.read_csv('datasets/Worlddataset.csv')

# Create a GeoDataFrame from the DataFrame
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['lng'], df['lat']), crs="EPSG:4326")


# Function to fetch data from the API
def fetch_api_data(lat, lon):
    api_url = f'https://my.meteoblue.com/packages/basic-1h_basic-day?apikey=cYbzFuMOhynBHd68&lat={lat}&lon={lon}&asl=211&format=json'
    response = requests.get(api_url)
    if response.status_code == 200:  # Check if the request was successful
        return response.json()  # Parse the JSON data
    else:
        print(f'Failed to retrieve data for ({lat}, {lon}):', response.status_code)
        return None


# Function to get weather data by city name
def get_weather_by_city(city_name):
    row = gdf[gdf['city'].str.lower() == city_name.lower()]
    if not row.empty:
        lon, lat = row.geometry.x.values[0], row.geometry.y.values[0]
        data = fetch_api_data(lat, lon)
        if data:
            # Store the data in a variable
            weather_data = data

            # Extract the maximum temperature value
            max_temp = max(weather_data["data_day"]["temperature_max"])

            print(f"Maximum temperature for {city_name} is {max_temp}°C")
            return max_temp  # Return the maximum temperature value
        else:
            print(f"No data found for {city_name}.")
            return None
    else:
        print(f"City {city_name} not found in the dataset.")
        return None


# Example usage
city_name = input("Enter city name: ")
max_temperature = get_weather_by_city(city_name)
if max_temperature is not None:
    print(f"The maximum temperature in {city_name} is {max_temperature}°C")

###############################################################################################################################

pd.set_option('display.max_columns', None)

# Load materials from the CSV
materials_df = pd.read_csv('datasets/U-value marcos.csv')

# Convert columns to appropriate data types
materials_df['density'] = materials_df['density'].astype(float)
materials_df['min_thickness'] = materials_df['min_thickness'].astype(float)
materials_df['max_thickness'] = materials_df['max_thickness'].astype(float)
materials_df['conductivity'] = materials_df['conductivity'].astype(float)
materials_df['embodied_carbon_coefficient'] = materials_df['embodied_carbon_coefficient'].astype(float)
materials_df['cost'] = materials_df['cost'].astype(float)
materials_df['recyclability'] = materials_df['recyclability'].astype(int)
materials_df['bio_based'] = materials_df['bio_based'].astype(bool)
materials_df['responsible'] = materials_df['responsible'].astype(bool)
materials_df['preserved'] = materials_df['preserved'].astype(bool)

# Function to create a wall with unique properties
def create_wall(wall_id, total_wall_area, wall_options, materials_df, outside_temp, inside_temp):
    wall_type = random.choice(wall_options)
    wall = {
        'wall_id': wall_id,
        'materials': [],
        'total_thickness': 0,
        'total_r_value': 0,
        'total_u_value': 0,
        'total_embodied_carbon': 0,
        'heat_transfer': 0,
        'total_cost': 0,
        'construction_demolition_waste': 0,
        'circular_economy': 0,
        'heritage_preservation': 0
    }
    preserved_masses = []
    total_masses = []
    circular_masses = []
    responsible_sourcing_values = []
    preservation_values = []

    for material_type in wall_type:
        filtered_materials = materials_df[materials_df['material type'] == material_type]
        selected_material = filtered_materials.sample().iloc[0]
        material_thickness = round(random.uniform(selected_material['min_thickness'], selected_material['max_thickness']), 3)
        r_value = round(material_thickness / selected_material['conductivity'], 3)
        u_value = round(1 / r_value, 3)

        material_mass = selected_material['density'] * material_thickness * total_wall_area
        total_masses.append(material_mass)

        if selected_material['recyclability'] == 5:
            preserved_mass = material_mass
        elif selected_material['recyclability'] == 4:
            preserved_mass = 0.75 * material_mass
        elif selected_material['recyclability'] == 3:
            preserved_mass = 0.5 * material_mass
        else:
            preserved_mass = 0 * material_mass

        preserved_masses.append(preserved_mass)

        if selected_material['bio_based']:
            circular_mass = material_mass
        elif selected_material['recyclability'] == 5:
            circular_mass = material_mass
        elif selected_material['recyclability'] == 4:
            circular_mass = 0.75 * material_mass
        elif selected_material['recyclability'] == 3:
            circular_mass = 0.5 * material_mass
        else:
            circular_mass = 0

        circular_masses.append(circular_mass)

        responsible_sourcing_value = 100 if selected_material['responsible'] else 0
        responsible_sourcing_values.append(responsible_sourcing_value)

        preservation_value = 100 if selected_material['preserved'] else 0
        preservation_values.append(preservation_value)

        material_data = {
            'material': selected_material['material'],
            'thickness': material_thickness,
            'density': selected_material['density'],
            'conductivity': selected_material['conductivity'],
            'u_value': u_value,
            'embodied_carbon_coefficient': selected_material['embodied_carbon_coefficient'],
            'cost': selected_material['cost'],
            'recyclability': selected_material['recyclability'],
            'bio_based': selected_material['bio_based'],
            'color': selected_material['colour']
        }

        wall['materials'].append(material_data)
        wall['total_thickness'] = round(wall['total_thickness'] + material_thickness, 3)
        wall['total_r_value'] = round(wall['total_r_value'] + r_value, 3)
        wall['total_u_value'] = round(wall['total_u_value'] + u_value, 3)
        wall['total_embodied_carbon'] = round(wall['total_embodied_carbon'] + material_thickness * total_wall_area * selected_material['density'] * selected_material['embodied_carbon_coefficient'], 3)
        wall['heat_transfer'] = round((outside_temp - inside_temp) / wall['total_r_value'], 3)
        wall['total_cost'] = round(wall['total_cost'] + selected_material['cost'] * total_wall_area, 3)

    total_mass = sum(total_masses)
    preserved_mass_total = sum(preserved_masses)
    circular_mass_total = sum(circular_masses)

    wall['construction_demolition_waste'] = round((preserved_mass_total / total_mass) * 100, 2) if total_mass > 0 else 0
    wall['circular_economy'] = round((circular_mass_total / total_mass) * 100, 2) if total_mass > 0 else 0
    wall['responsible_material_sourcing'] = round(sum(responsible_sourcing_values)/len(responsible_sourcing_values),2) if responsible_sourcing_values else 0
    wall['heritage_preservation'] = round(sum(preservation_values)/ len(preservation_values),2) if preservation_values else 0
    return wall

# Get user inputs
num_walls = int(input("Enter the number of walls to be made: "))
total_wall_area = float(input("Enter the total wall area: "))
outside_temp = float(max_temperature)
inside_temp = float(20)

wall_population = []
wall_options = [
    ['finishing', 'insulation', 'structure', 'finishing'],
    ['finishing', 'insulation', 'finishing'],
    #['glass'],
    ['facade', 'insulation', 'finishing']
]

# Create unique walls
while len(wall_population) < num_walls:
    new_wall = create_wall(len(wall_population) + 1, total_wall_area, wall_options, materials_df, outside_temp, inside_temp)
    if new_wall['total_thickness'] <= 0.300 and new_wall not in wall_population:
        wall_population.append(new_wall)

# Create a DataFrame from the wall population
wall_population_df = pd.DataFrame(wall_population)

# Normalize 'total_embodied_carbon' and compute 'embodied_ghg_emissions' and 'Affordable_adoption_high-quality_housing_conditions'
max_embodied_carbon = wall_population_df['total_embodied_carbon'].max()
max_cost = wall_population_df['total_cost'].max()

wall_population_df['embodied_ghg_emissions'] = wall_population_df['total_embodied_carbon'].apply(lambda x: round((1 - (x / max_embodied_carbon)) * 100, 2) if max_embodied_carbon > 0 else 0)
wall_population_df['affordable_adoption_high-quality_housing_conditions'] = wall_population_df['total_cost'].apply(lambda x: round((1 - (x / max_cost)) * 100, 2) if max_cost > 0 else 0)
wall_population_df['overall_score'] = round(sum([wall_population_df['construction_demolition_waste'],wall_population_df['circular_economy'],wall_population_df['heritage_preservation'],wall_population_df['responsible_material_sourcing'],wall_population_df['embodied_ghg_emissions'],wall_population_df['affordable_adoption_high-quality_housing_conditions']])/6,2)
# Print the DataFrame
print(wall_population_df.head(20).to_string())

# Save the DataFrame to a CSV file
path = "datasets"
wall_population_df.to_csv(os.path.join(path,r'wall_population.csv'), index=False)

############################################################################################################################
# Ensure the DataFrame columns are appropriately converted to native Python data types
def convert_types(df):
    df['wall_id'] = df['wall_id'].astype(int)
    df['total_thickness'] = df['total_thickness'].astype(float)
    df['total_r_value'] = df['total_r_value'].astype(float)
    df['total_u_value'] = df['total_u_value'].astype(float)
    df['total_embodied_carbon'] = df['total_embodied_carbon'].astype(float)
    df['heat_transfer'] = df['heat_transfer'].astype(float)
    df['total_cost'] = df['total_cost'].astype(float)
    df['construction_demolition_waste'] = df['construction_demolition_waste'].astype(float)
    df['circular_economy'] = df['circular_economy'].astype(float)
    df['heritage_preservation'] = df['heritage_preservation'].astype(float)
    df['responsible_material_sourcing'] = df['responsible_material_sourcing'].astype(float)
    df['embodied_ghg_emissions'] = df['embodied_ghg_emissions'].astype(float)
    df['affordable_adoption_high-quality_housing_conditions'] = df['affordable_adoption_high-quality_housing_conditions'].astype(float)
    df['overall_score'] = df['overall_score'].astype(float)
    return df


wall_population_df = convert_types(wall_population_df)


# Function to convert DataFrame to JSON format
def dataframe_to_json(df):
    json_list = []

    for _, row in df.iterrows():
        materials_list = row['materials']

        # Ensure that all materials are dictionaries with appropriate types
        processed_materials = [
            {
                "material": material["material"],
                "thickness": float(material["thickness"]),
                "density": float(material["density"]),
                "conductivity": float(material["conductivity"]),
                "u_value": float(material["u_value"]),
                "embodied_carbon_coefficient": float(material["embodied_carbon_coefficient"]),
                "cost": float(material["cost"]),
                "recyclability": int(material["recyclability"]),
                "bio_based": bool(material["bio_based"]),
                "color": material["color"]
            }
            for material in materials_list
        ]

        json_row = {
            "wall_id": int(row['wall_id']),
            "materials": processed_materials,
            "total_thickness": float(row['total_thickness']),
            "total_r_value": float(row['total_r_value']),
            "total_u_value": float(row['total_u_value']),
            "total_embodied_carbon": float(row['total_embodied_carbon']),
            "heat_transfer": float(row['heat_transfer']),
            "total_cost": float(row['total_cost']),
            "construction_demolition_waste": float(row['construction_demolition_waste']),
            "circular_economy": float(row['circular_economy']),
            "heritage_preservation": float(row['heritage_preservation']),
            "responsible_material_sourcing": float(row['responsible_material_sourcing']),
            "embodied_ghg_emissions": float(row['embodied_ghg_emissions']),
            "affordable_adoption_high-quality_housing_conditions": float(row['affordable_adoption_high-quality_housing_conditions']),
            "overall_score": float(row['overall_score'])
        }
        json_list.append(json_row)

    return json_list


# Convert DataFrame to JSON
json_data = dataframe_to_json(wall_population_df)

# Save JSON to a file
with open('datasets/wall_population.json', 'w') as json_file:
    json.dump(json_data, json_file, indent=4)

print("DataFrame successfully converted to JSON file.")