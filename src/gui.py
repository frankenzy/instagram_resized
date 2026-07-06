#!/usr/bin/env python3

"""
Interface graphique pour le redimensionneur d'images Instagram
Une interface simple et intuitive pour traiter vos images.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from .image_processor import ImageProcessor

class InstagramResizerGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Redimensionneur Instagram")
        self.window.geometry("600x400")
        
        # Configuration du style
        self.style = ttk.Style()
        self.style.configure("Custom.TButton", padding=10)
        self.style.configure("Custom.TFrame", padding=20)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_frame = ttk.Frame(self.window, style="Custom.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title = ttk.Label(
            main_frame,
            text="Redimensionneur d'Images Instagram",
            font=("Helvetica", 16)
        )
        title.pack(pady=20)
        
        # Description
        description = ttk.Label(
            main_frame,
            text="Sélectionnez un dossier contenant vos images.\nElles seront redimensionnées au format Instagram (1080x1080)",
            wraplength=400
        )
        description.pack(pady=10)
        
        # Bouton de sélection
        select_button = ttk.Button(
            main_frame,
            text="Sélectionner un dossier",
            command=self.select_folder,
            style="Custom.TButton"
        )
        select_button.pack(pady=20)
        
        # Zone de progression
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, padx=50, pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400
        )
        
        # Zone de log
        self.log_text = tk.Text(main_frame, height=8, width=50)
        self.log_text.pack(pady=10)
        self.log_text.config(state=tk.DISABLED)
        
    def select_folder(self):
        """Gère la sélection du dossier et lance le traitement"""
        folder = filedialog.askdirectory(title="Sélectionner le dossier d'images")
        if folder:
            self.process_folder(folder)
    
    def update_progress(self, filename: str, success: bool, message: str):
        """Met à jour l'interface avec la progression"""
        status = "✓" if success else "❌"
        log_message = f"{status} {filename}: {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.window.update()
    
    def process_folder(self, folder: str):
        """Lance le traitement du dossier"""
        # Affiche la barre de progression
        self.progress_bar.pack(pady=10)
        self.progress_label.config(text="Traitement en cours...")
        
        # Compte le nombre total de fichiers à traiter
        total_files = len([f for f in os.listdir(folder) 
                          if f.endswith(ImageProcessor.SUPPORTED_FORMATS)])
        self.progress_bar["maximum"] = total_files
        self.progress_bar["value"] = 0
        
        # Vide la zone de log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Lance le traitement
        success_count, error_count = ImageProcessor.process_folder(
            folder,
            callback=self.update_progress
        )
        
        # Affiche le résumé
        message = f"Terminé !\n{success_count} images traitées avec succès\n"
        if error_count > 0:
            message += f"{error_count} erreurs rencontrées"
        
        messagebox.showinfo("Traitement terminé", message)
        
        # Cache la barre de progression
        self.progress_bar.pack_forget()
        self.progress_label.config(text="")
    
    def run(self):
        """Lance l'application"""
        self.window.mainloop()

if __name__ == "__main__":
    app = InstagramResizerGUI()
    app.run()
