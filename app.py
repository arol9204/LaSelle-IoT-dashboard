from shiny import  App, Inputs, Outputs, Session, ui, reactive, render
from shinywidgets import reactive_read, render_widget, output_widget, register_widget, render_plotly


import ipyleaflet as L
from faicons import icon_svg
import plotly.express as px
import pandas as pd

from pathlib import Path
dir = Path(__file__).resolve().parent

from shared import Bins, Parks, BASEMAPS
#from shinywidgets import output_widget, render_widget

# Names of parks and bin IDs
park_names = sorted(list(Parks.keys()))
#bin_numbers = sorted(list(Bins.keys()))


# Data transformations -------------------------------------
sheet_id = '1jQMIyQh-CSFfFp3ag2DUCIhpBafP5UerPfm21VnnWvg'
df = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")


# Extracting park names and bins ID for each park
parks_bins = df.drop_duplicates(subset=['Bin_no', 'Park_name'])[['Park_name', 'Bin_no']]
parks_bins_dict = parks_bins.groupby('Park_name')['Bin_no'].apply(list).to_dict()



# Extracting median measure for each day
df[["date", "time"]] = df.Date_Time.str.split(' ', n=1, expand=True)
# Convert the date and time columns to datetime
df['date'] = pd.to_datetime(df['date'], format="%d/%m/%Y")
# df['time'] = pd.to_datetime(df['time'], format="%H%M%S").dt.time


# Group by date, Park and Bin_no, calculate median for the sensor measure columns
df_aggregated = df.groupby(['date', 'Park_name', 'Bin_no'], as_index=False).agg({
    'Humidity': 'median',
    'Temperature': 'median',
    'Ultrasonic': 'median',
    'Laser': 'median',
    'time': 'max'
})

# Assuming 300cm of deep in the bin
df_aggregated['fill_level'] = ((300 - df_aggregated['Laser'])/300)*100


# Creating KPI variables
# Ensure the data is sorted by 'Bin_no' and 'date'
df_sorted = df_aggregated.sort_values(by=['Bin_no', 'date'])

# Group by 'Bin_no' and calculate the difference in 'fill_level' for each bin
df_sorted['fill_level_increase'] = df_sorted.groupby('Bin_no')['fill_level'].diff()

# Fill NaN values in the 'fill_level_increase' column (for the first entry of each bin)
df_sorted['fill_level_increase'] = df_sorted['fill_level_increase'].fillna(0)

# Create the 'collected' variable which means the garbage was collected, it will be 1 if 'fill_level_increase' is less than -50, else 0
df_sorted['collected'] = (df_sorted['fill_level_increase'] < -50).astype(int)

# Initializing the first 

# Define the function to calculate the last collection date and average fill level increase for a bin
def get_fill_level_stats(bin_no):
    # Step 1: Filter data for the specific bin
    bin_data = df_sorted[df_sorted['Bin_no'] == bin_no]
    
    # Step 2: Find the last collection date where 'collected' is 1
    last_collection = bin_data[bin_data['collected'] == 1]
    
    # If there was no collection, return None
    if last_collection.empty:
        return None, None
    
    # Get the last collected date
    last_collection_date = last_collection['date'].max()
    
    # Step 3: Filter the data from the last collected date to the present
    data_since_last_collection = bin_data[bin_data['date'] > last_collection_date]
    
    # If there is no data after the last collection, return None for the average
    if data_since_last_collection.empty:
        return last_collection_date, None
    
    # Step 4: Calculate the average 'fill_level_increase' from that date to the present
    avg_fill_level_increase = data_since_last_collection['fill_level_increase'].mean()
    
    # Return the last collected date and the average fill level increase
    return last_collection_date, avg_fill_level_increase



# ------------------------------------------------------------------------
# Define user interface
# ------------------------------------------------------------------------

