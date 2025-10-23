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
|   └── de_p3            # Paquete
│       ├── __init__.py      # Inicialización del paquete
│       ├── processing.py    # ⭐ Pipeline ETL completo
│       ├── config.py        # Configuración (rutas, parámetros)
│       └── utils.py         # Utilidades (logging, validaciones)
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
uv run run-pipeline-mongo
```

**Opción 2 (Módulo directo):**
```bash
uv run python -m de_p3.processing
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
- **Normalización de PixelSpacing**: Redondea a bins predefinidos (0.6, 0.65, 0.7, 0.75, 0.8), separado en X e Y
- **Normalización de ContrastAgent**: Estandariza valores vacíos/inválidos
- **Conversión de imágenes**: DICOM → JPEG (256x256, normalizado 0-255)
- **Generación de surrogate keys**: Hashes MD5 para identificadores únicos
- **Extracción de campos adicionales**: BodyPartExamined, PatientPosition, ExposureTime, Rows, Columns, PhotometricInterpretation, ManufacturerModelName

### 3. **Carga (Load)**
- Modelo relacional en MongoDB (database: `medical_imaging_dw`)
  - **PATIENT**: Datos demográficos de pacientes
  - **STATION**: Información de equipos/estaciones
  - **PROTOCOL**: Protocolos de adquisición
  - **DATE**: Dimensión temporal
  - **IMAGE**: Características técnicas de imagen
  - **STUDY**: Tabla de hechos (relaciona todas las entidades)

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

### Opción 1: MongoDB Compass (GUI) ⭐ Recomendado
1. Abrir MongoDB Compass
2. Conectar a: `mongodb://localhost:27017`
3. Explorar database: `medical_imaging_dw`
4. Ver colecciones: **PATIENT**, **STATION**, **PROTOCOL**, **DATE**, **IMAGE**, **STUDY**
5. Usar pipelines de agregación (ver `consultas_mongodb_nuevo_modelo.md`)

### Opción 2: Línea de comandos
```bash
mongosh

use medical_imaging_dw

# Ver pacientes
db.PATIENT.find().pretty()

# Contar registros en todas las colecciones
db.PATIENT.countDocuments()
db.STATION.countDocuments()
db.PROTOCOL.countDocuments()
db.DATE.countDocuments()
db.IMAGE.countDocuments()
db.STUDY.countDocuments()

# JOIN: Estudios con información del paciente
db.STUDY.aggregate([
  {
    $lookup: {
      from: "PATIENT",
      localField: "patient_id",
      foreignField: "patient_id",
      as: "patient"
    }
  },
  { $unwind: "$patient" },
  { $limit: 5 }
])
```

## Estructura de Datos (Modelo Relacional)

### Diagrama del Modelo
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ PATIENT  │     │ STATION  │     │ PROTOCOL │
│────────  │     │──────────│     │──────────│
│patient_id│◄───┐│station_id│◄───┐│protocol_ │
│sex       │    ││manufact. │    ││id        │
│age       │    ││model     │    ││body_part │
└──────────┘    │└──────────┘    ││contrast_ │
                │                ││agent     │
┌──────────┐    │                ││patient_  │
│   DATE   │    │                ││position  │
│──────────│    │                │└──────────┘
│date_id   │◄───┤                │
│year      │    │                │
│month     │    │  ┌──────────┐  │
└──────────┘    │  │  STUDY   │  │
                └──┤(Fact Tbl)│──┘
