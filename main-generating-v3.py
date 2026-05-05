import os
import time
import tempfile
from google import genai
from google.genai import types
from PIL import Image, ImageOps, UnidentifiedImageError
from pathlib import Path
from dotenv import load_dotenv
import io
from google.genai.types import GenerateContentConfig, Modality

from constants import *

# VERSIONE 3: PIPELINE OLD + STANDARDIZZAZIONE RISOLUZIONE INPUT + USO OPZIONALE DELLE STYLE REFERENCE IMAGES + VECCHIO PROMPT

"""
LONDON SET
    - 1350x1350 px, 1:1 aspect ratio, 5 levels of anthropomorphism
CHICAGO FACE DATASET:
    - 2444x1718 px, 3:2 aspect ratio, 5 levels of anthropomorphism
MultiRacialDataset: 
    - 2444x1718 -> aspect ratio 3:2
FACES Dataset: 
    - 2835x3543 -> aspect ratio 4:5
"""

"""GOOGLE API NANO BANANA PIPELINE:
    - $0.039 per immagine
    - Le immagini di output fino a 1024 x 1024 px consumano 1290 token e corrispondono a 0,039 $per immagine.
    *
    Five anthropomorphism levels (imported from constants.py via LEVELS):
        "high"        → Level 1: Highly polished photorealism, studio retouching
        "medium_high" → Level 2: Enhanced realism, subtle CGI skin quality
        "medium"      → Level 3: 3D video game character, game-engine render
        "medium_low"  → Level 4: Stylized 3D animation / semi-cartoon
        "low"         → Level 5: 2D cartoon illustration, fully illustrated
"""

