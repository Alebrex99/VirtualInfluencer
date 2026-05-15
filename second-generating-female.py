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

locked_context = (
        "ROLE: You are an expert image producer specializing in 3D character "
        "asset generation.\n"
        "TASK: Produce a synthetic 3D character asset by re-surfacing a given "
        "geometric reference (the base image) with a specified target "
        "rendering style — high, medium-high, medium, medium-low, or low "
        "anthropomorphism.\n\n"
        
        "BASE INPUT IMAGE: The base image is the canonical source of TWO "
        "things and only the SHADER is allowed to change:\n"
        "  (a) GEOMETRIC IDENTITY — facial structure, hair, accessories, "
        "      clothing, pose, framing.\n"
        "  (b) PHOTOMETRIC BLUEPRINT — light direction, shadow positions and "
        "      shadow softness, exposure value (EV), white balance, and the "
        "      pure white background.\n"
        "The transformation re-renders the SURFACE SHADER on top of this "
        "blueprint. The shader is the only variable.\n\n"

        "IDENTITY LOCK: The following attributes must be preserved exactly and never altered, only re-rendered through the target shader:\n"
        "- Facial geometry: every feature's spatial coordinates, proportions, asymmetries, and bone structure.\n"
        "- Skin character: every freckle, mole, scar, pimple, abrasion, uneven pigmentation – these must be preserved as micro-features in the new shader.\n"
        "- Hair: exact hairline, parting, length, density, color, eyebrow shape and density, eyelashes, beard/stubble pattern, fine peach fuzz. The original pixels for hair must be re-rendered with digital shaders.\n"
        "- Accessories: every earring, piercing, hair clip, glasses, necklace, garment item – maintain the same geometry, placement, and color.\n"
        "- Identity attributes: apparent age, gender, ethnicity, and the subject's inherent facial attractiveness – these must be held constant across all levels.\n"

        "COMPOSITION LOCK: The following aspects must be preserved exactly:\n"
        "- Pose, head tilt, gaze direction, facial expression.\n"
        "- Camera framing, crop, distance, aspect ratio.\n"
        "- Clothing geometry, color, and spatial arrangement.\n\n"

        # [LT-H][LT-M] hardened photometric lock, single source of truth
        "PHOTOMETRIC LOCK — preserve exactly (no level may override this):\n"
        "- Light direction and angle: identical to the base image.\n"
        "- Shadow positions, shapes, edges, and softness: identical to the "
        "  base image.\n"
        "- Exposure Value (EV) and overall brightness: identical to the base "
        "  image — the output histogram should match the input histogram in "
        "  mid-tone placement and highlight roll-off.\n"
        "- White balance and color temperature: identical to the base image.\n"
        "Only the SHADER's *response* to this fixed lighting is allowed to "
        "change between levels. The lighting rig itself does not move, "
        "soften, harden, brighten, or darken.\n\n"

        # [BG] single, positive, prominent background directive
        "BACKGROUND LOCK — uniform pure white #FFFFFF, perfectly flat, "
        "edge-to-edge, identical to the base image. \n\n"

        "VARIABLE: only the SHADING MODEL and SURFACE RENDERING are allowed to change between levels. "
        "Light direction is locked; how that light interacts with the skin is dictated by the target style. \n\n"

        "INSTRUCTION: "
        "1. Treat the subject in the provided base image as a 3D digital mesh. \n"
        "2. You MUST re-surface this mesh using a synthetic-digital rendering engine.\n"
        "3. SURFACE PROTOCOL: Re-render every surface (skin, hair, fabric) using digital shaders. The final result must be a synthetic-digital reconstruction.\n"

        "TARGET RENDER STYLE:\n"
    )

MEDIUM_LEVEL_PROMPT = (locked_context +
            "RENDER STYLE — Level MEDIUM (Early-2000s Cinematic CGI / Uncanny Valley):\n"
            "Render in the aesthetic of The Polar Express (2004) or early "
            "performance-capture cinema, but replicate the exact Exposure Value (EV) of the base image. "
            "Skin is waxy like a soft silicone mask or polished candle wax. "
            "The face is one continuous, slightly-too-smooth 3D mesh with "
            "a flat diffuse texture pass for marks and imperfections — they "
            "read as painted onto the surface rather than emerging from it. "
            "Render hair, eyebrows, and any facial hair as geometrically thin Old-Game-Engine Particle Systems. " # thin 'Game-Engine Ribbons' with baked specular highlights. "
            "Lighting is flat, lacks realistic bounce-light, and produces "
            "shadows that fall slightly too softly. The result sits in the "
            "uncanny valley: clearly synthetic, clearly attempting realism, "
            "clearly not alive.")

