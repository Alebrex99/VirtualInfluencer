from pathlib import Path

ROOT_DIR = Path(__file__).parent # VirtualInfluencer project root directory
#INPUT_DIR = ROOT_DIR / "Images" / "LondonSet" # se usi il LondonSet
INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset" / "WhiteMale" # se usi il Chicago Face Dataset
OUTPUT_DIR = ROOT_DIR / "Output_images"
STYLE_REFERENCE_DIR = ROOT_DIR / "Images" / "StyleRefImages"

MAX_IMAGES = 1
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5          # seconds; doubles on each subsequent attempt
ALLOWED_EXTENSIONS = {".png", ".jpeg", ".jpg"}
RETRY_BASE_DELAY_SECONDS = 1.5

DEFAULT_MODEL            = "gemini-2.5-flash-image-preview"

# ── Anthropomorphism levels — ordered from most realistic to most stylized ──
# Used by build_prompt() and process_one_image() in generate_pipeline.py.
# Adding or removing a level here automatically propagates through the pipeline.
LEVELS = ["high", "medium_high", "medium", "medium_low", "low"]
EDITING_LEVELS = ["level_1", "level_2", "level_3", "level_4", "level_5"]


# IMAGES
INPUT_RESOLUTION = (1080, 1080) # (1080, 1080) # Set to None to keep original resolution; otherwise, specify target resolution as (width, height) tuple.
STANDARDIZED_IMAGES_DIR = ROOT_DIR / "Images" / "StandardizedImages" # da usare solo con v3.1