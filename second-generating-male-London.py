import os
import time
from google import genai
from google.genai import types
from PIL import Image, ImageOps, UnidentifiedImageError
from pathlib import Path
from dotenv import load_dotenv
import io
from google.genai.types import GenerateContentConfig, Modality

from constants import *

# VERSION :5 PIPELINE FOR GEMINI 3 PRO IMAGE PREVIEW + OPUS GENERATED PROMPT AND GEMINI CLOUD REPHRASING



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

# USED --------------------------------------------------
ENHANCEMENT_PROMPT = (
     "Using the attached image as the exact source, generate a hyper-beautified version of the same person — "
    "an idealized representation that pushes beauty optimization to a level beyond what is typically achievable in ordinary men, "
    "comparable to top-tier male AI virtual influencers and to the aesthetic logic of hyper-optimized male synthetic models. "
    "The result must remain credible and avoid any uncanny-valley, plastic, doll-like, mannequin, or grotesque appearance. "
    "Beauty optimization (Western male beauty canon): maximize facial symmetry; sharpen and define the jawline into a strong, "
    "angular, well-defined shape with a clean mandibular line and a defined gonial angle; refine the chin with subtle prominence and a balanced projection; "
    "elevate and define cheekbones with clean, masculine hollows; straighten and refine the nose with a well-proportioned bridge and a clean, defined tip "
    "(no delicate or upturned tip); subtly emphasize a refined brow ridge consistent with masculine sexual dimorphism; brighten the eyes with crisp iris definition, "
    "clear whites, and an alert, confident gaze (no lash emphasis, no enlargement); shape the eyebrows into a clean, well-groomed, "
    "naturally masculine line — fuller, straighter, not over-arched; define the lips with clear, balanced contours and a well-formed shape — "
    "proportionate to the face, not enlarged and without an exaggerated cupid's bow; clear, healthy skin with even tone, natural radiance, and a subtle, "
    "credible male skin texture (not waxy, not over-smoothed, retaining a believable level of micro-texture); preserve any existing facial hair (stubble, beard, mustache) "
    "exactly as in the source but groom it to appear cleaner, denser where present, and more defined in its outline; idealize overall facial proportions following the canonical Western standard of male attractiveness "
    "(averageness + masculine sexual dimorphism cues — pronounced jaw, chin, cheekbones, refined brow — and a slightly higher facial width-to-height ratio, all applied with restraint to stay believable). "
    "Strict preservation (do NOT change): identity must remain clearly recognizable as the same individual; head pose, gaze direction, framing, crop, "
    "background (neutral grey, identical to the source), "                          # CHANGED: added "(neutral grey, identical to the source)"
    "lighting setup, clothing, hairstyle, hair color, hair length, facial hair style and length must be identical to the source; critically, preserve the exact same rendering style and "
    "level of photorealism/anthropomorphism as the source image — if the source looks photorealistic, the output must look photorealistic; if the source has a stylized/CGI/synthetic rendering, "
    "the output must keep that exact same stylized/CGI/synthetic rendering. Do not shift the rendering style in either direction."
    "Negative constraints: no plastic or waxy skin, no doll-like or mannequin appearance, no feminized features (no soft V-shape jawline, no enlarged eyes, no exaggerated or visible lashes, "
    "no fuller-than-natural lips, no over-arched or thinned brows, no neotenous proportions), no facial distortion, no change of ethnicity, no change of age range, no different person, no removal or addition of facial hair relative to the source."
    "Output: a hyper-optimized but credible \"more handsome version of the same person in the same photo, in the same rendering style.\"")
#USATO PRIMA
ENHANCED_MEDIUM_PROMPT1 = (
    "Using the attached image as the exact source, re-shade this synthetic "
    "character asset into the Level MEDIUM rendering style: mid-2000s cinematic CGI "
    "in the exact visual aesthetic of The Polar Express (2004) — the definitive "
    "reference for this style.\n\n"

    "SURFACE SHADER: the skin is rendered as a continuous, slightly-too-smooth 3D "
    "mesh surface with a flat diffuse albedo — soft, uniform, and waxy like polished "
    "candle wax. The surface is matte and diffuse, carrying no specular highlights "
    "and no sub-surface glow. The albedo brightness is calibrated so that the face "
    "reads at the same overall exposure level as the attached image. "
    "Any skin marks visible in the source are re-expressed as flat painted decals "
    "with no geometric relief. The skin reads as one continuous poured surface with "
    "no visible pore structure or micro-normal variation. "
    "Hair, eyebrows, and any facial hair are rendered as geometrically thin "
    "Old-Game-Engine Particle Systems. "
    "The overall result sits in the uncanny valley: clearly synthetic, clearly "
    "attempting human realism, clearly not alive.\n\n"

    "PRESERVE FROM SOURCE (keep exactly as in the attached image): the subject's "
    "identity and all facial features — facial geometry, proportions, jawline, "
    "cheekbones, nose, eyes, eyebrows, and lips; apparent age, gender, and "
    "ethnicity; the subject's facial attractiveness as it appears in the source; "
    "hairline, parting, length, density, and color; all accessories and clothing "
    "in their exact spatial coordinates and colors; head pose, head tilt, gaze "
    "direction, neutral closed-mouth expression; camera framing, crop, distance, "
    "and aspect ratio.\n\n"

    "PHOTOMETRIC LOCK (overrides all shader instructions): the light direction, "
    "shadow positions, shadow softness, exposure value, and white balance of the "
    "attached image are reproduced exactly. Shadow intensity, coverage, and spread "
    "remain within the bounds visible in the source. The background is a uniform "
    "neutral grey (#C8C8C8), perfectly flat and edge-to-edge, identical to the source."  # CHANGED: pure white (#FFFFFF) → uniform neutral grey
)


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


