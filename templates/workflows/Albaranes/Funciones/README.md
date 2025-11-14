# Procesador de Documentos con Azure Document Intelligence

Script Python para extraer información OCR de documentos usando el servicio Azure Document Intelligence.

## Requisitos

- Python 3.8+
- UV (gestor de paquetes)

## Instalación

1. Instalar dependencias:

```bash
uv pip install -r requirements.txt
```

## Configuración

1. Crear archivo `.env` en este directorio con las credenciales de Azure:

```env
DOCUMENT_INTELLIGENCE_ENDPOINT=https://tu-endpoint.cognitiveservices.azure.com/
DOCUMENT_INTELLIGENCE_KEY=tu-clave-api
```

## Uso

Ejecutar el script:

```bash
uv run process_document.py
```

El script procesará el documento especificado en `DOCUMENT_PATH` y guardará los resultados en `output/document_analysis.json`.

## Salida

El archivo JSON generado contiene:

- **document_content**: Contenido completo extraído del documento
- **styles**: Información sobre estilos detectados (ej: escritura manuscrita)
- **pages**: Array con información de cada página:
  - **lines**: Líneas de texto con bounding boxes y confianza
  - **words**: Palabras individuales con bounding boxes y confianza

## Estructura del Proyecto

```
Funciones/
├── process_document.py      # Script principal
├── requirements.txt         # Dependencias
├── .env                     # Credenciales (no versionar)
├── README.md               # Este archivo
└── output/                 # Resultados JSON generados
```

## Notas

- Las credenciales en `.env` no deben versionarse
- El script soporta archivos locales y URLs
- Los resultados se guardan automáticamente en formato JSON
