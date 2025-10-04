#!/usr/bin/env python3
"""
Paper Extractor - Extrae metadatos y elementos visuales de un paper
Llama a los módulos simplificados para hacer la extracción completa
"""

import sys
import argparse
import json
import time
from pathlib import Path
from metadata_extractor import extract_paper_metadata
from visual_extractor_simple import extract_visual_elements

def main():
    """Función principal que extrae metadatos y elementos visuales"""
    parser = argparse.ArgumentParser(
        description='Extractor de Papers - Metadatos y elementos visuales'
    )
    
    parser.add_argument(
        'url', 
        help='URL del paper a extraer (ej: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/)'
    )
    
    parser.add_argument(
        '-o', '--output', 
        default='extracted_paper',
        help='Directorio de salida (por defecto: extracted_paper)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PAPER EXTRACTOR")
    print("="*60)
    print(f"📄 URL: {args.url}")
    print(f"📁 Salida: {args.output}")
    print()
    
    # Crear directorio de salida
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # PASO 1: Extraer metadatos
    print("🔍 Extrayendo metadatos...")
    metadata = extract_paper_metadata(args.url)
    
    if "error" in metadata:
        print(f"❌ Error en metadatos: {metadata['error']}")
    else:
        print("✅ Metadatos extraídos")
        print(f"   📄 Título: {metadata.get('title', 'N/A')[:60]}...")
        print(f"   👥 Autores: {len(metadata.get('authors', []))}")
        print(f"   📚 Revista: {metadata.get('journal', 'N/A')}")
        print(f"   🔗 DOI: {metadata.get('doi', 'N/A')}")
    
    print()
    
    # PASO 2: Extraer elementos visuales
    print("🔍 Extrayendo elementos visuales...")
    visual_elements = extract_visual_elements(args.url, args.output)
    
    if not visual_elements:
        print("❌ Error extrayendo elementos visuales")
        return False
    
    print("✅ Elementos visuales extraídos")
    print(f"   📊 Figuras: {len(visual_elements['figures'])}")
    print(f"   📋 Tablas: {len(visual_elements['tables'])}")
    print(f"   🖼️  Imágenes: {len(visual_elements['images'])}")
    print(f"   📈 Total: {visual_elements['metadata']['total_elements']}")
    
    print()
    
    # PASO 3: Combinar y guardar resultados
    print("💾 Guardando resultados...")
    
    # Crear resultado combinado
    combined_result = {
        "extraction_info": {
            "url": args.url,
            "extraction_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "output_directory": str(output_dir.absolute())
        },
        "metadata": metadata,
        "visual_elements": visual_elements
    }
    
    # Guardar JSON combinado
    json_file = output_dir / "paper_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(combined_result, f, indent=2, ensure_ascii=False)
    
    print("✅ Resultados guardados")
    print(f"📄 JSON: {json_file}")
    
    # Resumen final
    print("\n" + "="*60)
    print("EXTRACCIÓN COMPLETADA")
    print("="*60)
    print(f"📁 Directorio: {output_dir.absolute()}")
    print(f"📄 Archivo JSON: paper_data.json")
    print(f"📁 Imágenes: images/")
    print(f"📁 Tablas: tables/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
