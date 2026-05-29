from shapely.geometry import Point
import geopandas as gpd

class GeospatialProcessor:
    @staticmethod
    def generate_risk_buffer_wkt(lat: float, lon: float, radius_degrees: float = 0.01) -> str:
        """
        Creates a circular risk zone around the point (approx 1km buffer).
        Returns the geometry as a Well-Known Text (WKT) string for SQLite storage.
        """
        point = Point(lon, lat)
        # Using GeoPandas to handle geometry creation efficiently
        gdf = gpd.GeoDataFrame(index=[0], geometry=[point], crs="EPSG:4326")
        
        # Suppress the CRS warning since a geographic buffer is acceptable for MVP
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            buffered = gdf.geometry.buffer(radius_degrees)
            
        return buffered.iloc[0].wkt

    @staticmethod
    def calculate_slope(elevation: float) -> float:
        """Mock calculation for terrain slope based on regional elevation heuristics"""
        # In a full raster pipeline, we would read a DEM TIFF here.
        # For free-tier MVP without heavy TIFFs, we estimate slope risk factor.
        return min(elevation / 1000.0, 1.0)