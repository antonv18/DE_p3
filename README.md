# P3 - Data Engineering Project

## Descripción
Proyecto de ingeniería de datos para procesamiento y análisis de imágenes médicas DICOM.
Implementa un pipeline ETL completo con modelo dimensional en MongoDB.

## Estructura del Proyecto

```
p3/
├── main.py               # Punto de entrada principal
├── pyproject.toml        # Configuración del proyecto y dependencias
├── README.md             # Este archivo
├── data/                 # Datos del proyecto
│   ├── dicom_dir/       # 100 archivos DICOM (CT scans)
│   ├── tiff_images/     # 100 imágenes TIFF
│   ├── overview.csv     # Metadata (Age, Contrast, IDs)
│   ├── full_archive.npz # Numpy archive
│   └── output/          # Resultados generados
│       └── jpeg_images/ # Imágenes JPEG convertidas
├── src/                  # Código fuente
│   ├── __init__.py      # Inicialización del paquete
│   ├── processing.py    # ⭐ Pipeline ETL completo
│   ├── config.py        # Configuración (rutas, parámetros)
│   └── utils.py         # Utilidades (logging, validaciones)
└── test_functions.py    # Tests de funciones de utilidad
```

## Requisitos

- Python >= 3.12
- UV (gestor de paquetes)
- **MongoDB Community Edition** (debe estar ejecutándose)
- MongoDB Compass (opcional, para visualizar datos)

## Instalación

### 1. Instalar MongoDB

Descargar e instalar desde: https://www.mongodb.com/try/download/community

Iniciar MongoDB:
```bash
# Windows (PowerShell como administrador)
net start MongoDB

# O ejecutar manualmente:
mongod
```

### 2. Instalar dependencias Python

```bash
uv sync
```

## Uso

### Ejecutar el pipeline ETL completo:

**Opción 1 (Recomendada):**
```bash
uv run main.py
```

**Opción 2 (Módulo directo):**
```bash
uv run python -m src.processing
```

### Probar funciones de utilidad:

```bash
uv run python test_functions.py
```

## Pipeline ETL

El pipeline implementa las siguientes fases:

### 1. **Extracción (Extract)**
- Carga 100 archivos DICOM desde `data/dicom_dir/`
- Extrae metadata: PatientID, PatientAge, PatientSex, StudyDate, Modality, PixelSpacing, ContrastAgent, etc.

### 2. **Transformación (Transform)**
- **Normalización de edad**: Convierte formato DICOM ('061Y') a entero (61)
- **Normalización de PixelSpacing**: Redondea a bins predefinidos (0.6, 0.65, 0.7, 0.75, 0.8)
- **Normalización de ContrastAgent**: Estandariza valores vacíos/inválidos
- **Conversión de imágenes**: DICOM → JPEG (256x256, normalizado 0-255)
- **Generación de surrogate keys**: Hashes MD5 para identificadores únicos

### 3. **Carga (Load)**
- Modelo dimensional en MongoDB (database: `medical_imaging_dw`)
  - **DimPatient**: Dimensión de pacientes
  - **DimStudy**: Dimensión de estudios
  - **DimImage**: Dimensión de imágenes (características técnicas)
  - **FactScan**: Tabla de hechos (relaciona dimensiones)

### 4. **Visualización**
- Grid 4x4 con las primeras 16 imágenes DICOM
- Se guarda como `dicom_grid_output.png`

## Funciones Implementadas

### `surrogate_key(values)`
Genera una clave sustituta única (hash MD5) a partir de un diccionario de valores.

### `get_or_create(collection, values, pk_name)`
Busca un registro en MongoDB. Si no existe, lo inserta usando surrogate key.

### `format_age(age_str)`
Convierte edad DICOM ('061Y') a entero (61).

### `normalize_pixel_spacing(raw_value)`
Redondea pixel spacing al bin más cercano [0.6, 0.65, 0.7, 0.75, 0.8].

### `normalize_contrast_agent(val)`
Estandariza metadata de agente de contraste.

### `dicom_to_jpeg(input_path, output_dir, size)`
Convierte archivo DICOM a JPEG (normalizado y redimensionado).

## Acceso a los Datos

### Opción 1: MongoDB Compass (GUI)
1. Abrir MongoDB Compass
2. Conectar a: `mongodb://localhost:27017`
3. Explorar database: `medical_imaging_dw`
4. Ver colecciones: DimPatient, DimStudy, DimImage, FactScan

### Opción 2: Línea de comandos
```bash
mongosh

use medical_imaging_dw

# Ver pacientes
db.DimPatient.find().pretty()

# Contar registros
db.FactScan.countDocuments()

# Buscar pacientes por sexo y edad
db.DimPatient.find({ PatientSex: "M", PatientAge: { $gte: 60 } })
```

## Estructura de Datos (Modelo Dimensional)

### DimPatient
```json
{
  "PatientSK": "hash_md5_unico",
  "PatientID": "12345",
  "PatientAge": 61,
  "PatientSex": "M"
}
```

### DimStudy
```json
{
  "StudySK": "hash_md5_unico",
  "StudyDate": "20230115",
  "StudyTime": "085723",
  "StudyDescription": "CT CHEST",
  "Modality": "CT"
}
```

### DimImage
```json
{
  "ImageSK": "hash_md5_unico",
  "SliceThickness": 5.0,
  "PixelSpacing": 0.7,
  "ContrastAgent": "No contrast agent",
  "KVP": 120.0,
  "Manufacturer": "SIEMENS",
  "StationName": "CT01"
}
```

### FactScan
```json
{
  "PatientSK": "ref_to_patient",
  "StudySK": "ref_to_study",
  "ImageSK": "ref_to_image",
  "OriginalDicomPath": "path/to/file.dcm",
  "JpegPath": "path/to/file.jpg",
  "JpegFilename": "file.jpg",
  "ProcessedDate": "2025-10-22T10:30:00"
}
```

## Troubleshooting

### MongoDB no conecta
```bash
# Verificar que MongoDB está ejecutándose
# Windows:
net start MongoDB

# O iniciar manualmente:
mongod
```

### Error en imports
```bash
# Reinstalar dependencias
uv sync
```

### No se encuentran archivos DICOM
Verificar que existe el directorio `data/dicom_dir/` con archivos `.dcm`

Este script:
- Carga los 100 archivos DICOM desde `data/dicom_dir/`
- Crea un DataFrame con pandas
- Visualiza 16 imágenes en un grid 4x4
- Guarda el resultado como PNG

## Dependencias Principales

- **pandas**: Manipulación de datos y DataFrames
- **numpy**: Operaciones numéricas
- **pydicom**: Lectura de archivos DICOM
- **matplotlib**: Visualización de imágenes
- **scikit-image**: Procesamiento de imágenes
- **seaborn**: Visualización estadística

## Configuración

Edita `src/config.py` para ajustar:
```python
RAW_DATA_DIR = DATA_DIR / "dicom_dir"      # Archivos DICOM
TIFF_DATA_DIR = DATA_DIR / "tiff_images"   # Imágenes TIFF
OVERVIEW_CSV = DATA_DIR / "overview.csv"   # Metadata CSV
OUTPUT_DIR = DATA_DIR / "output"           # Resultados
```

## Dataset

**100 CT Scans** con información:
- Edad del paciente (44-83 años)
- Contraste aplicado (50 con, 50 sin)
- Formato DICOM + TIFF
- Metadata en CSV

## Desarrollo

Agregar nuevas dependencias:
```bash
uv add nombre-paquete
```

---

**Data Engineering - P3 Project**
