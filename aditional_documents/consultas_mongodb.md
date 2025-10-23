# Consultas MongoDB - Apartado 4

## ⚠️ NOTA: Este archivo está desactualizado

**Por favor, usa el archivo actualizado:** `consultas_mongodb_nuevo_modelo.md`

El modelo de datos ha sido actualizado de un modelo dimensional a un modelo relacional.

---

## Base de Datos: `medical_imaging_dw`

## 📊 Esquema del Modelo Relacional (Actualizado)

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

---

## 🔄 Cambios Principales

| Antes | Ahora |
|-------|-------|
| `dim_patient` | `PATIENT` |
| `dim_protocol` | `PROTOCOL` |
| `dim_image` | `IMAGE` |
| `dim_station` | `STATION` |
| `dim_time` | `DATE` |
| `fact_table` | `STUDY` |

---

### 1️⃣ Consultas Simples (Filter en Documents)

#### Pacientes masculinos
Colección: `PATIENT`
```json
{ "sex": "M" }
```

#### Pacientes mayores de 60 años
Colección: `dim_patient`
```json
{ "PatientAge": { "$gte": 60 } }
```

#### Protocolos sin contraste
Colección: `dim_protocol`
```json
{ "ContrastAgent": "No contrast agent" }
```

#### Estudios de tipo CT
Colección: `dim_protocol`
```json
{ "Modality": "CT" }
```

#### Estaciones del fabricante SIEMENS
Colección: `dim_station`
```json
{ "Manufacturer": "SIEMENS" }
```

---

## 2️⃣ Aggregations (Consultas Avanzadas)

### Ejemplo 1: Contar pacientes por sexo

**Pipeline:**
```javascript
// Stage 1: JOIN con dim_patient
{
  "$lookup": {
    "from": "dim_patient",
    "localField": "patient_sk",
    "foreignField": "patient_sk",
    "as": "patient"
  }
}

// Stage 2: Desempaquetar array
{
  "$unwind": "$patient"
}

// Stage 3: Agrupar por sexo y contar
{
  "$group": {
    "_id": "$patient.PatientSex",
    "count": { "$sum": 1 }
  }
}

// Stage 4: Ordenar descendente
{
  "$sort": { "count": -1 }
}
```

**Resultado esperado:**
```json
[
  { "_id": "M", "count": 60 },
  { "_id": "F", "count": 40 }
]
```

---

### Ejemplo 2: Promedio de edad por sexo

**Pipeline:**
```javascript
// Stage 1: JOIN
{
  "$lookup": {
    "from": "dim_patient",
    "localField": "patient_sk",
    "foreignField": "patient_sk",
    "as": "patient"
  }
}

// Stage 2: Unwind
{
  "$unwind": "$patient"
}

// Stage 3: Calcular promedio
{
  "$group": {
    "_id": "$patient.PatientSex",
    "averageAge": { "$avg": "$patient.PatientAge" },
    "count": { "$sum": 1 },
    "minAge": { "$min": "$patient.PatientAge" },
    "maxAge": { "$max": "$patient.PatientAge" }
  }
}

// Stage 4: Formatear salida
{
  "$project": {
    "_id": 0,
    "sex": "$_id",
    "averageAge": { "$round": ["$averageAge", 1] },
    "totalPatients": "$count",
    "ageRange": {
      "$concat": [
        { "$toString": "$minAge" },
        "-",
        { "$toString": "$maxAge" }
      ]
    }
  }
}
```

---

### Ejemplo 3: Distribución de uso de contraste

**Pipeline:**
```javascript
// Stage 1: JOIN con dim_protocol
{
  "$lookup": {
    "from": "dim_protocol",
    "localField": "protocol_sk",
    "foreignField": "protocol_sk",
    "as": "protocol"
  }
}

// Stage 2: Unwind
{
  "$unwind": "$protocol"
}

// Stage 3: Agrupar por agente de contraste
{
  "$group": {
    "_id": "$protocol.ContrastAgent",
    "scanCount": { "$sum": 1 }
  }
}

// Stage 4: Ordenar
{
  "$sort": { "scanCount": -1 }
}

// Stage 5: Proyectar
{
  "$project": {
    "_id": 0,
    "contrastAgent": "$_id",
    "scans": "$scanCount"
  }
}
```

---

### Ejemplo 4: Top fabricantes de equipos (por estaciones)

