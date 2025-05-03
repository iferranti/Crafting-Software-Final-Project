import xml.etree.ElementTree as ET
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

#def read_nd2_file(nd2_file_path):


def main():
    print("Hello from crafting-software-final-project!")


if __name__ == "__main__":
    main()
