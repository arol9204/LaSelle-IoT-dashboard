from ipyleaflet import basemaps

BASEMAPS = {
    "WorldImagery": basemaps.Esri.WorldImagery,
    "Mapnik": basemaps.OpenStreetMap.Mapnik,
    "Positron": basemaps.CartoDB.Positron,
    "DarkMatter": basemaps.CartoDB.DarkMatter,
    "NatGeoWorldMap": basemaps.Esri.NatGeoWorldMap,
    "France": basemaps.OpenStreetMap.France,
    "DE": basemaps.OpenStreetMap.DE,
}


# Bins = {
#     "Bin 1": {"latitude": 40.7128, "longitude": -74.0060, "altitude": 0},
#     "Bin 2": {"latitude": 51.5074, "longitude": -0.1278, "altitude": 0},
#     "Bin 3": {"latitude": 48.8566, "longitude": 2.3522, "altitude": 0},
#     "Bin 4": {"latitude": 35.6895, "longitude": 139.6917, "altitude": 0},
#     "Bin 5": {"latitude": -33.8688, "longitude": 151.2093, "altitude": 0},
#     "Bin 6": {"latitude": 34.0522, "longitude": -118.2437, "altitude": 0},
#     "Bin 7": {"latitude": 52.5200, "longitude": 13.4050, "altitude": 0},
#     "Bin 8": {"latitude": 41.9028, "longitude": 12.4964, "altitude": 0},
#     "Bin 9": {"latitude": 39.9042, "longitude": 116.4074, "altitude": 0},
#     #"Bin 10": {"latitude": 55.7558, "longitude": 37.6176, "altitude": 0},
# }

# Parks = {
#     "LaSelle Marina": {"latitude": 42.2378, "longitude": -83.1054, "altitude": 0},
#     "Vollmer": {"latitude": 42.2224, "longitude": -83.0529, "altitude": 0},
#     "Burnet": {"latitude": 42.2406, "longitude": -83.0445, "altitude": 0},
# }

Bins = {
    "1": (42.23699097985084, -83.1070979329771),
    "2": (42.23714579054847, -83.1070733057825),
    "3": (42.23730468963785, -83.10412199807335),
    "4": (42.22154181710679, -83.05035454170714),
    "5": (42.22082734675422, -83.05114270283765),
    "6": (42.22134654458914, -83.05092384161651),
    "7": (42.241734885209766, -83.04515124418585),
    "8": (42.24171529405549, -83.04540176364362),
    "9": (42.24120522247013, -83.04542460219686),
    #"Bin 10":(55.7558, 37.6176),
}

Parks = {
    "LaSelle Marina": (42.2378, -83.1054),
    "Vollmer": (42.2224, -83.0529),
    "Burnet": (42.2406, -83.0445),
}