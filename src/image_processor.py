#!/usr/bin/env python3

"""
Module de traitement d'images pour Instagram
Ce module contient les fonctions nécessaires pour redimensionner les images
au format Instagram tout en conservant leurs proportions.
"""

import os
from PIL import Image
from typing import Tuple, Optional

class ImageProcessor:
    """Classe pour gérer le traitement des images"""
    
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
    TARGET_SIZE = 1080  # Taille cible pour Instagram
    
    @staticmethod
    def process_image(input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Traite une seule image pour Instagram.
        
        Args:
            input_path: Chemin vers l'image source
            output_path: Chemin où sauvegarder l'image traitée
            
        Returns:
            Tuple[bool, str]: (Succès, Message)
        """
        try:
            with Image.open(input_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calcul des nouvelles dimensions
                width, height = img.size
                new_width, new_height = ImageProcessor._calculate_dimensions(width, height)
                
                # Redimensionnement avec haute qualité
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Création d'une image carrée
                square_img = Image.new('RGB', (ImageProcessor.TARGET_SIZE, ImageProcessor.TARGET_SIZE), 'white')
                
                # Centrage de l'image
                paste_x = (ImageProcessor.TARGET_SIZE - new_width) // 2
                paste_y = (ImageProcessor.TARGET_SIZE - new_height) // 2
                
                square_img.paste(resized_img, (paste_x, paste_y))
                square_img.save(output_path, quality=95, optimize=True)
                
                return True, f"Image traitée avec succès"
                
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    @staticmethod
    def _calculate_dimensions(width: int, height: int) -> Tuple[int, int]:
        """
        Calcule les nouvelles dimensions en conservant les proportions.
        
        Args:
            width: Largeur originale
            height: Hauteur originale
            
        Returns:
            Tuple[int, int]: Nouvelles dimensions (largeur, hauteur)
        """
        if width > height:
            new_width = ImageProcessor.TARGET_SIZE
            new_height = int((height / width) * ImageProcessor.TARGET_SIZE)
        else:
            new_height = ImageProcessor.TARGET_SIZE
            new_width = int((width / height) * ImageProcessor.TARGET_SIZE)
        return new_width, new_height
    
    @staticmethod
    def process_folder(input_folder: str, callback: Optional[callable] = None) -> Tuple[int, int]:
        """
        Traite tous les fichiers images d'un dossier.
        
        Args:
            input_folder: Chemin du dossier contenant les images
            callback: Fonction de rappel pour mise à jour de l'interface
            
        Returns:
            Tuple[int, int]: (Nombre de succès, Nombre d'échecs)
        """
        output_folder = os.path.join(input_folder, "instagram_resized")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        success_count = 0
        error_count = 0
        
        for filename in os.listdir(input_folder):
            if filename.endswith(ImageProcessor.SUPPORTED_FORMATS):
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, filename)
                
                success, message = ImageProcessor.process_image(input_path, output_path)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
                if callback:
                    callback(filename, success, message)
        
        return success_count, error_count
