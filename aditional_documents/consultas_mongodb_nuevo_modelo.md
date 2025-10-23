# 📊 Consultas MongoDB - Modelo Relacional DICOM

## Modelo de Datos

### Entidades del modelo relacional:

```
medical_imaging_dw/
├── PATIENT (patient_id PK, sex, age)
├── STATION (station_id PK, manufacturer, model)
├── PROTOCOL (protocol_id PK, body_part, contrast_agent, patient_position)
├── DATE (date_id PK, year, month)
├── IMAGE (image_id PK, rows, columns, pixel_spacing_x, pixel_spacing_y, slice_thickness, photometric_interp)
└── STUDY (FKs: station_id, patient_id, image_id, protocol_id, study_date, + exposure_time, file_path)
```

### Mapeo de etiquetas DICOM:

- **PATIENT**: (0010, 0040) sex, (0010, 1010) age
- **STATION**: (0008, 0070) manufacturer, (0008, 1090) model
- **PROTOCOL**: (0018, 0015) body_part, (0018, 0010) contrast_agent, (0018, 5100) patient_position
- **DATE**: Derivado de StudyDate (0008, 0020)
- **IMAGE**: (0028, 0010) rows, (0028, 0011) columns, (0028, 0030) pixel_spacing, (0018, 0050) slice_thickness, (0028, 0004) photometric_interp
- **STUDY**: (0018, 1150) exposure_time, (0018, 1151) file_path

---

## 🔍 Consultas Básicas

### 1. Ver todos los estudios con información del paciente

**Filtro simple en STUDY:**
```javascript
{
  "patient_id": { "$exists": true }
}
```

**Pipeline con JOIN:**
```javascript
[
  {
    "$lookup": {
      "from": "PATIENT",
      "localField": "patient_id",
      "foreignField": "patient_id",
      "as": "patient_info"
    }
  },
  {
    "$unwind": "$patient_info"
  },
  {
    "$project": {
      "_id": 0,
      "study_id": "$_id",
      "patient_sex": "$patient_info.sex",
      "patient_age": "$patient_info.age",
      "exposure_time": 1,
      "file_path": 1
    }
  },
  {
    "$limit": 10
  }
]
```

---

### 2. Análisis de edad de pacientes

**Pipeline para agrupar por rangos de edad:**
```javascript
[
  {
    "$lookup": {
      "from": "PATIENT",
      "localField": "patient_id",
      "foreignField": "patient_id",
      "as": "patient"
    }
  },
  {
    "$unwind": "$patient"
  },
  {
    "$bucket": {
      "groupBy": "$patient.age",
      "boundaries": [40, 50, 60, 70, 80, 90],
      "default": "90+",
      "output": {
        "count": { "$sum": 1 },
        "avgExposureTime": { "$avg": "$exposure_time" }
      }
    }
  }
]
```

---

### 3. Estudios con agente de contraste

**Pipeline:**
```javascript
[
  {
    "$lookup": {
      "from": "PROTOCOL",
      "localField": "protocol_id",
      "foreignField": "protocol_id",
      "as": "protocol"
    }
  },
  {
    "$unwind": "$protocol"
  },
  {
    "$match": {
      "protocol.contrast_agent": { "$ne": "No contrast agent" }
    }
  },
  {
    "$group": {
      "_id": "$protocol.contrast_agent",
      "studyCount": { "$sum": 1 },
      "avgExposure": { "$avg": "$exposure_time" }
    }
  },
  {
    "$sort": { "studyCount": -1 }
  }
]
```

---

### 4. Top fabricantes de equipos (STATION)

**Pipeline:**
```javascript
[
  {
    "$lookup": {
      "from": "STATION",
      "localField": "station_id",
      "foreignField": "station_id",
      "as": "station"
    }
  },
  {
    "$unwind": "$station"
  },
  {
    "$group": {
      "_id": {
        "manufacturer": "$station.manufacturer",
        "model": "$station.model"
      },
      "studyCount": { "$sum": 1 }
    }
  },
  {
    "$sort": { "studyCount": -1 }
  },
  {
    "$project": {
      "_id": 0,
      "manufacturer": "$_id.manufacturer",
      "model": "$_id.model",
      "totalStudies": "$studyCount"
    }
  }
]
```

