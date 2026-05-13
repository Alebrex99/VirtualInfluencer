# VERSION 1

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
        "TASK: produce a synthetic 3D character asset by re-surfacing the "
        "geometric reference (Image 1) with a target rendering style. "
        "Image 1 is the canonical mesh — never the source of pixels, "
        "always the source of structure.\n\n"

        "IDENTITY LOCK — re-render through the target shader, never alter:\n"
        "- Facial geometry: every feature's spatial coordinates, "
        "proportions, asymmetries, bone structure\n"
        "- Skin character: every freckle, mole, scar, pimple, abrasion, "
        "uneven pigmentation — preserved as micro-features in the new shader\n"
        "- Hair: exact hairline, parting, length, density, color, eyebrow "
        "shape and density, eyelashes, beard/stubble pattern, fine peach fuzz\n"
        "- Accessories: every earring, piercing, hair clip, glasses, "
        "necklace, garment item — same geometry, same placement, same color\n"
        "- Identity attributes: apparent age, gender, ethnicity, and the "
        "subject's inherent facial attractiveness — held constant across all levels\n\n"

        "COMPOSITION LOCK — preserve exactly:\n"
        "- Pose, head tilt, gaze direction, facial expression\n"
        "- Camera framing, crop, distance, aspect ratio\n"
        "- Lighting direction (where key/fill/rim originate) and shadow placement\n"
        "- Background and environment\n"
        "- Clothing geometry, color, and spatial arrangement\n\n"

        "VARIABLE: only the SHADING MODEL and SURFACE RENDERING change "
        "between levels. Light direction is locked; how that light "
        "interacts with the new shader is dictated by the target style below.\n\n"
    )

    # ── HARD NEGATIVES (shared, appended at end of every prompt) ──────────
    hard_negatives = (
        "\n\nDO NOT:\n"
        "- alter facial proportions, geometry, or asymmetries\n"
        "- change identity, apparent age, gender, or ethnicity\n"
        "- remove, relocate, smooth-over, or invent skin marks\n"
        "- change hair style, length, density, parting, or color\n"
        "- swap, remove, or reposition any accessory or garment\n"
        "- recrop, reframe, or rotate the camera\n"
        "- shift the direction of the key light"
    )

    # ── LEVEL-SPECIFIC RENDER STYLE (the ASK, anchored at the end) ────────

    # ── HIGH — Hyperreal CGI / MetaHuman / "AI-signature" look ────────────
    # Resolves v4 contradiction: imperfections become hyper-detailed
    # micro-features rendered THROUGH the synthetic shader, not erased.
    if level == "high":
        return (
            locked_context +
            "RENDER STYLE — Level HIGH (Hyperreal Synthetic CGI):\n"
            "Render as an Unreal Engine 5 MetaHuman / hyper-detailed virtual-"
            "influencer asset. Every pore, freckle, and skin imperfection is "
            "preserved BUT re-rendered as ultra-sharp, algorithmically-traced "
            "micro-detail — the way raw generative-AI portraits exhibit "
            "impossible micro-clarity. Skin is denoised, micro-contrasted, "
            "with a subtle synthetic sheen and unnatural HDR mid-tones. "
            "Eyes are glassy and over-specular, irises mathematically perfect, "
            "original eye color preserved. All natural edges (hair strands, "
            "eyelashes, garment seams) are algorithmically over-sharpened. "
            "The overall surface reads as 'too clean to be a photograph' — "
            "the signature look of a high-end synthetic asset."
            + hard_negatives
        )

    # ── MEDIUM-HIGH — AAA real-time game character (CoD MW 2019) ──────────
    if level == "medium_high":
        return (
            locked_context +
            "RENDER STYLE — Level MEDIUM-HIGH (AAA Real-Time Game Asset):\n"
            "Render as a high-end playable character in the IW 8.0 engine "
            "(Call of Duty: Modern Warfare 2019 character aesthetic). The "
            "image must read as a real-time game-engine frame, not a "
            "photograph. Skin is a dense PBR material with hard-clamped "
            "subsurface scattering — opaque, mathematically computed, with "
            "the subtle plasticity of a real-time shader. Hair, eyebrows, "
            "and any facial hair are rendered as discrete digital strands "
            "or hair-cards with engine-baked specular highlights. Eyes "
            "carry baked viewport reflections and a piercing, digitally-"
            "rendered iris. The lighting is the same as the source, but "
            "computed by an engine rather than captured by a sensor."
            + hard_negatives
        )

    # ── MEDIUM — Mid-2000s cinematic CGI / Uncanny Valley ─────────────────
    if level == "medium":
        return (
            locked_context +
            "RENDER STYLE — Level MEDIUM (Early-2000s Cinematic CGI / Uncanny Valley):\n"
            "Render in the aesthetic of The Polar Express (2004) or early "
            "performance-capture cinema. Skin is waxy and slightly "
            "translucent, like a soft silicone mask or polished candle wax. "
            "The face is one continuous, slightly-too-smooth 3D mesh with "
            "a flat diffuse texture pass for marks and imperfections — they "
            "read as painted onto the surface rather than emerging from it. "
            "Lighting is flat, lacks realistic bounce-light, and produces "
            "shadows that fall slightly too softly. The result sits in the "
            "uncanny valley: clearly synthetic, clearly attempting realism, "
            "clearly not alive."
            + hard_negatives
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
            + hard_negatives
        )

    # ── LOW — Early-2000s low-poly (The Sims 2) ───────────────────────────
    if level == "low":
        return (
            locked_context +
            "RENDER STYLE — Level LOW (Early-2000s Low-Poly Game Asset):\n"
            "Render in the aesthetic of The Sims 2 (2004) or comparable "
            "early-2000s low-poly 3D characters. Geometry is visibly "
            "low-polygon: facial planes are blocky and faceted, edges "
            "between polygons readable on the silhouette. STRICTLY NO PBR — "
            "all surfaces use simple flat albedo textures with baked-in "
            "shading. Skin is a single uniform tone with painted-on "
            "shadows. Hair is a solid sculptural cap of low-poly geometry "
            "with painted directional strokes — no individual strands. "
            "Eyes are simple textured spheres. Expression and identity "
            "are still readable, but rendered with the unmistakable "
            "computational economy of mid-2000s consumer-PC 3D graphics."
            + hard_negatives
        )

    raise ValueError(f"Unsupported level: {level}")