┌──────────┐       │──────────│
│  IMAGE   │       │patient_id│
│──────────│◄──────│station_id│
│image_id  │       │protocol_ │
│rows      │       │id        │
│columns   │       │image_id  │
│pixel_sp_x│       │study_date│
│pixel_sp_y│       │exposure_t│
│slice_thk │       │file_path │
│photo_int │       └──────────┘
└──────────┘
```

### PATIENT (Entidad demográfica)
```json
{
  "_id": ObjectId("..."),
  "patient_id": "a1b2c3d4e5f6...",  // PK (MD5 hash)
  "sex": "M",                       // (0010, 0040)
  "age": 65                         // (0010, 1010)
}
```

### STATION (Equipos de adquisición)
```json
{
  "_id": ObjectId("..."),
  "station_id": "f6e5d4c3b2a1...",  // PK (MD5 hash)
  "manufacturer": "SIEMENS",        // (0008, 0070)
  "model": "SOMATOM Definition AS"  // (0008, 1090)
}
```

### PROTOCOL (Protocolos de estudio)
```json
{
  "_id": ObjectId("..."),
  "protocol_id": "1a2b3c4d5e6f...",      // PK (MD5 hash)
  "body_part": "CHEST",                  // (0018, 0015)
  "contrast_agent": "Iodine contrast",   // (0018, 0010)
  "patient_position": "HFS"              // (0018, 5100)
}
```

### DATE (Dimensión temporal)
```json
{
  "_id": ObjectId("..."),
  "date_id": "9z8y7x6w5v...",  // PK (MD5 hash)
  "year": "2018",
  "month": "03"
}
```

### IMAGE (Características técnicas)
```json
{
  "_id": ObjectId("..."),
  "image_id": "5t4r3e2w1q...",          // PK (MD5 hash)
  "rows": 512,                          // (0028, 0010)
  "columns": 512,                       // (0028, 0011)
  "pixel_spacing_x": 0.75,              // (0028, 0030)[1]
  "pixel_spacing_y": 0.75,              // (0028, 0030)[0]
  "slice_thickness": 5.0,               // (0018, 0050)
  "photometric_interp": "MONOCHROME2"   // (0028, 0004)
}
```

### STUDY (Tabla de hechos - Fact Table)
```json
{
  "_id": ObjectId("..."),
  "patient_id": "a1b2c3d4e5f6...",      // FK → PATIENT
  "station_id": "f6e5d4c3b2a1...",      // FK → STATION
  "protocol_id": "1a2b3c4d5e6f...",     // FK → PROTOCOL
  "image_id": "5t4r3e2w1q...",          // FK → IMAGE
  "study_date": "9z8y7x6w5v...",        // FK → DATE
  "exposure_time": 120.5,               // (0018, 1150)
  "file_path": "C:\\...\\ID_0042.dcm",
  "jpeg_path": "C:\\...\\ID_0042.jpg",
  "jpeg_filename": "ID_0042.jpg",
  "processed_date": "2025-10-22T14:30:00"
}
```

### Etiquetas DICOM Extraídas

| Entidad | Campo | Etiqueta DICOM | Descripción |
|---------|-------|----------------|-------------|
| PATIENT | sex | (0010, 0040) | Sexo del paciente |
| PATIENT | age | (0010, 1010) | Edad del paciente |
| STATION | manufacturer | (0008, 0070) | Fabricante del equipo |
| STATION | model | (0008, 1090) | Modelo del equipo |
| PROTOCOL | body_part | (0018, 0015) | Parte del cuerpo examinada |
| PROTOCOL | contrast_agent | (0018, 0010) | Agente de contraste |
| PROTOCOL | patient_position | (0018, 5100) | Posición del paciente |
| DATE | year, month | (0008, 0020) | Fecha del estudio |
| IMAGE | rows | (0028, 0010) | Número de filas |
| IMAGE | columns | (0028, 0011) | Número de columnas |
| IMAGE | pixel_spacing_x/y | (0028, 0030) | Espaciado de píxeles |
| IMAGE | slice_thickness | (0018, 0050) | Grosor del corte |
| IMAGE | photometric_interp | (0028, 0004) | Interpretación fotométrica |
| STUDY | exposure_time | (0018, 1150) | Tiempo de exposición |

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

## Consultas y Análisis

Ver ejemplos completos de consultas MongoDB en:
- **`consultas_mongodb_nuevo_modelo.md`** → Guía completa de queries
- **`MODELO_RELACIONAL_RESUMEN.md`** → Documentación técnica del modelo
- **`RESUMEN_CAMBIOS.md`** → Cambios vs. versión anterior

### Ejemplos rápidos:

**Top fabricantes de equipos:**
```javascript
db.STUDY.aggregate([
  { $lookup: { from: "STATION", localField: "station_id", foreignField: "station_id", as: "station" } },
  { $unwind: "$station" },
  { $group: { _id: "$station.manufacturer", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

**Distribución por edad:**
```javascript
db.STUDY.aggregate([
  { $lookup: { from: "PATIENT", localField: "patient_id", foreignField: "patient_id", as: "patient" } },
  { $unwind: "$patient" },
  { $bucket: { groupBy: "$patient.age", boundaries: [40, 50, 60, 70, 80, 90], default: "90+", output: { count: { $sum: 1 } } } }
])
```

**Análisis de partes del cuerpo:**
```javascript
db.STUDY.aggregate([
  { $lookup: { from: "PROTOCOL", localField: "protocol_id", foreignField: "protocol_id", as: "protocol" } },
  { $unwind: "$protocol" },
  { $group: { _id: "$protocol.body_part", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

## Desarrollo

Agregar nuevas dependencias:
```bash
uv add nombre-paquete
```

---

**Data Engineering - P3 Project**
