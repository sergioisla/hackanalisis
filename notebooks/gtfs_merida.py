import pandas as pd
import gtfs_kit as gk

datos = "/mnt/d/datos/HackTransporte"
feed_file = f"{datos}/hack/Datos y fichas técnicas/Información transporte público/GTFS/gtfs-merida.zip"

class GTFSMerida:

    def __init__(self, feed_file):
        self.feed_file = feed_file
        self.feed = gk.read_feed(feed_file, dist_units='km')

    def get_stops(self):
        stops = self.feed.get_stops(as_gdf=True).cx[-89.8:-89.5, :].to_crs(epsg=4326)
        stops["stop_id"] = stops["stop_id"].astype(int)
        return stops

    def get_stop_times(self):
        stoptimes = self.feed.stop_times
        stoptimes["hora"] = stoptimes.departure_time.str[:2].astype(int)
        stoptimes["stop_id"] = stoptimes["stop_id"].astype(int)
        return stoptimes

    def get_rutas(self):
        shapes = self.feed.get_shapes(as_gdf=True).cx[-89.8:-89.5, :].to_crs(epsg=4326)
        shapes["route_id"] = shapes["shape_id"].str.split("D").str[0].astype(int)
        return shapes
