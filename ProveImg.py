import os
import time
import tempfile
from google import genai
from google.genai import types
from PIL import Image, ImageOps, UnidentifiedImageError
from pathlib import Path
from dotenv import load_dotenv

def standardize_input_image(image_path, target_resolution):
    """
    Standardize the input image resolution before sending it to the API.
    If *target_resolution* is None, the original image path is returned unchanged.
    If a target resolution is provided, create a temporary resized image that
    matches it exactly while preserving visual proportions via center-crop.

    Returns:
        (processed_image_path, output_size, output_aspect_ratio, created_temp_file)

    - LondonSet: 1350x1350 -> aspect ratio 1:1
    - ChicagoFaceDataset: 2444x1718 -> aspect ratio 3:2
    - MultiRacialDataset: 2444x1718 -> aspect ratio 3:2
    - FACES Dataset: 2835x3543 -> aspect ratio 4:5
    """
    with Image.open(image_path) as source_image:
        input_size = source_image.size # es. 1350x1350 (London), oppure 2444x1718 (Chicago)
        if target_resolution is None:
            input_aspect_ratio = get_supported_aspect_ratio(source_image.width, source_image.height)
            return (input_size, input_aspect_ratio)

        if source_image.size == target_resolution:
            input_aspect_ratio = get_supported_aspect_ratio(source_image.width, source_image.height)
            return (input_size, input_aspect_ratio)
        
        
        """
        requested_size = 1080x1080
        - contain(): mantenere l'aspect ratio originale, ma rendendo più piccola l'img se più grande del target (su un asse)
          es. 2444x1718 -> 1080x759 (aspect ratio 3:2) ; 2835x3543 -> 864x1080 (aspect ratio 4:5) ; 1350x1350 -> 1080x1080 (aspect ratio 1:1)
        - cover(): mantenere l'aspect ratio originale, ma rendendo più grande l'img se più piccola del target (su un asse)
        - fit(): Se vuoi che l'immagine finale abbia esattamente le dimensioni del target, ma accetti di tagliare parti dell'immagine originale (center-crop).
        """

        standardized = ImageOps.fit(
            source_image.convert("RGB"),
            target_resolution,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        '''standardized = ImageOps.contain(
            source_image.convert("RGB"),
            target_resolution,
            method=Image.Resampling.LANCZOS)'''
        '''
        standardized = ImageOps.cover(
            source_image, 
            target_resolution, 
            method=Image.Resampling.LANCZOS)'''
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_file.close()
        standardized.save(temp_file.name, format="PNG", optimize=False)
        processed_path = Path(temp_file.name)
        
    return processed_path


# ──────────────────────────────────────────────
# IMAGE PROCESSING, SAVING, AND VERIFICATION
# ──────────────────────────────────────────────

def get_supported_aspect_ratio(width: int, height: int) -> str:
    """
    Convert input dimensions to the closest supported aspect-ratio string.
    Supported values: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
    """
    supported = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
    target_ratio = (width / height) if height else 1.0

    def to_float(ratio_str: str) -> float:
        w, h = ratio_str.split(":")
        return int(w) / int(h)

    return min(supported, key=lambda r: abs(to_float(r) - target_ratio))



def main():
    # Example usage of process_input_image_resolution
    '''
    - LondonSet: 1350x1350 -> aspect ratio 1:1
    - ChicagoFaceDataset: 2444x1718 -> aspect ratio 3:2
    - MultiRacialDataset: 2444x1718 -> aspect ratio 3:2
    - FACES Dataset: 2835x3543 -> aspect ratio 4:5'''
    #image_path = Path("Images","Prove", "CFD-WM-001-014-N.jpg")
    image_path = Path("Output_images", "CFD-WM-001-014-N_high.png")
    print (f"Processing image: {image_path}")
    target_resolution = (1080, 1080)  # Example target resolution
    result = standardize_input_image(image_path, target_resolution)
    img = Image.open(result)
    img.show()

if __name__ == "__main__":
    main()