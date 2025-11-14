"""
Script para procesar documentos con Azure Document Intelligence.
Extrae información OCR de imágenes y guarda los resultados en JSON.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import numpy as np


# Cargar variables de entorno
load_dotenv()

ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
KEY = os.getenv("DOCUMENT_INTELLIGENCE_KEY")

# Rutas
DOCUMENT_PATH = "../Albaranes de Ejemplo/Albaran 1.jpg"
OUTPUT_DIR = "./output"


def format_bounding_box(bounding_box):
    """Formatea el bounding box para mejor legibilidad."""
    if not bounding_box:
        return "N/A"
    reshaped_bounding_box = np.array(bounding_box).reshape(-1, 2)
    return [[float(x), float(y)] for x, y in reshaped_bounding_box]


def extract_document_data(document_path):
    """
    Procesa un documento con Azure Document Intelligence.
    
    Args:
        document_path: Ruta al documento (local o URL)
    
    Returns:
        dict: Datos extraídos del documento
    """
    
    # Crear cliente
    client = DocumentIntelligenceClient(
        endpoint=ENDPOINT, 
        credential=AzureKeyCredential(KEY)
    )
    
    # Leer archivo local y convertir a bytes
    with open(document_path, "rb") as f:
        document_data = f.read()
    
    # Analizar documento
    poller = client.begin_analyze_document(
        "prebuilt-read",
        AnalyzeDocumentRequest(bytes_source=document_data)
    )
    result = poller.result()
    
    # Extraer datos
    extracted_data = {
        "document_content": result.content,
        "styles": [],
        "pages": []
    }
    
    # Procesar estilos
    for style in result.styles:
        extracted_data["styles"].append({
            "is_handwritten": style.is_handwritten
        })
    
    # Procesar páginas
    for page in result.pages:
        page_data = {
            "page_number": page.page_number,
            "width": page.width,
            "height": page.height,
            "unit": page.unit,
            "lines": [],
            "words": []
        }
        
        # Procesar líneas
        for line in page.lines:
            page_data["lines"].append({
                "content": line.content,
                "bounding_box": format_bounding_box(line.polygon),
                "confidence": line.confidence if hasattr(line, 'confidence') else None
            })
        
        # Procesar palabras
        for word in page.words:
            page_data["words"].append({
                "content": word.content,
                "confidence": word.confidence,
                "bounding_box": format_bounding_box(word.polygon)
            })
        
        extracted_data["pages"].append(page_data)
    
    return extracted_data


def save_results(data, output_filename="document_analysis.json"):
    """
    Guarda los datos extraídos en un archivo JSON.
    
    Args:
        data: Datos a guardar
        output_filename: Nombre del archivo de salida
    """
    
    # Crear directorio de salida si no existe
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Resultados guardados en: {output_path}")
    return output_path


def main():
    """Función principal."""
    
    print("=" * 60)
    print("Azure Document Intelligence - Procesador de Documentos")
    print("=" * 60)
    
    # Validar credenciales
    if not ENDPOINT or not KEY:
        print("❌ Error: Credenciales no configuradas en .env")
        return
    
    # Validar archivo
    if not os.path.exists(DOCUMENT_PATH):
        print(f"❌ Error: Archivo no encontrado: {DOCUMENT_PATH}")
        return
    
    print(f"\n📄 Procesando documento: {DOCUMENT_PATH}")
    print("⏳ Enviando a Azure Document Intelligence...")
    
    try:
        # Procesar documento
        extracted_data = extract_document_data(DOCUMENT_PATH)
        
        # Guardar resultados
        output_path = save_results(extracted_data)
        
        # Mostrar resumen
        print("\n📊 Resumen de extracción:")
        print(f"   - Páginas procesadas: {len(extracted_data['pages'])}")
        if extracted_data['pages']:
            first_page = extracted_data['pages'][0]
            print(f"   - Líneas extraídas: {len(first_page['lines'])}")
            print(f"   - Palabras extraídas: {len(first_page['words'])}")
        print(f"   - Estilos detectados: {len(extracted_data['styles'])}")
        
        # Mostrar preview del contenido
        print(f"\n📝 Preview del contenido:")
        print(f"   {extracted_data['document_content'][:200]}...")
        
        print("\n✅ Procesamiento completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        raise


if __name__ == "__main__":
    main()
