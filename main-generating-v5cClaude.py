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
    
    folder_male = input_dir / "WhiteMale"
    folder_female = input_dir / "WhiteFemale"
    valid_images = []
    for sub in (folder_male, folder_female):
        if not sub.exists():
            continue
        for item in sorted(sub.iterdir()):
            if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
                valid_images.append(item)
                if len(valid_images) >= max_images:
                    return valid_images
    
    ''''
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
            valid_images.append(item)
        if len(valid_images) >= max_images:
            break'''
    return valid_images

def get_test_input_images(test_input_dir):
    """
    Deterministically return the two test images by stem:
      - CFD-WF-233-112-N  (from FEMALE_INPUT_DIR)
      - CFD-WM-201-063-N  (from MALE_INPUT_DIR)

    Minimal checks: looks for exact-stem + any allowed extension; falls back
    to case-insensitive stem scan in the folder if exact filename not found.
    """
    #VERSION SEMPLICE CON FOLDER DEDICATO
    folder = test_input_dir  # Usare Path(test_input_dir) quando test_input_dir è già un Path, non cambia nulla
    result = []
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        return []
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
            result.append(item)
        if len(result) >= 2:  # We only need two test images
            break

    # RICERCA IN TUTTO IL DATASET (PER USO FUTURO)
    '''
    targets = [
        ("CFD-WF-233-112-N", FEMALE_INPUT_DIR),
        ("CFD-WM-201-063-N", MALE_INPUT_DIR),
    ]
    results = []
    for stem, folder in targets:
        if not folder.exists():
            print(f"Test folder missing: {folder}")
            continue

        found = None
        # try exact filename with allowed extensions
        for ext in ALLOWED_EXTENSIONS:
            candidate = folder / f"{stem}{ext}"
            if candidate.exists():
                found = candidate
                break

        # fallback: search for matching stem (case-insensitive)
        if not found:
            for item in sorted(folder.iterdir()):
                if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS and item.stem.lower() == stem.lower():
                    found = item
                    break

        if found:
            results.append(found)
        else:
            print(f"Test image not found: {stem} in {folder}")
    '''

    return result




