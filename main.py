"""
MIT License

Copyright (c) 2024 Guillaume CLEMENT
https://www.linkedin.com/in/guillaume-clement-erp-cloud/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import csv
from bs4 import BeautifulSoup
from pathlib import Path

def get_relative_path(root_dir: str, file_path: str) -> str:
    """
    Calcule le chemin relatif d'un fichier par rapport au répertoire racine.
    Retourne le nom du répertoire parent relatif.
    """
    root = Path(root_dir).resolve()
    file = Path(file_path).resolve()
    try:
        relative = file.relative_to(root)
        # Si le fichier est directement dans le répertoire racine, retourne un string vide
        if len(relative.parts) == 1:
            return ""
        # Sinon retourne le chemin du répertoire parent
        return str(relative.parent)
    except ValueError:
        return ""

def get_metadata_from_html(file_path: str) -> dict:
    """
    Extrait les métadonnées d'un fichier HTML.
    """
    try:
        # Garde l'encodage UTF-8 pour la lecture des fichiers HTML
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extraction des métadonnées
        metadata = {
            'keywords': '',
            'description': '',
            'module': '',
            'title': ''
        }
        
        # Recherche des meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if name == 'keywords':
                metadata['keywords'] = content
            elif name == 'description':
                metadata['description'] = content
            elif name == 'module':
                metadata['module'] = content
        
        # Recherche du title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.string or ''
            
        return metadata
        
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")
        return {
            'keywords': '',
            'description': '',
            'module': '',
            'title': ''
        }

def scan_directory(root_dir: str, output_file: str):
    """
    Scanne récursivement un répertoire pour trouver les fichiers HTML et HTM,
    extrait leurs métadonnées et les écrit dans un fichier CSV.
    """
    html_files = []
    
    # Parcours récursif du répertoire
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.html', '.htm')):
                full_path = os.path.join(root, file)
                
                # Obtention du chemin relatif
                rel_dir = get_relative_path(root_dir, full_path)
                
                # Obtention du nom de fichier sans extension
                filename = os.path.splitext(file)[0]
                
                # Extraction des métadonnées
                metadata = get_metadata_from_html(full_path)
                
                # Stockage des informations
                html_files.append({
                    'relative_dir': rel_dir,
                    'filename': filename,
                    'keywords': metadata['keywords'],
                    'description': metadata['description'],
                    'module': metadata['module'],
                    'title': metadata['title']
                })
    
    # Écriture dans le fichier CSV avec Windows-1252
    if html_files:
        with open(output_file, 'w', newline='', encoding='cp1252', errors='replace') as f:
            writer = csv.DictWriter(f, 
                fieldnames=[
                    'relative_dir', 'filename', 'keywords', 
                    'description', 'module', 'title'
                ],
                delimiter=';',
                quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(html_files)
        print(f"Scan terminé. {len(html_files)} fichiers HTML traités.")
    else:
        print("Aucun fichier HTML trouvé.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python script.py <répertoire_source> <fichier_sortie.csv>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_csv = sys.argv[2]
    
    if not os.path.isdir(source_dir):
        print(f"Erreur: Le répertoire {source_dir} n'existe pas.")
        sys.exit(1)
    
    scan_directory(source_dir, output_csv)