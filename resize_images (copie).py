#!/usr/bin/env python3

import os
from PIL import Image

def resize_for_instagram(input_folder):

    output_folder = os.path.join(input_folder, "instagram_resized")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    supported_formats = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
    
    for filename in os.listdir(input_folder):
        if filename.endswith(supported_formats):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            try:
                
                with Image.open(input_path) as img:

                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    width, height = img.size
                    target_size = 1080
                    
                    if width > height:
                        new_width = target_size
                        new_height = int((height / width) * target_size)
                    else:
                        new_height = target_size
                        new_width = int((width / height) * target_size)
                    
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    square_img = Image.new('RGB', (target_size, target_size), 'white')
                    
                    paste_x = (target_size - new_width) // 2
                    paste_y = (target_size - new_height) // 2
                    
                    square_img.paste(resized_img, (paste_x, paste_y))
                    
                    square_img.save(output_path, quality=95, optimize=True)
                    print(f"✓ Traité : {filename}")
            
            except Exception as e:
                print(f"❌ Erreur avec {filename}: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 resize_images.py /chemin/vers/dossier/images")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    if not os.path.isdir(input_folder):
        print(f"Erreur: Le dossier '{input_folder}' n'existe pas.")
        sys.exit(1)
    
    print(f"Traitement des images dans: {input_folder}")
    resize_for_instagram(input_folder)
    print("\nTerminé! Les images redimensionnées sont dans le dossier 'instagram_resized'")