def build_prompt(level: str) -> str:

    # ─────────────────────────────────────────────────────────────────────
    # SHARED LOCKED CONTEXT
    # ─────────────────────────────────────────────────────────────────────
    locked_context = (
        "Generate an image of a synthetic 3D character asset produced by a professional "
        "real-time rendering engine. "

        "The attached reference photograph serves exclusively as the canonical geometric "
        "source mesh — a 3D scan providing structure, never pixels. "
        "Every surface in the output must be re-rendered through a digital shader "
        "engine; the result must read as a fully synthetic, computer-generated character, "
        "never a photograph or a retouched photo. "

        # ── IDENTITY LOCK ────────────────────────────────────────────────
        "The following identity attributes from the reference mesh must be preserved "
        "with full fidelity, re-expressed through the target shader: "
        "the exact spatial layout and proportions of every facial feature, all asymmetries "
        "and individual bone structure; every freckle, mole, scar, pimple, and area of "
        "uneven pigmentation, reproduced as localised texture data mapped onto the new "
        "surface material; the complete hair system including exact hairline position, "
        "parting direction, length, density, and natural colour, re-rendered in the "
        "target digital shading style; eyebrow shape, density, and colour; "
        "eyelashes; any fine facial hair or peach fuzz, preserved as shader-level detail; "
        "every accessory present in the reference (hair clips, earrings, piercings, "
        "glasses, necklaces, garments), kept at their exact spatial coordinates, "
        "geometry, and original colour value. "
        "The subject's apparent age, gender, ethnicity, and the specific facial "
        "attractiveness that defines this individual must remain identical — "
        "the inherent aesthetic quality of the subject is constant; "
        "only the rendering style changes. "

        # ── COMPOSITION LOCK ─────────────────────────────────────────────
        "The following composition parameters are fixed and must be reproduced exactly: "
        "a centered, frontal head-and-shoulders portrait with the subject looking directly "
        "at the camera; the exact head tilt, gaze direction, and neutral closed-mouth "
        "expression of the reference; the original camera framing, crop, distance, and "
        "aspect ratio; the original key-light direction and light angle — the light vector "
        "is locked and must not be shifted; "
        "the clothing geometry, colour, and spatial arrangement from the reference; "
        "a solid, uniform, pure white background (#FFFFFF, fully opaque, "
        "no gradient, no vignette, no coloured cast) filling the entire "
        "area outside the subject. "

        # ── EXPOSURE + SHADOW LOCK ───────────────────────────────────────
        # This is the critical shared fix: prevents over-darkening on all levels.
        "EXPOSURE AND SHADOW LOCK — this constraint overrides all shader-style "
        "instructions: the overall brightness of the face and clothing must match "
        "the reference photograph. "
        "The shadow coverage, shadow intensity, and shadow spread across the face, "
        "neck, and clothing must not exceed what is visible in the reference — "
        "do not deepen, expand, or intensify shadows beyond the reference. "
        "The shadow terminator position follows the locked light vector. "
        "The background is rendered as bright, clean, solid white (#FFFFFF). "

        # ── VARIABLE ─────────────────────────────────────────────────────
        "The ONLY variable allowed to change is the surface shading model and material "
        "rendering style, as specified below. "
        "Target render style:\n\n"
    )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: HIGH
    # ─────────────────────────────────────────────────────────────────────
    if level == "high":
        return (
            locked_context +
            "RENDER STYLE — HIGH: Hyper-detailed AI-generated virtual influencer asset "
            "in the aesthetic of Midjourney v5 or top-tier generative portrait art. "
            "Re-render the skin surface with ultra-sharp algorithmic micro-detail: "
            "every pore, freckle, and skin mark is present and rendered as a "
            "mathematically precise, high-contrast micro-texture — the impossible "
            "clarity that is the signature of raw generative AI portraits. "
            "The skin tone carries a subtle synthetic luminance, with micro-contrasted "
            "mid-tones and a slight denoised sheen that reads as 'too clean to be a "
            "photograph'. "
            "Eyes are rendered with over-specular, glassy irises showing a "
            "mathematically perfect radial pattern in the original eye colour, "
            "with crisp, high-contrast limbal rings. "
            "Hair strands, eyelashes, and garment edges are algorithmically "
            "over-sharpened, with individually rendered fibres and precise specular "
            "highlights on each strand. "
            "The final image reads unmistakably as a high-end synthetic character "
            "asset — technically flawless, slightly uncanny, hyper-precise. "
            "Exposure is bright and clean, matching the original, with a solid "
            "white (#FFFFFF) background."
        )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: MEDIUM_HIGH
    # Fix: removed "shadows are hard-edged and computed, not naturally diffused"
    # which was causing the heavy jaw/neck shadow.
    # Replaced with explicit shadow-intensity match instruction.
    # ─────────────────────────────────────────────────────────────────────
    if level == "medium_high":
        return (
            locked_context +
            "RENDER STYLE — MEDIUM-HIGH: A high-poly real-time 3D character asset for "
            "a AAA game engine, in the visual aesthetic of Uncharted 4 CHARACTERS, but maintaining the lighting exposure and intensity conditions of the original photo. "
            "The skin surface is rendered using a PBR material with a strongly "
            "diffuse-dominant albedo: subsurface scattering is present but clamped, "
            "producing an opaque, dense, slightly waxy appearance that clearly rejects "
            "biological photorealism. "
            "Freckles, moles, and skin marks are re-expressed as albedo and normal-map "
            "data — visible as high-contrast texture stamps on the surface, reading as "
            "digitally authored rather than organic. "
            "Micro-surface detail (pores, fine skin texture) is rendered as "
            "mathematically generated normal-map noise, uniform and slightly too "
            "regular to be real. "
            "Hair strands and eyebrows are rendered as game-engine hair ribbons: "
            "distinct, geometrically clean alpha cards with baked specular highlights, "
            "retaining the original hairline, density, and colour. "
            "Eyes have static, pre-baked environment reflections with sharp specular "
            "hotspots — no dynamic caustics. "
            "Light interacts with the surface as a real-time directional shader: "
            "the light direction and shadow placement match the reference exactly; "
            "shadow intensity and coverage area must not exceed the reference — "
            "only the computed, slightly harder edge quality of the shadow terminator "
            "reflects the game-engine shader, not its depth or spread. "
            "The final image is unmistakably a high-poly, next-gen game character "
            "render — detailed but clearly synthetic, with the visual density of a "
            "AAA cutscene asset. "
            "Exposure and image brightness match the reference. "
            "The background is solid, uniform white (#FFFFFF)."
        )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: MEDIUM
    # Fix: restored "The Polar Express (2004)" as sole visual anchor.
    # Restored explicit "flat diffuse" language.
    # Added brightness compensation note for flat-diffuse materials.
    # Removed second film reference (ambiguity source).
    # ─────────────────────────────────────────────────────────────────────
    if level == "medium":
        return (
            locked_context +
            "RENDER STYLE — MEDIUM: Cinematic CGI in the exact visual aesthetic of "
            "The Polar Express (2004) — the definitive reference for this level. "
            "The skin is rendered as a continuous, slightly-too-smooth 3D mesh surface "
            "with a flat diffuse albedo: soft, uniform, and waxy like polished candle "
            "wax — the surface is matte and diffuse, carrying no specular highlights "
            "and no sub-surface glow. "
            "Because a flat-diffuse material naturally absorbs more light than a "
            "photographic surface, the albedo brightness must be boosted so that the "
            "face reads at the same overall exposure level as the reference photograph. "
            "Freckles, moles, and skin marks are present as flat, painted-on albedo "
            "patches with no geometric relief — they sit on the surface like a decal "
            "rather than rising from it. "
            "The overall skin reads as one continuous poured surface with no visible "
            "pore structure or micro-normal variation. "
            "Lighting follows the locked reference direction; shadow placement and "
            "intensity match the reference — shadows are soft, low-contrast, and "
            "slightly too even, with gentle terminator edges characteristic of "
            "early performance-capture cinema. "
            "The overall image sits in the uncanny valley: clearly synthetic, "
            "clearly attempting human realism, clearly not alive. "
            "Image exposure is bright and correctly matched to the reference. "
            "The background is solid, uniform white (#FFFFFF)."
        )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: MEDIUM_LOW
    # ─────────────────────────────────────────────────────────────────────
    if level == "medium_low":
        return (
            locked_context +
            "RENDER STYLE — MEDIUM-LOW: Hand-painted 3D character in the aesthetic of "
            "Life is Strange (2015) or similar hand-crafted narrative indie games. "
            "The entire surface is rendered using hand-painted albedo textures with "
            "no PBR normal maps, no specular maps, and no bump-map detail. "
            "Shadows, highlights, and skin-tone gradients are visibly brushed onto the "
            "model surface as directional digital paint strokes — the light appears "
            "baked into the texture rather than computed in real time. "
            "Skin marks (freckles, moles) are re-expressed as simplified painted spots "
            "with soft, hand-drawn edges. "
            "Facial geometry is simplified into smooth, soft angular planes with "
            "slightly stylised proportions that retain the subject's recognisable "
            "identity. "
            "Hair is a solid sculptural volume divided into chunky painted sections "
            "with visible directional highlight strokes — no individual strands, "
            "no alpha cards. "
            "The colour palette is slightly desaturated and warm, consistent with the "
            "hand-crafted indie aesthetic. "
            "Image exposure is correctly matched to the reference. "
            "The background is solid, uniform white (#FFFFFF)."
        )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: LOW
    # ─────────────────────────────────────────────────────────────────────
    if level == "low":
        return (
            locked_context +
            "RENDER STYLE — LOW: A low-poly 3D game character asset in the aesthetic "
            "of The Sims 2 (2004) or comparable early-2000s consumer PC games. "
            "The geometry is simplified into clean, rounded 3D volumes with smooth "
            "Gouraud shading: the silhouette is simplified and slightly boxy, "
            "while internal facial planes are smoothly interpolated with no visible "
            "faceting. "
            "All surfaces use simple, flat albedo textures with baked-in directional "
            "shading — no PBR, no normal maps, no specular maps. "
            "Skin is a uniform, low-frequency tone with painted-on shadow areas. "
            "Freckles and skin marks are simplified into a small number of flat "
            "painted spots, consistent with the low-texture-budget aesthetic. "
            "Hair is rendered as a solid, simplified sculptural cap with "
            "broad painted directional highlights — no individual strands. "
            "Eyes are simple textured spheres with a flat iris decal. "
            "The subject's identity and expression remain readable despite the "
            "computational economy. "
            "Image exposure is correctly matched to the reference. "
            "The background is solid, uniform white (#FFFFFF)."
        )

    raise ValueError(f"Unsupported level: {level!r}. Valid: high, medium_high, medium, medium_low, low")
 
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
                            aspect_ratio=aspect_ratio
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

    
# ──────────────────────────────────────────────
# FUTURE FUNCTIONS FOR: 
# - STESSA DIMENSIONE DI TUTTE LE IMMAGINI (INPUT/OUPUT)
# - USO DELLE REFERENCE STYLE IMAGES (OPZIONALE, DA SPERIMENTARE)
# ──────────────────────────────────────────────

