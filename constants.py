from pathlib import Path

ROOT_DIR = Path(__file__).parent # VirtualInfluencer project root directory

# MAIN-GENERATING.PY

#LONDON FACE DATASET:
INPUT_DIR = ROOT_DIR / "Images" / "LondonDataset"
TEST_INPUT_DIR = ROOT_DIR / "Images" / "LondonDataset" / "MinMaleMaxFemale"
EXPERIMENT_INPUT_DIR = ROOT_DIR / "Images" / "LondonDataset" / "ExperimentalDataset"

#CHICAGO FACE DATASET:
#INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset"  # se usi il Chicago Face Dataset
#MALE_INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset" / "WhiteMale"
#FEMALE_INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset" / "WhiteFemale"
#TEST_INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset" / "MinMaleMaxFemale"
#EXPERIMENT_INPUT_DIR = ROOT_DIR / "Images" / "ChicagoFaceDataset" / "ExperimentalDataset"

#TUTTI I DATASET
OUTPUT_DIR = ROOT_DIR / "Output_images"
STYLE_REFERENCE_DIR = ROOT_DIR / "Images" / "StyleRefImages"

MAX_IMAGES = 16 # le immagini totali = 16
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5          # seconds; doubles on each subsequent attempt
ALLOWED_EXTENSIONS = {".png", ".jpeg", ".jpg"}
RETRY_BASE_DELAY_SECONDS = 1.5

DEFAULT_MODEL            = "gemini-2.5-flash-image-preview"

LEVELS = ["high", "medium_high", "medium", "medium_low", "low"]
LEVELS_3 = ["high", "medium_high", "medium"]  # Subset of levels for v3.1, which performs best at medium anthropomorphism.
LEVELS_3_SIGLE = { "high": "H", "medium_high": "MH", "medium": "M"} # S = standard

# IMAGES
# Exact pixel sizes Gemini 3 Pro Image Preview returns at 1K for each aspect-ratio label.
# The labelled ratios (e.g. "3:2") are nominal — actual outputs deviate slightly
# (e.g. 1264/848 = 1.4906, not 1.5). Crop input to match the REAL ratio to keep
# the final .resize() uniform on both axes (zero distortion).
GEMINI_1K_OUTPUTS = {
    "1:1":  (1024, 1024),
    "2:3":  (848, 1264),
    "3:2":  (1264, 848),
    "3:4":  (896, 1200),
    "4:3":  (1200, 896),
    "4:5":  (928, 1152),
    "5:4":  (1152, 928),
    "9:16": (768, 1376),
    "16:9": (1376, 768),
    "21:9": (1584, 672),
}

def compute_crop_for_input(width: int, height: int) -> tuple[int, int]:
    """
    Return the (w, h) tuple to crop a `width x height` input to, so that its aspect
    ratio matches Gemini's nearest real 1K output pair. The crop loses the minimum
    pixels possible (centered). Use the returned value as INPUT_RESOLUTION.
    """
    input_ratio = width / height # 2444/ 1718 = 1.4225, closer to 3:2 (1.4906) than 4:3 (1.3333)
    _, (gw, gh) = min(
        GEMINI_1K_OUTPUTS.items(),
        key=lambda kv: abs(kv[1][0] / kv[1][1] - input_ratio),
    )
    target_ratio = gw / gh # e.g. 1264/848 = 1.4906
    # 1.4225 < 1.4906: input + largo del target -> riduco larghezza dell'input
    if input_ratio > target_ratio:           # input wider than target → crop width
        return (round(height * target_ratio), height)
    return (width, round(width / target_ratio))

def compute_gemini_1k_for_input(width: int, height: int) -> tuple[int, int]:
    """
    Return Gemini's native 1K (w, h) for the nearest AR to the input.
    Use as INPUT_RESOLUTION to get 1K-native output (no upscale, no resize-back).
    """
    input_ratio = width / height
    _, (gw, gh) = min(
        GEMINI_1K_OUTPUTS.items(),
        key=lambda kv: abs(kv[1][0] / kv[1][1] - input_ratio), # min -> prende tuple mappa -> cerca il minimo in base alla distanza con il rapporto in input
    )
    return (gw, gh)

# For cropping to Gemini's nearest real 1K AR output
# INPUT_RESOLUTION = compute_crop_for_input(2444, 1718)  # CFD 2444x1718 → (2444, 1640), matches Gemini 3:2 = 1264x848
INPUT_RESOLUTION = compute_gemini_1k_for_input(1350, 1350)  
# London 1350x1350 → (1024, 1024), Gemini 1:1 1K-native
# CFD 2444x1718 → (1264, 848), Gemini 3:2 1K-native
# If you want 1K target output (the cleanest path) -> Set INPUT_RESOLUTION directly to Gemini's pixel pair. For CFD (closest AR = 3:2): INPUT_RESOLUTION = (1264, 848)
STANDARDIZED_IMAGES_DIR = ROOT_DIR / "Images" / "StandardizedImages" # da usare solo con v3.1


# SECOND-GENERATING.PY
ENHANCED_LEVELS = ["high", "medium_high"]  # second-pipeline filter — only enhance these
ENHANCED_LEVELS_SIGLE = { "high": "H", "medium_high": "MH" }
INPUT_ENHANCED_MALE_DIR = ROOT_DIR / "Output_images" / "ReadyToEnhance" / "Male"
INPUT_ENHANCED_FEMALE_DIR = ROOT_DIR / "Output_images" / "ReadyToEnhance" / "Female"
OUTPUT_ENHANCED_DIR = ROOT_DIR / "Output_images" / "Enhanced"