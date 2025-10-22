"""Configuration settings for the project"""
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
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