---

### 5. Análisis temporal (por año y mes)

**Pipeline:**
```javascript
[
  {
    "$lookup": {
      "from": "DATE",
      "localField": "study_date",
      "foreignField": "date_id",
      "as": "date"
    }
  },
  {
    "$unwind": "$date"
  },
  {
    "$group": {
      "_id": {
        "year": "$date.year",
        "month": "$date.month"
      },
      "studyCount": { "$sum": 1 }
    }
  },
  {
    "$sort": { "_id.year": 1, "_id.month": 1 }
  },
  {
    "$project": {
      "_id": 0,
      "period": {
        "$concat": ["$_id.year", "-", "$_id.month"]
      },
      "studies": "$studyCount"
    }
  }
]
```

---

### 6. Calidad de imagen (resolución y pixel spacing)

**Pipeline para analizar características de imagen:**
```javascript
[
  {
    "$lookup": {
      "from": "IMAGE",
      "localField": "image_id",
      "foreignField": "image_id",
      "as": "image"
    }
  },
  {
    "$unwind": "$image"
  },
  {
    "$group": {
      "_id": {
        "rows": "$image.rows",
        "columns": "$image.columns"
      },
      "count": { "$sum": 1 },
      "avgPixelSpacingX": { "$avg": "$image.pixel_spacing_x" },
      "avgPixelSpacingY": { "$avg": "$image.pixel_spacing_y" },
      "avgSliceThickness": { "$avg": "$image.slice_thickness" }
    }
  },
  {
    "$sort": { "count": -1 }
  },
  {
    "$project": {
      "_id": 0,
      "resolution": {
        "$concat": [
          { "$toString": "$_id.rows" },
          "x",
          { "$toString": "$_id.columns" }
        ]
      },
      "studyCount": "$count",
      "avgPixelSpacingX": { "$round": ["$avgPixelSpacingX", 2] },
      "avgPixelSpacingY": { "$round": ["$avgPixelSpacingY", 2] },
      "avgSliceThickness": { "$round": ["$avgSliceThickness", 2] }
    }
  }
]
```

---

### 7. JOIN completo (todas las entidades)

**Pipeline para ver datos completos de un estudio:**
```javascript
[
  {
    "$lookup": {
      "from": "PATIENT",
      "localField": "patient_id",
      "foreignField": "patient_id",
      "as": "patient"
    }
  },
  {
    "$lookup": {
      "from": "STATION",
      "localField": "station_id",
      "foreignField": "station_id",
      "as": "station"
    }
  },
  {
    "$lookup": {
      "from": "PROTOCOL",
      "localField": "protocol_id",
      "foreignField": "protocol_id",
      "as": "protocol"
    }
  },
  {
    "$lookup": {
      "from": "DATE",
      "localField": "study_date",
      "foreignField": "date_id",
      "as": "date"
    }
  },
  {
    "$lookup": {
      "from": "IMAGE",
      "localField": "image_id",
      "foreignField": "image_id",
      "as": "image"
    }
  },
  {
    "$unwind": "$patient"
  },
  {
    "$unwind": "$station"
  },
  {
    "$unwind": "$protocol"
  },
  {
    "$unwind": "$date"
  },
  {
    "$unwind": "$image"
  },
  {
    "$project": {
      "_id": 0,
      "patient": {
        "sex": "$patient.sex",
        "age": "$patient.age"
      },
      "station": {
        "manufacturer": "$station.manufacturer",
        "model": "$station.model"
      },
      "protocol": {
        "body_part": "$protocol.body_part",
        "contrast_agent": "$protocol.contrast_agent",
        "patient_position": "$protocol.patient_position"
      },
      "date": {
        "year": "$date.year",
        "month": "$date.month"
      },
      "image": {
        "resolution": {
          "$concat": [
            { "$toString": "$image.rows" },
            "x",
            { "$toString": "$image.columns" }
          ]
        },
        "pixel_spacing_x": "$image.pixel_spacing_x",
        "pixel_spacing_y": "$image.pixel_spacing_y",
        "slice_thickness": "$image.slice_thickness",
        "photometric_interp": "$image.photometric_interp"
      },
      "study": {
        "exposure_time": "$exposure_time",
        "file_path": "$file_path"
      }
    }
  },
  {
    "$limit": 5
  }
]
```

