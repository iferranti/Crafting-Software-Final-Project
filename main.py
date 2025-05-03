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

def main():
    print("Hello from crafting-software-final-project!")


if __name__ == "__main__":
    main()
