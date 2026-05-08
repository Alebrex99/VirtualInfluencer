import os
import time
import sys
from google import genai
from google.genai import types
from PIL import Image, UnidentifiedImageError
from pathlib import Path
from dotenv import load_dotenv
import io
from google.genai.types import EditImageConfig, EditMode

sys.path.append(str(Path(__file__).resolve().parent.parent))
from constants import *

"""GOOGLE API IMAGEN EDITING PIPELINE (Parameter-based):
    Parameter-based image style transformation across 5 anthropomorphism levels.
    
    Instead of prompt-based generation (which hits safety blocks), we use:
    - A single base style prompt applied with varying parameter intensities
    - guidance_scale: Controls how strongly the style is applied (0.0 - 2.0)
    - base_steps: Controls transformation depth (higher = more effect)
    
    Five anthropomorphism levels (parameter-based intensity):
        "level_1" (high)       → guidance_scale=0.5, base_steps=10   (minimal transformation)
        "level_2" (medium_high) → guidance_scale=1.0, base_steps=15
        "level_3" (medium)      → guidance_scale=1.5, base_steps=20  (balanced)
        "level_4" (medium_low)  → guidance_scale=2.0, base_steps=25
        "level_5" (low)         → guidance_scale=2.0, base_steps=30  (maximum transformation)
"""

# ---------------------------
# Setup
# ---------------------------
def load_config():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("IMAGEN_MODEL")
    print(f"Using model: {model}, API key: {'set' if api_key else 'NOT SET'}")
    if "image" not in model.lower():
        print("Warning: selected model may not support image generation/editing output.")
    if not api_key or not model:
        raise ValueError("GEMINI_API_KEY and IMAGEN_MODEL must be set in the .env file.")
    return api_key, model


# ---------------------------
# File scanning and filtering
# ---------------------------
def scan_input_images(input_dir, max_images):
    """
    Return up to *max_images* valid image paths from *input_dir*.
    Creates the folder if it does not exist yet.
    """
    folder = input_dir  # Usare Path(input_dir) quando input_dir è già un Path, non cambia nulla
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        return []
    valid_images = []
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
            valid_images.append(item)
        if len(valid_images) >= max_images:
            break
    return valid_images


# ---------------------------
# Parameter-based transformation
# ---------------------------

BASE_STYLE_PROMPT = (
    "Transform this portrait into a professional digital artwork while maintaining the exact "
    "pose, framing, lighting, and composition. Apply a polished, stylized aesthetic."
)


def get_transformation_parameters(level: str) -> dict:
    """
    Map anthropomorphism level to EditImageConfig parameters.
    
    Lower levels (high) = minimal transformation intensity (stay realistic)
    Higher levels (low) = maximum transformation intensity (full stylization)
    
    Parameters:
      - guidance_scale: How strongly the style instruction is applied (0.0-2.0)
      - base_steps: Number of transformation steps (higher = more effect)
    """
    params = {
        "level_1": {"guidance_scale": 0.5, "base_steps": 10},
        "level_2": {"guidance_scale": 1.0, "base_steps": 15},
        "level_3": {"guidance_scale": 1.5, "base_steps": 20},
        "level_4": {"guidance_scale": 2.0, "base_steps": 25},
        "level_5": {"guidance_scale": 2.0, "base_steps": 30},
    }
    if level not in params:
        raise ValueError(f"Unsupported level: {level}")
    return params[level]

 
# ──────────────────────────────────────────────
# API CALLS
# ──────────────────────────────────────────────

