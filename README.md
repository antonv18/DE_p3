# P3 - Data Engineering Project

## Description

Data engineering project for processing and analyzing DICOM medical images.
Implements a complete ETL pipeline with a dimensional model in MongoDB.

## Project Structure

```
DE_p3/
├── .env                  # Environment variables (data and DB config)
├── .python-version       # Python version (for uv)
├── pyproject.toml        # Project configuration and dependencies
├── README.md             # This file
├── uv.lock               # Dependency lockfile
├── data/                 # Data directory (must be created manually)
│   └── dicom_dir/       # Downloaded DICOM files go here
└── src/                  # Source code
    └── de_p3            # Package
        ├── __init__.py      # Package initialization
        ├── processing.py    # ⭐ Complete ETL pipeline
        ├── config.py        # Configuration (paths, parameters)
        └── utils.py         # Utilities (hashing, normalization)
```

## Data Setup (Important!)

This project **does not** include the medical image data. You must download it manually.

1. **Download Data**: Go to Kaggle and download the DICOM files:

   * **Link**: [SIIM-ACR Pneumothorax Segmentation Data](https://www.kaggle.com/datasets/kmader/siim-medical-images?select=dicom_dir)

   * You will need to download the files from the `dicom_dir` directory.

2. **Create Folder Structure**:

   * In the root of this project, create a folder named `data`.

   * Inside `data`, create another folder named `dicom_dir`.

   * The final path should be: `data/dicom_dir/`.

3. **Place Data**: Move all the `.dcm` files you downloaded from Kaggle into the `data/dicom_dir/` folder.

The script is configured to read data from this location, as defined in the `.env` file (`DATA_DIR="data"`) and `src/de_p3/config.py`.

## Requirements

* Python >= 3.12

* UV (package manager)

* **MongoDB Community Edition** (must be running)

* MongoDB Compass (optional, for viewing data)

## Installation

### 1. Install MongoDB

Download and install from: https://www.mongodb.com/try/download/community

Start MongoDB:

```
# Windows (PowerShell as administrator)
net start MongoDB

# Or run manually:
mongod
```

### 2. Package Installation Options

Choose **one** of the following options:

#### Option 1: Local Installation (Recommended for running)

This option uses `uv` to create a virtual environment and sync the exact project dependencies.

```
# 1. Clone the repository
git clone [https://github.com/antonv18/DE_p3.git](https://github.com/antonv18/DE_p3.git)
cd DE_p3

# 2. Sync the environment and dependencies
uv sync
```

#### Option 2: Install from GitHub (Pip)

This option installs the package directly from GitHub using `pip`.

```
# Correct syntax using git+
pip install git+[https://github.com/antonv18/DE_p3.git](https://github.com/antonv18/DE_p3.git)
```

#### Option 3: Local Installation (Editable for development)

This option clones the repository and installs the package in "editable mode," which means changes to the source code are reflected immediately.

```
# 1. Clone the repository
git clone [https://github.com/antonv18/DE_p3.git](https://github.com/antonv18/DE_p3.git)
cd DE_p3

# 2. Install the package in editable mode
# (pip will install the dependencies listed in pyproject.toml)
pip install -e .
```

## Usage

Make sure you have MongoDB running and the data in the `data/dicom_dir/` folder.

### Run the complete ETL pipeline:

**Option 1 (Recommended if you used `uv sync`):**

```
# Runs the script defined in pyproject.toml
uv run run-pipeline-mongo
```

**Option 2 (Direct module):**

```
# Works with any installation method
uv run python -m de_p3.processing

# Or if not using uv:
python -m de_p3.processing
```

## ETL Pipeline

The pipeline implements the following phases:

### 1. **Extraction (Extract)**

* Loads DICOM files from `data/dicom_dir/`

* Extracts metadata: PatientID, PatientAge, PatientSex, StudyDate, Modality, PixelSpacing, ContrastAgent, etc.

### 2. **Transformation (Transform)**

* **Age normalization**: Converts DICOM format ('061Y') to integer (61)

* **PixelSpacing normalization**: Rounds to predefined bins \[0.6, 0.65, 0.7, 0.75, 0.8\], separated into X and Y

* **ContrastAgent normalization**: Standardizes empty/invalid values

* **Image conversion**: DICOM → JPEG (256x256, normalized 0-255)

* **Surrogate key generation**: MD5 hashes for unique identifiers

* **Extraction of additional fields**: BodyPartExamined, PatientPosition, ExposureTime, Rows, Columns, PhotometricInterpretation, ManufacturerModelName

### 3. **Load**

* Relational model in MongoDB (database: `medical_imaging_dw`)

  * **patient_dim**: Patient demographic data

  * **station_dim**: Equipment/station information

  * **protocol_dim**: Acquisition protocols

  * **date_dim**: Date dimension

  * **image_dim**: Image technical characteristics

  * **fact_table**: Fact table (links all dimensions)

### 4. **Visualization**

* 4x4 grid with the first 16 DICOM images

* Saves as `dicom_grid_output.png`

## Implemented Functions

### `surrogate_key(values)`

Generates a unique surrogate key (MD5 hash) from a dictionary of values.

### `get_or_create(collection, values, pk_name)`

Searches for a record in MongoDB. If it doesn't exist, it inserts it using a surrogate key.

Failure to do so will result in a compilation error.

### `format_age(age_str)`

Converts DICOM age ('061Y') to integer (61).

### `normalize_pixel_spacing(raw_value)`

Rounds pixel spacing to the nearest bin \[0.6, 0.65, 0.7, 0.75, 0.8\].

### `normalize_contrast_agent(val)`

Standardizes contrast agent metadata.

### `dicom_to_jpeg(input_path, output_dir, size)`

Converts DICOM file to JPEG (normalized and resized).

## Main Dependencies

* **pandas**: Data manipulation and DataFrames

* **numpy**: Numeric operations

* **pydicom**: DICOM file reading

* **matplotlib**: Image visualization

* **scikit-image**: Image processing

* **seaborn**: Statistical visualization

* **pymongo**: Python client for MongoDB

## Configuration

Edit `.env` to adjust:

```
DATA_DIR="data"
DB_HOST="localhost"
DB_PORT=207
```