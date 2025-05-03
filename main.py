import xml.etree.ElementTree as ET
import nd2
import csv
import pandas as pd
import os
import re
import glob
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

def get_file_path(file_name):
    """Returns the full path of a file"""
    return Path.cwd() / file_name

def read_nd2_file(nd2_file_path):
    """Read the ND2 file and return the XML string."""
    try:
        with nd2.ND2File(nd2_file_path) as f:
            ome = f.ome_metadata()
            return ome.to_xml()
    except Exception as e:
        logging.error(f"Error reading ND2 file {nd2_file_path}: {e}")
        return None

def parse_nd2_xml(xml_data, ns):
    """Parse ND2 XML data and extract image planes."""
    tree = ET.ElementTree(ET.fromstring(xml_data))
    root = tree.getroot()
    planes = []

    for image in root.findall('ome:Image', ns):
        image_name = image.get('Name')
        plane = image.find('.//ome:Plane', ns)
        if plane is not None:
            posX = float(plane.get('PositionX'))
            posY = float(plane.get('PositionY'))
            planes.append({
                'image_name': image_name,
                'posX': posX,
                'posY': posY
            })
    
    return planes

def parse_xml(xml_data, ns):
    """Parse XML data and extract image planes."""
    tree = ET.ElementTree(ET.fromstring(xml_data))
    root = tree.getroot()
    planes = []

    for image in root.findall('ome:Image', ns):
        image_name = image.get('Name')
        plane = image.find('.//ome:Plane', ns)
        if plane is not None:
            posX = float(plane.get('PositionX'))
            posY = float(plane.get('PositionY'))
            planes.append({
                'image_name': image_name,
                'posX': posX,
                'posY': posY
            })
    
    return planes


def parse_multipoints_xml(positions_file):
    """Parse the multipoints XML file and return a list of points with their names and poisitons."""
    try:
        tree_positions = ET.parse(positions_file)
        root_positions = tree_positions.getroot()
        no_name = root_positions.find('no_name')
        points = []

        for point in no_name:
            name_elem = point.find('strName')
            x_elem = point.find('dXPosition')
            y_elem = point.find('dYPosition')

            if name_elem is not None and x_elem is not None and y_elem is not None:
                strName = name_elem.get('value')
                dX = float(x_elem.get('value'))
                dY = float(y_elem.get('value'))
                points.append({
                    'strName': strName,
                    'dX': dX,
                    'dY': dY
                })

        return points
    
    except Exception as e:
        logging.error(f"Error parsing multipoints XML {positions_file}: {e}")
        return []


def match_positions(planes, points, error_margin=1e-3):
    """Compare the planes and points based on X and Y positions."""
    matches = []
    for plane in planes:
        for point in points:
            if abs(plane['posX'] - point['dX']) <= error_margin and abs(plane['posY'] - point['dY']) <= error_margin:
                matches.append({
                    'image_name': plane['image_name'],
                    'point_name': point['strName'],
                    'posX': plane['posX'],
                    'posY': plane['posY'],
                    'dX': point['dX'],
                    'dY': point['dY']
                })
    return matches


def main():
    print("Hello from crafting-software-final-project!")


if __name__ == "__main__":
    main()
