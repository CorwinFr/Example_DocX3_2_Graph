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
import networkx as nx
import json

class KnowledgeGraphGenerator:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes_info = {}
        
    def get_node_id(self, relative_dir: str, filename: str) -> str:
        """Génère un identifiant unique pour un nœud."""
        if relative_dir:
            return f"{relative_dir}/{filename}"
        return filename

    def normalize_path(self, current_dir: str, href: str) -> str:
        """Normalise un chemin relatif vers un chemin absolu."""
        try:
            # Ignorer les liens externes et ancres
            if href.startswith(('http://', 'https://', 'mailto:', '#', 'javascript:')):
                return None
            
            # Nettoyer le href et enlever l'extension
            href = href.split('#')[0]
            href = os.path.splitext(href)[0]
            
            # Construire le chemin absolu
            if href.startswith('../'):
                parts = href.split('/')
                up_count = 0
                while parts and parts[0] == '..':
                    up_count += 1
                    parts.pop(0)
                
                current_parts = current_dir.split('/')
                if len(current_parts) >= up_count:
                    new_path = '/'.join(current_parts[:-up_count] + parts)
                    return new_path
                return None
            elif href.startswith('./'):
                return os.path.join(current_dir, href[2:])
            else:
                return os.path.join(current_dir, href)
                
        except Exception as e:
            print(f"Erreur lors de la normalisation du chemin {href}: {str(e)}")
            return None

    def extract_links_from_html(self, file_path: str, current_dir: str) -> list:
        """Extrait les liens et leur texte d'un fichier HTML."""
        links = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                link_text = a_tag.get_text(strip=True)
                
                normalized_path = self.normalize_path(current_dir, href)
                if normalized_path:
                    links.append((normalized_path, link_text or ""))
            
        except Exception as e:
            print(f"Erreur lors de l'analyse des liens dans {file_path}: {str(e)}")
        
        return links

    def add_metadata_to_graph(self, csv_file: str):
        """Ajoute les métadonnées de base au graphe depuis le fichier CSV."""
        with open(csv_file, 'r', encoding='cp1252') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                node_id = self.get_node_id(row['relative_dir'], row['filename'])
                self.nodes_info[node_id] = {
                    'relative_dir': row['relative_dir'],
                    'filename': row['filename']
                }
                self.graph.add_node(node_id)

    def add_links_to_graph(self, root_dir: str):
        """Ajoute uniquement les liens explicites entre les pages."""
        for node_id, info in self.nodes_info.items():
            # Essayer d'abord .html puis .htm
            html_path = os.path.join(root_dir, info['relative_dir'], f"{info['filename']}.html")
            htm_path = os.path.join(root_dir, info['relative_dir'], f"{info['filename']}.htm")
            
            file_path = html_path if os.path.exists(html_path) else htm_path
            current_dir = info['relative_dir'] if info['relative_dir'] else ""
            
            if os.path.exists(file_path):
                links = self.extract_links_from_html(file_path, current_dir)
                for target_path, link_text in links:
                    if target_path in self.nodes_info:
                        self.graph.add_edge(node_id, target_path, relationship=link_text)

    def export_graph(self, output_file: str):
        """Exporte le graphe au format JSON."""
        graph_data = {
            'nodes': [{'id': node_id} for node_id in self.graph.nodes()],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    'relationship': data.get('relationship', '')
                }
                for source, target, data in self.graph.edges(data=True)
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

def build_knowledge_graph(root_dir: str, csv_file: str, output_file: str):
    """Construit le graphe de connaissances basé uniquement sur les liens HTML."""
    generator = KnowledgeGraphGenerator()
    generator.add_metadata_to_graph(csv_file)
    generator.add_links_to_graph(root_dir)
    generator.export_graph(output_file)
    
    return {
        'nodes': generator.graph.number_of_nodes(),
        'edges': generator.graph.number_of_edges()
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python script.py <répertoire_source> <fichier_csv> <fichier_sortie.json>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    csv_file = sys.argv[2]
    output_json = sys.argv[3]
    
    if not os.path.isdir(source_dir):
        print(f"Erreur: Le répertoire {source_dir} n'existe pas.")
        sys.exit(1)
    
    if not os.path.exists(csv_file):
        print(f"Erreur: Le fichier CSV {csv_file} n'existe pas.")
        sys.exit(1)
    
    stats = build_knowledge_graph(source_dir, csv_file, output_json)
    print("\nGraphe de connaissances généré:")
    print(f"Nombre de nœuds: {stats['nodes']}")
    print(f"Nombre de liens: {stats['edges']}")