# ---------------------------
# Setup
# ---------------------------
def load_config():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    print(f"Using model: {model}, API key: {'set' if api_key else 'NOT SET'}")
    if "image" not in model.lower():
        print("Warning: selected model may not support image generation/editing output.")
    if not api_key or not model:
        raise ValueError("GEMINI_API_KEY and GEMINI_MODEL must be set in the .env file.")
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
# Prompt construction
# ---------------------------
def build_prompt(level: str) -> str:
    """
    Build anthropomorphism prompt with shared constraints + level-specific style.
 
    Five levels are defined, progressing from full photorealism (high) to full
    cartoon illustration (low). The two intermediate levels (medium_high and
    medium_low) bridge the gap while following the same prompt engineering
    approach: style-based requests that focus exclusively on rendering style
    and visual aesthetic, never on identity or facial structure changes.
    This framing avoids content-policy blocks by keeping requests
    style-transfer-only rather than face-manipulation requests.
 
    To elevate your results from good to great, incorporate these professional strategies into your workflow.
    - Be Hyper-Specific: The more detail you provide, the more control you have. Instead of "fantasy armor," describe it: "ornate elven plate armor, etched with silver leaf patterns, with a high collar and pauldrons shaped like falcon wings."
    - Provide Context and Intent: Explain the purpose of the image. The model's understanding of context will influence the final output. For example, "Create a logo for a high-end, minimalist skincare brand" will yield better results than just "Create a logo."
    - Iterate and Refine: Don't expect a perfect image on the first try. Use the conversational nature of the model to make small changes. Follow up with prompts like, "That's great, but can you make the lighting a bit warmer?" or "Keep everything the same, but change the character's expression to be more serious."
    Use Step-by-Step Instructions: For complex scenes with many elements, break your prompt into steps. 
    - "First, create a background of a serene, misty forest at dawn. Then, in the foreground, add a moss-covered ancient stone altar. Finally, place a single, glowing sword on top of the altar."
    - Use "Semantic Negative Prompts": Instead of saying "no cars," describe the desired scene positively: "an empty, deserted street with no signs of traffic."
    Control the Camera: Use photographic and cinematic language to control the composition. Terms like wide-angle shot, macro shot, low-angle perspective.
    
    PROMPT BASE (sostituire)
    Using the provided images, place [element from image 2] onto [element from
    image 1]. Ensure that the features of [element from image 1] remain
    completely unchanged. The added element should [description of how the
    element should integrate].
    """

    shared_prompt = (
        "Transform the provided photograph of a person into the following artistic style (Style), "
        "preserve strictly the original composition, pose, lighting, and framing."
        "Preserve strictly the original human anatomical proportions of all facial features and hair"
        "Preserve all the external features/attributes of the subject, such as hairstyle, hair color, skin tone, eye color, expression, accessories, and clothing. " 
        "Ensure Do NOT exaggerate features. Do not alter the subject's gender or age."
        "Apply the following specific artistic style: "
    )
    
    # ── Level 1 — High (Polished Photorealism) ──────────────────────────────
    # Massima aderenza alla realtà. Solo pulizia estetica estrema.
    if level == "high":
        return (
            shared_prompt
            + "Style: Highly polished photorealism. "
            + "Retain full human realism but apply professional studio retouching. "
            + "Mantain the hair volume and natural flow. "
            + "Smooth the skin perfectly, remove blemishes, skin imperfections and enhance lighting for a flawless, "
            + "magazine-cover digital aesthetic while keeping human facial proportions intact."
        )

    # ── Level 2 — Medium-High (High-End Video Game) ─────────────────────────
    # Molto realistico, ma la perfezione di texture e luci tradisce la natura CGI.
    # NON FUNZIONA
    if level == "medium_high":
        return (
            shared_prompt
            + "Style: 3D Digital realism with an evident CGI quality. "
            + "change the skin: poreless skin texture, soft subsurface, light scattering that gives the skin a slightly luminous, synthetic glow. "
            + "change the hair: refine the hair to look like a high-resolution CGI render. "
            + "The result should appear with a noticeable digital "
            + "perfection that hints at computer generation rather than a real photograph."
        )

    # ── Level 3 — Medium (Mid-tier CGI / Uncanny Valley) ────────────────────
    # CGI evidente e imperfetta. L'effetto "Polar Express": gommoso, vetroso, perturbante.
    if level == "medium":
        return (
            shared_prompt
            + "Style: Mid-2000s cinematic 3D computer render, similar to 'The Polar Express'. "
            + "change the skin: a slightly waxy and rubbery finish, making it appear distinctly artificial and waxy, "
            + "change the eyes: a glassy, slightly lifeless quality that gives away the CGI nature. "
            + "change the hair: 3D rendered hair with visible clumping and a slightly stiff, unnatural flow. "
        )

    # ── Level 4 — Medium-Low (Proportional 3D Animation) ────────────────────
    # Shading stile Pixar/Disney, ma con le proporzioni anatomiche di un umano vero.
    # PERFECT
    if level == "medium_low":
        return (
            shared_prompt
            + "Style: Modern 3D animated feature film CGI. "
            + "Render it with soft, stylized 3D shading, smooth plastic-like surfaces, and volumetric simplified hair, but with the same proportions to the original. "
            + "Apply only the texture, coloring, and lighting style of a 3D family animation to the exact original geometry."
        )

    # ── Level 5 — Low (Proportional 2D Cartoon / Illustration) ──────────────
    # Passaggio al 2D puro, ma senza diventare una caricatura.
    # PERFECT
    if level == "low":
        return (
            shared_prompt
            + "Style: Flat 2D digital illustration. "
            + "Render it with vector-style art and flat color blocking "
            + "Completely transform the visual style into a stylized digital painting or vector-style cartoon. "
            + "Use simplified facial features, flat textures, and illustrative strokes, "
            + "moving away from photographic realism into a fully illustrated character concept."
        )
    raise ValueError(f"Unsupported level: {level}")

 
# ──────────────────────────────────────────────
# API CALLS
# ──────────────────────────────────────────────

