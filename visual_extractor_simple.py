#!/usr/bin/env python3
"""
Visual Extractor Simple - Solo extrae elementos visuales de un paper específico
Versión simplificada basada en visual_extractor.py
"""

import requests
import json
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
from pathlib import Path

class SimpleVisualExtractor:
    def __init__(self, paper_url: str, output_dir: str = "extracted_visuals"):
        """
        Initialize the extractor with paper URL and output directory.
        
        Args:
            paper_url: URL of the research paper
            output_dir: Directory to save extracted visual elements
        """
        self.paper_url = paper_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "tables").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.extracted_elements = {
            'images': [],
            'tables': [],
            'figures': [],
            'metadata': {
                'source_url': paper_url,
                'total_elements': 0
            }
        }

    def fetch_page_content(self) -> Optional[BeautifulSoup]:
        """Fetch and parse the webpage content."""
        try:
            response = self.session.get(self.paper_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except requests.RequestException as e:
            print(f"Error fetching page content: {e}")
            return None

    def extract_figures(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract images from the page."""
        figures = []
        figure_number = 1  # Contador separado para figuras válidas
        
        # Buscar todas las imágenes directamente
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            # Saltar imágenes de interfaz
            img_url = img.get('src')
            if not img_url or self._should_skip_image(img, img_url):
                continue
            
            figure_data = {
                'number': figure_number,
                'image_path': ''
            }
            
            # Procesar URL de imagen
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = urljoin(self.paper_url, img_url)
            
            # Descargar imagen
            local_path = self.download_image(img_url, f"image_{figure_number}")
            if local_path:
                figure_data['image_path'] = str(local_path)
                figures.append(figure_data)
                figure_number += 1  # Solo incrementar si la imagen se descargó exitosamente
        
        return figures

    def extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract tables from the page."""
        tables = []
        
        # Find all table elements
        table_elements = soup.find_all('table')
        
        for i, table in enumerate(table_elements):
            table_data = {
                'number': i + 1,
                'table_path': ''
            }
            
            # Save table as HTML file
            table_file = self.output_dir / "tables" / f"table_{i+1}.html"
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(f"<html><head><meta charset='utf-8'></head><body>{str(table)}</body></html>")
            table_data['table_path'] = str(table_file)
            
            tables.append(table_data)
        
        return tables


    def _should_skip_image(self, img, img_url: str) -> bool:
        """Check if an image should be skipped."""
        # Solo saltar imágenes de datos base64
        if img_url.startswith('data:'):
            return True
        
        # Solo saltar imágenes obviamente de interfaz
        skip_patterns = [
            'icon-', 'logo', 'banner', 'header', 'footer',
            'nav-', 'button', 'arrow', 'close', 'search', 'menu', 'flag'
        ]
        
        for pattern in skip_patterns:
            if pattern in img_url.lower():
                return True
        
        # Solo saltar si el alt text es obviamente de interfaz
        alt_text = img.get('alt', '').lower()
        if alt_text in ['logo', 'icon', 'button', 'arrow', 'close', 'search', 'menu', 'flag']:
            return True
        
        return False

    def download_image(self, url: str, filename: str) -> Optional[Path]:
        """Download an image from URL and save it locally."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension
            parsed_url = urlparse(url)
            ext = os.path.splitext(parsed_url.path)[1]
            if not ext:
                ext = '.jpg'
            
            filename = f"{filename}{ext}"
            file_path = self.output_dir / "images" / filename
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return None

    def extract_visual_elements(self):
        """Extract all visual elements from the paper."""
        # Fetch page content
        soup = self.fetch_page_content()
        if not soup:
            return None
        
        # Extract different types of visual elements
        self.extracted_elements['figures'] = self.extract_figures(soup)
        self.extracted_elements['tables'] = self.extract_tables(soup)
        self.extracted_elements['images'] = []  # No extraemos imágenes independientes
        
        # Update total count
        total_elements = (len(self.extracted_elements['tables']) + 
                         len(self.extracted_elements['figures']))
        self.extracted_elements['metadata']['total_elements'] = total_elements
        
        return self.extracted_elements

def extract_visual_elements(paper_url: str, output_dir: str = "extracted_visuals"):
    """
    Función simple para extraer elementos visuales de un paper
    
    Args:
        paper_url: URL del paper
        output_dir: Directorio de salida
        
    Returns:
        dict: Elementos visuales extraídos
    """
    extractor = SimpleVisualExtractor(paper_url, output_dir)
    return extractor.extract_visual_elements()

if __name__ == "__main__":
    # Prueba
    test_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/"
    result = extract_visual_elements(test_url)
    print("Resultado:", result)