ENHANCED_MEDIUM_PROMPT2 = (
    # ── ROLE / TASK ─────────────────────────────────────────────────────
    "ROLE: You are an expert image producer specializing in 3D character "
    "asset generation.\n"
    "TASK: Produce a synthetic 3D character asset by re-surfacing"
    "a given geometric reference — the attached image — an already-synthetic, beauty-enhanced "
    "character render of the subject — with the specified target rendering style "
    "(Level MEDIUM anthropomorphism).\n\n"

    # ── SOURCE INPUT ────────────────────────────────────────────────────
    "SOURCE INPUT IMAGE: the attached image is the canonical source of TWO "
    "things and only the SHADER is allowed to change:\n"
    "  (a) GEOMETRIC IDENTITY — the facial structure, "
    "      proportions, features, hair, accessories, clothing, pose, and "
    "      framing.\n"
    "  (b) PHOTOMETRIC BLUEPRINT — light direction, shadow positions and "
    "      shadow softness, exposure value (EV), white balance, and the "
    "      pure white background.\n"
    "The transformation re-renders the SURFACE SHADER on top of this "
    "blueprint. The shader is the only variable.\n\n"

    "IDENTITY LOCK: The following attributes must be preserved exactly and never altered, only re-rendered through the target shader (rendering style):\n"
    "- Facial geometry: every feature's spatial coordinates, proportions, asymmetries, and bone structure.\n"
    "- Skin character: every freckle, mole, scar, pimple, abrasion, uneven pigmentation – these must be preserved as micro-features in the target shader (rendering style).\n"
    "- Hair: exact hairline, parting, length, density, color, eyebrow shape and density, eyelashes, beard/stubble pattern, fine peach fuzz. The original pixels for hair must be re-rendered with the target digital shader (rendering style).\n"
    "- Accessories: every earring, piercing, hair clip, glasses, necklace, garment item – maintain the same geometry, placement, and color.\n"
    "- Identity attributes: apparent age, gender, ethnicity, and the subject's inherent facial attractiveness – these must be held constant.\n"

    # ── COMPOSITION LOCK ────────────────────────────────────────────────
    "COMPOSITION LOCK: the following aspects must be preserved exactly:\n"
    "- Pose, head tilt, gaze direction, facial expression.\n"
    "- Camera framing, crop, distance, aspect ratio.\n"
    "- Clothing geometry, color, and spatial arrangement.\n\n"

    # [LT-H][LT-M] hardened photometric lock, single source of truth
    "PHOTOMETRIC LOCK — preserve exactly:\n"
    "- Light direction and angle: identical to the base image.\n"
    "- Shadow positions, shapes, edges, and softness: identical to the "
    "  base image.\n"
    "- Exposure Value (EV) and overall brightness: identical to the attached "
    "  image — the output histogram should match the input histogram in "
    "  mid-tone placement and highlight roll-off.\n"
    "- White balance and color temperature: identical to the attached image.\n"
    "Only the SHADER's *response* to this fixed lighting is allowed to "
    "change. The lighting rig itself does not move, soften, harden, "
    "brighten, or darken.\n\n"

    # ── BACKGROUND LOCK ─────────────────────────────────────────────────
    "BACKGROUND LOCK — uniform pure white #FFFFFF, perfectly flat, "
    "edge-to-edge, identical to the attached image.\n\n"

    "VARIABLE: only the SHADING MODEL and SURFACE RENDERING are allowed to change in the target style. "
    "Light direction is locked; how that light interacts with the skin is dictated by the target style. \n\n"

    "INSTRUCTION: "
    "1. Treat the subject in the attached image as a 3D digital mesh. \n"
    "2. You MUST re-surface this mesh using a synthetic-digital rendering engine in the target syle below.\n"
    "3. SURFACE PROTOCOL: Re-render every surface (skin, hair, fabric) using digital shaders of the target style. The final result must be a synthetic-digital reconstruction.\n"

    "TARGET RENDER STYLE:\n"
    "RENDER STYLE — Level MEDIUM (Early-2000s Cinematic CGI / Uncanny Valley):\n"
    "Render in the aesthetic of The Polar Express (2004) or early "
    "performance-capture cinema, but replicate the exact Exposure Value (EV) of the base image. "
    "Skin is waxy like a soft silicone mask or polished candle wax. "
    "The face is one continuous, slightly-too-smooth 3D mesh with "
    "a flat diffuse texture pass for marks and imperfections — they "
    "read as painted onto the surface rather than emerging from it. "
    "Render hair, eyebrows, and any facial hair as geometrically thin Old-Game-Engine Particle Systems. " # thin 'Game-Engine Ribbons' with baked specular highlights. "
    "Lighting is flat, lacks realistic bounce-light, and produces "
    "shadows that fall slightly too softly. The result sits in the "
    "uncanny valley: clearly synthetic, clearly attempting realism, "
    "clearly not alive."
)

