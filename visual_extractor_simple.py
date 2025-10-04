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
        """Extract figures and their captions from the page."""
        figures = []
        
        # Look for figure elements with various patterns
        figure_selectors = [
            'div.figure',
            'div.fig',
            'div[class*="figure"]',
            'div[class*="fig"]',
            'figure',
            'div[data-fig]'
        ]
        
        for selector in figure_selectors:
            figure_elements = soup.select(selector)
            
            for i, fig in enumerate(figure_elements):
                figure_data = {
                    'type': 'figure',
                    'number': i + 1,
                    'caption': '',
                    'image_url': '',
                    'local_path': '',
                    'context': ''
                }
                
                # Extract caption
                caption_selectors = [
                    'div.caption',
                    'div.fig-caption',
                    'p.caption',
                    'span.caption',
                    'div[class*="caption"]'
                ]
                
                for cap_sel in caption_selectors:
                    caption = fig.select_one(cap_sel)
                    if caption:
                        figure_data['caption'] = caption.get_text(strip=True)
                        break
                
                # Extract image URL
                img = fig.find('img')
                if img and img.get('src'):
                    img_url = img.get('src')
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(self.paper_url, img_url)
                    
                    figure_data['image_url'] = img_url
                    
                    # Download image
                    local_path = self.download_image(img_url, f"figure_{i+1}")
                    figure_data['local_path'] = str(local_path) if local_path else ''
                
                # Extract context
                parent = fig.parent
                if parent:
                    context_text = parent.get_text(strip=True)
                    figure_data['context'] = context_text[:500] + "..." if len(context_text) > 500 else context_text
                
                if figure_data['image_url'] or figure_data['caption']:
                    figures.append(figure_data)
        
        return figures

    def extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract tables and their captions from the page."""
        tables = []
        
        # Find all table elements
        table_elements = soup.find_all('table')
        
        for i, table in enumerate(table_elements):
            table_data = {
                'type': 'table',
                'number': i + 1,
                'caption': '',
                'html_content': str(table),
                'local_path': '',
                'context': ''
            }
            
            # Look for caption
            caption = table.find('caption')
            if caption:
                table_data['caption'] = caption.get_text(strip=True)
            else:
                # Look for caption in previous sibling
                prev_sibling = table.find_previous_sibling()
                if prev_sibling and ('caption' in prev_sibling.get('class', []) or 
                                   'table-caption' in prev_sibling.get('class', [])):
                    table_data['caption'] = prev_sibling.get_text(strip=True)
                else:
                    # Look for caption in parent div
                    parent = table.parent
                    if parent:
                        caption_elem = parent.find(['div', 'p'], class_=re.compile(r'caption|table-caption'))
                        if caption_elem:
                            table_data['caption'] = caption_elem.get_text(strip=True)
            
            # Extract table data
            table_data['data'] = self.extract_table_data(table)
            
            # Save table as HTML file
            table_file = self.output_dir / "tables" / f"table_{i+1}.html"
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(f"<html><head><meta charset='utf-8'></head><body>{str(table)}</body></html>")
            table_data['local_path'] = str(table_file)
            
            # Extract context
            parent = table.parent
            if parent:
                context_text = parent.get_text(strip=True)
                table_data['context'] = context_text[:500] + "..." if len(context_text) > 500 else context_text
            
            tables.append(table_data)
        
        return tables

    def extract_table_data(self, table) -> List[Dict[str, Any]]:
        """Extract structured data from HTML table."""
        data = []
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = []
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                row_data.append(cell_text)
            if row_data:
                data.append(row_data)
        
        return data

    def extract_images(self, soup: BeautifulSoup, exclude_figures: bool = True) -> List[Dict[str, Any]]:
        """Extract standalone images from the page."""
        images = []
        
        # Find all img elements
        img_elements = soup.find_all('img')
        
        for i, img in enumerate(img_elements):
            # Skip images that are already captured as figures
            if exclude_figures:
                parent_figure = img.find_parent(['div', 'figure'], class_=lambda x: x and 'fig' in x.lower() if x else False)
                if parent_figure:
                    continue
                
                figure_containers = img.find_parents(['div', 'figure'], class_=lambda x: x and any(
                    keyword in x.lower() for keyword in ['figure', 'fig', 'caption']
                ) if x else False)
                if figure_containers:
                    continue
            
            # Get image URL
            img_url = img.get('src')
            if not img_url or self._should_skip_image(img, img_url):
                continue
            
            img_data = {
                'type': 'image',
                'number': len(images) + 1,
                'alt_text': img.get('alt', ''),
                'image_url': '',
                'local_path': '',
                'context': ''
            }
            
            # Process image URL
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = urljoin(self.paper_url, img_url)
            
            img_data['image_url'] = img_url
            
            # Download image
            local_path = self.download_image(img_url, f"image_{len(images)+1}")
            img_data['local_path'] = str(local_path) if local_path else ''
            
            # Extract context
            parent = img.parent
            if parent:
                context_text = parent.get_text(strip=True)
                img_data['context'] = context_text[:500] + "..." if len(context_text) > 500 else context_text
            
            if img_data['image_url']:
                images.append(img_data)
        
        return images

    def _should_skip_image(self, img, img_url: str) -> bool:
        """Check if an image should be skipped."""
        if img_url.startswith('data:'):
            return True
        
        skip_patterns = [
            'static/img/', 'icon-', 'logo', 'banner', 'header', 'footer',
            'nav-', 'button', 'arrow', 'close', 'search', 'menu', 'flag',
            'dot-gov', 'https', 'usa-icons', 'ncbi-logos'
        ]
        
        for pattern in skip_patterns:
            if pattern in img_url.lower():
                return True
        
        alt_text = img.get('alt', '').lower()
        skip_alt_patterns = [
            'logo', 'icon', 'button', 'arrow', 'close', 'search', 
            'menu', 'flag', 'banner', 'header', 'footer', 'nav'
        ]
        
        for pattern in skip_alt_patterns:
            if pattern in alt_text:
                return True
        
        # Check if image is very small
        width = img.get('width')
        height = img.get('height')
        if width and height:
            try:
                w, h = int(width), int(height)
                if w < 50 or h < 50:
                    return True
            except ValueError:
                pass
        
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
        self.extracted_elements['images'] = self.extract_images(soup)
        
        # Update total count
        total_elements = (len(self.extracted_elements['images']) + 
                         len(self.extracted_elements['tables']) + 
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
