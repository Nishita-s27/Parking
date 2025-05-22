import tkinter as tk
from tkinter import ttk
import tkintermapview

class MapView(ttk.Frame):
    def __init__(self, parent, width=800, height=600):
        super().__init__(parent)
        self.map_widget = tkintermapview.TkinterMapView(
            self,
            width=width,
            height=height,
            corner_radius=0
        )
        self.map_widget.pack(fill="both", expand=True)
        self.markers = {}

    def set_position(self, latitude, longitude, zoom=13):
        self.map_widget.set_position(latitude, longitude, zoom)

    def add_marker(self, latitude, longitude, text, marker_id=None):
        marker = self.map_widget.set_marker(latitude, longitude, text)
        if marker_id:
            self.markers[marker_id] = marker
        return marker

    def clear_markers(self):
        for marker in self.markers.values():
            marker.delete()
        self.markers.clear()
