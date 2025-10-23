# Estructura del Proyecto P3

## ✅ Archivos Finales (Limpieza Completada)

```
p3/
├── main.py               # Punto de entrada principal
├── README.md             # Documentación del proyecto
├── PROJECT_STRUCTURE.md  # Este archivo
├── pyproject.toml        # Dependencias (UV)
├── .gitignore            # Archivos ignorados
├── data/                 # 📦 Datos del proyecto
│   ├── dicom_dir/       # 100 archivos DICOM
│   ├── tiff_images/     # 100 imágenes TIFF
│   ├── overview.csv     # Metadata
│   └── full_archive.npz # Numpy archive
└── src/                  # Código fuente
    ├── __init__.py      # Paquete Python
    ├── processing.py    # ⭐ Script principal - Procesamiento DICOM
    ├── config.py        # ⚙️ Configuración (rutas)
    └── utils.py         # 🛠️ Utilidades (logging)
```

## 🎯 Archivo Principal: `src/processing.py`

**Funcionalidad:**
- Carga 100 archivos DICOM desde `data/dicom_dir/`
- Crea DataFrame con pandas (path + filename)
- Visualiza grid 4x4 de 16 imágenes
- Guarda resultado como PNG

**Ejecutar:**
```bash
# Opción 1 (desde main.py)
uv run main.py

# Opción 2 (módulo directo)
uv run python -m src.processing
```

## 📁 Archivos Eliminados

- ❌ `src/database.py` - No necesario aún
- ❌ `src/data_loader.py` - No necesario aún
- ❌ `src/dicom_analyzer.py` - Funcionalidad en processing.py
- ❌ `src/image_processor.py` - No necesario aún
- ❌ `src/visualization.py` - No necesario aún
- ❌ `examples/` - Carpeta eliminada
- ❌ Imágenes de prueba generadas

## 🚀 Siguiente Paso

Seguir el enunciado de la práctica y agregar funcionalidades según se necesiten.

## 📝 Comandos Útiles

```bash
# Ejecutar procesamiento (opción 1)
uv run main.py

# Ejecutar procesamiento (opción 2)
uv run python -m src.processing

# Agregar dependencias
uv add nombre-paquete

# Ver estructura
ls src/
```
