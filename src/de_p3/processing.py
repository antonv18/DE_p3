"""
Procesamiento de imágenes DICOM
Pipeline ETL completo para modelo dimensional en MongoDB
"""
import os
import pandas as pd
import pydicom
import matplotlib.pyplot as plt
from glob import glob
from pathlib import Path
from pymongo import MongoClient


# Importar configuración
from de_p3.config import RAW_DATA_DIR as DATA_PATH
from de_p3.config import DB_HOST, DB_PORT
from de_p3.utils import (
    format_age,
    normalize_contrast_agent,
    get_or_create,
    normalize_pixel_spacing,
    dicom_to_jpeg
    )

def main():
    """
    Función principal de procesamiento DICOM
    Implementa el pipeline ETL completo:
    1. Extracción de metadata DICOM
    2. Transformación y normalización de datos
    3. Carga a MongoDB con modelo dimensional
    4. Conversión de DICOM a JPEG
    """
    print("="*80)
    print("DICOM ETL PIPELINE - Data Engineering Practice")
    print("="*80)
    
    # ============================================
    # 1. EXTRACT: Load DICOM files
    # ============================================
    print("\n[1/5] Loading DICOM files...")
    DICOM_FILES_PATH = os.path.join(DATA_PATH, '*.dcm')
    dicom_files = glob(DICOM_FILES_PATH)
    print(f"Searching in: {DICOM_FILES_PATH}")
    
    if not dicom_files:
        print(f"ERROR: No DICOM files found in {DATA_PATH}")
        return
    
    print(f"Found {len(dicom_files)} DICOM files")
    
    # Create DataFrame with file paths
    dicom_data = pd.DataFrame([{'path': filepath} for filepath in dicom_files])
    dicom_data['file'] = dicom_data['path'].map(os.path.basename)
    
    # ============================================
    # 2. VISUALIZE: Show 4x4 grid of first 16 images
    # ============================================
    print("\n[2/5] Creating visualization grid (4x4)...")
    # Transform first 16 DICOM rows from DataFrame to list of dicts
    img_data = list(dicom_data[:16].T.to_dict().values())
    f, ax = plt.subplots(4, 4, figsize=(16, 20))
    
    for i, data_row in enumerate(img_data):
        data_row_img = pydicom.dcmread(data_row['path'])
        ax[i//4, i%4].imshow(data_row_img.pixel_array, cmap=plt.cm.bone)
        ax[i//4, i%4].axis('off')
        ax[i//4, i%4].set_title(f"Image {i+1}", fontsize=10)
    
    plt.tight_layout()
    output_image = DATA_PATH.parent / 'dicom_grid_output.png'
    plt.savefig(output_image, dpi=100, bbox_inches='tight')
    print(f"Grid saved to: {output_image}")
    plt.close()
    
    # Show metadata of first file
    print("\n[3/5] Inspecting DICOM metadata...")
    # Show all DICOM metadata of one file
    dicom_file_path = list(dicom_data[:1].T.to_dict().values())[0]['path']
    dicom_file_metadata = pydicom.dcmread(dicom_file_path)
    print(f"\nSample metadata from: {Path(dicom_file_path).name}")
    print("-" * 60)
    
    # Print relevant metadata fields
    metadata_fields = [
        'PatientID', 'PatientName', 'PatientAge',
        'PatientSex', 'Modality', 'Manufacturer'
    ]
    for field in metadata_fields:
        if hasattr(dicom_file_metadata, field):
            value = getattr(dicom_file_metadata, field)
            print(f"  {field}: {value}")
    
    # ============================================
    # 3. MONGODB CONNECTION
    # ============================================
    print("\n[4/5] Connecting to MongoDB...")
    client = MongoClient("mongodb://"+ DB_HOST +":"+ str(DB_PORT) )
    
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB: {e}")
        return
    
    # Create/access database
    db = client["medical_imaging_dw"]
    
    # Clear existing tables
    print("\nClearing existing tables...")
    db["patient_dim"].delete_many({})
    db["station_dim"].delete_many({})
    db["protocol_dim"].delete_many({})
    db["date_dim"].delete_many({})
    db["image_dim"].delete_many({})
    db["fact_table"].delete_many({})
    print("Tables cleared")
    
    # ============================================
    # 4. ETL PIPELINE: Process all DICOM files
    # ============================================
    print(f"\n[5/5] Processing {len(dicom_files)} DICOM files...")
    print("Creating JPEG directory...")
    
    # Create output directory for JPEG images
    jpeg_output_dir = DATA_PATH.parent / 'output' / 'jpeg_images'
    jpeg_output_dir.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    
    for idx, file_path in enumerate(dicom_files, 1):
        try:
            # Read DICOM file
            dcm = pydicom.dcmread(file_path)
            
            # ========================================
            # EXTRACT metadata using DICOM tags
            # ========================================
            
            # patient_dim entity (0010, xxxx)
            patient_id = str(getattr(dcm, 'PatientID', f'UNKNOWN_{idx}'))
            patient_age_str = getattr(dcm, 'PatientAge', None)  # (0010,1010)
            patient_age = format_age(patient_age_str)
            patient_sex = str(getattr(dcm, 'PatientSex', 'U'))  # (0010,0040)
            
            # station_dim entity (0008, xxxx)
            manufacturer = str(getattr(dcm, 'Manufacturer', ''))  # (0008,0070)
            model = str(getattr(dcm, 'ManufacturerModelName', ''))  # (0008,1090)

            # protocol_dim entity (0018, xxxx)
            body_part = str(getattr(dcm, 'BodyPartExamined', ''))  # (0018,0015)
            contrast_agent_raw = str(getattr(dcm, 'ContrastBolusAgent', ''))  # (0018,0010)
            contrast_agent = normalize_contrast_agent(contrast_agent_raw)
            patient_position = str(getattr(dcm, 'PatientPosition', ''))  # (0018,5100)
            
            # date_dim entity
            study_date = str(getattr(dcm, 'StudyDate', ''))  # (0008,0020)
            year = study_date[:4] if len(study_date) >= 4 else ""
            month = study_date[4:6] if len(study_date) >= 6 else ""
            
            # image_dim entity (0028, xxxx)
            rows = int(getattr(dcm, 'Rows', 0))  # (0028,0010)
            columns = int(getattr(dcm, 'Columns', 0))  # (0028,0011)

            # PixelSpacing (0028,0030) - returns [row_spacing, col_spacing]
            pixel_spacing_raw = getattr(dcm, 'PixelSpacing', None)
            if pixel_spacing_raw and len(pixel_spacing_raw) >= 2:
                pixel_spacing_x = float(pixel_spacing_raw[1])  # column spacing
                pixel_spacing_y = float(pixel_spacing_raw[0])  # row spacing
            else:
                pixel_spacing_x = 0.0
                pixel_spacing_y = 0.0
            
            # Normalize pixel spacing
            pixel_spacing_x = normalize_pixel_spacing(pixel_spacing_x)
            pixel_spacing_y = normalize_pixel_spacing(pixel_spacing_y)

            slice_thickness = float(getattr(dcm, 'SliceThickness', 0.0))  # (0018,0050)
            photometric_interp = str(getattr(dcm, 'PhotometricInterpretation', ''))  # (0028,0004)

            # fact_table entity attributes
            exposure_time = float(getattr(dcm, 'ExposureTime', 0.0))  # (0018,1150)
            tube_current = float(getattr(dcm, 'XRayTubeCurrent', 0.0))  # (0018,1151)

            # ========================================
            # TRANSFORM: Convert DICOM to JPEG
            # ========================================
            jpeg_path = dicom_to_jpeg(file_path, jpeg_output_dir, size=(256, 256))
            jpeg_filename = Path(jpeg_path).name
            
            # ========================================
            # LOAD: Insert into MongoDB collections
            # ========================================
            
            # Insert/get patient_dim
            patient_values = {
                "sex": patient_sex,  # (0010,0040)
                "age": patient_age   # (0010,1010)
            }
            patient_id_pk = get_or_create(db["patient_dim"], patient_values, "patient_id")
            
            # Insert/get station_dim
            station_values = {
                "manufacturer": manufacturer,  # (0008,0070)
                "model": model                 # (0008,1090)
            }
            station_id_pk = get_or_create(db["station_dim"], station_values, "station_id")
            
            # Insert/get protocol_dim
            protocol_values = {
                "body_part": body_part,              # (0018,0015)
                "contrast_agent": contrast_agent,    # (0018,0010)
                "patient_position": patient_position # (0018,5100)
            }
            protocol_id_pk = get_or_create(db["protocol_dim"], protocol_values, "protocol_id")
            
            # Insert/get date_dim
            date_values = {
                "year": year,
                "month": month
            }
            date_id_pk = get_or_create(db["date_dim"], date_values, "date_id")
            
            # Insert/get image_dim
            image_values = {
                "rows": rows,                             # (0028,0010)
                "columns": columns,                       # (0028,0011)
                "pixel_spacing_x": pixel_spacing_x,       # (0028,0030)
                "pixel_spacing_y": pixel_spacing_y,       # (0028,0030)
                "slice_thickness": slice_thickness,       # (0018,0050)
                "photometric_interp": photometric_interp  # (0028,0004)
            }
            image_id_pk = get_or_create(db["image_dim"], image_values, "image_id")
            
            # Insert fact_table (fact table with foreign keys)
            study_values = {
                "station_id": station_id_pk,     # FK to station_dim
                "patient_id": patient_id_pk,     # FK to patient_dim
                "image_id": image_id_pk,         # FK to image_dim
                "protocol_id": protocol_id_pk,   # FK to protocol_dim
                "study_date": date_id_pk,        # FK to date_dim
                "exposure_time": exposure_time,  # (0018, 1150)
                "tube_current": tube_current,    # (0018, 1151)
                "file_path": file_path,          # Original DICOM path
                "jpeg_path": jpeg_path,          # Converted JPEG path
                "jpeg_filename": jpeg_filename,
                "processed_date": pd.Timestamp.now().isoformat()
            }
            
            db["fact_table"].insert_one(study_values)
            
            processed_count += 1
            
            # Progress indicator
            if processed_count % 10 == 0:
                print(f"  Processed {processed_count}/{len(dicom_files)} files...")
            
        except Exception as e:
            error_count += 1
            print(f"  ERROR processing {Path(file_path).name}: {e}")
            continue
    
    # ============================================
    # 5. SUMMARY
    # ============================================
    print("\n" + "="*80)
    print("ETL PIPELINE COMPLETED")
    print("="*80)
    print(f"Total files processed: {processed_count}")
    print(f"Errors: {error_count}")
    print(f"\nMongoDB Database: medical_imaging_dw")
    print(f"  - patient_dim: {db['patient_dim'].count_documents({})} records")
    print(f"  - station_dim: {db['station_dim'].count_documents({})} records")
    print(f"  - protocol_dim: {db['protocol_dim'].count_documents({})} records")
    print(f"  - date_dim: {db['date_dim'].count_documents({})} records")
    print(f"  - image_dim: {db['image_dim'].count_documents({})} records")
    print(f"  - fact_table: {db['fact_table'].count_documents({})} records")
    print(f"\nJPEG images saved to: {jpeg_output_dir}")


if __name__ == "__main__":
    main()
