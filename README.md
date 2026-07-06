# Redimensionneur d'Images Instagram

Une application simple et intuitive pour redimensionner vos images au format Instagram (1080x1080 pixels).

## Fonctionnalités

- Interface graphique conviviale
- Redimensionnement automatique des images
- Préservation des proportions originales
- Ajout de bordures blanches pour format carré
- Support des formats PNG et JPEG
- Traitement par lot de plusieurs images

## Comment utiliser

1. Lancez l'application en exécutant :
   ```bash
   python main.py
   ```

2. Cliquez sur "Sélectionner un dossier" et choisissez le dossier contenant vos images

3. L'application va :
   - Créer un sous-dossier "instagram_resized"
   - Traiter toutes les images
   - Afficher la progression en temps réel
   - Vous informer une fois le traitement terminé

## Structure du projet

```
instagram_resizer/
├── main.py              # Point d'entrée de l'application
├── src/
│   ├── gui.py          # Interface graphique
│   └── image_processor.py  # Logique de traitement d'images
└── README.md           # Documentation
```

## Prérequis

- Python 3.6 ou supérieur
- Pillow (PIL) pour le traitement d'images
- Tkinter (inclus avec Python) pour l'interface graphique

## Installation

1. Clonez ou téléchargez ce dépôt

2. Installez les dépendances :
   ```bash
   pip install Pillow
   ```

3. Lancez l'application :
   ```bash
   python main.py
   ```