# VERSION 2
"""
build_prompt_v6.py
──────────────────────────────────────────────────────────────────────────────
OPTIMIZED PROMPT BUILDER — Gemini 3 Pro Image (gemini-3-pro-image-preview)
Version: 6.0
Key changes vs v5b:
  1. NO hard negatives anywhere — converted to positive affirmations.
     Gemini 3 interprets negated instructions unreliably and may propagate
     the named concept (e.g. mentioning "white background" in a DO NOT block
     can trigger the model to treat it as a variable, causing color drift).
  2. Narrative paragraph structure replaces instruction-list structure.
     Google's own best-practice guide: "describe the scene, don't list
     keywords". The locked_context is now a first-person production brief.
  3. Explicit "Generate an image of..." opening verb — required by the
     Google documentation so the multimodal model emits an image, not text.
  4. Exposure anchor added to every level — cures the brightness-drop issue.
  5. Background anchor promoted and made quantitative (#FFFFFF, solid,
     no gradient, no vignette) — prevents background color drift.
  6. Each level-specific block is a self-contained narrative paragraph
     rather than a mixed list + label block. This removes the contradiction
     risk that was causing plastic-sheen inconsistency on medium.
  7. Attractiveness/identity consistency made explicit in the shared context.
  8. The "3D mesh" framing is kept because it successfully bypasses the
     model's real-person IP filter.
──────────────────────────────────────────────────────────────────────────────
"""


