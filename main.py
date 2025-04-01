#!/usr/bin/env python3

"""
Point d'entrée principal de l'application
Lance l'interface graphique du redimensionneur d'images Instagram
"""

from src.gui import InstagramResizerGUI

def main():
    app = InstagramResizerGUI()
    app.run()

if __name__ == "__main__":
    main()
