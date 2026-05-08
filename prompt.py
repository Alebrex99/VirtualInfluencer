
# EXAMPLE PROMPT 1
anthropomorphism_prompts = {
    "subject_id": "subject01",

    "reference_image": "input/subject01_reference.jpg",

    "aa_scale_context": (
        "CONTEXT: Anthropomorphic Style Appearance (AA) Research. "
        "Anthropomorphic Style Appearance (AA) refers to the degree of digital-synthetic "
        "effect of a generated rendering. The goal is to create a synthetic rendering of "
        "a virtual influencer that observers classify on the AA Scale. "
        "AA1: the rendered virtual influencer is Humanlike. "
        "AA2: the rendered virtual influencer is Lifelike. "
        "AA3: the rendered virtual influencer has a Humanlike appearance. "
        "AA4: the rendered virtual influencer has physical characteristics that resemble "
        "a real person but through a synthetic lens."
    ),

    "shared_prompt": (
        "TASK: High-fidelity digital asset reconstruction. Transform the provided "
        "photograph into a synthetic-digital rendering. "
        "Treat the subject in the reference image as a 3D digital mesh. "
        "Re-surface this mesh using a synthetic-digital rendering engine. "
        "Maintain the exact spatial coordinates of all facial features, anatomical "
        "proportions, asymmetries, and specific skin traits, including freckles, scars, "
        "and blemishes. Maintain the exact length, density, and spatial coordinates of "
        "all facial and body hair, including hair, beard, eyebrows, eyelashes, and fine "
        "peach fuzz. Do not use the original pixels. Re-render every surface, including "
        "skin, hair, and fabric, using digital shaders. "
        "Keep the original pose, lighting direction, lighting angle, shadow placement, "
        "environment, background, framing, clothing, and accessories. Do not add or "
        "remove accessories or clothing items. The goal is a consistent aesthetic "
        "quality across all five anthropomorphism levels."
    ),

    "shared_constraints": (
        "Preserve the same identity, frontal head-and-shoulders portrait, neutral "
        "expression, direct gaze, plain pure white background #FFFFFF, same crop, same "
        "approximate lighting direction, same shadow placement, same age appearance, "
        "same gender presentation, same ethnicity, same hairstyle, same clothing, and "
        "same accessories. Only manipulate perceived anthropomorphism and synthetic "
        "digital rendering style."
    ),

    "base_positive": (
        "frontal portrait, head and shoulders, looking directly at camera, neutral "
        "expression, mouth closed, eyes open, even soft frontal lighting, plain pure "
        "white background #FFFFFF, centered, symmetrical framing, same hairstyle as "
        "reference, same age, same gender presentation, same ethnicity, no accessories "
        "added, no accessories removed"
    ),

    "negative_prompt": (
        "different person, changed identity, smile, laughing, emotional expression, "
        "open mouth, profile view, three-quarter view, side glance, different age, "
        "child, elderly, different gender presentation, different ethnicity, different "
        "hairstyle, beard added, beard removed, glasses added, hat, jewelry added, "
        "background change, colored background, cinematic background, fantasy character, "
        "robot, cyborg, monster, animal-like features, mask, costume, horror, uncanny "
        "horror, extra limbs, distortion, asymmetry, asymmetrical eyes, deformed mouth, "
        "low quality, blurry"
    ),

    "levels": [
        {
            "level": 1,
            "label": "very_low_anthropomorphism_painterly_2d",
            "target_evaluation": "Below AA4",
            "prompt": (
                "LEVEL: VERY LOW. TARGET EVALUATION: Below AA4. "
                "Transform the reference subject into a high-end 2.5D painterly animated "
                "character, inspired by the Arcane animated series aesthetic. "
                "Translate the original anatomical identity into sharp, chiseled, and "
                "angular facial planes. Keep the original proportions accurate to the "
                "reference image, but make the surface structure highly stylized and "
                "graphic. Apply rich, textured 2D digital brushstrokes over the 3D forms. "
                "Skin, hair, and clothing must look like high-end digital concept art or "
                "an oil painting brought to life. Apply dramatic graphic-novel lighting, "
                "with harsh colorful rim lights and bold cel-shaded shadow blocks that "
                "emphasize angular geometry. The final image should look like a flat yet "
                "dynamically shaded 2.5D illustration, blending 3D structural volumes with "
                "2D painterly art. Preserve identity, frontal pose, neutral expression, "
                "direct gaze, white background, crop, clothing, and accessories."
            ),
            "leonardo": {
                "model": "flux_dev",
                "init_strength": 0.35,
                "character_reference_strength": "High",
                "guidance_scale": 7,
                "num_images": 4
            }
        },

        {
            "level": 2,
            "label": "low_anthropomorphism_handpainted_3d",
            "target_evaluation": "Below AA3",
            "prompt": (
                "LEVEL: LOW. TARGET EVALUATION: Below AA3. "
                "Reconstruct the reference subject as a stylized, slightly low-poly 3D "
                "game character, inspired by the Life is Strange 1 aesthetic. "
                "Strictly remove all PBR elements. Do not use normal maps, bump maps, "
                "realistic skin shaders, or physically based reflections. All skin, "
                "clothing, and facial details must use hand-painted albedo textures. "
                "Shadows, highlights, and skin tones must appear directly painted onto "
                "the 3D model, with visible digital brushstrokes. Simplify facial features "
                "into soft, slightly angular 3D geometry. Render hair as solid sculptural "
                "volumetric blocks with painted directional strokes. Do not render "
                "individual hair strands. The final image should look like a charming, "
                "stylized 3D model with soft pastel hand-painted texture work. Preserve "
                "identity, frontal pose, neutral expression, direct gaze, white background, "
                "crop, clothing, and accessories."
            ),
            "leonardo": {
                "model": "flux_dev",
                "init_strength": 0.45,
                "character_reference_strength": "High",
                "guidance_scale": 7,
                "num_images": 4
            }
        },

        {
            "level": 3,
            "label": "medium_anthropomorphism_uncanny_cgi",
            "target_evaluation": "AA3",
            "prompt": (
                "LEVEL: MEDIUM. TARGET EVALUATION: AA3. "
                "Render the reference subject as an early 2000s cinematic CGI character, "
                "inspired by The Polar Express aesthetic and the uncanny valley. "
                "The skin must look waxy, resembling a soft silicone mask. The face must "
                "appear as a single uniform 3D mesh, with a simple diffuse texture used to "
                "define details and imperfections. Use flat lighting with limited realistic "
                "bounce-light, creating a lifeless synthetic appearance. Eyes should be "
                "three-dimensional but slightly artificial and emotionally muted. Hair "
                "should be CGI-rendered but not fully natural. The result should clearly "
                "look like a mid-2000s computer-generated character, not a real human photo. "
                "Preserve identity, frontal pose, neutral expression, direct gaze, white "
                "background, crop, clothing, and accessories."
            ),
            "leonardo": {
                "model": "flux_dev",
                "init_strength": 0.40,
                "character_reference_strength": "High",
                "guidance_scale": 7,
                "num_images": 4
            },
            "rpm_optional": {
                "body_type": "halfbody",
                "render": {
                    "resolution": 1024,
                    "camera": "frontal_headshot",
                    "lighting": "neutral_3point",
                    "background": "#FFFFFF"
                }
            }
        },

        {
            "level": 4,
            "label": "high_anthropomorphism_premium_game_cgi",
            "target_evaluation": "AA2",
            "prompt": (
                "LEVEL: HIGH. TARGET EVALUATION: AA2. "
                "Render the reference subject as a high-end playable videogame 3D "
                "character, inspired by the Resident Evil Remake aesthetic. The image must "
                "look like a premium game-engine render, not a photographic portrait. "
                "The skin must look like a synthetic digital material, artificial and "
                "mathematically calculated, with hard-clamped subsurface scattering. "
                "Add controlled skin texture, realistic but clearly rendered facial "
                "geometry, and digitally calculated highlights. Hair, eyebrows, eyelashes, "
                "and facial hair must be rendered as distinct digital strands with "
                "engine-calculated highlights. Strictly maintain the original hair density "
                "and placement from the reference image. Eyes must feature baked reflections "
                "and a piercing digitally rendered iris, clearly generated by a rendering "
                "engine. The final image should look like a premium sculpted 3D character "
                "asset with solid digital surfaces and a rendered appearance. Preserve "
                "identity, frontal pose, neutral expression, direct gaze, white background, "
                "crop, clothing, and accessories."
            ),
            "midjourney": {
                "version": 6,
                "style": "raw",
                "ar": "1:1",
                "cw": 80,
                "num_images": 4
            },
            "leonardo_optional": {
                "model": "phoenix",
                "photo_real": False,
                "init_strength": 0.30,
                "character_reference_strength": "High",
                "guidance_scale": 7,
                "num_images": 4
            },
            "notes": (
                "This level was previously inconsistent. Two strategies can be tested: "
                "first, reduce Midjourney character weight to 80 so the reference preserves "
                "identity without overriding the CGI style; second, route through Leonardo "
                "Phoenix with photo_real set to False to preserve CGI hardness without "
                "photographic bleed-through."
            )
        },

        {
            "level": 5,
            "label": "very_high_anthropomorphism_polished_cgi",
            "target_evaluation": "AA1",
            "prompt": (
                "LEVEL: VERY HIGH. TARGET EVALUATION: AA1. "
                "Create an ultra-realistic polished CGI virtual influencer portrait with "
                "the AI-signature look. The image should appear almost human-realistic "
                "while still being a synthetic CGI-rendered human. Use highly realistic "
                "skin texture, visible digital pores, subtle imperfections, lifelike facial "
                "geometry, realistic hair strands, natural lips, and physically plausible "
                "lighting. Increase micro-contrast in the skin, brightness in the eyes, "
                "glassy eye reflections, and algorithmic edge sharpness. The skin should "
                "have a high-specular shine and polished digital surface quality, typical "
                "of a high-resolution AI-generated virtual influencer asset. Avoid making "
                "the image look like an ordinary unedited photograph. Preserve identity, "
                "frontal pose, neutral expression, direct gaze, white background, crop, "
                "clothing, and accessories."
            ),
            "leonardo": {
                "model": "phoenix",
                "preset_style": "CINEMATIC",
                "photo_real": True,
                "init_strength": 0.25,
                "character_reference_strength": "High",
                "guidance_scale": 7,
                "num_images": 4
            }
        }
    ]
}

