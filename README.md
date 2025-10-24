# P3 - Data Engineering Project

## Descripción

Proyecto de ingeniería de datos para procesamiento y análisis de imágenes médicas DICOM.
Implementa un pipeline ETL completo con modelo dimensional en MongoDB.

## Estructura del Proyecto

```
DE_p3/
├── .env                  # Variables de entorno (configuración de datos y DB)
├── .python-version       # Versión de Python (para uv)
├── pyproject.toml        # Configuración del proyecto y dependencias
├── README.md             # Este archivo
├── uv.lock               # Lockfile de dependencias
├── data/                 # Directorio de datos (debe crearse manualmente)
│   └── dicom_dir/       # Aquí deben ir los archivos DICOM descargados
└── src/                  # Código fuente
    └── de_p3            # Paquete
        ├── __init__.py      # Inicialización del paquete
        ├── processing.py    # ⭐ Pipeline ETL completo
        ├── config.py        # Configuración (rutas, parámetros)
        └── utils.py         # Utilidades (hashing, normalización)
```

## Configuración de Datos 

Este proyecto **no** incluye los datos de imágenes médicas. Debes descargarlos manualmente.

1. **Descargar Datos**: Ve a Kaggle y descarga los archivos DICOM:

   * **Enlace**: [SIIM-ACR Pneumothorax Segmentation Data](https://www.kaggle.com/datasets/kmader/siim-medical-images?select=dicom_dir)

   * Necesitarás descargar los archivos del directorio `dicom_dir`.

2. **Crear Estructura de Carpetas**:

   * En la raíz de este proyecto, crea una carpeta llamada `data`.

   * Dentro de `data`, crea otra carpeta llamada `dicom_dir`.

   * La ruta final debe ser: `data/dicom_dir/`.

3. **Colocar Datos**: Mueve todos los archivos `.dcm` que descargaste de Kaggle dentro de la carpeta `data/dicom_dir/`.

El script está configurado para leer los datos de esta ubicación, según se define en el archivo `.env` (`DATA_DIR="data"`) y `src/de_p3/config.py`.

## Requisitos

* Python >= 3.12

* UV (gestor de paquetes)

* **MongoDB Community Edition** (debe estar ejecutándose)

* MongoDB Compass (opcional, para visualizar datos)

## Instalación

### 1. Instalar MongoDB

Descargar e instalar desde: https://www.mongodb.com/try/download/community

Iniciar MongoDB:

```
# Windows (PowerShell como administrador)
net start MongoDB

# O ejecutar manualmente:
mongod
```

### 2. Opciones de Instalación del Paquete

Elige **una** de las siguientes opciones:

#### Opción 1: Instalación Local (Recomendada para ejecutar)

Esta opción utiliza `uv` para crear un entorno virtual y sincronizar las dependencias exactas del proyecto.

```
# 1. Clona el repositorio
git clone [https://github.com/antonv18/DE_p3.git](https://github.com/antonv18/DE_p3.git)
cd DE_p3

# 2. Sincroniza el entorno y las dependencias
uv sync
```

#### Opción 2: Instalación desde GitHub (Pip)

Esta opción instala el paquete directamente desde GitHub usando `pip`.

```
# Sintaxis correcta usando git+
pip install git+[https://github.com/antonv18/DE_p3.git](https://github.com/antonv18/DE_p3.git)
```

#### Opción 3: Instalación Local (Editable para desarrollo)

Esta opción clona el repositorio e instala el paquete en "modo editable", lo que significa que los cambios en el código fuente se reflejan inmediatamente.

```
# 1. Clona el repositorio
git clone [https://github.com/antonv18/DE_p3.git](https://github.com/antonv18/DE_p3.git)
cd DE_p3

# 2. Instala el paquete en modo editable
# (pip instalará las dependencias listadas en pyproject.toml)
pip install -e .
```

## Uso

Asegúrate de tener MongoDB ejecutándose y los datos en la carpeta `data/dicom_dir/`.

### Ejecutar el pipeline ETL completo:

**Opción 1 (Recomendada si usaste `uv sync`):**

```
# Ejecuta el script definido en pyproject.toml
uv run run-pipeline-mongo
```

**Opción 2 (Módulo directo):**

```
# Funciona con cualquier método de instalación
uv run python -m de_p3.processing

# O si no usas uv:
python -m de_p3.processing
```

## Pipeline ETL

El pipeline implementa las siguientes fases:

### 1. **Extracción (Extract)**

* Carga archivos DICOM desde `data/dicom_dir/`

* Extrae metadata: PatientID, PatientAge, PatientSex, StudyDate, Modality, PixelSpacing, ContrastAgent, etc.

### 2. **Transformación (Transform)**

* **Normalización de edad**: Convierte formato DICOM ('061Y') a entero (61)

* **Normalización de PixelSpacing**: Redondea a bins predefinidos (0.6, 0.65, 0.7, 0.75, 0.8), separado en X e Y

* **Normalización de ContrastAgent**: Estandariza valores vacíos/inválidos

* **Conversión de imágenes**: DICOM → JPEG (256x256, normalizado 0-255)

* **Generación de surrogate keys**: Hashes MD5 para identificadores únicos

* **Extracción de campos adicionales**: BodyPartExamined, PatientPosition, ExposureTime, Rows, Columns, PhotometricInterpretation, ManufacturerModelName

### 3. **Carga (Load)**

* Modelo relacional en MongoDB (database: `medical_imaging_dw`)

  * **patient_dim**: Datos demográficos de pacientes

  * **station_dim**: Información de equipos/estaciones

  * **protocol_dim**: Protocolos de adquisición

  * **date_dim**: Dimensión temporal

  * **image_dim**: Características técnicas de imagen

  * **fact_table**: Tabla de hechos (relaciona todas las dimensiones)

### 4. **Visualización**

* Grid 4x4 con las primeras 16 imágenes DICOM

* Se guarda como `dicom_grid_output.png`

## Funciones Implementadas

### `surrogate_key(values)`

Genera una clave sustituta única (hash MD5) a partir de un diccionario de valores.

### `get_or_create(collection, values, pk_name)`

Busca un registro en MongoDB. Si no existe, lo inserta usando surrogate key.

### `format_age(age_str)`

Convierte edad DICOM ('061Y') a entero (61).

### `normalize_pixel_spacing(raw_value)`

Redondea pixel spacing al bin más cercano \[0.6, 0.65, 0.7, 0.75, 0.8\].

### `normalize_contrast_agent(val)`

Estandariza metadata de agente de contraste.

### `dicom_to_jpeg(input_path, output_dir, size)`

Convierte archivo DICOM a JPEG (normalizado y redimensionado).

## Dependencias Principales

* **pandas**: Manipulación de datos y DataFrames

* **numpy**: Operaciones numéricas

* **pydicom**: Lectura de archivos DICOM

* **matplotlib**: Visualización de imágenes

* **scikit-image**: Procesamiento de imágenes

* **seaborn**: Visualización estadística

* **pymongo**: Cliente de Python para MongoDB

## Configuración

Edita `.env` para ajustar:

```
DATA_DIR="data"
DB_HOST="localhost"
DB_PORT=27017
```