**Pipeline:**
```javascript
// Stage 1: JOIN con dim_station
{
  "$lookup": {
    "from": "dim_station",
    "localField": "station_sk",
    "foreignField": "station_sk",
    "as": "station"
  }
}

// Stage 2: Unwind
{
  "$unwind": "$station"
}

// Stage 3: Agrupar por fabricante
{
  "$group": {
    "_id": "$station.Manufacturer",
    "scanCount": { "$sum": 1 },
    "stations": { "$addToSet": "$station.StationName" }
  }
}

// Stage 4: Ordenar
{
  "$sort": { "scanCount": -1 }
}

// Stage 5: Proyectar
{
  "$project": {
    "_id": 0,
    "manufacturer": "$_id",
    "totalScans": "$scanCount",
    "uniqueStations": { "$size": "$stations" }
  }
}
```

---

### Ejemplo 5: Análisis temporal (scans por mes)

**Pipeline:**
```javascript
// Stage 1: JOIN con dim_time
{
  "$lookup": {
    "from": "dim_time",
    "localField": "time_sk",
    "foreignField": "time_sk",
    "as": "time"
  }
}

// Stage 2: Unwind
{
  "$unwind": "$time"
}

// Stage 3: Agrupar por año y mes
{
  "$group": {
    "_id": {
      "year": "$time.Year",
      "month": "$time.Month"
    },
    "scanCount": { "$sum": 1 }
  }
}

// Stage 4: Ordenar por fecha
{
  "$sort": { "_id.year": 1, "_id.month": 1 }
}

// Stage 5: Formatear salida
{
  "$project": {
    "_id": 0,
    "period": {
      "$concat": ["$_id.year", "-", "$_id.month"]
    },
    "scans": "$scanCount"
  }
}
```

---

### Ejemplo 6: Join completo (todas las dimensiones)

**Pipeline para ver datos completos de un scan:**
```javascript
// Stage 1: JOIN con dim_patient
{
  "$lookup": {
    "from": "dim_patient",
    "localField": "patient_sk",
    "foreignField": "patient_sk",
    "as": "patient"
  }
}

// Stage 2: JOIN con dim_protocol
{
  "$lookup": {
    "from": "dim_protocol",
    "localField": "protocol_sk",
    "foreignField": "protocol_sk",
    "as": "protocol"
  }
}

// Stage 3: JOIN con dim_image
{
  "$lookup": {
    "from": "dim_image",
    "localField": "image_sk",
    "foreignField": "image_sk",
    "as": "image"
  }
}

// Stage 4: JOIN con dim_station
{
  "$lookup": {
    "from": "dim_station",
    "localField": "station_sk",
    "foreignField": "station_sk",
    "as": "station"
  }
}

// Stage 5: JOIN con dim_time
{
  "$lookup": {
    "from": "dim_time",
    "localField": "time_sk",
    "foreignField": "time_sk",
    "as": "time"
  }
}

// Stage 6-10: Unwind todos los arrays
{
  "$unwind": "$patient"
}
{
  "$unwind": "$protocol"
}
{
  "$unwind": "$image"
}
{
  "$unwind": "$station"
}
{
  "$unwind": "$time"
}

// Stage 11: Proyectar solo campos relevantes
{
  "$project": {
    "_id": 0,
    "patientInfo": {
      "id": "$patient.PatientID",
      "age": "$patient.PatientAge",
      "sex": "$patient.PatientSex"
    },
    "protocolInfo": {
      "modality": "$protocol.Modality",
      "description": "$protocol.StudyDescription",
      "contrast": "$protocol.ContrastAgent",
      "sliceThickness": "$protocol.SliceThickness"
    },
    "imageInfo": {
      "pixelSpacing": "$image.PixelSpacing",
      "kvp": "$image.KVP",
      "manufacturer": "$image.Manufacturer"
    },
    "stationInfo": {
      "name": "$station.StationName",
      "manufacturer": "$station.Manufacturer"
    },
    "timeInfo": {
      "date": "$time.StudyDate",
      "time": "$time.StudyTime",
      "year": "$time.Year",
      "month": "$time.Month"
    },
    "files": {
      "dicom": "$original_dicom_path",
      "jpeg": "$jpeg_filename"
    }
  }
}

// Stage 12: Limitar resultados
{
  "$limit": 5
}
```

---

## 3️⃣ Consultas Útiles para el Análisis

### Distribución de edades (histograma)
```javascript
// En fact_table, agregar pipeline:
[
  {
    "$lookup": {
      "from": "dim_patient",
      "localField": "patient_sk",
      "foreignField": "patient_sk",
      "as": "patient"
    }
  },
  {
    "$unwind": "$patient"
  },
  {
    "$bucket": {
      "groupBy": "$patient.PatientAge",
      "boundaries": [40, 50, 60, 70, 80, 90],
      "default": "90+",
      "output": {
        "count": { "$sum": 1 }
      }
    }
  }
]
```

