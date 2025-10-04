# Visual Elements Extractor for Research Papers

Este proyecto extrae elementos visuales (imágenes, figuras, tablas y gráficos) de artículos de investigación y los prepara para inserción en una base de datos MySQL.

## Características

- ✅ Extracción automática de figuras, tablas e imágenes
- ✅ Descarga y almacenamiento local de archivos
- ✅ Generación de metadatos en formato JSON
- ✅ Integración con base de datos MySQL
- ✅ Estructura compatible con el esquema de base de datos proporcionado

## Instalación

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd Extraercositas
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos (opcional):**
```bash
cp db_config.json.example db_config.json
# Editar db_config.json con tus credenciales de base de datos
```

## Uso

### 1. 📄 Extracción de un Paper Específico

```bash
# Extraer de cualquier paper
python3 extract_custom_paper.py "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/"

# Con directorio personalizado
python3 extract_custom_paper.py "https://tu-url-del-paper.com" -o mi_extraccion
```

### 2. 🔧 Extracción Básica (Paper Predefinido)

```bash
python3 run_extraction.py
```

Este comando:
- Extrae elementos visuales del paper especificado
- Descarga imágenes y figuras
- Guarda tablas como archivos HTML
- Genera metadatos en JSON

### Estructura de Archivos Generados

```
extracted_visuals/
├── images/           # Imágenes descargadas
├── tables/           # Tablas en formato HTML
├── figures/          # Figuras descargadas
├── visual_elements_metadata.json  # Metadatos completos
└── database_data.json            # Datos para base de datos
```

### Integración con Base de Datos

El script genera automáticamente datos compatibles con el esquema de base de datos proporcionado:

- **Tabla `paper`**: Información del artículo
- **Tabla `author`**: Autores del artículo
- **Tabla `paper_resource`**: Recursos visuales extraídos
- **Tabla `paper_author`**: Relación entre papers y autores

## Configuración de Base de Datos

1. **Crear archivo de configuración:**
```json
{
  "host": "localhost",
  "user": "tu_usuario",
  "password": "tu_contraseña",
  "database": "defaultdb"
}
```

2. **Ejecutar integración:**
```python
from database_integration import DatabaseIntegrator

integrator = DatabaseIntegrator(**db_config)
integrator.process_extracted_data("extracted_visuals/database_data.json")
```

## Estructura de Datos

### Metadatos JSON
```json
{
  "images": [
    {
      "type": "image",
      "number": 1,
      "alt_text": "Descripción de la imagen",
      "image_url": "https://...",
      "local_path": "images/image_1.jpg",
      "context": "Texto contextual..."
    }
  ],
  "tables": [
    {
      "type": "table",
      "number": 1,
      "caption": "Título de la tabla",
      "html_content": "<table>...</table>",
      "local_path": "tables/table_1.html",
      "data": [["Header1", "Header2"], ["Row1", "Row2"]]
    }
  ],
  "figures": [
    {
      "type": "figure",
      "number": 1,
      "caption": "Título de la figura",
      "image_url": "https://...",
      "local_path": "images/figure_1.jpg"
    }
  ]
}
```

## Personalización

### Cambiar URL del Paper
Editar `run_extraction.py`:
```python
paper_url = "https://tu-url-del-paper.com"
```

### Modificar Selectores CSS
Editar `visual_extractor.py` para ajustar los selectores según el sitio web.

## Troubleshooting

### Error de Conexión
- Verificar que la URL del paper sea accesible
- Comprobar conexión a internet

### Error de Base de Datos
- Verificar credenciales en `db_config.json`
- Asegurar que la base de datos existe
- Comprobar que las tablas están creadas según el esquema

### Archivos No Descargados
- Verificar permisos de escritura en el directorio
- Comprobar que las URLs de imágenes son válidas

## Dependencias

- `requests`: Para descargar contenido web
- `beautifulsoup4`: Para parsing HTML
- `lxml`: Parser XML/HTML
- `mysql-connector-python`: Para integración con MySQL
- `Pillow`: Para procesamiento de imágenes

## Licencia

Este proyecto está bajo la licencia MIT.