def build_prompt(level: str) -> str:
    """
    Build prompt using the textual corpus copied from prompt.py.
    Maps local level names to the appropriate prompt text.
    """
    # Testi copiati direttamente da prompt.py
    aa_scale_context = (
        "CONTEXT: Anthropomorphic Style Appearance (AA) Research. "
        "Anthropomorphic Style Appearance (AA) refers to the degree of digital-synthetic "
        "effect of a generated rendering. The goal is to create a synthetic rendering of "
        "a virtual influencer that observers classify on the AA Scale. "
        "AA1: the rendered virtual influencer is Humanlike. "
        "AA2: the rendered virtual influencer is Lifelike. "
        "AA3: the rendered virtual influencer has a Humanlike appearance. "
        "AA4: the rendered virtual influencer has physical characteristics that resemble "
        "a real person but through a synthetic lens."
    )

    shared_prompt = (
        "TASK: High-fidelity digital asset reconstruction. Transform the provided "
        "photograph into a synthetic-digital rendering. "
        "Treat the subject in the reference image as a 3D digital mesh. "
        "Re-surface this mesh using a synthetic-digital rendering engine. "
        "Maintain the exact spatial coordinates of all facial features, anatomical "
        "proportions, asymmetries, and specific skin traits, including freckles, scars, "
        "and blemishes. Maintain the exact length, density, and spatial coordinates of "
        "all facial and body hair, including hair, beard, eyebrows, eyelashes, and fine "
        "peach fuzz. Do not use the original pixels. Re-render every surface, including "
        "skin, hair, and fabric, using digital shaders. "
        "Keep the original pose, lighting direction, lighting angle, shadow placement, "
        "environment, background, framing, clothing, and accessories. Do not add or "
        "remove accessories or clothing items. The goal is a consistent aesthetic "
        "quality across all five anthropomorphism levels."
    )

    shared_constraints = (
        "Preserve the same identity, frontal head-and-shoulders portrait, neutral "
        "expression, direct gaze, plain pure white background #FFFFFF, same crop, same "
        "approximate lighting direction, same shadow placement, same age appearance, "
        "same gender presentation, same ethnicity, same hairstyle, same clothing, and "
        "same accessories. Only manipulate perceived anthropomorphism and synthetic "
        "digital rendering style."
    )

    base_positive = (
        "frontal portrait, head and shoulders, looking directly at camera, neutral "
        "expression, mouth closed, eyes open, even soft frontal lighting, plain pure "
        "white background #FFFFFF, centered, symmetrical framing, same hairstyle as "
        "reference, same age, same gender presentation, same ethnicity, no accessories "
        "added, no accessories removed"
    )

    negative_prompt = (
        "different person, changed identity, smile, laughing, emotional expression, "
        "open mouth, profile view, three-quarter view, side glance, different age, "
        "child, elderly, different gender presentation, different ethnicity, different "
        "hairstyle, beard added, beard removed, glasses added, hat, jewelry added, "
        "background change, colored background, cinematic background, fantasy character, "
        "robot, cyborg, monster, animal-like features, mask, costume, horror, uncanny "
        "horror, extra limbs, distortion, asymmetry, asymmetrical eyes, deformed mouth, "
        "low quality, blurry"
    )

    level_prompts = {
        "low": (
            "LEVEL: VERY LOW. TARGET EVALUATION: Below AA4. "
            "Transform the reference subject into a high-end 2.5D painterly animated "
            "character, inspired by the Arcane animated series aesthetic. "
            "Translate the original anatomical identity into sharp, chiseled, and "
            "angular facial planes. Keep the original proportions accurate to the "
            "reference image, but make the surface structure highly stylized and "
            "graphic. Apply rich, textured 2D digital brushstrokes over the 3D forms. "
            "Skin, hair, and clothing must look like high-end digital concept art or "
            "an oil painting brought to life. Apply dramatic graphic-novel lighting, "
            "with harsh colorful rim lights and bold cel-shaded shadow blocks that "
            "emphasize angular geometry. The final image should look like a flat yet "
            "dynamically shaded 2.5D illustration, blending 3D structural volumes with "
            "2D painterly art. Preserve identity, frontal pose, neutral expression, "
            "direct gaze, white background, crop, clothing, and accessories."
        ),
        "medium_low": (
            "LEVEL: LOW. TARGET EVALUATION: Below AA3. "
            "Reconstruct the reference subject as a stylized, slightly low-poly 3D "
            "game character, inspired by the Life is Strange 1 aesthetic. "
            "Strictly remove all PBR elements. Do not use normal maps, bump maps, "
            "realistic skin shaders, or physically based reflections. All skin, "
            "clothing, and facial details must use hand-painted albedo textures. "
            "Shadows, highlights, and skin tones must appear directly painted onto "
            "the 3D model, with visible digital brushstrokes. Simplify facial features "
            "into soft, slightly angular 3D geometry. Render hair as solid sculptural "
            "volumetric blocks with painted directional strokes. Do not render "
            "individual hair strands. The final image should look like a charming, "
            "stylized 3D model with soft pastel hand-painted texture work. Preserve "
            "identity, frontal pose, neutral expression, direct gaze, white background, "
            "crop, clothing, and accessories."
        ),
        "medium": (
            "LEVEL: MEDIUM. TARGET EVALUATION: AA3. "
            "Render the reference subject as an early 2000s cinematic CGI character, "
            "inspired by The Polar Express aesthetic and the uncanny valley. "
            "The skin must look waxy, resembling a soft silicone mask. The face must "
            "appear as a single uniform 3D mesh, with a simple diffuse texture used to "
            "define details and imperfections. Use flat lighting with limited realistic "
            "bounce-light, creating a lifeless synthetic appearance. Eyes should be "
            "three-dimensional but slightly artificial and emotionally muted. Hair "
            "should be CGI-rendered but not fully natural. The result should clearly "
            "look like a mid-2000s computer-generated character, not a real human photo. "
            "Preserve identity, frontal pose, neutral expression, direct gaze, white "
            "background, crop, clothing, and accessories."
        ),
        "medium_high": (
            "LEVEL: HIGH. TARGET EVALUATION: AA2. "
            "Render the reference subject as a high-end playable videogame 3D "
            "character, inspired by the Resident Evil Remake aesthetic. The image must "
            "look like a premium game-engine render, not a photographic portrait. "
            "The skin must look like a synthetic digital material, artificial and "
            "mathematically calculated, with hard-clamped subsurface scattering. "
            "Add controlled skin texture, realistic but clearly rendered facial "
            "geometry, and digitally calculated highlights. Hair, eyebrows, eyelashes, "
            "and facial hair must be rendered as distinct digital strands with "
            "engine-calculated highlights. Strictly maintain the original hair density "
            "and placement from the reference image. Eyes must feature baked reflections "
            "and a piercing digitally rendered iris, clearly generated by a rendering "
            "engine. The final image should look like a premium sculpted 3D character "
            "asset with solid digital surfaces and a rendered appearance. Preserve "
            "identity, frontal pose, neutral expression, direct gaze, white background, "
            "crop, clothing, and accessories."
        ),
        "high": (
            "LEVEL: VERY HIGH. TARGET EVALUATION: AA1. "
            "Create an ultra-realistic polished CGI virtual influencer portrait with "
            "the AI-signature look. The image should appear almost human-realistic "
            "while still being a synthetic CGI-rendered human. Use highly realistic "
            "skin texture, visible digital pores, subtle imperfections, lifelike facial "
            "geometry, realistic hair strands, natural lips, and physically plausible "
            "lighting. Increase micro-contrast in the skin, brightness in the eyes, "
            "glassy eye reflections, and algorithmic edge sharpness. The skin should "
            "have a high-specular shine and polished digital surface quality, typical "
            "of a high-resolution AI-generated virtual influencer asset. Avoid making "
            "the image look like an ordinary unedited photograph. Preserve identity, "
            "frontal pose, neutral expression, direct gaze, white background, crop, "
            "clothing, and accessories."
        ),
    }

    if level not in level_prompts:
        raise ValueError(f"Unsupported level: {level}")

    return (
        f"{aa_scale_context}\n\n"
        f"{shared_prompt}\n\n"
        f"{shared_constraints}\n\n"
        f"POSITIVE PROMPT:\n{base_positive}\n\n"
        f"NEGATIVE PROMPT:\n{negative_prompt}\n\n"
        f"{level_prompts[level]}"
    )