def get_style_reference_image(level):
    """
    Return the style reference image path for the given level.
    Assumes reference images are named like "reference_high.jpg", "reference_medium_high.jpg", etc. and located in a "StyleRefImages" folder.
    The image file type can be .jpg, .jpeg, or .png. If the expected image does not exist, returns None.
    """
    ref_dir = STYLE_REFERENCE_DIR
    if not ref_dir.exists():
        print(f"Style reference directory does not exist: {ref_dir}. Proceeding without style reference images.")
        return None

    target_stem = f"reference_{level}".lower()
    for ref in sorted(ref_dir.iterdir()):
        if (
            ref.is_file()
            and ref.suffix.lower() in ALLOWED_EXTENSIONS
            and ref.stem.lower() == target_stem
        ):
            return ref

    print(f"Style reference image not found for level '{level}' in {ref_dir}. Proceeding without style reference images.")
    return None

# Alla fine del process -> avrò img di input tutte alla stessa dimensione e aspect ratio
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
        
        expected_standardized_path = STANDARDIZED_IMAGES_DIR / f"{image_path.stem}_{target_resolution[0]}x{target_resolution[1]}.png"
        if expected_standardized_path.exists():
            return (expected_standardized_path, target_resolution, get_supported_aspect_ratio(target_resolution[0], target_resolution[1]))

        standardized = ImageOps.fit(
            source_image.convert("RGB"),
            target_resolution,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        STANDARDIZED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        standardized_image_path = STANDARDIZED_IMAGES_DIR / f"{image_path.stem}_{target_resolution[0]}x{target_resolution[1]}.png"
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
    try:
        standardized_image_path, standardized_input_size, standardized_input_aspect_ratio = standardize_input_image(
            image_path,
            INPUT_RESOLUTION,
        )
    except (UnidentifiedImageError, OSError):
        print(f"Skipping unreadable image: {image_path.name}")
        return
    
    #use LEVELS_3 to test only the 3 middle levels with style reference images, or LEVELS to use all 5 levels without style reference images
    for level in LEVELS_3:  # LEVELS #Use LEVELS to use all 5 levels, or LEVELS_3 to use only the 3 middle levels with style reference images
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
            
            # CONTROLLO FINALE: SAME RESOLUTION INPUT = OUTPUT
            # Enforce same resolution as source
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


def main():
    api_key, model = load_config()
    client = genai.Client(vertexai= True, api_key=api_key)
    isTest = True

    # riempire la lista di paths delle immagini da processare
    image_paths = scan_input_images(INPUT_DIR, MAX_IMAGES)
    if not image_paths:
        print("No valid input images found.")
        return
    
    # TESTING
    if isTest:
        # TEST: Prendi direttamente due immagini note: WhiteMale/WM-201 e WhiteFemale/WF-233
        test_image_paths = get_test_input_images(TEST_INPUT_DIR)
        print(f"Testing with {len(test_image_paths)} images: {[p.name for p in test_image_paths]}")
        for idx, image_path in enumerate(test_image_paths, start=1):
            print(f"\n[TEST {idx}/{len(test_image_paths)}] Processing: {image_path.name}")
            process_one_image(client, model, image_path)
        print("Pipeline completed.")
        return

    # FULL RUN
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
