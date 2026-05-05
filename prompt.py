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