def generate_with_retry(client, model, image_path, prompt, aspect_ratio, style_reference_image=None):
    """
    Call the API and return raw image bytes.
    Retries up to MAX_RETRIES times with exponential back-off.
    Raises RuntimeError if every attempt fails.
    Nota: l'immagine restituita da Gemini si trova nella risposta come Blob di byte, formato stringa codifica base64
    non una PIL image direttamente.
    image = Image.open("/path/to/cat_image.png")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, image],
    )
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Direct image input using PIL.Image (no byte conversion for input)
            with Image.open(image_path) as input_image:
                contents = [prompt]
                
                if style_reference_image is not None:
                    with Image.open(style_reference_image) as style_image:
                        contents.append(style_image.copy())
                
                contents.append(input_image)
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=GenerateContentConfig(
                        response_modalities=[Modality.TEXT, Modality.IMAGE],
                        image_config= types.ImageConfig(
                            aspect_ratio=aspect_ratio
                        ))
                )
            
            # DEBUG =====================================
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                print(f"  Blocked — prompt feedback: {response.prompt_feedback}")
            #finishReason: Il motivo per cui il modello ha smesso di generare token. Se None allora tutto ok
            if response.candidates:
                reason = getattr(response.candidates[0], "finish_reason", None) 
                if reason and "IMAGE" in str(reason) or "SAFETY" in str(reason):
                    print(f"  Blocked — finish reason: {reason}")
                    return None  # skip cleanly instead of crashing
            # ============================================

            # Usando as_image()
            # generated_image = extract_generated_pil_image(response)
            # Usando PIL images
            generated_image = extract_pil_image(response)

            if generated_image is None:
                response_text = getattr(response, "text", None)
                if response_text:
                    raise RuntimeError(f"API response did not contain a generated image. Text response: {response_text}")
                raise RuntimeError("API response did not contain a generated image")
            return generated_image

        except Exception as error:
            last_error = error
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                print(f"Retry {attempt}/{MAX_RETRIES} failed for {image_path.name}. Waiting {delay:.1f}s...")
                time.sleep(delay)

    raise RuntimeError(f"Generation failed for {image_path.name}: {last_error}")


def extract_pil_image(response):
    """
    Extract the first image from the API response as a PIL Image.
    The SDK's part.as_image() returns a Gemini-internal type, NOT a PIL Image,
    so we read part.inline_data.data (raw PNG/JPEG bytes) and decode with PIL.
    This works regardless of which candidate/parts structure the SDK returns.
    """
    # Path 1: flat response.parts
    parts = getattr(response, "parts", None)
    if parts:
        for part in parts:
            raw = getattr(part, "inline_data", None)
            if raw and getattr(raw, "data", None):
                return Image.open(io.BytesIO(raw.data)).convert("RGB")
    # Path 2: nested response.candidates[*].content.parts[*]
    candidates = getattr(response, "candidates", None)
    if candidates:
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            cparts = getattr(content, "parts", None) if content else None
            if not cparts:
                continue
            for part in cparts:
                raw = getattr(part, "inline_data", None)
                if raw and getattr(raw, "data", None):
                    return Image.open(io.BytesIO(raw.data)).convert("RGB")
    return None

    
# ──────────────────────────────────────────────
# FUTURE FUNCTIONS FOR: 
# - STESSA DIMENSIONE DI TUTTE LE IMMAGINI (INPUT/OUPUT)
# - USO DELLE REFERENCE STYLE IMAGES (OPZIONALE, DA SPERIMENTARE)
# ──────────────────────────────────────────────

def get_style_reference_image(level):
    """
    Return the style reference image path for the given level.
    Assumes reference images are named like "reference_high.png", "reference_medium_high.png", etc. and located in a "StyleRefImages" folder.
    """
    ref_dir = STYLE_REFERENCE_DIR
    if not ref_dir.exists():
        return None
    ref_path = STYLE_REFERENCE_DIR / f"reference_{level}.png"
    if not ref_path.exists():
        return None
    return ref_path

# Alla fine del process -> avrò img di input tutte alla stessa dimensione e aspect ratio
def standardize_input_image(image_path, target_resolution):
    """
    Standardize the input image resolution before sending it to the API.
    If *target_resolution* is None, the original image path is returned unchanged.
    If a target resolution is provided, create a temporary resized image that
    matches it exactly while preserving visual proportions via center-crop.

    Returns:
        (standardized_path, output_size, output_aspect_ratio, created_temp_file)

    - LondonSet: 1350x1350 -> aspect ratio 1:1
    - ChicagoFaceDataset: 2444x1718 -> aspect ratio 3:2
    - MultiRacialDataset: 2444x1718 -> aspect ratio 3:2
    - FACES Dataset: 2835x3543 -> aspect ratio 4:5
    """
    with Image.open(image_path) as source_image:
        input_size = source_image.size
        if target_resolution is None:
            input_aspect_ratio = get_supported_aspect_ratio(source_image.width, source_image.height)
            return (image_path, input_size, input_aspect_ratio, False)

        if source_image.size == target_resolution:
            input_aspect_ratio = get_supported_aspect_ratio(source_image.width, source_image.height)
            return (image_path, input_size, input_aspect_ratio, False)
        
        standardized = ImageOps.fit(
            source_image.convert("RGB"),
            target_resolution,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_file.close()
        standardized.save(temp_file.name, format="PNG", optimize=False)
        standardized_path = Path(temp_file.name)
        return (
            standardized_path,
            standardized.size,
            get_supported_aspect_ratio(standardized.width, standardized.height),
            True,
        )


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
    and save them to OUTPUT_DIR.
    Levels in order: high → medium_high → medium → medium_low → low
    """
    standardized_image_path = image_path
    created_temp_file = False
    try:
        standardized_image_path, standardized_input_size, standardized_input_aspect_ratio, created_temp_file = standardize_input_image(
            image_path,
            INPUT_RESOLUTION,
        )
    except (UnidentifiedImageError, OSError):
        print(f"Skipping unreadable image: {image_path.name}")
        return
    
    try:
        for level in LEVELS:
            print(f"Generating [{level}]...")
            prompt = build_prompt(level)
            # Se vogliamo usare uno style transfer da immagini reference
            style_reference_image = get_style_reference_image(level)  # Ottieni l'immagine di riferimento per lo stile specifico del livello
            
            # Dato il livello corrente, prima di generare un'immagine e spendere soldi,
            # 1. verifica che l'immagine associata a quel livello non esista già (potrebbe essere stata generata in un run precedente)
            # 2. se esiste già, skip al prossimo livello senza chiamare l'API, altrimenti procedi con la generazione
            expected_out_path = OUTPUT_DIR / f"{image_path.stem}_{level}.png"  # image_path.stem = nome del file senza estensione, es. "001_03" per "001_03.jpg"
            if expected_out_path.exists():
                print(f"Output already exists for level [{level}]: {expected_out_path}. Skipping generation.")
                continue
 
            try:
                if style_reference_image is None:
                    print(f"No style reference image for level [{level}]. Proceeding without it.")
                    generated = generate_with_retry(client, model, standardized_image_path, prompt, standardized_input_aspect_ratio)  # Devo ritornare una PIL Image da questa funzione
                else:
                    print(f"Using style reference image for level [{level}]: {style_reference_image}")
                    generated = generate_with_retry(
                        client,
                        model,
                        standardized_image_path,
                        prompt,
                        standardized_input_aspect_ratio,
                        style_reference_image=style_reference_image,
                    )
                print(f"Image Generated features: size= {generated.size}, aspect_ratio= {generated.size[0]/generated.size[1]:.2f}")
                
                # SAME RESOLUTION INPUT = OUTPUT
                # Enforce same resolution as standardized input
                if generated.size != standardized_input_size:
                    final_image = generated.resize(standardized_input_size, Image.Resampling.LANCZOS)
                else:
                    final_image = generated
                out_path = save_image(OUTPUT_DIR, image_path, level, final_image)
                if verify_saved_image(out_path):
                    print(f"Saved: {out_path}")
                else:
                    print(f"Saved but verification failed: {out_path}")
            except Exception as error:
                print(f"Failed for {image_path.name} at level {level}: {error}")
    finally:
        if created_temp_file and standardized_image_path.exists():
            standardized_image_path.unlink(missing_ok=True)


def main():
    api_key, model = load_config()
    client = genai.Client(api_key=api_key)
 
    # riempire la lista di paths delle immagini da processare
    image_paths = scan_input_images(INPUT_DIR, MAX_IMAGES)
    if not image_paths:
        print("No valid input images found.")
        return
    for idx, image_path in enumerate(image_paths, start=1):
        print(f"\n[{idx}/{len(image_paths)}] Processing: {image_path.name}")
        process_one_image(client, model, image_path)
    print("Pipeline completed.")
 
    # STANDARD SETUP
    '''    
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = (
        "" ""
    )
    image = Image.open("/path/to/cat_image.png")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, image],
    )
    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            image.save("generated_image.png")
    '''
 
 
if __name__ == "__main__":
    main()