app_ui = ui.page_fixed(
ui.page_sidebar(
    ui.sidebar(
        ui.input_selectize( "park", "Park", choices=park_names),
        ui.input_selectize("bin", "Bin", choices=[], selected=None),
        ui.input_selectize("basemap", "Choose a basemap", choices=list(BASEMAPS.keys()), selected="WorldImagery",),
        ui.input_dark_mode(mode="dark"),
    ),

    ui.card(
        ui.page_navbar(
            ui.nav_panel("Map", 
                             ui.layout_columns(
                                                    ui.output_image("green_bin"),
                                                    "<50%",
                                                    ui.output_image("yellow_bin"),
                                                    "50% - 80%",
                                                    ui.output_image("red_bin"),
                                                    ">80%",
                                                #col_widths=[1, 2, 1, 2, 1, 2, -3],
                                                #col_widths={"xs":(1, 1, 1, 1, 1, 1)},
                                                #fill=False,
                                                
                                                #fillable=False,
                                                height="5px",
                                                ),
                             output_widget("map", height="300px"),
                        ),
            ui.nav_panel("Table", 
                         ui.card(
                             ui.output_data_frame("bins_df")
                             ),
                        ),
            title="Views"

        ),
        height="550px",
        
    ),
    ui.card(
                # Last reading information boxes
                ui.layout_column_wrap(
                                        ui.value_box(
                                            "Fill level",
                                            ui.output_text("fill_level"),
                                            theme="gradient-blue-indigo",
                                            showcase=icon_svg("trash-can-arrow-up"), # trash-can-arrow-up, trash, dumpster
                                            height="100px",
                                        ),
                                        ui.value_box(
                                            "Temperature",
                                            ui.output_text("temperature"),
                                            theme="gradient-blue-indigo",
                                            showcase=icon_svg("temperature-three-quarters"),
                                            height="100px",
                                        ),
                                        ui.value_box(
                                            "Humidity",
                                            ui.output_text("humidity"),
                                            theme="gradient-blue-indigo",
                                            showcase=icon_svg("water"),
                                            height="100px",
                                        ),
                                        fill=False,
                                        height="150px",
                                    ),
                ui.accordion(
                            ui.accordion_panel("+ Show Serial Data", 
                                               # Sensor serial data charts
                                               ui.layout_column_wrap(
                                                                        output_widget('distance_chart'),
                                                                        output_widget('temperaturee_chart'),
                                                                        output_widget('humidity_chart'),
                                                                    ),
                                                                    
                                               ),
                                            
                            ),
    height="700px",
    ),

    title="Smart Waste Management",
    fillable=True,
    class_="bslib-page-dashboard",
    ),
)



# ------------------------------------------------------------------------
# Server logic
# ------------------------------------------------------------------------