def edit_image_with_retry(client, model, image_path, level):
    """
    Call the Imagen edit_image API with parameter-based transformation.
    Retries up to MAX_RETRIES times with exponential back-off.
    Returns PIL Image on success, None on safety block or failure.
    """
    params = get_transformation_parameters(level)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Load reference image
            with Image.open(image_path) as ref_image:
                # Call edit_image with parameter-based config
                response = client.models.edit_image(
                    model=model,
                    prompt=BASE_STYLE_PROMPT,
                    reference_images=[ref_image],
                    config=EditImageConfig(
                        guidance_scale=params["guidance_scale"],
                        base_steps=params["base_steps"],
                        edit_mode=types.EditMode.EDIT_MODE_STYLE,
                        number_of_images=1,
                        output_mime_type="image/png",
                    )
                )

            # DEBUG: Check response structure
            print(f"  Edit response: {response}")
            
            # Check for safety blocks
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                print(f"  Blocked — prompt feedback: {response.prompt_feedback}")
            
            # Give the API time to process
            time.sleep(1)

            # Extract generated image from response
            generated_image = extract_generated_image(response)

            if generated_image is None:
                raise RuntimeError(f"API response did not contain a generated image")
            return generated_image

        except Exception as error:
            last_error = error
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                print(f"  Retry {attempt}/{MAX_RETRIES} failed for {image_path.name}. Waiting {delay:.1f}s...")
                time.sleep(delay)

    print(f"Failed for {image_path.name}: {last_error}")
    return None


def extract_generated_image(response):
    """
    Extract generated image from Imagen edit_image response.
    EditImageResponse has: generated_images (list of GeneratedImage)
    """
    if not hasattr(response, "generated_images") or not response.generated_images:
        return None
    
    first_image = response.generated_images[0]
    
    # GeneratedImage has: image (Blob), rai_reason, etc.
    if hasattr(first_image, "image") and first_image.image:
        blob = first_image.image
        if hasattr(blob, "data"):
            return Image.open(io.BytesIO(blob.data)).convert("RGB")
        # Try as_image() if available
        if hasattr(blob, "as_image"):
            pil_img = blob.as_image()
            if isinstance(pil_img, Image.Image):
                return pil_img
    
    return None
 

def save_image(output_dir, source_path, level, image):
    """
    Save *image* to *output_dir* using the naming scheme:
        <original_stem>_<level>.png
    Creates the directory if missing. Returns the output Path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"{source_path.stem}_{level}.png"
    image.save(out_path, format="PNG")
    return out_path


def verify_saved_image(path):
    """Return True only if the file exists, is non-empty, and is a valid image."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False
    



def process_one_image(client, model, image_path):
    """
    Generate all five anthropomorphism variants for a single source image
    using parameter-based transformation at different intensities.
    """
    # Read original resolution for the resize-check after generation
    try:
        with Image.open(image_path) as source_image:
            original_size = source_image.size
    except (UnidentifiedImageError, OSError):
        print(f"Skipping unreadable image: {image_path.name}")
        return

    for level in EDITING_LEVELS:
        print(f"  Generating [{level}]...")

        # Check if output already exists
        expected_out_path = OUTPUT_DIR / f"{image_path.stem}_{level}.png"
        if expected_out_path.exists():
            print(f"  Output already exists for level [{level}]: {expected_out_path}. Skipping generation.")
            continue

        try:
            generated = edit_image_with_retry(client, model, image_path, level)
            if generated is None:
                print(f"Generation returned None for level [{level}]")
                continue

            # Enforce same resolution as source
            if generated.size != original_size:
                final_image = generated.resize(original_size, Image.Resampling.LANCZOS)
            else:
                final_image = generated

            out_path = save_image(OUTPUT_DIR, image_path, level, final_image)
            if verify_saved_image(out_path):
                print(f"Saved: {out_path}")
            else:
                print(f"Saved but verification failed: {out_path}")
        except Exception as error:
            print(f"Failed for {image_path.name} at level {level}: {error}")



def main():
    api_key, model = load_config()
    client = genai.Client(vertexai= True ) # api_key=api_key # tolto API perchè autenticazione fatta con gcloud CLI, non serve più la chiave API esplicita

    # Scan for input images
    image_paths = scan_input_images(INPUT_DIR, MAX_IMAGES)
    if not image_paths:
        print("No valid input images found.")
        return

    for idx, image_path in enumerate(image_paths, start=1):
        print(f"\n[{idx}/{len(image_paths)}] Processing: {image_path.name}")
        process_one_image(client, model, image_path)

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()