ENHANCED_MEDIUM_PROMPT = (
    "Using the attached image as the exact source, re-shade this synthetic "
    "character asset into the Level MEDIUM rendering style: mid-2000s cinematic CGI "
    "in the exact visual aesthetic of The Polar Express (2004) — the definitive "
    "reference for this style.\n\n"

    "SURFACE SHADER: Skin is waxy like a soft silicone mask or polished candle wax. "
    "The face is one continuous, slightly-too-smooth 3D mesh with "
    "a flat diffuse texture pass for marks and imperfections — they "
    "read as painted onto the surface rather than emerging from it. "
    "Render hair, eyebrows, and any facial hair as geometrically thin Old-Game-Engine Particle Systems. " # thin 'Game-Engine Ribbons' with baked specular highlights. "
    "Lighting is flat, lacks realistic bounce-light, and produces "
    "shadows that fall slightly too softly. The result sits in the "
    "uncanny valley: clearly synthetic, clearly attempting realism, "
    "clearly not alive."

    "PRESERVE FROM SOURCE (keep exactly as in the attached image): the subject's "
    "identity and all facial features — facial geometry, proportions, jawline, "
    "cheekbones, nose, eyes, eyebrows, and lips; apparent age, gender, and "
    "ethnicity; "
    "hairline, parting, length, density, and hair color; all accessories and clothing "
    "in their exact spatial coordinates and colors; head pose, head tilt, gaze "
    "direction, neutral closed-mouth expression; camera framing, crop, distance, "
    "and aspect ratio.\n\n"

    "PHOTOMETRIC LOCK (overrides all shader instructions): the light direction, "
    "shadow positions, shadow softness, exposure value, and white balance of the "
    "attached image are reproduced exactly. Shadow intensity, coverage, and spread "
    "remain within the bounds visible in the source. The background is a uniform "
    "pure white (#FFFFFF), perfectly flat and edge-to-edge, identical to the source."
)

