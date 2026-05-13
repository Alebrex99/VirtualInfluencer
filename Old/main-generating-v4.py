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

# VERSION 4: PIPELINE WITH REFERENCE STYLE IMAGE

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
    
    # Definiamo la scala AA per il contesto del modello
    aa_scale_context = (
        "CONTEXT: Anthropomorphic Style Appearance (AA) Research. "
        "'Anthropomorphic Style Appearance' (AA) refers to the degree of digital-synthetic effect of a generated rendering. "
        "Goal: Create a synthetic rendering of a virtual influencer that observers classify on the AA Scale. "
        "AA1: the rendered virtual influencer is Humanlike. "
        "AA2: the rendered virtual influencer is Lifelike. "
        "AA3: the rendered virtual influencer has a Humanlike appearance. "
        "AA4: the rendered virtual influencer has Physical characteristics that resemble a real person but through a synthetic lens."
    )

    minimal_shared_prompt = (
        "TASK: Digital Asset Reconstruction. "
        "Transform the provided photograph (base image) into a synthetic-digital rendering. "
    )
    shared_prompt = (
        "TASK: Digital Asset Reconstruction. "
        "Transform the provided photograph (Base Image) into a synthetic-digital rendering. "
 
        "INPUT: Base image is the geometric identity. Use this for Identity, Geometry, and Composition. "
        #"2. IMAGE 2 (Style Reference - Optional) is the shader source: Use ONLY as a rendering tool for textures, "
        #"the absolute source for the rendering engine, texture and shader/light quality. Do NOT adopt the identity of Image 2. "
 
        "INSTRUCTION: Treat the subject in base image as a 3D digital mesh. "
        "You MUST re-surface this mesh using a synthetic-digital rendering engine. "
 
        "IDENTITY ANCHOR: Maintain the exact spatial coordinates of all facial features, anatomical proportions, "
        "asymmetries, and specific skin traits (freckles, scars, blemishes). "
        "Maintain the exact length, density, and spatial coordinates of all facial and body hair (including hair, haircut, beard, eyebrows, eyelashes, and fine peach fuzz). "
        "However, re-render the original pixels with digital shaders."
 
        "SURFACE PROTOCOL: Re-render every surface (skin, hair, fabric) "
        "using digital shaders. The final result must be a synthetic-digital reconstruction."
 
        "COMPOSITION: "
        "Keep the original pose, lighting directions and angles, shadow placement, environment, background and framing. "
        "Keep the original clothing and accessories, including their exact geometry and spatial arrangement. "
        "Keep the original accessories or clothing items. "
        "The goal is a consistent aesthetic quality across all 5 digital levels. "
    )
    
    # ── Level 1 — High (Polished Photorealism) ──────────────────────────────
    #PROMPT BUONO SE VOGLIAMO TOGLIERE BRUFOLI E RENDERE TIPICO AI-GENERATED: 
    #    + "LEVEL: HIGH. TARGET EVALUATION: AA1. "
    #    + "STYLE: Midjourney v5 signature look / AI-generated digital art. "
    #    + "INSTRUCTION: Render the subject with extreme algorithmic smoothness. "
    #    + "The skin must appear flawlessly airbrushed and digitally perfect, exhibiting a synthetic, denoised plastic quality typical of raw generative AI outputs. "
    #    + "Lighting should be uniform and clinical, highlighting the artificial perfection of the digital reconstruction."
    if level == "high":
        return (
            shared_prompt
            + "ANTHROPOMORPHISM LEVEL: HIGH."
            + "STYLE: 'The AI-Signature Look' / Hyper-detailed CGI. " # PROVA: + "STYLE: Midjourney v5 signature look / AI-generated digital art. "
            + "INSTRUCTION: Create an unrealistic HDR effect. " # "Apply micro-contrast and extreme clarity to the skin. "
            + "Increase the 'glassy' reflection of the eyes, mantaining the original color. "
            + "Apply extreme algorithmic sharpening to all natural edges. "
            + "The edge sharpness must come entirely from the high-resolution digital rendering and edge-contrast, "
            + "typical of raw AI-generated assets. "
            + "The skin must appear flawlessly airbrushed and digitally perfect, exhibiting a synthetic, denoised plastic quality typical of raw generative AI outputs and " # + "The skin must have a high-specular shine and visible digital pores, looking like a "
            + "highlighting the artificial perfection of the digital reconstruction and micro-details." # + "perfectly polished Virtual Influencer asset."
        )

    # ── Level 2 — Medium-High (High-End Video Game) ─────────────────────────
    # Molto realistico, ma la perfezione di texture e luci tradisce la natura CGI.
    # PROMPT EFFICACE
    #    + "LEVEL: MEDIUM-HIGH. TARGET EVALUATION: AA2. "
    #    + "STYLE: High-end 3D Character Game Asset / Real-time Engine Render. "
    #    + "INSTRUCTION: Render the subject as a solid, playable 3D videogame character model. "
    #    + "TEXTURE & SHADER: Apply a standardized PBR game shader. The skin must look like a dense, opaque digital material with hard-clamped Subsurface Scattering, revealing its nature as a computational surface. "
    #    + "HAIR & GROOMING: Render the scalp hair and eyebrows as structured geometric hair-cards. Treat any jawline shading strictly as a flat albedo texture overlay, maintaining the exact original density. "          
    #    + "EYES: Feature baked viewport reflections and a mathematically precise, digitally-rendered iris. "
    #    + "OVERALL EFFECT: A sculpted 3D character asset showcasing clean digital surfaces and robust engine-computed shading."
    if level == "medium_high":
        return (
            shared_prompt
            + "ANTHROPOMORPHISM LEVEL: MEDIUM-HIGH. "
            + "STYLE: high-end 3D Character Game Asset (call of duty modern warfare 2019 characters aesthetic). "
            + "INSTRUCTION: Render a high-end playable videogame 3D character. "
            + "The image must look like a game engine render, rejecting any photographic realism."
        
            + "The skin must look like a synthetic material, artificial and mathematically calculated, with a hard-clamped Subsurface Scattering. "
            + "Hair, eyebrows and facial hair must be rendered as distinct digital strands with engine-calculated highlights. "  
            + "Strictly maintain the original hair density and placement from base image. "  
            + "Strictly maintain the original facial characteristics, position, form, proportions, and lighting condition placement from base image. "          
            + "Eyes must feature 'baked' reflections and a piercing, digitally-rendered iris, clearly mathematically generated. "
            + "OVERALL EFFECT: A premium sculpted 3D character asset with digital surfaces and a solid, rendered appearance."
        )

    # ── Level 3 — Medium (Mid-tier CGI / Uncanny Valley) ────────────────────
    # CGI evidente e imperfetta. L'effetto "Polar Express": gommoso, vetroso, perturbante.
    if level == "medium":
        return (
            shared_prompt
            + "LEVEL: MEDIUM. TARGET EVALUATION: AA3. "
            + "STYLE: Early 2000s Cinematic CGI (The Polar Express aesthetic / Uncanny Valley). "
            + "INSTRUCTION: Render a mid-2000s 3D character. "
            
            + "The skin must be waxy, resembling a soft silicone mask. "
            + "The face must be a single, uniform 3D mesh with a simple diffuse texture to define details and imperfections. "

            + "Lighting must be flat and lacks realistic bounce-light, creating a lifeless, 'uncanny' synthetic appearance. "
        )

    # ── Level 4 — Medium-Low (Proportional 3D Animation) ────────────────────
    # Shading stile Pixar/Disney, ma con le proporzioni anatomiche di un umano vero.
    # PERFECT
    if level == "medium_low":
        return (
            shared_prompt
            + "ANTHROPOMORPHISM LEVEL: MEDIUM-LOW. "
            + "STYLE: 2015 Indie Narrative Game Asset (Life is Strange 1 aesthetic). "
            + "INSTRUCTION: Reconstruct the subject as a stylized, slightly low-poly 3D game character. "
            
            + "HAND-PAINTED TEXTURES: Strictly remove all PBR elements (no Normal or Bump maps). "
            + "All skin, clothing, and details must use 'Hand-Painted Albedo Textures'. "
            + "Shadows, highlights, and skin tones must appear directly painted onto the 3D model with visible digital brushstrokes. "
            + "Strictly maintain the original facial characteristics, position, form, proportions, and lighting condition placement from base image. "          

            + "GEOMETRY & HAIR: Simplify facial features into soft, slightly angular 3D geometry. "
            + "Hair must be rendered as solid, sculptural volumetric blocks with painted directional strokes. "
            + "Do not render individual hair strands. "
            + "OVERALL EFFECT: A charming, stylized 3D model characterized by its hand-painted, soft pastel texture work."
        )

    # ── Level 5 — Low (Proportional 2D Cartoon / Illustration) ──────────────
    # Passaggio al 2D puro, ma senza diventare una caricatura.
    # PERFECT
    #+ "LEVEL: LOW. TARGET EVALUATION: Below AA4. "
    #+ "STYLE: Stylized 2D Painterly Animation (animated series aesthetic). "
    #+ "INSTRUCTION: Transform the subject into a 2D painterly animated character. "
    #+ "GEOMETRY & PLANES: Translate the original anatomical identity into sharp, chiseled, and angular facial planes. "
    #+ "Proportions and expressions remain accurate to base image, but the surface structure is stylized and graphic. "
    # + "PAINTERLY TEXTURES: Apply rich, textured 2D digital brushstrokes over the 3D forms. "
    #+ "The skin, hair, and clothing must look like high-end digital concept art or an oil painting brought to life. "
            
    #+ "LIGHTING: Keep the same style lighting of base image. "
    #+ "OVERALL EFFECT: A flat yet dynamically shaded 2D illustration, blending 3D structural volumes with 2D painterly art."
    if level == "low":
        return (
            shared_prompt
            + "ANTHROPOMORPHISM LEVEL: LOW. "
            + "STYLE: 2006 Narrative Game Asset (The sims 2 aesthetic). "
            + "INSTRUCTION: Reconstruct the subject as a stylized, slightly low-poly 3D game character. "
            + "Strictly maintain the original facial characteristics, position, form, proportions, and lighting condition placement from base image. "          

            + "TEXTURES: Strictly remove all PBR elements (no Normal or Bump maps). "
     
            
            + "GEOMETRY & HAIR: Simplify facial features into soft, slightly angular 3D geometry. "
            + "Hair must be rendered as solid, sculptural volumetric blocks with painted directional strokes. "
            + "Do not render individual hair strands. "
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
