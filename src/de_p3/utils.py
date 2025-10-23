"""Utility functions"""
import logging
from pathlib import Path
from typing import Optional
import hashlib
import numpy as np
import pydicom
from PIL import Image
from pymongo.collection import Collection

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO):
    """
    Configure logging for the project
    
    Args:
        log_file: Optional path to log file
        level: Logging level
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def validate_file_exists(file_path: Path) -> bool:
    """Check if a file exists"""
    return file_path.exists() and file_path.is_file()


def validate_directory_exists(dir_path: Path) -> bool:
    """Check if a directory exists"""
    return dir_path.exists() and dir_path.is_dir()


def surrogate_key(values: dict) -> str:
    """
    Generate a unique hash string (surrogate key) from a dictionary.
    Uses MD5 algorithm. Same combination always produces the same key.
    
    Args:
        values (dict): Dictionary with values to hash
        
    Returns:
        str: MD5 hash string
    """
    # Sort keys to ensure consistent ordering
    sorted_items = sorted(values.items())
    # Create string representation
    values_str = str(sorted_items).encode('utf-8')
    # Generate MD5 hash
    return hashlib.md5(values_str).hexdigest()


def get_or_create(
    collection: Collection, 
    values: dict, 
    pk_name: str
) -> str:
    """
    Check if a record exists in a MongoDB collection.
    If not, insert a new one using surrogate key as primary key.
    
    Args:
        collection: MongoDB collection object
        values (dict): Values to search/insert
        pk_name (str): Name of the primary key field
        
    Returns:
        str: The surrogate key
    """
    # Generate surrogate key
    sk = surrogate_key(values)

    # Check if record exists
    existing = collection.find_one({pk_name: sk})

    if existing is None:
        # Insert new record
        record = {pk_name: sk, **values}
        collection.insert_one(record)

    return sk


def format_age(age_str: str) -> Optional[int]:
    """
    Transform DICOM age string (e.g., '061Y') to integer (e.g., 61).
    Handles missing or malformed data safely.
    
    Args:
        age_str (str): DICOM age string
        
    Returns:
        int or None: Age as integer, or None if invalid
    """
    if not age_str or not isinstance(age_str, str):
        return None

    try:
        # Remove 'Y' suffix and convert to int
        age_str = age_str.strip()
        if age_str.endswith('Y'):
            age_str = age_str[:-1]
        return int(age_str)
    except (ValueError, AttributeError):
        return None


def dicom_to_jpeg(
    input_path: str| Path, 
    output_dir: str | Path, 
    size=(256, 256)):
    """
    Convert DICOM file to JPEG format.
    - Normalize pixel values to 0-255
    - Resize to specified size (default 256x256)
    - Save as grayscale JPEG
    
    Args:
        input_path (str or Path): Path to input DICOM file
        output_dir (str or Path): Directory to save JPEG
        size (tuple): Target size (width, height)
        
    Returns:
        str: Path to saved JPEG file
    """
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read DICOM file
    dcm = pydicom.dcmread(input_path)
    pixel_array = dcm.pixel_array

    # Normalize pixel values to 0-255
    pixel_array = pixel_array.astype(float)
    pixel_min = pixel_array.min()
    pixel_max = pixel_array.max()

    if pixel_max > pixel_min:
        pixel_array = ((pixel_array - pixel_min) /
                       (pixel_max - pixel_min)) * 255.0
    else:
        pixel_array = np.zeros_like(pixel_array)

    pixel_array = pixel_array.astype(np.uint8)

    # Convert to PIL Image and resize
    image = Image.fromarray(pixel_array, mode='L')  # 'L' for grayscale
    image = image.resize(size, Image.LANCZOS)

    # Generate output filename
    input_path = Path(input_path)
    output_filename = input_path.stem + '.jpg'
    output_path = output_dir / output_filename

    # Save as JPEG
    image.save(output_path, 'JPEG')

    return str(output_path)


def normalize_pixel_spacing(raw_value: float | str) -> Optional[float]:
    """
    Round pixel spacing value to nearest bin from predefined set.
    Bins: [0.6, 0.65, 0.7, 0.75, 0.8]
    
    Args:
        raw_value (float or str): Raw pixel spacing value
        
    Returns:
        float or None: Normalized value, or None if invalid
    """
    bins = [0.6, 0.65, 0.7, 0.75, 0.8]

    try:
        # Convert to float if string
        if isinstance(raw_value, str):
            raw_value = float(raw_value)

        # Find nearest bin
        nearest = min(bins, key=lambda x: abs(x - raw_value))
        return nearest
    except (ValueError, TypeError):
        return None


def normalize_contrast_agent(val: str) -> str:
    """
    Standardize DICOM contrast agent metadata.
    - Replace missing, empty, or single-character values with "No contrast agent"
    - Otherwise return cleaned string
    
    Args:
        val (str): Raw contrast agent value
        
    Returns:
        str: Normalized contrast agent string
    """
    # Check if missing, empty, or single character
    if not val or not isinstance(val, str) or len(val.strip()) <= 1:
        return "No contrast agent"

    # Return cleaned string
    return val.strip()
