from flask import Flask, render_template, send_from_directory, url_for, request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from netCDF4 import Dataset
from mpl_toolkits.axes_grid1 import make_axes_locatable
import geopandas as gpd
import descartes
import os

app = Flask(__name__)

IMAGE_DIR = os.path.join(app.root_path, 'static', 'images')
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def make_map(feature):
    cmap_coloring = ""

    if feature == 'Average heatwaves duration':
        cmap_coloring = "Reds"
    elif feature == "Number of days above 95°F":
        cmap_coloring = "Reds"
    elif feature == "Consecutive wet days":
        cmap_coloring = "Greens"
    elif feature == "Total precipitation":
        cmap_coloring = "Blues"
    else:
        cmap_coloring = "Oranges"
    if feature == "Population" or feature == "DOR Income Per Capita":
        df_demo = pd.read_excel("DOR_Income_EQV_Per_Capita.xlsx")
        df_demo["Municipality"] = df_demo["Municipality"].str.upper()
        gdf = gpd.read_file('C:/Users/User/Documents/College/hackathon/towns_shp/TOWNSSURVEY_POLY.shp')
        merged = gdf.merge(df_demo, how='left', left_on='TOWN', right_on='Municipality')
        ax= merged.plot(column=feature, legend=True, cmap = cmap_coloring, edgecolor='black',      # Set the border color to black
                    linewidth=0.2)

        plt.title(f'{feature}')
        ax.set_axis_off()
        image_path = os.path.join(IMAGE_DIR, f'{feature}_map.png')
        plt.savefig(image_path, bbox_inches='tight', pad_inches=0.1)
        return f'{feature}_map.png'
    
    
    dataset = Dataset('towns.imperial.future.nc', 'r')
    names_attribute = dataset.getncattr('Names')
    names_list = names_attribute.split(";")  # Split by semicolon if it's a list
    names_list = [name.strip() for name in names_list]  # Clean up extra spaces

    stats_data = dataset.variables['STATS'][:]

    feature_index = names_list.index(feature)
    feature_data = stats_data[0,0, :,0, feature_index, 0]

    units_attribute = dataset.getncattr('Units')
    units_list = units_attribute.split(";")  # Split by semicolon if it's a list
    units_list = [unit.strip() for unit in units_list]  # Clean up extra spaces
    units = units_list[feature_index]

    spatial_encoding = dataset.getncattr('SpatialList')
    spatial_list = spatial_encoding.split(";") 
    spatial_list = [space.strip() for space in spatial_list] 

    city_dict = {}
    for city in spatial_list:
        # Split each string by the first space
        city_parts = city.split(' ', 1)
        # Use the first part as the key (number) and the second part as the value (city name)
        city_dict[int(city_parts[0])-1] = city_parts[1]

    data_dict = {}

    for i in range(351):
        data_dict[city_dict[i].upper()] = feature_data[i]
    data_dict_shifted =  { 'Municipality' : data_dict.keys(), feature: data_dict.values()}
    df = pd.DataFrame(data_dict_shifted)
    df.to_csv(f'{feature}.csv', index = False)
    gdf = gpd.read_file('C:/Users/User/Documents/College/hackathon/towns_shp/TOWNSSURVEY_POLY.shp')

    
    
    merged = gdf.merge(df, how='left', left_on='TOWN', right_on='Municipality')
    ax= merged.plot(column=feature, legend=True, cmap = cmap_coloring)

    plt.title(f'{feature};  Units: {units}')
    ax.set_axis_off()
    image_path = os.path.join(IMAGE_DIR, f'{feature}_map.png')
    plt.savefig(image_path, bbox_inches='tight', pad_inches=0.1)
    return f'{feature}_map.png'
    
    
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        feature = request.form.get('feature')  # Get the selected feature from the radio buttons
        image_filename = make_map(feature)  # Generate the map and save it
        return render_template('index.html', image_generated=True, image_filename=image_filename)
    return render_template('index.html', image_generated=False)

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)


if __name__ == '__main__':
 app.run(debug=True)