# EXAMPLE PROMPT 2
def build_prompt(level: str) -> str:

    aa_scale_context = (
        "CONTEXT: Anthropomorphic Style Appearance (AA) Research. "
        "'Anthropomorphic Style Appearance' (AA) refers to the degree of digital-synthetic effect of a generated rendering. "
        "Goal: Create a synthetic rendering of a virtual influencer that observers classify on the AA Scale. "
        "AA1: the rendered virtual influencer is Humanlike. "
        "AA2: the rendered virtual influencer is Lifelike. "
        "AA3: the rendered virtual influencer has a Humanlike appearance. "
        "AA4: the rendered virtual influencer has Physical characteristics that resemble a real person but through a synthetic lens."
    )

    shared_prompt = (
        f"{aa_scale_context}\n"
        "TASK: High-fidelity Digital Asset Reconstruction. "
        "Transform the provided photograph (Base Image) into a synthetic-digital rendering. "

        "INPUT: 1. IMAGE 1 (Base) is the geometric identity. Use this for Identity, Geometry, and COMPOSITION. "
        "2. IMAGE 2 (Style Reference - Optional) is the shader source: Use ONLY as a rendering tool for textures, "
        "the absolute source for the rendering engine, texture and shader/light quality. Do NOT adopt the identity of Image 2. "

        "INSTRUCTION: Treat the subject in IMAGE 1 as a 3D digital mesh. "
        "You MUST re-surface this mesh using a synthetic-digital rendering engine. "

        "IDENTITY ANCHOR: Maintain the exact spatial coordinates of all facial features, anatomical proportions, "
        "asymmetries, and specific skin traits (freckles, scars, blemishes). "
        "Maintain the exact length, density, and spatial coordinates of all facial and body hair (including hair, beard, eyebrows, eyelashes, and fine peach fuzz). "
        "However, re-render the original pixels with digital shaders."

        "SURFACE PROTOCOL: Re-render every surface (skin, hair, fabric) "
        "using digital shaders. The final result must be a synthetic-digital reconstruction."

        "COMPOSITION: "
        "Keep the original pose, lighting directions and angles, shadow placement, environment, background and framing. "
        "Keep the original clothing and accessories, including their exact geometry and spatial arrangement. "
        "Keep the original accessories or clothing items. "
        "The goal is a consistent aesthetic quality across all 5 digital levels. "
    )

    # ── Level 1 — High (AI-Signature Look) ─────────────────────────────────
    #
    # PROBLEMA: bagliori di luce errati sul viso.
    # CAUSA: "Increase the brightness", "glassy reflection", "high-specular shine"
    #   sono istruzioni additive di luce — il modello aggiunge highlight casuali.
    # FIX: L'AI-look non è luce aggiuntiva. È ipernítidezza della superficie e
    #   saturazione artificiale dei dettagli. La sorgente luminosa rimane quella
    #   dell'originale — cambia solo la qualità sintetica della superficie.
    #   La speculare è descritta come "mathematically uniform" (non "bright"),
    #   e i riflessi degli occhi come "perfectly spherical" (non "glassy/bright").
    #   Rimossi tutti i termini additivi: "Increase", "glassy", "high-specular shine".
    #
    if level == "high":
        return (
            shared_prompt
            + "LEVEL: HIGH. TARGET EVALUATION: AA1. "
            + "STYLE: 'The AI-Signature Look' — Hyper-detailed synthetic CGI portrait. "

            + "SURFACE QUALITY: Re-render the skin with a mathematically uniform, "
            + "high-frequency micro-detail layer. Every pore, fine line, and skin texture "
            + "must be rendered with algorithmic precision and extreme sharpness, "
            + "as if sampled from a 16K digital texture map. "
            + "The result must feel over-processed and artificially perfect, "
            + "not like a photograph but like a raw AI-generated asset. "

            + "LIGHTING: Preserve the exact lighting direction, intensity, and shadow placement "
            + "from IMAGE 1. Do not add new light sources or increase overall brightness. "
            + "Apply only a mathematically uniform specular response across the skin surface: "
            + "every micro-facet must reflect with the same artificial precision, "
            + "eliminating the natural randomness of real human skin reflectance. "

            + "EYES: Render the iris with a perfectly symmetrical, algorithmically generated texture. "
            + "Add a single, geometrically perfect specular highlight positioned by the engine. "
            + "The cornea must look like a precisely machined optical surface. "

            + "OVERALL EFFECT: A hyper-sharp, synthetically perfect portrait — "
            + "recognizable as AI-generated by its uncanny surface precision and "
            + "the total absence of photographic imperfection, not by added brightness or glare."
        )

    # ── Level 2 — Medium-High (High-End Video Game / RE Engine) ────────────
    #
    # PROBLEMA: barba che cresce in zone non presenti nell'originale.
    # CAUSA: "distinct digital strands with engine-calculated highlights" lascia
    #   il modello libero di "interpretare" la geometria dei capelli.
    # FIX: Anchor geometrico esplicito e positivo — il modello deve mappare
    #   1:1 la geometria visibile in IMAGE 1, non generare capelli autonomamente.
    #   Rimossa ogni libertà interpretativa sulla densità dei capelli.
    #
    if level == "medium_high":
        return (
            shared_prompt
            + "LEVEL: MEDIUM-HIGH. TARGET EVALUATION: AA2. "
            + "STYLE: High-end 3D Character Game Asset (Resident Evil Remake / RE Engine aesthetic). "
            + "INSTRUCTION: Render a premium playable videogame 3D character. "
            + "The image must look like a game engine render, rejecting any photographic realism. "

            + "SKIN MATERIAL: Re-surface the skin with a synthetic PBR material. "
            + "Use crisp Normal Maps to render only the micro-geometry already present in IMAGE 1 "
            + "(pores, fine lines, asymmetries). "
            + "Apply hard-clamped Subsurface Scattering: the skin must feel like a dense, "
            + "solid synthetic material — opaque and dry, with no warm biological translucency. "
            + "The specular response must be controlled and localized to the T-zone only "
            + "(forehead and nose bridge), appearing as a dry geometric sheen, never as moisture or sweat. "

            + "HAIR GEOMETRY LOCK: Perform a strict 1-to-1 geometric remap of all hair present in IMAGE 1. "
            + "Render exclusively the hair that is geometrically visible in IMAGE 1, "
            + "mapped to its exact position, density, boundary, and color. "
            + "Render each hair element (scalp hair, eyebrows, eyelashes, beard if present) "
            + "as Alpha Hair Cards with anisotropic specular highlights along the strand direction. "
            + "Generating hair in any region where IMAGE 1 shows bare skin is strictly forbidden. "

            + "EYES: Baked reflections with a high-definition, mathematically generated iris texture "
            + "and a sharp limbus ring. "

            + "OVERALL EFFECT: A premium sculpted 3D character asset — "
            + "sharp, dry, and unmistakably digital, with solid synthetic surfaces and engine-precise lighting."
        )

    # ── Level 3 — Medium (Uncanny Valley / Early CGI) ──────────────────────
    #
    # PROBLEMA: proporzioni cambiate, identità diversa.
    # CAUSA: "single, uniform 3D mesh" + "simple diffuse texture" sono istruzioni
    #   sul materiale troppo astratte — senza un anchor di identità esplicito
    #   dentro questo livello, il modello rifà il viso liberamente.
    # FIX: Aggiunto IDENTITY LOCK esplicito dentro il livello. Le istruzioni
    #   sul materiale waxy ora specificano che agiscono sulla SUPERFICIE,
    #   non sulla geometria — la geometria è bloccata a IMAGE 1.
    #
    if level == "medium":
        return (
            shared_prompt
            + "LEVEL: MEDIUM. TARGET EVALUATION: AA3. "
            + "STYLE: Early 2000s Cinematic CGI (The Polar Express aesthetic / Uncanny Valley). "
            + "INSTRUCTION: Render a mid-2000s 3D character. "

            + "IDENTITY LOCK: The 3D mesh geometry — all facial proportions, feature positions, "
            + "asymmetries, and anatomical measurements — must be an exact copy of IMAGE 1. "
            + "The mesh must not be resculpted, idealized, or altered in any spatial dimension. "
            + "Only the surface material changes. "

            + "SURFACE MATERIAL: Apply a waxy, uniform diffuse shader to the skin surface. "
            + "The skin must resemble soft silicone or a theatrical mask — "
            + "a single-layer material with no subsurface depth or biological warmth. "
            + "Remove all high-frequency micro-detail (no visible pores or fine lines). "
            + "Skin tones must be uniform and slightly desaturated, as if lit by a flat CG light rig. "

            + "LIGHTING: Flat and directionless, lacking realistic bounce light or ambient occlusion depth. "
            + "Shadows are present but soft and unconvincing, creating a lifeless, "
            + "uncanny synthetic appearance. "

            + "OVERALL EFFECT: A recognizably human face rendered as an unsettling CG approximation — "
            + "the geometry is correct but the surface material makes it feel artificial and inert."
        )

    # ── Level 4 — Medium-Low (Stylized Hand-Painted Game Asset) ────────────
    # PERFECT — nessuna modifica
    if level == "medium_low":
        return (
            shared_prompt
            + "LEVEL: MEDIUM-LOW. TARGET EVALUATION: Below AA3. "
            + "STYLE: 2015 Indie Narrative Game Asset (Life is Strange 1 aesthetic). "
            + "INSTRUCTION: Reconstruct the subject as a stylized, slightly low-poly 3D game character. "

            + "HAND-PAINTED TEXTURES: Strictly remove all PBR elements (no Normal or Bump maps). "
            + "All skin, clothing, and details must use Hand-Painted Albedo Textures. "
            + "Shadows, highlights, and skin tones must appear directly painted onto the 3D model with visible digital brushstrokes. "

            + "GEOMETRY & HAIR: Simplify facial features into soft, slightly angular 3D geometry. "
            + "Hair must be rendered as solid, sculptural volumetric blocks with painted directional strokes. "
            + "Do not render individual hair strands. "

            + "OVERALL EFFECT: A charming, stylized 3D model characterized by its hand-painted, soft pastel texture work."
        )

    # ── Level 5 — Low (2.5D Painterly Illustration) ─────────────────────────
    #
    # PROBLEMA: IMAGE_OTHER safety block.
    # CAUSA: "Arcane animated series aesthetic" cita una IP protetta da copyright.
    #   Il modello riconosce il riferimento e blocca la generazione.
    # FIX: Rimosso qualsiasi riferimento a IP, serie, film, o studio specifico.
    #   Lo stile è ora descritto puramente in termini tecnici di rendering:
    #   piani facciali angolari, brushstroke digitali, rim light colorati,
    #   shadow blocks cel-shaded — stessa estetica, zero riferimenti IP.
    #
    if level == "low":
        return (
            shared_prompt
            + "LEVEL: LOW. TARGET EVALUATION: Below AA4. "
            + "STYLE: 2.5D Painterly Digital Illustration with angular graphic stylization. "
            + "INSTRUCTION: Transform the subject into a stylized 2.5D illustrated character. "

            + "GEOMETRY & PLANES: Translate the subject's facial anatomy into sharp, "
            + "chiseled, and angular surface planes. "
            + "Proportions must remain accurate to IMAGE 1, "
            + "but every surface must be broken into graphic, stylized facets. "

            + "PAINTERLY TEXTURES: Apply rich, layered 2D digital brushstrokes over the 3D volumes. "
            + "Skin, hair, and clothing must have the texture of high-end digital concept art — "
            + "visible brushwork, painterly color blending, and illustrative edge definition. "

            + "LIGHTING: Dramatic graphic-novel style. "
            + "Use hard-edged colored rim lights and bold cel-shaded shadow blocks "
            + "that emphasize the angular geometry. "
            + "No soft photographic gradients — light and shadow must feel drawn, not rendered. "

            + "OVERALL EFFECT: A high-quality 2.5D illustration that blends structural 3D volumes "
            + "with 2D painterly art — graphic, angular, and stylized, "
            + "with no reference to any specific animated franchise or IP."
        )

    raise ValueError(f"Unsupported level: {level}")








