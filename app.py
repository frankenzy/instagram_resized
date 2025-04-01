#!/usr/bin/env python3

"""
Serveur web pour l'application Instagram Resizer
Gère l'interface web et les appels API pour traiter les images
"""

import os
import json
import subprocess
import platform
from flask import Flask, request, jsonify, send_from_directory
from src.image_processor import ImageProcessor

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    """Route principale qui affiche l'interface web"""
    return send_from_directory('.', 'index.html')

@app.route('/process_images', methods=['POST'])
def process_images():
    """API pour traiter les images d'un dossier"""
    try:
        data = request.json
        folder_path = data.get('folderPath')
        
        if not folder_path:
            return jsonify({"success": False, "message": "Chemin du dossier non spécifié"}), 400
        
        # Trouver le chemin complet du dossier
        for root, dirs, files in os.walk('.'):
            if folder_path in dirs:
                input_folder = os.path.join(root, folder_path)
                break
        else:
            return jsonify({"success": False, "message": f"Dossier {folder_path} non trouvé"}), 404
        
        # Créer le dossier de sortie
        output_folder = os.path.join(input_folder, "instagram_resized")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Traiter les images
        success_count, error_count = ImageProcessor.process_folder(input_folder)
        
        return jsonify({
            "success": True, 
            "successCount": success_count, 
            "errorCount": error_count,
            "outputFolder": output_folder
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/open_folder', methods=['POST'])
def open_folder():
    """API pour ouvrir le dossier des images traitées"""
    try:
        data = request.json
        folder_path = data.get('folderPath')
        
        if not folder_path or not os.path.exists(folder_path):
            return jsonify({"success": False, "message": "Dossier non trouvé"}), 404
        
        # Ouvrir le dossier selon le système d'exploitation
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
