"""Configuration settings for the project"""
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()  

# Database settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))

# Data directories
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
RAW_DATA_DIR = DATA_DIR / "dicom_dir"  # Archivos DICOM (100 CT scans)
TIFF_DATA_DIR = DATA_DIR / "tiff_images"  # Imágenes TIFF (100 archivos)
OVERVIEW_CSV = DATA_DIR / "overview.csv"  # CSV con metadata
FULL_ARCHIVE = DATA_DIR / "full_archive.npz"  # Numpy archive
PROCESSED_DATA_DIR = DATA_DIR / "processed"  # Para datos procesados
OUTPUT_DIR = DATA_DIR / "output"  # Para resultados/visualizaciones

# Image processing settings
IMAGE_SIZE = (512, 512)
SUPPORTED_FORMATS = [".dcm", ".tif", ".tiff", ".jpg", ".png"]

# Create output directories if they don't exist
for directory in [PROCESSED_DATA_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