---

## 🔍 Consultas Adicionales Útiles

### Distribución por sexo

```javascript
[
  {
    "$lookup": {
      "from": "PATIENT",
      "localField": "patient_id",
      "foreignField": "patient_id",
      "as": "patient"
    }
  },
  {
    "$unwind": "$patient"
  },
  {
    "$group": {
      "_id": "$patient.sex",
      "count": { "$sum": 1 }
    }
  },
  {
    "$sort": { "count": -1 }
  }
]
```

---

### Análisis de posición del paciente (PROTOCOL)

```javascript
[
  {
    "$lookup": {
      "from": "PROTOCOL",
      "localField": "protocol_id",
      "foreignField": "protocol_id",
      "as": "protocol"
    }
  },
  {
    "$unwind": "$protocol"
  },
  {
    "$group": {
      "_id": "$protocol.patient_position",
      "count": { "$sum": 1 },
      "avgExposure": { "$avg": "$exposure_time" }
    }
  },
  {
    "$sort": { "count": -1 }
  }
]
```

---

### Análisis de partes del cuerpo examinadas

```javascript
[
  {
    "$lookup": {
      "from": "PROTOCOL",
      "localField": "protocol_id",
      "foreignField": "protocol_id",
      "as": "protocol"
    }
  },
  {
    "$unwind": "$protocol"
  },
  {
    "$group": {
      "_id": "$protocol.body_part",
      "studyCount": { "$sum": 1 }
    }
  },
  {
    "$match": {
      "_id": { "$ne": "" }
    }
  },
  {
    "$sort": { "studyCount": -1 }
  }
]
```

---

## 💡 Consejos para MongoDB Compass

1. **Navegación**: Después de conectarte a `mongodb://localhost:27017`, selecciona la base de datos `medical_imaging_dw`
2. **Colecciones**: Verás 6 colecciones: PATIENT, STATION, PROTOCOL, DATE, IMAGE, STUDY
3. **Aggregations**: Haz clic en la pestaña "Aggregations" en cualquier colección (recomendado: STUDY)
4. **Copiar pipelines**: Copia el array completo `[...]` y pégalo en el editor
5. **Ejecutar por stages**: Puedes añadir stages uno por uno y ver resultados intermedios
6. **Exportar**: Usa el botón "Export" para guardar resultados en JSON/CSV
7. **Performance**: Si las consultas tardan, añade `{ "$limit": 100 }` al final

---

## 📊 Diagrama del Modelo

```
┌─────────────┐
│   PATIENT   │
│ patient_id  │◄──┐
│ sex         │   │
│ age         │   │
└─────────────┘   │
                  │
┌─────────────┐   │
│   STATION   │   │
│ station_id  │◄──┤
│ manufacturer│   │
│ model       │   │
└─────────────┘   │
                  │
┌─────────────┐   │     ┌─────────────┐
│  PROTOCOL   │   │     │    STUDY    │
│ protocol_id │◄──┼─────┤ (Fact Table)│
│ body_part   │   │     ├─────────────┤
│ contrast_ag.│   │     │ patient_id  │──┘
│ patient_pos.│   │     │ station_id  │
└─────────────┘   │     │ protocol_id │
                  │     │ image_id    │
┌─────────────┐   │     │ study_date  │
│    DATE     │   │     │ exposure_t. │
│  date_id    │◄──┤     │ file_path   │
│  year       │   │     └─────────────┘
│  month      │   │
└─────────────┘   │
                  │
┌─────────────┐   │
│    IMAGE    │   │
│  image_id   │◄──┘
│  rows       │
│  columns    │
│ pixel_sp_x  │
│ pixel_sp_y  │
│ slice_thick.│
│ photo_interp│
└─────────────┘
```

---

## 📚 Recursos

- [MongoDB Aggregation Framework](https://docs.mongodb.com/manual/aggregation/)
- [DICOM Standard Browser](https://dicom.innolitics.com/ciods)
- [MongoDB Compass Documentation](https://docs.mongodb.com/compass/current/)

---

**¡Modelo relacional completamente implementado!** 🚀