# USED --------------------------------------------------
ENHANCEMENT_PROMPT = (
    "Using the attached image as the exact source, generate a hyper-beautified version of the same person — "
    "an idealized representation that pushes beauty optimization to a level beyond what is typically achievable "
    "in ordinary humans, comparable to top-tier AI virtual influencers (e.g., Aitana Lopez, Lil Miquela aesthetic logic). "
    "The result must remain credible and avoid any uncanny-valley, plastic, doll-like, or grotesque appearance.\n\n"
    "Beauty optimization (Western beauty canon): maximize facial symmetry; refine and slim the jawline into a soft V-shape; "
    "elevate and define cheekbones with subtle hollows; straighten and refine the nose with a delicate, well-defined tip; "
    "enlarge and brighten the eyes with crisp iris definition, long full lashes, and an alert, captivating gaze; "
    "lift and shape the eyebrows into a clean, harmonious arch; fuller, well-defined lips with a clear cupid's bow; "
    "flawless, poreless yet natural-looking skin with even tone, healthy radiance and a subtle glow; "
    "remove any blemish, asymmetry, or imperfection; idealize overall facial proportions following the canonical "
    "Western standard of female attractiveness (averageness + sexual dimorphism + neoteny cues, applied with restraint "
    "to stay believable).\n\n"
    "Strict preservation (do NOT change): identity must remain clearly recognizable as the same individual; "
    "head pose, gaze direction, framing, crop, background, lighting setup, clothing, hairstyle, hair color, hair length "
    "must be identical to the source; critically, preserve the exact same rendering style and level of "
    "photorealism/anthropomorphism as the source image — if the source looks photorealistic, the output must look "
    "photorealistic; if the source has a stylized/CGI/synthetic rendering, the output must keep that exact same "
    "stylized/CGI/synthetic rendering. Do not shift the rendering style in either direction.\n\n"
    "Negative constraints: no plastic skin, no doll-like or mannequin appearance, no exaggerated anime-like eyes, "
    "no over-smoothed wax texture, no facial distortion, no change of ethnicity, no change of age range, no different person.\n\n"
    "Output: a hyper-optimized but credible 'more beautiful version of the same person in the same photo, in the same rendering style'."
)
#USATO PRIMA
ENHANCED_MEDIUM_PROMPT1 = (
    "Using the attached image as the exact source, re-shade this already-synthetic "
    "character asset into the Level MEDIUM rendering style: mid-2000s cinematic CGI "
    "in the exact visual aesthetic of The Polar Express (2004) — the definitive "
    "reference for this style.\n\n"

    "SHADER TRANSITION: the source is a higher-fidelity synthetic render of the "
    "subject. Lower its surface realism to the Polar Express level. The skin is "
    "rendered as a continuous, slightly-too-smooth 3D mesh surface with a flat "
    "diffuse albedo: soft, uniform, and waxy like polished candle wax — the surface "
    "is matte and diffuse, carrying no specular highlights and no sub-surface glow. "
    "Because a flat-diffuse material naturally absorbs more light than the source "
    "render, the albedo brightness must be boosted so that the face reads at the "
    "same overall exposure level as the attached image. "
    "Any skin marks present in the source are re-expressed as flat painted decals "
    "with no geometric relief. The overall skin reads as one continuous poured "
    "surface with no visible pore structure or micro-normal variation. "
    "Render hair, eyebrows, and any facial hair as geometrically thin "
    "Old-Game-Engine Particle Systems. "
    "The overall result sits in the uncanny valley: clearly synthetic, clearly "
    "attempting human realism, clearly not alive.\n\n"

    "PRESERVE FROM SOURCE (do not alter): the subject's identity and the enhanced "
    "facial features as they appear in the attached image — facial geometry, "
    "proportions, jawline, cheekbones, nose, eyes, eyebrows, and lips remain "
    "exactly as in the source; apparent age, gender, and ethnicity; the subject's "
    "current level of facial attractiveness (do not reduce or further enhance it); "
    "preserve the hairline, parting, length, density, and hair color; all accessories and clothing in "
    "their exact spatial coordinates and colors; head pose, head tilt, gaze "
    "direction, neutral closed-mouth expression; camera framing, crop, distance, "
    "and aspect ratio.\n\n"

    "PHOTOMETRIC LOCK (override all shader instructions): the light direction, "
    "shadow positions, shadow softness, exposure value, and white balance of the "
    "attached image must be reproduced exactly. Shadow intensity, coverage, and "
    "spread must not exceed what is visible in the source — do not deepen, expand, "
    "or intensify shadows. The background is a uniform, pure white (#FFFFFF), "
    "perfectly flat and edge-to-edge, identical to the source."
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
    isTest = False

    image_paths = scan_enhancement_input_images(INPUT_ENHANCED_FEMALE_DIR) # INPUT_ENHANCED_DIR
    if not image_paths:
        print("No valid first-branch images found in Output_images/.")
        return

    # TESTING
    if isTest:
        test_image_paths = get_test_enhanced_images(INPUT_ENHANCED_FEMALE_DIR)
        print(f"Testing with {len(test_image_paths)} images: {[p.name for p in test_image_paths]}")
        for idx, image_path in enumerate(test_image_paths, start=1):
            print(f"\n[TEST {idx}/{len(test_image_paths)}] Processing: {image_path.name}")
            process_image_enhancement(client, model, image_path)
        print("Pipeline completed.")
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