def scan_enhancement_input_images(input_dir):
    """
    Scan *input_dir* for images eligible for enhancement.
    Accepts files whose stem ends exactly with _high, _medium_high, or _medium
    (numbered attempt files like *_high-8.png are excluded).
    """
    folder = input_dir
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        return []

    target_suffixes = {f"_{lvl}" for lvl in ENHANCED_LEVELS_SIGLE.values()} #ENHANCED_LEVELS
    valid_images = []
    for item in sorted(folder.iterdir()):
        if not item.is_file() or item.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if any(item.stem.endswith(s) for s in target_suffixes):# come funziona any: any() restituisce True se almeno uno degli elementi dell'iterabile è vero. In questo caso, controlla se il nome del file (senza estensione) termina con uno dei suffissi target (_high, _medium_high, _medium). Se sì, l'immagine è considerata valida per l'elaborazione.
            valid_images.append(item)
    return valid_images


def get_test_enhanced_images(input_dir):
    """Return the two reference test images (high level) from Output_images/."""
    test_stems = ["CFD-WF-233-112-N_high", "CFD-WM-201-063-N_high"]
    result = []
    for stem in test_stems:
        for ext in ALLOWED_EXTENSIONS:
            candidate = input_dir / f"{stem}{ext}"
            if candidate.exists():
                result.append(candidate)
                break
    return result


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

    Per impostazione predefinita, il modello abbina le dimensioni dell'immagine di output a 
    quelle dell'immagine di input oppure genera quadrati 1:1.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Direct image input using PIL.Image (no byte conversion for input)
            with Image.open(image_path) as input_image:
                # L'ordine è fondamentale: [Prompt, Image 1 (Identity), Image 2 (Style)]
                contents = [prompt]
                contents.append(input_image)  # Image 1: Base Identity

                if style_reference_image is not None:
                    with Image.open(style_reference_image) as style_image:
                        contents.append(style_image.copy())
                
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=GenerateContentConfig(
                        response_modalities=[Modality.TEXT, Modality.IMAGE],
                        image_config= types.ImageConfig(
                            aspect_ratio=aspect_ratio,
                            image_size = "2K"
                        ))
                )
            
            # DEBUG =====================================
            # Controlla se la risposta contiene feedback di moderazione o motivi di blocco
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

