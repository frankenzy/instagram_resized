#!/usr/bin/env python3

"""
Module de suppression d'arrière-plan pour Instagram Resizer
Utilise rembg pour supprimer l'arrière-plan des images de manière précise, 
même pour des cas complexes comme des vêtements avec motifs ou personnes avec des cheveux longs.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from rembg import remove, new_session
from typing import Tuple, Optional, Dict, Any, List

class BackgroundRemover:
    """Classe pour gérer la suppression d'arrière-plan des images"""
    
    # Modèles disponibles dans rembg
    MODELS = {
        "u2net": "Modèle standard pour objets généraux",
        "u2netp": "Modèle léger (plus rapide mais moins précis)",
        "u2net_human_seg": "Spécial pour segmentation humaine",
        "silueta": "Optimisé pour les silhouettes",
        "isnet-general-use": "Modèle avancé pour cas généraux"
    }
    
    # Modèle par défaut, isnet-general-use est le plus performant pour les cas généraux
    DEFAULT_MODEL = "isnet-general-use"
    
    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """
        Prétraite l'image pour améliorer la détection des contours
        
        Args:
            image: Image PIL à prétraiter
            
        Returns:
            Image.Image: Image prétraitée
        """
        # Améliorer le contraste légèrement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        # Améliorer la netteté pour mieux définir les contours
        image = image.filter(ImageFilter.SHARPEN)
        
        return image
    
    @staticmethod
    def postprocess_mask(mask: np.ndarray) -> np.ndarray:
        """
        Raffine le masque de segmentation pour améliorer les résultats
        
        Args:
            mask: Masque alpha en tant que numpy array
            
        Returns:
            np.ndarray: Masque raffié
        """
        # Convertir en uint8 si ce n'est pas déjà le cas
        if mask.dtype != np.uint8:
            mask = (mask * 255).astype(np.uint8)
            
        # Appliquer un flou gaussien pour adoucir les bords
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Ajuster les valeurs de seuil pour améliorer la segmentation
        _, mask = cv2.threshold(mask, 30, 255, cv2.THRESH_BINARY)
        
        # Appliquer une opération de dilatation pour récupérer les détails des bords
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        # Lisser les bords
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        return mask
    
    @staticmethod
    def remove_background(input_path: str, output_path: str, options: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Supprime l'arrière-plan d'une image avec des optimisations pour les cas complexes.
        
        Args:
            input_path: Chemin vers l'image source
            output_path: Chemin où sauvegarder l'image traitée
            options: Options supplémentaires (modèle, alpha_matting, etc.)
            
        Returns:
            Tuple[bool, str]: (Succès, Message)
        """
        try:
            # Charger l'image
            input_img = Image.open(input_path)
            
            # Prétraiter l'image pour améliorer la détection
            preprocessed_img = BackgroundRemover.preprocess_image(input_img)
            
            # Options pour rembg
            model_name = options.get('model', BackgroundRemover.DEFAULT_MODEL) if options else BackgroundRemover.DEFAULT_MODEL
            session = new_session(model_name)
            
            # Paramètres avancés pour les cas complexes
            # Réduction des seuils pour être plus sensible aux détails
            alpha_matting = options.get('alpha_matting', True) if options else True
            alpha_matting_foreground_threshold = options.get('foreground_threshold', 220) if options else 220  # Réduit de 240 à 220
            alpha_matting_background_threshold = options.get('background_threshold', 5) if options else 5  # Réduit de 10 à 5
            alpha_matting_erode_size = options.get('erode_size', 7) if options else 7  # Réduit de 10 à 7
            
            # Suppression d'arrière-plan avec paramètres avancés
            output_img = remove(
                preprocessed_img,
                session=session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size
            )
            
            # Récupérer le masque alpha et le raffiner
            alpha = np.array(output_img.getchannel('A'))
            refined_alpha = BackgroundRemover.postprocess_mask(alpha)
            
            # Réappliquer le masque alpha raffié à l'image originale
            output_array = np.array(output_img)
            output_array[:, :, 3] = refined_alpha
            output_img = Image.fromarray(output_array)
            
            # Sauvegarder l'image avec fond transparent
            output_img.save(output_path, format="PNG")
            
            return True, "Arrière-plan supprimé avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de la suppression de l'arrière-plan: {str(e)}"
    
    @staticmethod
    def process_folder(input_folder: str, callback: Optional[callable] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[int, int]:
        """
        Traite tous les fichiers images d'un dossier pour supprimer l'arrière-plan.
        
        Args:
            input_folder: Chemin du dossier contenant les images
            callback: Fonction de rappel pour mise à jour de l'interface
            options: Options pour la suppression d'arrière-plan
            
        Returns:
            Tuple[int, int]: (Nombre de succès, Nombre d'échecs)
        """
        output_folder = os.path.join(input_folder, "background_removed")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Extensions d'images supportées
        supported_formats = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
        
        success_count = 0
        error_count = 0
        
        for filename in os.listdir(input_folder):
            if filename.endswith(supported_formats):
                input_path = os.path.join(input_folder, filename)
                
                # Toujours utiliser l'extension PNG pour la sortie (pour supporter la transparence)
                output_filename = os.path.splitext(filename)[0] + '.png'
                output_path = os.path.join(output_folder, output_filename)
                
                success, message = BackgroundRemover.remove_background(input_path, output_path, options)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
                if callback:
                    callback(filename, success, message)
        
        return success_count, error_count
