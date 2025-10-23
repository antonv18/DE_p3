# 📊 Nuevo Modelo Relacional - Resumen de Cambios

## 🔄 Cambios Principales

### Modelo Anterior (Dimensional)
```
- dim_patient (patient_sk, PatientID, Age, Sex)
- dim_protocol (protocol_sk, Modality, StudyDescription, etc.)
- dim_image (image_sk, PixelSpacing, KVP, Manufacturer)
- dim_station (station_sk, StationName, Manufacturer)
- dim_time (time_sk, StudyDate, Year, Month, etc.)
- fact_table (FKs + paths)
```

### Modelo Actual (Relacional según especificación)
```
- PATIENT (patient_id PK, sex, age)
- STATION (station_id PK, manufacturer, model)
- PROTOCOL (protocol_id PK, body_part, contrast_agent, patient_position)
- DATE (date_id PK, year, month)
- IMAGE (image_id PK, rows, columns, pixel_spacing_x, pixel_spacing_y, slice_thickness, photometric_interp)
- STUDY (FKs: patient_id, station_id, protocol_id, image_id, study_date + exposure_time, file_path)
```

---

## 📋 Mapeo de Etiquetas DICOM

### PATIENT
| Atributo | Etiqueta DICOM | Descripción |
|----------|----------------|-------------|
| sex | (0010, 0040) | Sexo del paciente (M/F/U) |
| age | (0010, 1010) | Edad del paciente (años) |

### STATION
| Atributo | Etiqueta DICOM | Descripción |
|----------|----------------|-------------|
| manufacturer | (0008, 0070) | Fabricante del equipo |
| model | (0008, 1090) | Modelo del equipo |

### PROTOCOL
| Atributo | Etiqueta DICOM | Descripción |
|----------|----------------|-------------|
| body_part | (0018, 0015) | Parte del cuerpo examinada |
| contrast_agent | (0018, 0010) | Agente de contraste usado |
| patient_position | (0018, 5100) | Posición del paciente (HFS, FFS, etc.) |

### DATE
| Atributo | Derivado de | Descripción |
|----------|-------------|-------------|
| year | StudyDate (0008, 0020) | Año del estudio (YYYY) |
| month | StudyDate (0008, 0020) | Mes del estudio (MM) |

### IMAGE
| Atributo | Etiqueta DICOM | Descripción |
|----------|----------------|-------------|
| rows | (0028, 0010) | Número de filas de la imagen |
| columns | (0028, 0011) | Número de columnas de la imagen |
| pixel_spacing_x | (0028, 0030)[1] | Espaciado de píxeles en X (mm) |
| pixel_spacing_y | (0028, 0030)[0] | Espaciado de píxeles en Y (mm) |
| slice_thickness | (0018, 0050) | Grosor del corte (mm) |
| photometric_interp | (0028, 0004) | Interpretación fotométrica |

### STUDY (Tabla de hechos)
| Atributo | Etiqueta DICOM | Descripción |
|----------|----------------|-------------|
| patient_id | FK | Referencia a PATIENT |
| station_id | FK | Referencia a STATION |
| protocol_id | FK | Referencia a PROTOCOL |
| image_id | FK | Referencia a IMAGE |
| study_date | FK | Referencia a DATE |
| exposure_time | (0018, 1150) | Tiempo de exposición (ms) |
| file_path | (0018, 1151) | Ruta del archivo DICOM |

---

## 🔑 Claves Primarias y Foráneas

### Claves Primarias (PKs)
Todas las entidades usan **MD5 hash** como clave primaria:
- `patient_id` = MD5(sex + age)
- `station_id` = MD5(manufacturer + model)
- `protocol_id` = MD5(body_part + contrast_agent + patient_position)
- `date_id` = MD5(year + month)
- `image_id` = MD5(rows + columns + pixel_spacing_x + pixel_spacing_y + slice_thickness + photometric_interp)

### Claves Foráneas (FKs) en STUDY
- `patient_id` → PATIENT.patient_id
- `station_id` → STATION.station_id
- `protocol_id` → PROTOCOL.protocol_id
- `image_id` → IMAGE.image_id
- `study_date` → DATE.date_id

---

## 🆕 Nuevos Atributos Extraídos

### Antes NO se extraían:
- ✅ **ManufacturerModelName** (0008, 1090) → STATION.model
- ✅ **BodyPartExamined** (0018, 0015) → PROTOCOL.body_part
- ✅ **PatientPosition** (0018, 5100) → PROTOCOL.patient_position
- ✅ **Rows** (0028, 0010) → IMAGE.rows
- ✅ **Columns** (0028, 0011) → IMAGE.columns
- ✅ **PhotometricInterpretation** (0028, 0004) → IMAGE.photometric_interp
- ✅ **ExposureTime** (0018, 1150) → STUDY.exposure_time

### Cambios en atributos existentes:
- **PixelSpacing** ahora se divide en `pixel_spacing_x` y `pixel_spacing_y`
- **StudyDate** ahora genera entidad DATE separada con year/month
- **Manufacturer** ahora está en STATION (antes en IMAGE)

---

## 🗂️ Estructura de Archivos Modificados