def build_prompt(level: str) -> str:
    """
    Return a single prompt string for the specified anthropomorphism level.

    Levels (most realistic → most stylised):
        "high"        → Hyperreal AI-art / Virtual Influencer signature look
        "medium_high" → AAA real-time game character (high-poly PBR, CoD / GoW)
        "medium"      → Mid-2000s cinematic CGI / Uncanny Valley (Polar Express)
        "medium_low"  → Hand-painted indie 3D (Life is Strange)
        "low"         → Early-2000s low-poly game asset (The Sims 2)
    """

    # ─────────────────────────────────────────────────────────────────────
    # SHARED LOCKED CONTEXT
    # Written as a narrative production brief, not a bullet list.
    # Opens with the required "Generate an image" verb.
    # All constraints are stated positively.
    # ─────────────────────────────────────────────────────────────────────
    locked_context = (
        "Generate an image of a synthetic 3D character asset produced by a professional "
        "real-time rendering engine. "

        "The attached reference photograph serves exclusively as the canonical geometric "
        "source mesh — a 3D scan providing structure, never pixels. "
        "Every surface in the output must be re-rendered through a digital shader "
        "engine; the result must read as a fully synthetic, computer-generated character, "
        "never a photograph or a retouched photo. "

        # ── IDENTITY LOCK (positive framing) ────────────────────────────
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
        "attractiveness that defines this individual must remain identical across all "
        "shader levels — the inherent aesthetic quality of the subject is constant; "
        "only the rendering style changes. "

        # ── COMPOSITION LOCK (positive framing) ─────────────────────────
        "The following composition parameters are fixed and must be reproduced exactly: "
        "a centered, frontal head-and-shoulders portrait with the subject looking directly "
        "at the camera; the exact head tilt, gaze direction, and neutral closed-mouth "
        "expression of the reference; the original camera framing, crop, distance, and "
        "aspect ratio; the original key-light direction, light angle, and shadow placement "
        "on the face — the light vector is locked, only its interaction with the new "
        "surface material may change according to the target shader; "
        "the clothing geometry, colour, and spatial arrangement from the reference; "
        "a solid, uniform, pure white background (#FFFFFF, fully opaque, "
        "no gradient, no vignette, no coloured cast, no variation) filling the entire "
        "area outside the subject. "

        # ── EXPOSURE ANCHOR ──────────────────────────────────────────────
        "The overall image exposure and brightness must match the reference photograph. "
        "The background reads as bright, clean white. The face and clothing are "
        "correctly exposed with the same tonal range as the original. "

        # ── VARIABLE ─────────────────────────────────────────────────────
        "The ONLY variable allowed to change is the surface shading model and material "
        "rendering style, as specified below. "
        "Target render style:\n\n"
    )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: HIGH
    # Goal: hyperreal AI-art / Virtual Influencer signature look.
    # Key fix: imperfections are KEPT but rendered as algorithm-traced
    # micro-detail — resolves the prior contradiction between "preserve marks"
    # and "denoised skin".
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
    # Goal: AAA real-time game character (GoW 4 / CoD MW aesthetic).
    # Key fix: removed the term "Matte-Plastic" which was causing the
    # plastic-sheen inconsistency. Replaced with PBR language that describes
    # the specific visual outcome (opaque, diffuse-dominant, slightly waxy)
    # without triggering a literal plastic-material interpretation.
    # Also removed the rim-lighting instruction to avoid overriding the locked
    # light vector.
    # ─────────────────────────────────────────────────────────────────────
    if level == "medium_high":
        return (
            locked_context +
            "RENDER STYLE — MEDIUM-HIGH: A high-poly real-time 3D character asset for "
            "a AAA game engine, in the visual aesthetic of Gears of War 4 or "
            "Call of Duty Modern Warfare (2019). "
            "The skin surface is rendered using a PBR material with a strongly "
            "diffuse-dominant albedo: subsurface scattering is present but clamped "
            "and hard-edged, producing an opaque, dense, slightly waxy appearance "
            "that clearly rejects biological photorealism. "
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
            "the light direction matches the reference, but shadows are hard-edged and "
            "computed, not naturally diffused. "
            "The final image is unmistakably a high-poly, next-gen game character "
            "render — detailed but clearly synthetic, with the visual density of a "
            "AAA cutscene asset. "
            "Exposure and image brightness match the reference. "
            "The background is solid, uniform white (#FFFFFF)."
        )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: MEDIUM
    # Goal: mid-2000s cinematic CGI / uncanny valley (Polar Express aesthetic).
    # Key fix: the prior prompt created two competing interpretations — a
    # "flat diffuse texture" (which some runs rendered as matte+dull) vs the
    # "waxy silicone" description (which other runs rendered as shiny).
    # Unified into a single unambiguous description: soft candle-wax diffuse,
    # specifically NOT shiny. Also removed "lacks realistic bounce-light"
    # which was causing the exposure drop.
    # ─────────────────────────────────────────────────────────────────────
    if level == "medium":
        return (
            locked_context +
            "RENDER STYLE — MEDIUM: Cinematic CGI from the mid-2000s motion-capture "
            "era, in the visual aesthetic of The Polar Express (2004) or Final Fantasy: "
            "The Spirits Within. "
            "The skin is rendered as a continuous, slightly-too-smooth 3D mesh surface: "
            "soft, diffuse, and waxy like polished candle wax or a dense silicone mould — "
            "with a flat, uniform diffuse albedo and minimal specular response (the surface "
            "does not shine or gleam; it is matte-waxy, not plastic-shiny). "
            "Freckles, moles, and skin marks are present as flat, painted-on albedo "
            "patches with no geometric relief — they sit on the surface like a decal "
            "rather than rising from it. "
            "The overall skin reads as one continuous poured surface with no visible "
            "pore structure or micro-normal variation. "
            "Lighting follows the locked reference direction and produces soft, slightly "
            "too-even shadows with gentle terminator edges — the characteristic "
            "low-frequency shading of early performance-capture cinema. "
            "Hair is rendered as a solid, slightly chunky volume with smooth, painted "
            "highlights — not individual strands, but a continuous sculpted shape. "
            "The overall image sits in the uncanny valley: clearly synthetic, "
            "clearly attempting human realism, clearly pre-HDR-era CGI. "
            "Image exposure is bright, correctly exposed, matching the reference. "
            "The background is solid, uniform white (#FFFFFF), fully bright."
        )

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL: MEDIUM_LOW
    # Goal: hand-painted indie 3D (Life is Strange aesthetic).
    # Relatively stable level — minor refinements for consistency.
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
    # Goal: early-2000s low-poly game asset (The Sims 2 aesthetic).
    # Relatively stable level — minor refinements for consistency.
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

    raise ValueError(f"Unsupported level: {level!r}. Valid values: high, medium_high, medium, medium_low, low")





#VERSION 3

"""
build_prompt_v6.1
─────────────────────────────────────────────────────────────────────────────
Changes vs v6.0
  SHARED locked_context:
    • Exposure/shadow anchor strengthened: now explicitly prohibits deepening,
      expanding, or intensifying shadow coverage beyond the reference.
      (Fixes the over-dark face + heavy shadow problem on all levels.)

  MEDIUM_HIGH:
    • Removed "shadows are hard-edged and computed, not naturally diffused" —
      this was the direct cause of the heavy rim-shadow on jaw/neck.
    • Replaced with: shadow intensity and spread must match the reference;
      only the edge quality (computed vs. organically diffused) may differ.

  MEDIUM:
    • Restored "The Polar Express (2004)" as the sole, strong visual anchor.
      (Multiple anchors in v6.0 created ambiguity → wrong aesthetic.)
    • Restored explicit "flat diffuse" language.
    • Added a level-specific brightness lock: flat-diffuse materials naturally
      read darker — the model must compensate to match reference exposure.
    • Removed "Final Fantasy: The Spirits Within" second reference.
─────────────────────────────────────────────────────────────────────────────
"""


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
            "a AAA game engine, in the visual aesthetic of Uncharted 4 (mantain the original lighting conditions and intensity). "
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