### Calidad de imagen por estación
```javascript
// Análisis de pixel spacing y KVP por fabricante/estación
[
  {
    "$lookup": {
      "from": "dim_image",
      "localField": "image_sk",
      "foreignField": "image_sk",
      "as": "image"
    }
  },
  {
    "$lookup": {
      "from": "dim_station",
      "localField": "station_sk",
      "foreignField": "station_sk",
      "as": "station"
    }
  },
  {
    "$unwind": "$image"
  },
  {
    "$unwind": "$station"
  },
  {
    "$group": {
      "_id": {
        "manufacturer": "$station.Manufacturer",
        "station": "$station.StationName"
      },
      "avgPixelSpacing": { "$avg": "$image.PixelSpacing" },
      "avgKVP": { "$avg": "$image.KVP" },
      "scanCount": { "$sum": 1 }
    }
  },
  {
    "$sort": { "scanCount": -1 }
  }
]
```

### Scans por mes (serie temporal)
```javascript
[
  {
    "$lookup": {
      "from": "dim_time",
      "localField": "time_sk",
      "foreignField": "time_sk",
      "as": "time"
    }
  },
  {
    "$unwind": "$time"
  },
  {
    "$group": {
      "_id": {
        "year": "$time.Year",
        "month": "$time.Month"
      },
      "scans": { "$sum": 1 }
    }
  },
  {
    "$sort": { "_id.year": 1, "_id.month": 1 }
  },
  {
    "$project": {
      "_id": 0,
      "period": {
        "$concat": [
          { "$toString": "$_id.year" },
          "-",
          { "$toString": "$_id.month" }
        ]
      },
      "scans": 1
    }
  }
]
```

### Pacientes únicos con múltiples scans
```javascript
[
  {
    "$lookup": {
      "from": "dim_patient",
      "localField": "patient_sk",
      "foreignField": "patient_sk",
      "as": "patient"
    }
  },
  {
    "$unwind": "$patient"
  },
  {
    "$group": {
      "_id": "$patient.PatientID",
      "scanCount": { "$sum": 1 },
      "age": { "$first": "$patient.PatientAge" },
      "sex": { "$first": "$patient.PatientSex" }
    }
  },
  {
    "$match": {
      "scanCount": { "$gt": 1 }
    }
  },
  {
    "$sort": { "scanCount": -1 }
  }
]
```

---

## 💡 Consejos para MongoDB Compass

1. **Ejecuta las consultas paso a paso**: Agrega stages uno por uno para ver cómo se transforman los datos
2. **Copiar queries**: Selecciona el pipeline completo y copia directamente al campo "Aggregations"
3. **Ver resultados intermedios**: Compass muestra el output de cada stage
4. **Guarda tus pipelines**: Click en "Save Pipeline" para reutilizarlos
5. **Exporta resultados**: Puedes exportar a JSON o CSV
6. **Performance**: Si tarda mucho, añade `{ "$limit": 100 }` al final
7. **Usa el AI Assistant**: Compass tiene IA integrada para generar consultas
8. **Valida con EXPLAIN**: Click en "Explain" para ver el plan de ejecución

---

## 📊 Estructura del Data Warehouse (recordatorio)

```
medical_imaging_dw/
├── PATIENT (sex, age)
├── STATION (manufacturer, model)
├── PROTOCOL (body_part, contrast_agent, patient_position)
├── DATE (year, month)
├── IMAGE (rows, columns, pixel_spacing_x, pixel_spacing_y, slice_thickness, photometric_interp)
└── STUDY (FKs: patient_id, station_id, protocol_id, image_id, study_date + exposure_time, file_path)
```

---

## ⚠️ AVISO IMPORTANTE

**Este archivo contiene información desactualizada.**

Para consultas actualizadas con el nuevo modelo relacional, consulta:
📄 **`consultas_mongodb_nuevo_modelo.md`**

El nuevo modelo incluye:
- ✅ 7 campos nuevos extraídos de DICOM
- ✅ Estructura relacional mejorada
- ✅ Consultas optimizadas
- ✅ Ejemplos completos de JOIN entre todas las entidades

---

## 📚 Recursos

- [MongoDB Aggregation Docs](https://docs.mongodb.com/manual/aggregation/)
- [Aggregation Pipeline Stages](https://docs.mongodb.com/manual/reference/operator/aggregation-pipeline/)
- [MongoDB Compass Tutorial](https://docs.mongodb.com/compass/current/)
- **Consultas actualizadas**: `consultas_mongodb_nuevo_modelo.md` ⭐

---

**¡Usa el archivo `consultas_mongodb_nuevo_modelo.md` para consultas actualizadas!** 🚀