### `src/processing.py`
**Cambios principales:**
1. Nuevas extracciones de metadatos DICOM (ManufacturerModelName, BodyPartExamined, etc.)
2. División de PixelSpacing en `pixel_spacing_x` y `pixel_spacing_y`
3. Creación de colecciones: PATIENT, STATION, PROTOCOL, DATE, IMAGE, STUDY
4. Nueva lógica de generación de claves primarias (MD5 hash)
5. Nuevas relaciones FK en la tabla STUDY

### `consultas_mongodb_nuevo_modelo.md`
**Nuevo archivo con:**
- Ejemplos de consultas adaptadas al nuevo modelo
- Pipelines de agregación usando los nuevos nombres de colecciones
- Queries que aprovechan los nuevos atributos (body_part, model, exposure_time, etc.)
- Diagrama ASCII del modelo relacional

---

## 🚀 Cómo Ejecutar con el Nuevo Modelo

### 1. Limpiar base de datos anterior (opcional)
```powershell
# Conectar a MongoDB
mongosh

# Seleccionar base de datos
use medical_imaging_dw

# Borrar colecciones antiguas
db.dim_patient.drop()
db.dim_protocol.drop()
db.dim_image.drop()
db.dim_station.drop()
db.dim_time.drop()
db.fact_table.drop()

# Salir
exit
```

### 2. Ejecutar pipeline ETL
```powershell
cd c:\Users\anton\Desktop\DE\p3\p3
uv run main.py
```

Esto creará las nuevas colecciones:
- PATIENT
- STATION
- PROTOCOL
- DATE
- IMAGE
- STUDY

### 3. Verificar en MongoDB Compass
1. Conectar a `mongodb://localhost:27017`
2. Abrir base de datos `medical_imaging_dw`
3. Verificar las 6 colecciones
4. Probar consultas de `consultas_mongodb_nuevo_modelo.md`

---

## 📊 Ejemplo de Documento en Cada Colección

### PATIENT
```json
{
  "_id": ObjectId("..."),
  "patient_id": "a1b2c3d4e5f6...",
  "sex": "M",
  "age": 65
}
```

### STATION
```json
{
  "_id": ObjectId("..."),
  "station_id": "f6e5d4c3b2a1...",
  "manufacturer": "SIEMENS",
  "model": "SOMATOM Definition AS"
}
```

### PROTOCOL
```json
{
  "_id": ObjectId("..."),
  "protocol_id": "1a2b3c4d5e6f...",
  "body_part": "CHEST",
  "contrast_agent": "Iodine contrast",
  "patient_position": "HFS"
}
```

### DATE
```json
{
  "_id": ObjectId("..."),
  "date_id": "9z8y7x6w5v...",
  "year": "2018",
  "month": "03"
}
```

### IMAGE
```json
{
  "_id": ObjectId("..."),
  "image_id": "5t4r3e2w1q...",
  "rows": 512,
  "columns": 512,
  "pixel_spacing_x": 0.75,
  "pixel_spacing_y": 0.75,
  "slice_thickness": 5.0,
  "photometric_interp": "MONOCHROME2"
}
```

### STUDY
```json
{
  "_id": ObjectId("..."),
  "patient_id": "a1b2c3d4e5f6...",
  "station_id": "f6e5d4c3b2a1...",
  "protocol_id": "1a2b3c4d5e6f...",
  "image_id": "5t4r3e2w1q...",
  "study_date": "9z8y7x6w5v...",
  "exposure_time": 120.5,
  "file_path": "C:\\...\\ID_0042_AGE_0071_CONTRAST_1_CT.dcm",
  "jpeg_path": "C:\\...\\jpeg_images\\ID_0042.jpeg",
  "jpeg_filename": "ID_0042.jpeg",
  "processed_date": "2025-10-22T14:30:00"
}
```

---

## ✅ Ventajas del Nuevo Modelo

1. **Conformidad DICOM**: Usa etiquetas estándar oficiales
2. **Normalización**: Elimina redundancia (manufacturer en STATION, no en IMAGE)
3. **Granularidad**: PixelSpacing separado en X e Y
4. **Trazabilidad**: ExposureTime permite análisis de calidad de radiación
5. **Flexibilidad**: PatientPosition y BodyPart permiten análisis clínicos más ricos
6. **Escalabilidad**: Modelo relacional clásico facilita joins y agregaciones

---

## 🔍 Consultas de Validación

### Contar documentos en cada colección
```javascript
// En MongoDB Compass o mongosh
db.PATIENT.countDocuments({})
db.STATION.countDocuments({})
db.PROTOCOL.countDocuments({})
db.DATE.countDocuments({})
db.IMAGE.countDocuments({})
db.STUDY.countDocuments({})
```

### Verificar FKs válidas
```javascript
// En STUDY collection
db.STUDY.aggregate([
  {
    $lookup: {
      from: "PATIENT",
      localField: "patient_id",
      foreignField: "patient_id",
      as: "patient_check"
    }
  },
  {
    $match: {
      patient_check: { $size: 0 }
    }
  }
])
// Debe retornar 0 documentos (todas las FKs son válidas)
```

---

**Modelo relacional completamente implementado según especificación!** ✅
