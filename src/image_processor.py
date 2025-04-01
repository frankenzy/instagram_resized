#!/usr/bin/env python3

"""
Module de traitement d'images pour Instagram
Ce module contient les fonctions nécessaires pour redimensionner les images
au format Instagram tout en conservant leurs proportions.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional, Dict, Any

class ImageProcessor:
    """Classe pour gérer le traitement des images"""
    
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
    TARGET_SIZE = 1080  # Taille cible pour Instagram
    
    @staticmethod
    def process_image(input_path: str, output_path: str, options: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
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
                # Appliquer un filigrane si demandé
                if options and options.get('watermarkText'):
                    watermark_text = options.get('watermarkText')
                    watermark_position = options.get('watermarkPosition', 'center')
                    opacity = options.get('watermarkOpacity', 50) / 100.0  # Convertir en pourcentage
                    
                    # Ajouter le filigrane avec la position spécifiée
                    square_img = ImageProcessor._add_watermark(
                        square_img, 
                        watermark_text, 
                        opacity, 
                        watermark_position
                    )
                
                # Déterminer le format et la qualité
                format_option = options.get('format', 'jpg').lower() if options else 'jpg'
                quality = options.get('quality', 95) if options else 95
                
                # Déterminer le format de fichier
                if format_option == 'png':
                    # Pour PNG, on utilise le format PNG
                    file_extension = '.png'
                    save_format = 'PNG'
                    output_path = os.path.splitext(output_path)[0] + file_extension
                    square_img.save(output_path, format=save_format, optimize=True)
                elif format_option == 'webp':
                    # Pour WebP
                    file_extension = '.webp'
                    save_format = 'WEBP'
                    output_path = os.path.splitext(output_path)[0] + file_extension
                    square_img.save(output_path, format=save_format, quality=quality, method=6)
                else:
                    # Par défaut, JPEG
                    file_extension = '.jpg'
                    output_path = os.path.splitext(output_path)[0] + file_extension
                    square_img.save(output_path, format='JPEG', quality=quality, optimize=True)
                
                return True, f"Image traitée avec succès au format {format_option.upper()}"
                
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
    def _add_watermark(image: Image.Image, text: str, opacity: float = 0.5, position: str = "center") -> Image.Image:
        """Ajoute un filigrane texte à l'image
        
        Args:
            image: Image sur laquelle ajouter le filigrane
            text: Texte à ajouter comme filigrane
            opacity: Opacité du filigrane (entre 0 et 1)
            position: Position du filigrane ('center', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'diagonal')
            
        Returns:
            Image avec filigrane
        """
        if not text.strip():
            return image
            
        # Créer une nouvelle image transparente pour le filigrane
        watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Essayer de trouver une police installée
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Chemin standard sur de nombreux systèmes Linux
            font_size = min(image.width, image.height) // 15
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Mesurer la taille du texte
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else font.getsize(text)
        padding = 20  # Espace entre le texte et les bords
        
        # Déterminer les coordonnées en fonction de la position
        if position == "top-left":
            x, y = padding, padding
        elif position == "top-right":
            x, y = image.width - text_width - padding, padding
        elif position == "bottom-left":
            x, y = padding, image.height - text_height - padding
        elif position == "bottom-right":
            x, y = image.width - text_width - padding, image.height - text_height - padding
        elif position == "diagonal":
            # Centrer sur la diagonale et faire pivoter plus tard
            x, y = (image.width - text_width) // 2, (image.height - text_height) // 2
        else:  # center ou valeur par défaut
            x, y = (image.width - text_width) // 2, (image.height - text_height) // 2
        
        # Dessiner le texte en blanc semi-transparent
        text_color = (255, 255, 255, int(255 * opacity))
        
        if position == "diagonal":
            # Pour la diagonale, on crée une image séparée, on la fait pivoter, puis on la colle
            diagonal_text = Image.new('RGBA', (image.width, image.height), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(diagonal_text)
            text_draw.text((x, y), text, fill=text_color, font=font)
            
            # Pivoter de 45 degrés
            rotated_text = diagonal_text.rotate(45, expand=0, resample=Image.Resampling.BILINEAR)
            
            # Superposer sur le filigrane
            watermark = Image.alpha_composite(watermark, rotated_text)
        else:
            # Dessiner normalement pour les autres positions
            draw.text((x, y), text, fill=text_color, font=font)
        
        # Combiner l'image originale avec le filigrane
        return Image.alpha_composite(image.convert('RGBA'), watermark).convert('RGB')
        
    @staticmethod
    def process_folder(input_folder: str, callback: Optional[callable] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[int, int]:
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
                
                success, message = ImageProcessor.process_image(input_path, output_path, options)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
                if callback:
                    callback(filename, success, message)
        
        return success_count, error_count
