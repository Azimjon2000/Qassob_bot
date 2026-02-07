"""Geolocation services."""
import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple:
    """
    Calculate bounding box for SQL pre-filtering.
    Returns (min_lat, max_lat, min_lon, max_lon).
    
    V8 MANDATORY: Use this for SQL WHERE clause before applying haversine.
    """
    # Earth's radius in km
    R = 6371.0
    
    # Angular distance in radians
    angular = radius_km / R
    
    lat_rad = math.radians(lat)
    
    # Latitude bounds (simple)
    min_lat = lat - math.degrees(angular)
    max_lat = lat + math.degrees(angular)
    
    # Longitude bounds (adjusted for latitude)
    # At the equator, 1 degree longitude = 111 km
    # At higher latitudes, it's less
    delta_lon = math.degrees(angular / math.cos(lat_rad))
    min_lon = lon - delta_lon
    max_lon = lon + delta_lon
    
    return (min_lat, max_lat, min_lon, max_lon)


def sort_by_distance(butchers: list, user_lat: float, user_lon: float) -> list:
    """
    Sort butchers by distance from user. 
    Adds 'distance' field to each butcher dict.
    """
    for butcher in butchers:
        if butcher["lat"] is not None and butcher["lon"] is not None:
            dist = haversine(user_lat, user_lon, butcher["lat"], butcher["lon"])
            butcher["distance"] = dist
        else:
            butcher["distance"] = float('inf')  # Put at the end if no location
            
    return sorted(butchers, key=lambda x: x["distance"])
