#!/usr/bin/env python3

"""
Module de suppression d'arrière-plan pour Instagram Resizer
Utilise rembg pour supprimer l'arrière-plan des images de manière précise,
même pour des cas complexes comme des vêtements avec motifs ou personnes avec des cheveux longs.

CORRECTIF: élimine l'artefact "tache noire en escalier" qui apparaissait sur les objets
sombres (écran de laptop, etc.) proches d'un fond clair.
"""

import os

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from rembg import new_session, remove

try:
    import cv2

    _HAS_CV2 = True
except Exception:
    cv2 = None
    _HAS_CV2 = False
    try:
        from scipy import ndimage as _ndimage

        _HAS_SCIPY = True
    except Exception:
        _ndimage = None
        _HAS_SCIPY = False
from typing import Any, Dict, List, Optional, Tuple


class BackgroundRemover:
    """Classe pour gérer la suppression d'arrière-plan des images"""

    MODELS = {
        "u2net": "Modèle standard pour objets généraux",
        "u2netp": "Modèle léger (plus rapide mais moins précis)",
        "u2net_human_seg": "Spécial pour segmentation humaine",
        "silueta": "Optimisé pour les silhouettes",
        "isnet-general-use": "Modèle avancé pour cas généraux",
    }

    DEFAULT_MODEL = "isnet-general-use"

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        image = image.filter(ImageFilter.SHARPEN)
        return image

    @staticmethod
    def postprocess_mask(mask: np.ndarray) -> np.ndarray:
        """
        Raffine le masque de segmentation. Utilise un seuil moins agressif
        et un nettoyage morphologique pour éviter de "durcir" en bloc plein
        des zones où le matting était incertain (ex: bordure objet sombre / fond clair).
        """
        if mask.dtype != np.uint8:
            mask = (mask * 255).astype(np.uint8)

        if _HAS_CV2:
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            # Seuil un peu plus haut (60 au lieu de 30) : réduit le risque de
            # transformer en "plein opaque" des pixels que le matting jugeait
            # à peine plus foreground que background.
            _, mask = cv2.threshold(mask, 60, 255, cv2.THRESH_BINARY)
            # Ouverture (erode puis dilate) pour supprimer les petits îlots/bavures
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=1)
            mask = cv2.GaussianBlur(mask, (3, 3), 0)
            return mask
        else:
            if _HAS_SCIPY and _ndimage is not None:
                mask = _ndimage.gaussian_filter(mask, sigma=1)
                mask = (mask > 60).astype(np.uint8) * 255
                structure = np.ones((3, 3))
                mask = (
                    _ndimage.binary_opening(mask / 255, structure=structure).astype(
                        np.uint8
                    )
                    * 255
                )
                mask = (
                    _ndimage.binary_dilation(mask / 255, structure=structure).astype(
                        np.uint8
                    )
                    * 255
                )
                mask = _ndimage.gaussian_filter(mask, sigma=0.8)
                mask = (mask > 127).astype(np.uint8) * 255
                return mask
            else:
                pil_mask = Image.fromarray(mask)
                pil_mask = pil_mask.filter(ImageFilter.GaussianBlur(radius=1))
                pil_mask = pil_mask.convert("L")
                mask = np.array(pil_mask)
                mask = (mask > 60).astype(np.uint8) * 255
                pil_mask = Image.fromarray(mask)
                pil_mask = pil_mask.filter(
                    ImageFilter.MinFilter(size=3)
                )  # erode approx
                pil_mask = pil_mask.filter(
                    ImageFilter.MaxFilter(size=3)
                )  # dilate approx (= opening)
                pil_mask = pil_mask.filter(ImageFilter.MaxFilter(size=3))  # dilate
                mask = np.array(pil_mask)
                pil_mask = Image.fromarray(mask)
                pil_mask = pil_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
                mask = np.array(pil_mask)
                mask = (mask > 127).astype(np.uint8) * 255
                return mask

    @staticmethod
    def _keep_largest_component(image: Image.Image) -> Image.Image:
        """
        Ne conserve que la plus grande composante connexe du canal alpha.
        Élimine les taches/îlots isolés déconnectés de l'objet principal
        (le genre d'artefact visible sur l'image du laptop).
        Nécessite OpenCV ; si absent, retourne l'image telle quelle.
        """
        if not _HAS_CV2:
            return image

        arr = np.array(image)
        alpha = arr[:, :, 3]
        binary = (alpha > 0).astype(np.uint8)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )
        if num_labels <= 1:
            return image  # rien à faire (pas de foreground détecté)

        # Ignore le label 0 (fond), garde le plus grand parmi les autres
        areas = stats[1:, cv2.CC_STAT_AREA]
        largest_label = 1 + int(np.argmax(areas))

        cleaned_alpha = np.where(labels == largest_label, alpha, 0).astype(np.uint8)
        arr[:, :, 3] = cleaned_alpha
        return Image.fromarray(arr, mode="RGBA")

    @staticmethod
    def remove_background(
        input_path: str, output_path: str, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        try:
            input_img = Image.open(input_path)
            preprocessed_img = BackgroundRemover.preprocess_image(input_img)

            model_name = (
                options.get("model", BackgroundRemover.DEFAULT_MODEL)
                if options
                else BackgroundRemover.DEFAULT_MODEL
            )
            session = new_session(model_name)

            # NOTE: pour des objets "durs" (produits, électronique, meubles) sans
            # cheveux/fourrure, l'alpha matting fait souvent PLUS de mal que de bien,
            # surtout sur les zones de fort contraste (écran noir / fond clair).
            # On le laisse configurable, mais on désactive par défaut pour ce type
            # de scène produit ; passe alpha_matting=True dans options pour portraits/cheveux.
            alpha_matting = options.get("alpha_matting", False) if options else False
            alpha_matting_foreground_threshold = (
                options.get("foreground_threshold", 240) if options else 240
            )
            alpha_matting_background_threshold = (
                options.get("background_threshold", 10) if options else 10
            )
            alpha_matting_erode_size = options.get("erode_size", 10) if options else 10

            output_img = remove(
                preprocessed_img,
                session=session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size,
            )

            alpha = np.array(output_img.getchannel("A"))
            refined_alpha = BackgroundRemover.postprocess_mask(alpha)

            # CORRECTIF PRINCIPAL: on reconstruit le RGB à partir de l'image ORIGINALE,
            # pas de output_img. rembg met souvent du noir (0,0,0) dans les zones "fond".
            # Si on garde son RGB et que le masque déborde un peu, ça affiche un bloc
            # noir opaque au lieu d'un léger débordement transparent/blanc.
            original_rgb = np.array(input_img.convert("RGB"))
            if original_rgb.shape[:2] != refined_alpha.shape[:2]:
                original_rgb = np.array(
                    input_img.convert("RGB").resize(
                        (refined_alpha.shape[1], refined_alpha.shape[0])
                    )
                )

            output_array = np.dstack([original_rgb, refined_alpha]).astype(np.uint8)
            output_img = Image.fromarray(output_array, mode="RGBA")

            # Supprime les taches/îlots isolés déconnectés de l'objet principal
            output_img = BackgroundRemover._keep_largest_component(output_img)

            output_img.save(output_path, format="PNG")

            return True, "Arrière-plan supprimé avec succès"

        except Exception as e:
            return False, f"Erreur lors de la suppression de l'arrière-plan: {str(e)}"

    @staticmethod
    def process_folder(
        input_folder: str,
        callback: Optional[callable] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, int]:
        output_folder = os.path.join(input_folder, "background_removed")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        supported_formats = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG")

        success_count = 0
        error_count = 0

        for filename in os.listdir(input_folder):
            if filename.endswith(supported_formats):
                input_path = os.path.join(input_folder, filename)
                output_filename = os.path.splitext(filename)[0] + ".png"
                output_path = os.path.join(output_folder, output_filename)

                success, message = BackgroundRemover.remove_background(
                    input_path, output_path, options
                )

                if success:
                    success_count += 1
                else:
                    error_count += 1

                if callback:
                    callback(filename, success, message)

        return success_count, error_count
