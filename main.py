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
        # Attempt to open the ND2 file and extract its XML metadata
        with nd2.ND2File(nd2_file_path) as f:
            ome = f.ome_metadata()
            return ome.to_xml()
    except Exception as e:
        # Log an error if there is any issue with reading the ND2 file
        logging.error(f"Error reading ND2 file {nd2_file_path}: {e}")
        return None

def parse_nd2_xml(xml_data, ns):
    """Parse ND2 XML data and extract image planes."""
    tree = ET.ElementTree(ET.fromstring(xml_data))
    root = tree.getroot()
    planes = []  # List to store extracted planes

    # Iterate over each 'Image' element in the XML data
    for image in root.findall('ome:Image', ns):
        image_name = image.get('Name')  # Extract the image name
        plane = image.find('.//ome:Plane', ns) # Find the first 'Plane' element inside this image
        if plane is not None:
            # Extract the X and Y positions of the plane
            posX = float(plane.get('PositionX'))
            posY = float(plane.get('PositionY'))
            # Append a dictionary with the image name and positions to the planes list
            planes.append({
                'image_name': image_name,
                'posX': posX,
                'posY': posY
            })
    
    return planes

def parse_multipoints_xml(positions_file):
    """Parse the multipoints XML file and return a list of points with their names and poisitons."""
    try:
        # Attempt to parse the multipoints XML file
        tree_positions = ET.parse(positions_file)
        root_positions = tree_positions.getroot()
        no_name = root_positions.find('no_name')  # Find the parent element containing point data
        points = []  # List to store extracted points

        # Iterate over each point in the 'no_name' element
        for point in no_name:
            name_elem = point.find('strName')
            x_elem = point.find('dXPosition')
            y_elem = point.find('dYPosition')

            # Only add points that have valid name, X, and Y values
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
        # Log an error if there is an issue parsing the multipoints XML
        logging.error(f"Error parsing multipoints XML {positions_file}: {e}")
        return []


def match_positions(planes, points, error_margin=1e-3):
    """Compare the planes and points based on X and Y positions."""
    matches = []  # List to store the matching planes and points

    # Iterate through all the planes
    for plane in planes:
        # Compare each plane with each point
        for point in points:
            # Check if the X and Y positions are within margin of error
            if abs(plane['posX'] - point['dX']) <= error_margin and abs(plane['posY'] - point['dY']) <= error_margin:
                # If a match is found, append the match to the list
                matches.append({
                    'image_name': plane['image_name'],
                    'point_name': point['strName'],
                    'posX': plane['posX'],
                    'posY': plane['posY'],
                    'dX': point['dX'],
                    'dY': point['dY']
                })
    return matches

def save_matches_to_csv(matches, output_csv):
    """Save the matching positions to a CSV file."""
    if matches:
        fieldnames = matches[0].keys()  # Use the keys of the first match as the column names
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matches)
        logging.info(f"Saved {len(matches)} matching positions to '{output_csv}'")
    else:
        logging.warning("No matches found; nothing to save.")

def create_mapping_from_csv(csv_path):
    """Create a mapping from the CSV data."""
    mapping = {}  # Dictionary to store the mapping from image name 
    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                img_name = row['image_name']
                point = row['point_name']
                m = re.search(r'\(Series\s*(\d+)\)', img_name, re.IGNORECASE)
                if not m:
                    logging.warning(f"Bad image_name format: {img_name}")
                    continue
                series = int(m.group(1))  # Extract the series number

                base = img_name.split(' (Series')[0] + '.nd2' # Remove series info from the name
                mapping[(base, series)] = point  # Map the image name components to the point name
    except Exception as e:
        logging.error(f"Error reading CSV {csv_path}: {e}")

    return mapping


def process_tiff_files(tiff_dir, output_dir, mapping):
    """Process and rename TIFF files according to the CSV mapping."""
    tiffs = glob.glob(os.path.join(tiff_dir, '*.tif')) + glob.glob(os.path.join(tiff_dir, '*.tiff'))
    logging.info(f"Found {len(tiffs)} TIFFs in {tiff_dir}")

    pattern = re.compile(r'\(series\s*(\d+)\)', re.IGNORECASE)  # Regex to extract series number from file name
    renamed = 0  # Counter for renamed files

    # Iterate through all the TIFF files
    for src in tiffs:
        fname = os.path.basename(src)  # Extract the file name from the full path
        m = pattern.search(fname)  # Try to match the series number using the regex
        if not m:
            logging.warning(f"Skipping (no series in name): {fname}")
            continue
        #series = int(m.group(1))  # Extract the series number
        series = int(m.group(1))-1 # Adjust for ImageJ BioFormats incorrectly iterating starting at series 01, rather than series 00

        # Check if the series and base image name match the mapping
        for (base, ser), point in mapping.items():
            if ser == series and base in fname:
                old_chunk = f"{base} (series {m.group(1)})"  # Construct the old chunk to be replaced
                new_chunk = point  # The new chunk to replace the old one
                new_name = fname.replace(old_chunk, new_chunk)  # Replace the old chunk with the new chunk
                dst = os.path.join(output_dir, new_name)  # Destination path for the renamed file

                shutil.copy2(src, dst)  # Copy the file to the new destination
                renamed += 1  # Increment the counter
                break
        else:
            logging.warning(f"No mapping for {fname}")

    logging.info(f"Done. {renamed} files renamed into {output_dir}")




def main():
    #Configuration
    nd2_file_name = '20250220_Galvano-Full-Plate.nd2'
    multipoints_file_name = 'multipoints.xml'
    output_csv = 'matched_positions.csv'
    csv_path = 'matched_positions.csv'
    tiff_dir = Path('import-tiffs')
    output_dir = Path('output-tiffs')

    # Read and parse the ND2 file
    nd2_file_path = get_file_path(nd2_file_name)
    nd2_xml = read_nd2_file(nd2_file_path)
    if not nd2_xml:
        return
    
    # Parse the XML data from ND2 file
    ns = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}
    planes = parse_nd2_xml(nd2_xml, ns)

    # Parse the multipoints XML file
    positions_file = get_file_path(multipoints_file_name)
    points = parse_multipoints_xml(positions_file)

    # Match positions
    matches = match_positions(planes, points)

    # Save matches to CSV
    save_matches_to_csv(matches, output_csv)

    # Build mapping from CSV
    mapping = create_mapping_from_csv(csv_path)

    # Process TIFF files and rename them
    process_tiff_files(tiff_dir, output_dir, mapping)

    # List output directory contents
    logging.info("Contents of output directory:")
    for f in os.listdir(output_dir):
        logging.info(f"   {f}")


if __name__ == "__main__":
    main()
