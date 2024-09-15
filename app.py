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

#city_names = sorted(list(CITIES.keys()))
park_names = sorted(list(Parks.keys()))
bin_numbers = sorted(list(Bins.keys()))



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
df_aggregated['fill_level'] = ((300 - df_aggregated['Laser'])/300)*100






# ------------------------------------------------------------------------
# Define user interface
# ------------------------------------------------------------------------

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_selectize( "park", "Park", choices=park_names, selected=None),
        ui.input_selectize("bin", "Bin", choices=bin_numbers, selected=None),
        ui.input_selectize("basemap", "Choose a basemap", choices=list(BASEMAPS.keys()), selected="WorldImagery",),
        ui.input_dark_mode(mode="dark"),
    ),

    ui.card(
        ui.page_navbar(
            ui.nav_panel("Map", 
                             ui.layout_columns(
                                                    ui.output_image("green_bin", width='5%', height='10%',),
                                                    "<50%",
                                                    ui.output_image("yellow_bin", width='10%', height='10%',),
                                                    "50% - 80%",
                                                    ui.output_image("red_bin", width='10%', height='10%',),
                                                    ">80%",
                                                #fill=False,
                                                #col_widths={"xs":(1, 2, 1, 2, 1, 2)},
                                                #fillable=False,
                                                ),
                             output_widget("map", height="500px"),
                        ),
            ui.nav_panel("Table", 
                         ui.card(
                             ui.output_data_frame("bins_df")
                             ),
                        ),
            title="Views"

        ),
        height="700px",
        
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

    ),
    

    



    title="Smart Waste Management",
    fillable=True,
    class_="bslib-page-dashboard",
)


# ------------------------------------------------------------------------
# Server logic
# ------------------------------------------------------------------------

def server(input: Inputs, output: Outputs, session: Session):

    
    # Reactive values to store location information
    #park_selected = reactive.value()
    #bin_selected = reactive.value()
    #basemap_selected = reactive.value()

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
            # Calculating the filling level to decide the trash icon color
            # bin_id = df[df.Bin_no == int(i)]
            # last_reading_distance = bin_id[bin_id.Date_Time == bin_id.Date_Time.max()]["Laser"].median()
            # percentage = ((300 - last_reading_distance)/300)*100

            bin_id = df_aggregated[df_aggregated.Bin_no == int(i)]
            last_reading_fill_level = bin_id[bin_id.date == bin_id.date.max()]["fill_level"]
            if last_reading_fill_level.values < 50:
                point = L.Marker(location=Bins[i], draggable=False, icon = green_trash_icon)
            elif last_reading_fill_level.values < 80:
                point = L.Marker(location=Bins[i], draggable=False, icon = yellow_trash_icon)
            else:
                point = L.Marker(location=Bins[i], draggable=False, icon = red_trash_icon)
            m.add_layer(point)
        m.layout.height = "500px"
        return m

    # Store the current circle layer
    current_circle = reactive.Value(None)

    # Updating the center of the map given the bin selected
    @reactive.Effect
    @reactive.event(input.bin)
    def update_map():
        # Get the map widget
        m = map.widget
        
        # Center the map to the selected bin
        m.center = Bins[input.bin()]
        m.zoom = 25

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
        return render.DataTable(df_aggregated, filters=True)
    
    # Filtering the dataframe given the bin number selected in the input selection
    @reactive.calc
    def bin_number():
        bin_id = df_aggregated[df_aggregated.Bin_no == int(input.bin())]
        return bin_id
    
    
    # Extracting from the dataframe the last reading recorded (most recently date) for each sensor
    @reactive.calc
    def last_reading():
        last_reading_df = bin_number()[bin_number().date == bin_number().date.max()]
        return last_reading_df
        
    # Showing the last reading for the filling level
    @render.text
    def fill_level():
        fill_level = last_reading()["fill_level"].median()
        return f"{fill_level:.2f} %"
    
    # Showing the last reading for the temperature
    @render.text
    def temperature():
        close_temperature = last_reading()["Temperature"].median()
        return f"{close_temperature:.2f} °C"
    
    # Showing the last reading for the Humidity
    @render.text
    def humidity():
        close_humidity = last_reading()["Humidity"].median()
        return f"{close_humidity:.0f} %"
    
    # Ploting the serial data for the distances recorded from the sensor in the dataframe
    @render_plotly
    def distance_chart():
        bin_distance = bin_number()[['date', 'fill_level']]
        return px.line(bin_distance, x='date', y="fill_level")
    
    @render_plotly
    def temperaturee_chart():
        bin_distance = bin_number()[['date', 'Temperature']]
        return px.line(bin_distance, x='date', y="Temperature")
    
    @render_plotly
    def humidity_chart():
        bin_distance = bin_number()[['date', 'Humidity']]
        return px.line(bin_distance, x='date', y="Humidity")

app = App(app_ui, server)



# ---------------------------------------------------------------
# Helper functions and assets
# ---------------------------------------------------------------
def update_basemap(map: L.Map, basemap: str):
    for layer in map.layers:
        if isinstance(layer, L.TileLayer):
            map.remove_layer(layer)
    map.add_layer(L.basemap_to_tiles(BASEMAPS[input.basemap()]))




