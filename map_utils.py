import tkintermapview
from tkinter import messagebox
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import math
from database import create_db_connection


class ParkingMap:
    def __init__(self):
        self.markers = {}
        self.circles = {}
        self.geolocator = Nominatim(user_agent="parking_system")

    def create_map_widget(self, parent):
        """Create and return a map widget"""
        try:
            map_widget = tkintermapview.TkinterMapView(parent,
                                                       width=800,
                                                       height=600,
                                                       corner_radius=0)

            # Set default position (Pune)
            map_widget.set_position(18.5204, 73.8567)
            map_widget.set_zoom(12)

            return map_widget

        except Exception as e:
            messagebox.showerror("Map Error", f"Failed to create map widget: {str(e)}")
            return None

    def get_coordinates(self, address):
        """Get coordinates for an address using geocoding"""
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            return None

        except GeocoderTimedOut:
            messagebox.showerror("Error", "Geocoding service timed out. Please try again.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get coordinates: {str(e)}")
            return None

    def add_parking_marker(self, map_widget, coordinates, text="Parking Space", is_available=True):
        """Add a parking space marker to the map"""
        try:
            color = "green" if is_available else "red"

            marker = map_widget.set_marker(
                coordinates[0],
                coordinates[1],
                text=text,
                marker_color_circle=color,
                marker_color_outside=color
            )

            marker_id = f"parking_{coordinates[0]},{coordinates[1]}"
            self.markers[marker_id] = marker

            return marker

        except Exception as e:
            messagebox.showerror("Marker Error", f"Failed to add parking marker: {str(e)}")
            return None

    def draw_radius_circle(self, map_widget, coordinates, radius_km=0.5):
        """Draw a circle with given radius around a point"""
        try:
            center_lat, center_lon = coordinates
            points = []
            for i in range(60):  # 60 points for smooth circle
                angle = math.radians(i * 6)  # 360 / 60 = 6 degrees per point
                dx = radius_km * math.cos(angle)
                dy = radius_km * math.sin(angle)

                # Calculate new point (1 degree = 111.32 km)
                lat = center_lat + (dy / 111.32)
                lon = center_lon + (dx / (111.32 * math.cos(math.radians(center_lat))))
                points.append((lat, lon))

            # Close the circle
            points.append(points[0])

            # Create and return the circle as a polygon
            circle = map_widget.set_polygon(points,
                                            fill_color="blue",
                                            outline_color="blue")
            return circle

        except Exception as e:
            messagebox.showerror("Error", f"Failed to draw circle: {str(e)}")
            return None

    def is_within_radius(self, point1, point2, radius_km=0.5):
        """
        Check if point2 is within radius_km of point1
        """
        try:
            lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
            lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))

            # Earth's radius in kilometers
            r = 6371

            # Calculate distance
            distance = c * r

            return distance <= radius_km

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate distance: {str(e)}")
            return False

    def search_parking_spaces(self, map_widget, search_entry, update_spaces_list_callback):
        """Search for parking spaces near the entered location"""
        try:
            address = search_entry.get().strip()
            if not address:
                messagebox.showwarning("Warning", "Please enter a location to search")
                return

            # Get coordinates for the search location
            coordinates = self.get_coordinates(address)
            if not coordinates:
                messagebox.showerror("Error", "Could not find the specified location")
                return

            # Clear existing markers and add user marker
            self.remove_all_markers_and_circles(map_widget)
            self.add_user_marker(map_widget, coordinates, "Search Location")

            # Center map on search location
            map_widget.set_position(coordinates[0], coordinates[1])
            map_widget.set_zoom(14)

            # Search for parking spaces in database
            conn = create_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, address, latitude, longitude, capacity, rate_per_hour,
                       (SELECT COUNT(*) FROM parking_requests 
                        WHERE space_id = parking_spaces.id 
                        AND status IN ('PENDING', 'ACCEPTED')) as occupied
                FROM parking_spaces
            """)

            spaces = cursor.fetchall()
            nearby_spaces = []

            # Filter spaces within radius
            for space in spaces:
                space_coords = (space[2], space[3])
                if self.is_within_radius(coordinates, space_coords):
                    nearby_spaces.append(space)

                    # Add marker for each nearby space
                    available = space[4] - space[6]
                    marker_text = f"""Address: {space[1]}
Rate: ${space[5]}/hour
Available: {available}/{space[4]} spots"""

                    self.add_parking_marker(
                        map_widget,
                        space_coords,
                        marker_text,
                        available > 0
                    )

            # Update spaces list using callback
            update_spaces_list_callback(nearby_spaces)

            if not nearby_spaces:
                messagebox.showinfo("Info", "No parking spaces found in this area")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to search parking spaces: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def add_user_marker(self, map_widget, coordinates, text="Your Location"):
        """Add a user marker with radius circle to the map"""
        try:
            # Create marker
            marker = map_widget.set_marker(
                coordinates[0],
                coordinates[1],
                text=text,
                marker_color_circle="blue",
                marker_color_outside="blue"
            )

            # Draw radius circle
            circle = self.draw_radius_circle(map_widget, coordinates)

            # Store references
            marker_id = f"user_{coordinates[0]},{coordinates[1]}"
            self.markers[marker_id] = marker
            if circle:
                self.circles[marker_id] = circle

            return marker, circle

        except Exception as e:
            messagebox.showerror("Marker Error", f"Failed to add user marker: {str(e)}")
            return None, None

    def remove_all_markers_and_circles(self, map_widget):
        """Remove all markers and circles from the map"""
        try:
            # Remove markers
            for marker in self.markers.values():
                marker.delete()
            self.markers.clear()

            # Remove circles
            for circle in self.circles.values():
                circle.delete()
            self.circles.clear()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear map elements: {str(e)}")

    def get_address_from_coordinates(self, coordinates):
        """Get address from coordinates using reverse geocoding"""
        try:
            location = self.geolocator.reverse(f"{coordinates[0]}, {coordinates[1]}")
            return location.address if location else None

        except GeocoderTimedOut:
            messagebox.showerror("Error", "Geocoding service timed out. Please try again.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get address: {str(e)}")
            return None
