from shiny import  App, Inputs, Outputs, Session, ui, reactive, render

from shinywidgets import reactive_read, render_widget, output_widget, register_widget


import ipyleaflet as L
from faicons import icon_svg

from shared import Bins, Parks, BASEMAPS
#from shinywidgets import output_widget, render_widget

#city_names = sorted(list(CITIES.keys()))
park_names = sorted(list(Parks.keys()))
bin_numbers = sorted(list(Bins.keys()))


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
    ui.layout_column_wrap(
        ui.value_box(
            "Fill level",
            ui.output_text("fill_level"),
            theme="gradient-blue-indigo",
            showcase=icon_svg("trash-can-arrow-up"),
            # trash-can-arrow-up
            # trash
            # dumpster
        ),
        ui.value_box(
            "Temperature",
            ui.output_text("temperature"),
            theme="gradient-blue-indigo",
            showcase=icon_svg("temperature-three-quarters"),
        ),
        ui.value_box(
            "Humidity",
            ui.output_text("humidity"),
            theme="gradient-blue-indigo",
            showcase=icon_svg("water"),
        ),
        fill=False,
    ),
    ui.card(
        ui.card_header("Map"),
        output_widget("map"),
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


    @render_widget
    def map():
        m = L.Map(basemap = BASEMAPS[input.basemap()], center = (42.2665, -82.9856), zoom=10, scroll_wheel_zoom=True)
        for i in Bins.values():
            point = L.Marker(location=i, draggable=False, icon = icon_svg("trash"))
            m.add_layer(point)
        return m
    
    # # Update the basemap
    # @reactive.effect
    # def _():
    #     return update_basemap(map.widget, input.basemap())

    # @reactive.Effect
    # def _():
    #     map.widget.center = Parks[input.park()]
    #     map.widget.center = Bins[input.bin()]
    #     map.widget.zoom = 15


    

app = App(app_ui, server)



# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------
def update_basemap(map: L.Map, basemap: str):
    for layer in map.layers:
        if isinstance(layer, L.TileLayer):
            map.remove_layer(layer)
    map.add_layer(L.basemap_to_tiles(BASEMAPS[input.basemap()]))

