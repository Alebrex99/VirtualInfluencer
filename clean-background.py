"""
Clean Output_images backgrounds.

Walks Output_images/ recursively, uses rembg (AI-based segmentation) to extract
the subject, then composites the cutout onto a flat light-grey background
matching the London Face Research Lab dataset (~#C8C8C8). Outputs are saved to
Output_images_clean/ mirroring the source folder structure.

Idempotent: files that already exist in the destination are skipped.
Source extensions accepted: .png, .jpg, .jpeg — all outputs are saved as .png.

Setup:
    pip install rembg onnxruntime
Run:
    python clean-background.py
"""

import sys
from pathlib import Path

try:
    from rembg import new_session, remove
except ImportError:
    sys.exit("rembg not installed. Run: pip install rembg onnxruntime")

from PIL import Image, UnidentifiedImageError

from constants import OUTPUT_DIR, ROOT_DIR, ALLOWED_EXTENSIONS

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
CLEAN_OUTPUT_DIR = ROOT_DIR / "Output_images_clean"
BACKGROUND_RGB = (200, 200, 200)  # ~#C8C8C8 — matches London dataset background

# u2net_human_seg → portrait-optimized (best for faces).
# u2net             → general-purpose fallback.
# isnet-general-use → newer, sometimes sharper hair edges.
SEGMENTATION_MODEL = "u2net_human_seg"


# ──────────────────────────────────────────────
# Core
# ──────────────────────────────────────────────
def clean_one(src_path: Path, dst_path: Path, session) -> bool:
    """
    Remove background from *src_path*, composite on flat grey, save to *dst_path*.
    Returns True if a new file was written, False if skipped (already exists).
    """
    if dst_path.exists():
        return False
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src_path) as src:
        cutout = remove(src.convert("RGBA"), session=session)
    bg = Image.new("RGBA", cutout.size, BACKGROUND_RGB + (255,))
    composite = Image.alpha_composite(bg, cutout).convert("RGB")
    composite.save(dst_path, format="PNG", optimize=False)
    return True


def main():
    if not OUTPUT_DIR.exists():
        print(f"Source directory missing: {OUTPUT_DIR}")
        return

    images = sorted(
        p for p in OUTPUT_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
    )
    if not images:
        print(f"No images found under {OUTPUT_DIR}")
        return

    print(f"Loading segmentation model: {SEGMENTATION_MODEL}")
    session = new_session(SEGMENTATION_MODEL)

    print(f"Found {len(images)} images. Cleaning to {CLEAN_OUTPUT_DIR}\n")
    saved = skipped = failed = 0
    for idx, src in enumerate(images, start=1):
        rel = src.relative_to(OUTPUT_DIR)
        dst = (CLEAN_OUTPUT_DIR / rel).with_suffix(".png")
        print(f"[{idx}/{len(images)}] {rel}", end=" ")
        try:
            if clean_one(src, dst, session):
                print("→ saved")
                saved += 1
            else:
                print("→ skipped (exists)")
                skipped += 1
        except (UnidentifiedImageError, OSError) as e:
            print(f"→ FAILED (image error): {e}")
            failed += 1
        except Exception as e:
            print(f"→ FAILED: {e}")
            failed += 1

    print(f"\nDone. Saved={saved}, Skipped={skipped}, Failed={failed}")


if __name__ == "__main__":
    main()