def standardize_input_image(image_path, target_resolution):
    """
    Standardize the input image resolution before sending it to the API.
    If *target_resolution* is None, the original image path is returned unchanged.
    If a target resolution is provided, create a standardized image on disk in
    Images/StandardizedImages and return its path.

    Returns:
        (standardized_image_path, output_size, output_aspect_ratio)

    - LondonSet: 1350x1350 -> aspect ratio 1:1
    - ChicagoFaceDataset: 2444x1718 -> aspect ratio 3:2
    - MultiRacialDataset: 2444x1718 -> aspect ratio 3:2
    - FACES Dataset: 2835x3543 -> aspect ratio 4:5
    """

    with Image.open(image_path) as source_image:
        input_size = source_image.size
        if target_resolution is None:
            input_aspect_ratio = get_supported_aspect_ratio(source_image.width, source_image.height)
            return (image_path, input_size, input_aspect_ratio)

        if source_image.size == target_resolution:
            input_aspect_ratio = get_supported_aspect_ratio(source_image.width, source_image.height)
            return (image_path, input_size, input_aspect_ratio)
        
        #expected_standardized_path = STANDARDIZED_IMAGES_DIR / f"{image_path.stem}_{target_resolution[0]}x{target_resolution[1]}.png"
        expected_standardized_path = STANDARDIZED_IMAGES_DIR / f"{image_path.stem}.png"

        if expected_standardized_path.exists():
            return (expected_standardized_path, target_resolution, get_supported_aspect_ratio(target_resolution[0], target_resolution[1]))

        standardized = ImageOps.fit(
            source_image.convert("RGB"),
            target_resolution,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        STANDARDIZED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        # standardized_image_path = STANDARDIZED_IMAGES_DIR / f"{image_path.stem}_{target_resolution[0]}x{target_resolution[1]}.png"
        standardized_image_path = STANDARDIZED_IMAGES_DIR / f"{image_path.stem}.png"
        standardized.save(standardized_image_path, format="PNG", optimize=False)
        return (
            standardized_image_path,
            standardized.size,
            get_supported_aspect_ratio(standardized.width, standardized.height),
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


def process_image_enhancement(client, model, image_path):
    """
    Apply the beauty enhancement prompt to a single first-branch output image
    and save the result as {stem}_enhanced.png in OUTPUT_ENHANCED_DIR.
    """
    try:
        standardized_image_path, standardized_input_size, standardized_input_aspect_ratio = standardize_input_image(
            image_path,
            None,  # preserve original resolution
        )
    except (UnidentifiedImageError, OSError):
        print(f"Skipping unreadable image: {image_path.name}")
        return


    #expected_out_path = OUTPUT_ENHANCED_DIR / f"{image_path.stem}_enhanced.png"
    expected_out_path = OUTPUT_ENHANCED_DIR / f"{image_path.stem}E.png"
    if expected_out_path.exists():
        print(f"Output already exists: {expected_out_path}. Skipping.")
        return

    print(f"Enhancing [{image_path.name}]...")
    try:
        generated = generate_with_retry(
            client, model, standardized_image_path, ENHANCEMENT_PROMPT, standardized_input_aspect_ratio
        )
        print(f"Image Generated features: size= {generated.size}, aspect_ratio= {generated.size[0]/generated.size[1]:.2f}")

        if generated.size != standardized_input_size:
            final_image = generated.resize(standardized_input_size, Image.Resampling.LANCZOS)
        else:
            final_image = generated

        OUTPUT_ENHANCED_DIR.mkdir(parents=True, exist_ok=True)
        final_image.save(expected_out_path, format="PNG")
        if verify_saved_image(expected_out_path):
            print(f"Saved: {expected_out_path}")
        else:
            print(f"Saved but verification failed: {expected_out_path}")
    except Exception as error:
        print(f"Failed for {image_path.name}: {error}")

def process_medium_style(client, model, image_path):
    """
    input: ...high_enhanced.png 
    output: ...high_enhanced_medium.png
    Apply the MEDIUM-level style prompt to the enhanced image and save as {stem}_enhanced_medium.png."""

    #enhanced_image_path = OUTPUT_ENHANCED_DIR / f"{image_path.stem}_enhanced.png"
    enhanced_image_path = OUTPUT_ENHANCED_DIR / f"{image_path.stem}E.png" # prendi es. _HE and _MHE
    try:
        standardized_enhanced_image_path, standardized_input_size, standardized_input_aspect_ratio = standardize_input_image(
            enhanced_image_path,
            None,  # preserve original resolution
        )
    except (UnidentifiedImageError, OSError):
        print(f"Skipping unreadable image: {enhanced_image_path.name}")
        return
    
    #expected_out_path = OUTPUT_ENHANCED_DIR / f"{image_path.stem}_enhanced_medium.png"
    expected_out_path = OUTPUT_ENHANCED_DIR / f"{image_path.stem}EM.png"
    if expected_out_path.exists():
        print(f"Output already exists: {expected_out_path}. Skipping.")
        return

    print(f"Mediumizing [{enhanced_image_path.name}]...")
    try:
        generated = generate_with_retry(
            client, model, standardized_enhanced_image_path, ENHANCED_MEDIUM_PROMPT1, standardized_input_aspect_ratio
        )
        print(f"Image Generated features: size= {generated.size}, aspect_ratio= {generated.size[0]/generated.size[1]:.2f}")

        if generated.size != standardized_input_size:
            print(f"Resizing generated image from {generated.size} to {standardized_input_size}...")
            final_image = generated.resize(standardized_input_size, Image.Resampling.LANCZOS)
        else:
            final_image = generated

        OUTPUT_ENHANCED_DIR.mkdir(parents=True, exist_ok=True)
        final_image.save(expected_out_path, format="PNG")
        if verify_saved_image(expected_out_path):
            print(f"Saved: {expected_out_path}")
        else:
            print(f"Saved but verification failed: {expected_out_path}")
    except Exception as error:
        print(f"Failed for {image_path.name}: {error}")



def main():
    api_key, model = load_config()
    client = genai.Client(vertexai=True, api_key=api_key)

    image_paths = scan_enhancement_input_images(INPUT_ENHANCED_MALE_DIR)
    if not image_paths:
        print("No valid first-branch images found in Output_images/.")
        return

    # FULL RUN
    for idx, image_path in enumerate(image_paths, start=1):
        print(f"\n[{idx}/{len(image_paths)}] Processing: {image_path.name}")
        # ENHANCEMENT
        process_image_enhancement(client, model, image_path)

        # MEDIUM LEVEL APPLIED TO THE ENHANCED IMAGE
        process_medium_style(client, model, image_path)


    print("Pipeline completed.")
 
 
 
if __name__ == "__main__":
    main()
