from pathlib import Path

ROOT_DIR = Path(__file__).parent
#INPUT_DIR = ROOT_DIR / "Images" / "LondonSet" # se usi il LondonSet
INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset" # se usi il Chicago Face Dataset
OUTPUT_DIR = ROOT_DIR / "Output_images"

MAX_IMAGES = 2
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


# CARATTERISTICHE IMMMAGINI DI OUTPUT
OUTPUT_RESOLUTION = "1K" # per il modello 2.5 flash image preview, 1K (1024x1024) è la risoluzione massima supportata.
OUTPUT_ASPECT_RATIO = "1:1" # per il modello 2.5 flash image preview, è supportato solo l'aspect ratio 1:1.