def server(input: Inputs, output: Outputs, session: Session):

    
    # Reactive function to update bin numbers based on the selected park
    @reactive.Effect
    @reactive.event(input.park)  # This triggers when a park is selected
    def update_bins():
        selected_park = input.park()
        # Check if a valid park is selected
        if selected_park in parks_bins_dict:
            # Get the bins for the selected park
            bin_numbers = parks_bins_dict[selected_park]
            #sorted(list(Bins.keys()))
            
            # Update the 'bin' input choices
            ui.update_selectize("bin", choices=bin_numbers, session=session)
        else:
            # If no valid park is selected, clear the bin choices
            ui.update_selectize("bin", choices=[], session=session)

    # Loading the trash bin icon
    green_trash_icon = L.Icon(icon_size = (10, 15), icon_url = ("https://raw.githubusercontent.com/arol9204/LaSelle-IoT-dashboard/main/assets/icons/trash-solid%20(green).png"))
    yellow_trash_icon = L.Icon(icon_size = (10, 15), icon_url = ("https://raw.githubusercontent.com/arol9204/LaSelle-IoT-dashboard/main/assets/icons/trash-solid%20(yellow).png"))
    red_trash_icon = L.Icon(icon_size = (10, 15), icon_url = ("https://raw.githubusercontent.com/arol9204/LaSelle-IoT-dashboard/main/assets/icons/trash-solid%20(red).png"))
    
    # Showing the map bin legend:
    @render.image
    def green_bin():
        img = {"src": str(dir / "assets/icons/trash-solid (green).png"), "width": "20px"}
        return img
    @render.image
    def yellow_bin():
        img = {"src": str(dir / "assets/icons/trash-solid (yellow).png"), "width": "20px"}
        return img
    @render.image
    def red_bin():
        img = {"src": str(dir / "assets/icons/trash-solid (red).png"), "width": "20px"}
        return img



    # Rendering the map chart
    @render_widget
    def map():
        m = L.Map(basemap = BASEMAPS[input.basemap()], center = (42.2665, -82.9856), zoom=10, scroll_wheel_zoom=True)
        for i in Bins:
            # Selecting the color of the bin based on the fill level from the last report
            bin_id = df_sorted[df_sorted.Bin_no == int(i)]
            last_reading_fill_level = bin_id[bin_id.date == bin_id.date.max()]["fill_level"]
            if last_reading_fill_level.values < 50:
                point = L.Marker(location=Bins[i], draggable=False, icon = green_trash_icon)
            elif last_reading_fill_level.values < 80:
                point = L.Marker(location=Bins[i], draggable=False, icon = yellow_trash_icon)
            else:
                point = L.Marker(location=Bins[i], draggable=False, icon = red_trash_icon)
            m.add_layer(point)
        #m.layout.height = "500px"
        return m

    # Store the current circle layer
    current_circle = reactive.Value(None)

    # Updating the center of the map given the bin selected
    @reactive.Effect
    #@reactive.event(input.park)
    @reactive.event(input.bin)
    def update_map():

        if input.bin():
            # Get the map widget
            m = map.widget
            
            # Center the map to the selected bin
            m.center = Parks[input.park()]
            #m.center = Bins[input.bin()]
            m.zoom = 17.5

            # If there's a current circle on the map, remove it
            if current_circle():
                m.remove_layer(current_circle())

            # Create a new circle for the selected bin
            circle = L.Circle(location=Bins[input.bin()], radius=10, color="red")

            # Add the new circle to the map
            m.add_layer(circle)

            # Update the current_circle reactive value
            current_circle.set(circle)
        
    # Rendaring the dataframe loaded from the google spreadsheet
    @render.data_frame
    def bins_df():
        return render.DataTable(df_sorted, filters=True)
    
    # Filtering the dataframe given the bin number selected in the input selection
    @reactive.calc
    def bin_number():
        if not input.bin():
            return pd.DataFrame()  # Return an empty dataframe if no bin is selected
        bin_id = df_sorted[df_sorted.Bin_no == int(input.bin())]
        return bin_id
    
    
    # Extracting from the dataframe the last reading recorded (most recently date) for each sensor
    @reactive.calc
    def last_reading():
        if not input.bin():
            return pd.DataFrame()  # Return an empty dataframe if no bin is selected
        last_reading_df = bin_number()[bin_number().date == bin_number().date.max()]
        return last_reading_df
        
    # Showing the last reading for the filling level
    @render.text
    def fill_level():
        if not input.bin():
            return "N/A"  # Return an empty dataframe if no bin is selected
        fill_level = last_reading()["fill_level"].values
        return f"{fill_level[0]:.2f} %"
    
    # Showing the last reading for the temperature
    @render.text
    def temperature():
        if not input.bin():
            return "N/A"  # Return an empty dataframe if no bin is selected
        close_temperature = last_reading()["Temperature"].values
        return f"{close_temperature[0]:.2f} °C"
    
    # Showing the last reading for the Humidity
    @render.text
    def humidity():
        if not input.bin():
            return "N/A"  # Return an empty dataframe if no bin is selected
        close_humidity = last_reading()["Humidity"].values
        return f"{close_humidity[0]:.0f} %"
    
    # Ploting the serial data for the distances recorded from the sensor in the dataframe
    @render_plotly
    @reactive.event(input.bin)
    def distance_chart():
        if input.bin():
            bin_distance = bin_number()[['date', 'fill_level']]
            return px.line(bin_distance, x='date', y="fill_level")
    
    @render_plotly
    @reactive.event(input.bin)
    def temperaturee_chart():
        if input.bin():
            bin_distance = bin_number()[['date', 'Temperature']]
            return px.line(bin_distance, x='date', y="Temperature")
    
    @render_plotly
    @reactive.event(input.bin)
    def humidity_chart():
        if input.bin():
            bin_distance = bin_number()[['date', 'Humidity']]
            return px.line(bin_distance, x='date', y="Humidity")

app = App(app_ui, server)



# ---------------------------------------------------------------
# Helper functions and assets
# ---------------------------------------------------------------

# def update_basemap(map: L.Map, basemap: str):
#     for layer in map.layers:
#         if isinstance(layer, L.TileLayer):
#             map.remove_layer(layer)
#     map.add_layer(L.basemap_to_tiles(BASEMAPS[input.basemap()]))




