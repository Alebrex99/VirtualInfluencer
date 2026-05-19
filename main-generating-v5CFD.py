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
    
    valid_images = []
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
            valid_images.append(item)
        if len(valid_images) >= max_images:
            break
    return valid_images

    #folder_male = input_dir / "WhiteMale"
    #folder_female = input_dir / "WhiteFemale"
    #valid_images = []
    #for sub in (folder_male, folder_female):
    #    if not sub.exists():
    #        continue
    #    for item in sorted(sub.iterdir()):
    #        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
    #            valid_images.append(item)
    #            if len(valid_images) >= max_images:
    #                return valid_images
    
    '''
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
    Build anthropomorphism prompt for gemini-3-pro-image-preview.

    Five levels, ordered most-realistic → most-stylized:
        high         → Hyperreal CGI / MetaHuman / "AI-signature" look
        medium_high  → AAA real-time game character (CoD MW 2019)
        medium       → Mid-2000s cinematic CGI (Polar Express, uncanny valley)
        medium_low   → Hand-painted indie 3D (Life is Strange 1)
        low          → Early-2000s low-poly (The Sims 2)

    All five share the SAME identity + composition lock; only the
    RENDER STYLE block changes. This isolates the variable being studied.
    """

    # ── IDENTITY + COMPOSITION LOCK (shared across all 5 levels) ──────────
    # Concise. No repetition. Lives at the top because Gemini 3 anchors
    # later instructions to earlier context.
    locked_context = (
        "ROLE: You are an expert image producer specializing in 3D character asset generation. "
        "TASK: Your task is to produce a synthetic 3D character asset by re-surfacing a given geometric reference (base image) "
        "with a specified target rendering style, ranging from a high level of near-human photorealism, through medium-high, medium, medium-low, and low levels of anthropomorphism."
        
        "BASE INPUT IMAGE: The base image serves as the canonical mesh, providing the geometric identity (Identity, Geometry, and Composition). "
        "It is never the source of pixels, always the source of structure."

        "IDENTITY LOCK: The following attributes must be preserved exactly and never altered, only re-rendered through the target shader:\n"
        "- Facial geometry: Every feature's spatial coordinates, proportions, asymmetries, and bone structure.\n"
        "- Skin character: Every freckle, mole, scar, pimple, abrasion, uneven pigmentation – these must be preserved as micro-features in the new shader.\n"
        "- Hair: Exact hairline, parting, length, density, color, eyebrow shape and density, eyelashes, beard/stubble pattern, fine peach fuzz. The original pixels for hair must be re-rendered with digital shaders.\n"
        "- Accessories: Every earring, piercing, hair clip, glasses, necklace, garment item – maintain the same geometry, placement, and color.\n"
        "- Identity attributes: Apparent age, gender, ethnicity, and the subject's inherent facial attractiveness – these must be held constant across all levels.\n"

        "COMPOSITION LOCK: The following aspects must be preserved exactly:\n"
        "- Pose, head tilt, gaze direction, facial expression.\n"
        "- Camera framing, crop, distance, aspect ratio.\n"
        "- Lighting direction, light angle and shadow placement.\n"
        "- Replicate the exact Exposure Value (EV) of the base image\n"
        "- Background (plain white #FFFFFF) and environment: rendered as the base image background\n"
        "- Clothing geometry, color, and spatial arrangement\n\n"

        "VARIABLE: only the SHADING MODEL and SURFACE RENDERING are allowed to change between levels. "
        "Light direction is locked; how that light interacts with the new shader is dictated by the target style. \n\n"

        "INSTRUCTION: "
        "1. Treat the subject in the provided base image as a 3D digital mesh. \n"
        "2. You MUST re-surface this mesh using a synthetic-digital rendering engine.\n"
        "3. SURFACE PROTOCOL: Re-render every surface (skin, hair, fabric) using digital shaders. The final result must be a synthetic-digital reconstruction.\n"

        "TARGET RENDER STYLE:\n"
    )


    # ── LEVEL-SPECIFIC RENDER STYLE (the ASK, anchored at the end) ────────

    # ── HIGH — Hyperreal CGI / MetaHuman / "AI-signature" look ────────────
    # Resolves v4 contradiction: imperfections become hyper-detailed
    # micro-features rendered THROUGH the synthetic shader, not erased.
    if level == "high":
        return (
            locked_context +
            "RENDER STYLE — Level HIGH (Midjourney v5 signature look / AI-generated digital art):\n"
            "Render as an Midjourney v5 / hyper-detailed virtual-influencer asset. "
            "Every pore, freckle, and skin imperfection is "
            "preserved BUT re-rendered as ultra-sharp, algorithmically-traced "
            "micro-detail — the way raw generative-AI portraits exhibit "
            "impossible micro-clarity. Skin is denoised, micro-contrasted, "
            "with a subtle synthetic sheen and unnatural HDR mid-tones. "
            "Eyes are glassy and over-specular, irises mathematically perfect, "
            "original eye color preserved. All natural edges (hair strands, "
            "eyelashes, garment seams) are algorithmically over-sharpened. "
            "The overall surface reads as 'too clean to be a photograph' — "
            "the signature look of a high-end synthetic asset."
            #+ hard_negatives
        )

    # ── MEDIUM-HIGH — AAA real-time game character (CoD MW 2019) ──────────
    # DA PROVARE SE SI CREANO RISULTATI DIVERSI
    #"The skin surface is rendered using a PBR material with a strongly "
    #"diffuse-dominant albedo: subsurface scattering is present but clamped "
    #"and hard-edged, producing an opaque, dense, slightly waxy appearance "
    #"that clearly rejects biological photorealism. "
    if level == "medium_high":
        return (
            locked_context +
            "RENDER STYLE — Level MEDIUM-HIGH (AAA Video Game Asset Reconstruction):\n"
            "Render the subject as a 3D playable character for a real-time engine "
            "(Uncharted 4 CHARACTERS aesthetics). Replicate the exact Exposure Value (EV) of the base image "
            "SURFACE PROTOCOL: Treat the skin as a 'Synthetic PBR Material'. "
            "The skin is rendered as a opaque 'Matte-Plastic' texture, rejecting biological softness. "
            "TEXTURE MAPS: Render the surface using evident diffuse-dominant albedo and normal maps. "
            "Details must be rendered as mathematically generated digital noise, not organic skin. "
            "SHADING: Apply a 'Hard-Clamped Subsurface Scattering' effect to create an opaque, "
            "waxy appearance typical of sculpted digital assets. "
            "HAIR & EYES: Render hair, eyebrows, and any facial hair as geometrically thin high-end Game-Engine Particle Systems: " # thin 'Game-Engine Ribbons' with baked specular highlights. "
            "distinct, geometrically clean alpha cards with baked specular highlights. "
            "Eyes must have static, pre-rendered reflections. "
            "LIGHTING: Use 'Directional Rim Lighting' to express the 3D topology and volume of the mesh. "
            "The result must be an unmistakable, high-poly real-time game character render."
            #+ hard_negatives
        )

    # ── MEDIUM — Mid-2000s cinematic CGI / Uncanny Valley ─────────────────
    # DA PROVARE SE SI CREANO RISULTATI DIVERSI
    #"The skin is rendered as a continuous, slightly-too-smooth 3D mesh surface: "
    #"soft, diffuse, and waxy like polished candle wax or a dense silicone mould — "
    #"with a flat, uniform diffuse albedo and minimal specular response (the surface "
    #"does not shine or gleam; it is matte-waxy, not plastic-shiny). "
    if level == "medium":
        return (
            locked_context +
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
            #+ hard_negatives
        )

    # ── MEDIUM-LOW — Hand-painted indie 3D (Life is Strange 1) ────────────
    if level == "medium_low":
        return (
            locked_context +
            "RENDER STYLE — Level MEDIUM-LOW (Hand-Painted Indie 3D):\n"
            "Render in the aesthetic of Life is Strange (2015) or similar "
            "hand-painted indie 3D narrative games. STRICTLY NO PBR — no "
            "normal maps, no bump maps, no specular maps. All surfaces use "
            "hand-painted albedo textures: shadows, highlights, skin tones, "
            "and fabric details are visibly brushed onto the model with "
            "directional digital strokes. Facial geometry is simplified into "
            "soft, slightly angular planes. Hair is rendered as solid "
            "sculptural volumes — chunked, painted, with directional "
            "highlight strokes — never as individual strands. The palette "
            "is soft and slightly desaturated."
            #+ hard_negatives
        )

    # ── LOW — Early-2000s low-poly (The Sims 2) ───────────────────────────
    if level == "low":
        return (
            locked_context +
            "RENDER STYLE — Level LOW (Early-2000s Low-Poly Game Asset):\n"
            "Render in the aesthetic of The Sims 2 (2004) or comparable "
            "early-2000s low-poly 3D characters. Geometry is simplified into clean 3D volumes. "
            "Apply 'Smooth Shading' to the mesh: while the silhouette remains simplified "
            "and slightly angular, the internal facial planes must be smooth and rounded, "
            "with no visible faceted edges. STRICTLY NO PBR — "
            "all surfaces use simple flat albedo textures with baked-in "
            "shading. Skin is a single uniform tone with painted-on "
            "shadows. Hair is a solid sculptural cap of simplified geometry "
            "with painted directional strokes — no individual strands."
            "Eyes are simple textured spheres. Expression and identity "
            "are still readable, but rendered with the unmistakable "
            "computational economy of mid-2000s consumer-PC 3D graphics."
            #+ hard_negatives
        )

    raise ValueError(f"Unsupported level: {level}")

def build_enhanced_prompt(level: str) -> str:
    # ── IDENTITY + COMPOSITION LOCK (shared across all 5 levels) ──────────
    # Concise. No repetition. Lives at the top because Gemini 3 anchors
    # later instructions to earlier context.
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


    # ── LEVEL-SPECIFIC RENDER STYLE (the ASK, anchored at the end) ────────

    # ── HIGH — Hyperreal CGI / MetaHuman / "AI-signature" look ────────────
    # Resolves v4 contradiction: imperfections become hyper-detailed
    # micro-features rendered THROUGH the synthetic shader, not erased.
    # STABLE VERSION: 
    '''"RENDER STYLE — Level HIGH (Midjourney-v5 signature / "
            "AI-generated virtual-influencer asset):\n"
            "Render as a hyper-detailed virtual-influencer asset in the "
            "signature look of high-end generative AI portraits. Every pore, "
            "freckle, mole, and skin imperfection from the base image is "
            "PRESERVED and RE-RENDERED into ultra-sharp, algorithmically over-traced "
            "micro-relief - the way raw generative-AI portraits exhibit impossible micro-clarity. "
            "Skin carries a subtle synthetic sheen on the highlight side, "
            "with unnaturally even local contrast across mid-tones (local "
            "contrast only — overall EV unchanged). Eyes are glassy and "
            "over-specular, irises mathematically circular and over-detailed, "
            "original eye color preserved exactly. All natural edges — hair "
            "strands, eyelashes, lip line — are "
            "algorithmically over-sharpened, mantaining the original color and constraints. The surface reads as 'too "
            "perfectly detailed to be a photograph': the fingerprint of a "
            "high-end synthetic asset, not a smoothed beauty retouch."'''
    if level == "high":
        return (
            locked_context +
            "RENDER STYLE — Level HIGH (Midjourney-v5 signature / "
            "AI-generated virtual-influencer asset):\n"
            "Render as a hyper-detailed virtual-influencer asset in the "
            "signature look of high-end generative AI portraits. Every pore, "
            "freckle, mole, and skin imperfection from the base image is "
            "RE-RENDERED into ultra-sharp, algorithmically over-traced "
            "micro-relief - the way raw generative-AI portraits exhibit impossible micro-clarity. "
            "Skin carries a synthetic sheen on the highlight side, "
            "with unnaturally even local contrast across mid-tones and a noticeable plasticity. "
            "Eyes are glassy and over-specular, irises mathematically circular and over-detailed, "
            "original eye color preserved. All natural edges — hair "
            "strands, eyelashes, lip line — are "
            "algorithmically over-sharpened, detailed and shiny, preserving the original constraints. The surface reads as 'too "
            "perfectly detailed to be a photograph': the fingerprint of a "
            "high-end synthetic asset."
            #+ hard_negatives
        )

    # ── MEDIUM-HIGH — AAA real-time game character (CoD MW 2019) ──────────
    # DA PROVARE SE SI CREANO RISULTATI DIVERSI
    #"The skin surface is rendered using a PBR material with a strongly "
    #"diffuse-dominant albedo: subsurface scattering is present but clamped "
    #"and hard-edged, producing an opaque, dense, slightly waxy appearance "
    #"that clearly rejects biological photorealism. "
    if level == "medium_high":
        return (
            locked_context +
            "RENDER STYLE — Level MEDIUM-HIGH (AAA Video Game Asset Reconstruction):\n"
            "Render the subject as a 3D playable character for a real-time engine (skin aesthetics of Uncharted 4 characters). "
            "Replicate the exact Exposure Value (EV) of the base image. "
            "SURFACE PROTOCOL: Treat the skin as a 'Synthetic PBR Material'. "
            "The skin is rendered as a opaque 'Matte-Plastic' texture, rejecting biological softness. "
            "TEXTURE MAPS: Render the surface using evident diffuse-dominant albedo and normal maps. "
            "Details must be rendered as mathematically generated digital noise, not organic skin. "
            "SHADING: Apply a 'Hard-Clamped Subsurface Scattering' effect to create an opaque, "
            "waxy appearance typical of sculpted digital assets. "
            "HAIR & EYES: Render hair, eyebrows, and any facial hair as geometrically thin high-end Game-Engine Particle Systems: " # thin 'Game-Engine Ribbons' with baked specular highlights. "
            "distinct, geometrically clean alpha cards with baked specular highlights. "
            "Eyes must have static, pre-rendered reflections. "
            "LIGHTING: Use 'Directional Rim Lighting' to express the 3D topology and volume of the mesh. "
            "The result must be an unmistakable, high-poly real-time game character render."
            #+ hard_negatives
        )

    # ── MEDIUM — Mid-2000s cinematic CGI / Uncanny Valley ─────────────────
    # DA PROVARE SE SI CREANO RISULTATI DIVERSI
    #"The skin is rendered as a continuous, slightly-too-smooth 3D mesh surface: "
    #"soft, diffuse, and waxy like polished candle wax or a dense silicone mould — "
    #"with a flat, uniform diffuse albedo and minimal specular response (the surface "
    #"does not shine or gleam; it is matte-waxy, not plastic-shiny). "
    if level == "medium":
        return (
            locked_context +
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
            #+ hard_negatives
        )

    # ── MEDIUM-LOW — Hand-painted indie 3D (Life is Strange 1) ────────────
    if level == "medium_low":
        return (
            locked_context +
            "RENDER STYLE — Level MEDIUM-LOW (Hand-Painted Indie 3D):\n"
            "Render in the aesthetic of Life is Strange (2015) or similar "
            "hand-painted indie 3D narrative games. STRICTLY NO PBR — no "
            "normal maps, no bump maps, no specular maps. All surfaces use "
            "hand-painted albedo textures: shadows, highlights, skin tones, "
            "and fabric details are visibly brushed onto the model with "
            "directional digital strokes. Facial geometry is simplified into "
            "soft, slightly angular planes. Hair is rendered as solid "
            "sculptural volumes — chunked, painted, with directional "
            "highlight strokes — never as individual strands. The palette "
            "is soft and slightly desaturated."
            #+ hard_negatives
        )

    # ── LOW — Early-2000s low-poly (The Sims 2) ───────────────────────────
    if level == "low":
        return (
            locked_context +
            "RENDER STYLE — Level LOW (Early-2000s Low-Poly Game Asset):\n"
            "Render in the aesthetic of The Sims 2 (2004) or comparable "
            "early-2000s low-poly 3D characters. Geometry is simplified into clean 3D volumes. "
            "Apply 'Smooth Shading' to the mesh: while the silhouette remains simplified "
            "and slightly angular, the internal facial planes must be smooth and rounded, "
            "with no visible faceted edges. STRICTLY NO PBR — "
            "all surfaces use simple flat albedo textures with baked-in "
            "shading. Skin is a single uniform tone with painted-on "
            "shadows. Hair is a solid sculptural cap of simplified geometry "
            "with painted directional strokes — no individual strands."
            "Eyes are simple textured spheres. Expression and identity "
            "are still readable, but rendered with the unmistakable "
            "computational economy of mid-2000s consumer-PC 3D graphics."
            #+ hard_negatives
        )

    raise ValueError(f"Unsupported level: {level}")

# MEDIUM HIGH NON FUNZIONA -> IDENTICO A ORIGINAL
def build_gemini_style_prompt(level: str) -> str:
    """
    Gemini-3-native build_prompt(level).
    Drop-in for main-generating-v5c.py — same signature, same return type.
    """

    # ── STYLE BLOCK (the ASK) — Subject + Style first ─────────────────────
    style_blocks = {
        "high": (
            "STYLE — HIGH anthropomorphism (AI-signature virtual-influencer):\n"
            "A hyper-detailed virtual-influencer portrait in the signature "
            "look of high-end generative-AI imagery (Midjourney-v5 / "
            "MetaHuman). The skin is high-resolution synthetic: every pore "
            "from the base photograph is rendered as algorithmically "
            "over-traced micro-relief, freckles and moles have sub-pixel "
            "crisp edges, fine peach fuzz is etched with impossible "
            "micro-clarity. The highlight side of the face carries a subtle "
            "synthetic sheen; mid-tones show unnaturally even local contrast "
            "(local micro-contrast only — overall exposure is unchanged). "
            "Eyes are glassy and over-specular with mathematically circular "
            "irises in the subject's original eye color. Hair strands, "
            "eyelashes, lip contour, and garment seams are "
            "algorithmically over-sharpened. The overall texture reads as "
            "'too perfectly detailed to be a real photograph' — the "
            "fingerprint of a high-end synthetic asset, not a smoothed "
            "beauty retouch."
        ),
        "medium_high": (
            "STYLE — MEDIUM-HIGH anthropomorphism (AAA real-time game "
            "character, Uncharted 4):\n"
            "A 3D playable character for a real-time engine in the look of "
            "Uncharted 4 character assets. Skin is a dense, matte, "
            "synthetic PBR shader: diffuse-dominant albedo with "
            "hard-clamped subsurface scattering. The surface is opaque and "
            "matte — never plastic-shiny, never waxy. Pores, freckles, and "
            "every micro-imperfection from the base photograph are baked "
            "into the normal map and the diffuse pass as crisp, "
            "mathematically clean micro-detail. Hair, eyebrows, and any "
            "facial hair are rendered as high-end game-engine particle "
            "systems: distinct, geometrically clean alpha cards with baked "
            "specular highlights. Eyes have static, pre-rendered "
            "reflections. The overall image is unmistakably a high-poly "
            "real-time game character render."
        ),
        "medium": (
            "STYLE — MEDIUM anthropomorphism (Early-2000s Cinematic CGI / Uncanny Valley):"
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
        ),
        "medium_low": (
            "STYLE — MEDIUM-LOW anthropomorphism (hand-painted indie 3D, "
            "Life is Strange 2015):\n"
            "All surfaces are hand-painted albedo textures (strictly no "
            "PBR, no normal maps, no specular maps). Shadows, highlights, "
            "skin tones, and fabric details are visibly brushed onto the "
            "model with directional digital strokes. Facial geometry is "
            "simplified into soft, slightly angular planes. Hair is solid "
            "sculptural volumes — chunked, painted, directional highlight "
            "strokes, never individual strands. Palette is soft and "
            "slightly desaturated."
        ),
        "low": (
            "STYLE — LOW anthropomorphism (early-2000s low-poly game "
            "asset, The Sims 2 2004):\n"
            "Geometry is simplified into clean 3D volumes with smooth "
            "shading (slightly angular silhouette, smooth rounded internal "
            "planes, no faceted edges). Strictly no PBR — flat albedo "
            "textures with baked-in shading. Skin is a single uniform tone "
            "with painted-on shadows. Hair is a solid sculptural cap with "
            "painted directional strokes, no individual strands. Eyes are "
            "simple textured spheres. Expression and identity remain "
            "readable."
        ),
    }

    if level not in style_blocks:
        raise ValueError(f"Unsupported level: {level}")

    # ── PROMPT (Gemini-3-native order: subject → style → context → locks) ──
    return (
        # 1. Subject + the role of the reference image
        "Re-render the subject of the attached photograph as a synthetic 3D "
        "character asset. The attached image is BOTH the geometric "
        "reference (identity, pose, framing, clothing, accessories) AND the "
        "photometric reference (light direction, shadow positions and "
        "softness, exposure, white balance, and the pure white "
        "background).\n\n"

        # 2. The style block (the actual ask)
        + style_blocks[level] + "\n\n"

        # 3. What the transformation IS and is not (positively framed)
        "TRANSFORMATION SCOPE: only the SURFACE SHADER changes. The shader "
        "is the single variable. The lighting rig stays where it is, the "
        "exposure stays where it is, the background stays where it is, and "
        "every facial landmark from the photograph stays where it is — all "
        "of these are re-rendered THROUGH the target shader, never "
        "replaced by it.\n\n"

        # 4. Cinematographic preservation language for the photometric blueprint
        "LIGHTING TO PRESERVE (cinematographic terms): the base image is a "
        "frontal studio portrait lit by a soft frontal key with a balanced "
        "fill, on a seamless pure-white #FFFFFF cyclorama. The key/fill "
        "ratio, the shadow direction (look at where the shadow under the "
        "nose and the chin sits in the base image — that exact placement, "
        "shape, and softness must reappear in the output), and the overall "
        "exposure value are reproduced one-to-one. The shader changes how "
        "this lighting reads on the surface, but the lighting itself does "
        "not move, brighten, darken, soften, harden, or warm up.\n\n"

        # 5. Hard locks at the END (Gemini 3 weights this position highest)
        "ABSOLUTE OUTPUT CONSTRAINTS (highest priority):\n"
        "- BACKGROUND: pure white #FFFFFF, perfectly flat and uniform, "
        "edge-to-edge, identical to the base image. A solid white "
        "cyclorama. No gradient, no vignette, no gray cast, no tint, no "
        "shadow spill.\n"
        "- EXPOSURE: identical Exposure Value to the base image. The output "
        "histogram matches the input histogram in mid-tone placement and "
        "highlight roll-off.\n"
        "- LIGHTING & SHADOWS: identical light direction, identical shadow "
        "positions, identical shadow softness. The shader changes; the "
        "lighting rig does not.\n"
        "- IDENTITY: every freckle, mole, pore distribution, asymmetry, "
        "hair strand pattern, eyebrow shape, accessory (hair clip, "
        "earrings, garment), and the t-shirt geometry are present in the "
        "output, restyled into the target shader.\n"
        "- AGE, GENDER, ETHNICITY, and the subject's inherent facial "
        "attractiveness are held constant across all anthropomorphism "
        "levels.\n"
        "- ASPECT RATIO and crop match the base image exactly.\n"
        "These constraints override any stylistic interpretation of the "
        "STYLE block above if a conflict appears."
    )


 
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
                delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)) # es. input = 1.5, 3, 6, 12
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


def save_image(output_dir, source_path, level, image):
    """
    Save *image* to *output_dir* using the naming scheme:
        <stem>_<SIGLE>.png
    Creates the directory if missing. Returns the output Path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"{source_path.stem}_{LEVELS_3_SIGLE.get(level, level)}.png"
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
        #prompt = build_prompt(level)
        prompt = build_enhanced_prompt(level)
        #prompt = build_gemini_style_prompt(level)
        # Se vogliamo usare uno style transfer da immagini reference
        style_reference_image = get_style_reference_image(level)  # Ottieni l'immagine di riferimento per lo stile specifico del livello
        
        # Dato il livello corrente, prima di generare un'immagine e spendere soldi,
        # 1. verifica che l'immagine associata a quel livello non esista già (potrebbe essere stata generata in un run precedente)
        # 2. se esiste già, skip al prossimo livello senza chiamare l'API, altrimenti procedi con la generazione
        expected_out_path = OUTPUT_DIR / f"{image_path.stem}_{LEVELS_3_SIGLE.get(level, level)}.png"  # image_path.stem = nome del file senza estensione, es. "001_03" per "001_03.jpg"
        if expected_out_path.exists():
            print(f"Output already exists for level [{level}]: {expected_out_path}. Skipping generation.")
            continue
 
        try:
            if style_reference_image is None:
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
    isTest = False

    # riempire la lista di paths delle immagini da processare
    image_paths = scan_input_images(EXPERIMENT_INPUT_DIR, MAX_IMAGES)
    if not image_paths:
        print("No valid input images found.")
        return
    
    # ---------------------TESTING------------------------
    if isTest:
        # TEST: Prendi direttamente due immagini note: WhiteMale/WM-201 e WhiteFemale/WF-233
        test_image_paths = get_test_input_images(TEST_INPUT_DIR)
        print(f"Testing with {len(test_image_paths)} images: {[p.name for p in test_image_paths]}")
        for idx, image_path in enumerate(test_image_paths, start=1):
            print(f"\n[TEST {idx}/{len(test_image_paths)}] Processing: {image_path.name}")
            process_one_image(client, model, image_path)
        print("Pipeline completed.")
        return

    # --------------------FULL RUN------------------------
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
