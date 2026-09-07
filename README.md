# VirtualInfluencer — Stimuli Generation Pipelines

This repository contains the computational pipelines used to generate all experimental stimuli for the research on **synthetic facial rendering and perceived anthropomorphism**. Two datasets were used: the **Face Research Lab London Set** and the **Chicago Face Dataset (CFD)**. Each dataset has its own dedicated pipeline scripts, sharing a common configuration file (`constants.py`) and API key file (`.env`).

> **Status.** The **London Set is the production dataset**: it is the only one carried through to a complete stimulus set. The **CFD branch was piloted and abandoned**; its partial output is archived under `Output_images/CFD_PROBLEM/`. See [Section 2](#section-2--chicago-face-dataset-cfd).

The generation process is organised in two sequential stages, separated by a manual curation step:

1. **First Pipeline** — renders each original face photograph into three levels of CGI anthropomorphism.
2. **Manual curation** — visual inspection and colorimetric correction of the renders; selection and gender-splitting of the subset that feeds the second pipeline.
3. **Second Pipeline** — applies a beauty-enhancement pass to the selected renders, then *mediumizes* the enhanced image.

> **Terminology — *mediumization*.** Throughout this document, **mediumizing** an image means passing an already beauty-enhanced render through the Medium-anthropomorphism prompt (`ENHANCED_MEDIUM_PROMPT1`), so that it is re-shaded into the *Polar Express* aesthetic while retaining the beauty optimization it received in the previous step. An image that has undergone this pass is described as **mediumized** and carries a terminal `M` in its filename suffix (`_HEM`, `_MHEM`). The term is native to the codebase: `process_medium_style()` logs `Mediumizing [...]` at each such call.

The two pipelines are **not** directly chained: the second pipeline reads from a folder that is populated by hand (step 2), not from the first pipeline's output folder.

Most API calls use **Google Gemini 3 Pro Image Preview** (`gemini-3-pro-image-preview`, set in `.env`); four specific stimuli were generated with **Gemini 3.1 Flash Image Preview** because it produced a better result in those cases (see *Models used* below). Every output is saved at the standardized input resolution (1024 × 1024 for London, 1264 × 848 for CFD); if the model returns a different size it is resized back with LANCZOS before saving. Both pipelines are idempotent: if an output file already exists, it is skipped without an API call.

---

## Google API Infrastructure

### SDK
All model calls are made through the **Google AI Python SDK** (`google-genai`). The relevant entry point is `genai.Client`, and image generation is configured via [`GenerateContentConfig.image_config`](https://googleapis.github.io/python-genai/genai.html#genai.types.GenerateContentConfig.image_config) (`types.ImageConfig` with `aspect_ratio` and `image_size` fields). The SDK is installed as `google-genai` and imported as `from google import genai`.

### API key tiers
Two separate platforms were used to obtain API keys across the research lifecycle:

| Platform | Purpose | Auth method |
|---|---|---|
| **Google AI Studio** | Early development and debugging — fast key generation, no billing setup required | API key in `.env` (`GEMINI_API_KEY`) |
| **Gemini Enterprise Agent Platform** ([docs](https://docs.cloud.google.com/gemini-enterprise-agent-platform/)) | Final production runs — leveraging Vertex AI Express mode | API key in `.env` with `vertexai=True` client flag |

The client is always initialised as:
```python
client = genai.Client(vertexai=True, api_key=api_key)
```
`vertexai=True` routes the call through the Vertex AI backend regardless of which key is active, which is required for the Gemini Enterprise Agent Platform keys.

### Models used

| Model ID | Role |
|---|---|
| `gemini-3-pro-image-preview` | Production model for all pipeline calls. Read from `.env` as `GEMINI_MODEL`. |
| `gemini-3.1-flash-image-preview` | Used for four London stimuli where it produced a better result: `FT1_HEM`, `MC1_HE`, `MC1_HEM`, `FC3_MHEM` (all second-pipeline outputs). |
| `gemini-2.5-flash-image-preview` | **Fallback only.** `DEFAULT_MODEL` in `constants.py`, used by `load_config()` if `GEMINI_MODEL` is absent from `.env`. Never active in production — but note that a missing `.env` entry will silently downgrade the model instead of raising. |

The model switch for the four exception stimuli is **not encoded in the scripts**. It was performed by editing `GEMINI_MODEL` in `.env` and re-running with the previous outputs deleted (the skip-if-exists check would otherwise have preserved them).

---

## Shared Configuration

### `constants.py`
Central configuration imported (`from constants import *`) by every pipeline script. Active settings at time of writing (London dataset):

| Constant | Value | Dataset-specific? | Purpose |
|---|---|---|---|
| `EXPERIMENT_INPUT_DIR` | `Images/LondonDataset/ExperimentalDataset/` | **yes** — CFD variant commented out | Source images for first pipeline |
| `TEST_INPUT_DIR` | `Images/LondonDataset/MinMaleMaxFemale/` | **yes** — CFD variant commented out | Two-subject smoke-test folder |
| `OUTPUT_DIR` | `Output_images/` | no — shared | First pipeline outputs |
| `STANDARDIZED_IMAGES_DIR` | `Images/StandardizedImages/` | no — shared | Resized/cropped input copies |
| `INPUT_ENHANCED_FEMALE_DIR` | `Output_images/ReadyToEnhance/Female/` | no — shared | Second pipeline female inputs |
| `INPUT_ENHANCED_MALE_DIR` | `Output_images/ReadyToEnhance/Male/` | no — shared | Second pipeline male inputs |
| `OUTPUT_ENHANCED_DIR` | `Output_images/Enhanced/` | no — shared | Second pipeline outputs |
| `INPUT_RESOLUTION` | `compute_gemini_1k_for_input(1350, 1350)` → **(1024, 1024)** | **yes** — must be edited by hand | Target standardized size |
| `MAX_IMAGES` | `16` | no | Max images per full run (first pipeline only) |
| `MAX_RETRIES` | `3` | no | **Total** attempts per call (initial + 2 retries) |
| `RETRY_BASE_DELAY_SECONDS` | `1.5` | no | Back-off base, doubling each attempt → waits of 1.5 s, 3.0 s |
| `ALLOWED_EXTENSIONS` | `{".png", ".jpg", ".jpeg"}` | no | Accepted input formats |
| `LEVELS_3` | `["high", "medium_high", "medium"]` | no | Anthropomorphism levels actually generated |
| `LEVELS_3_SIGLE` | `{"high": "H", "medium_high": "MH", "medium": "M"}` | no | Output filename suffixes |
| `ENHANCED_LEVELS_SIGLE` | `{"high": "H", "medium_high": "MH"}` | no | Levels eligible for second pipeline |

> **`LEVELS` vs `LEVELS_3`.** `constants.py` also defines `LEVELS = ["high", "medium_high", "medium", "medium_low", "low"]`, a five-level scale retained from earlier script versions. **No pipeline iterates it.** Both `main-generating-v5London.py` and `main-generating-v5CFD.py` loop over `LEVELS_3`, so `medium_low` and `low` were never produced for either dataset. Prompt builders for those two levels still exist in the scripts but are unreachable.

> **Switching datasets is not fully automatic.** Only `INPUT_DIR`, `TEST_INPUT_DIR` and `EXPERIMENT_INPUT_DIR` have commented-out CFD variants. `OUTPUT_DIR`, `STANDARDIZED_IMAGES_DIR` and the three enhancement directories are **shared across both datasets**, so a CFD run and a London run write to the same folders. Switching from one dataset to the other therefore requires: (a) commenting the path block in `constants.py`, (b) editing `INPUT_RESOLUTION` by hand, and (c) **manually archiving the previous dataset's outputs**, or they will be mixed together — or skipped, since the skip-if-exists check matches on filename only and both datasets use the same `FC1`…`MT4` subject codes. This is why the CFD run is archived under `Output_images/CFD_PROBLEM/` and `Images/StandardizedImages/CFD/`.

### `.env`
Holds the Gemini API key and model name:
```
GEMINI_MODEL = gemini-3-pro-image-preview
GEMINI_API_KEY = <key>
```

### Output naming convention
Every generated filename encodes the full transformation chain applied to the source:

| Suffix | Meaning | Example |
|---|---|---|
| `_H` | High anthropomorphism (first pipeline) | `FC2_H.png` |
| `_MH` | Medium-high anthropomorphism (first pipeline) | `FC2_MH.png` |
| `_M` | Medium anthropomorphism (first pipeline) | `FC2_M.png` |
| `_HE` | High + beauty enhancement (second pipeline, step 1) | `FC2_HE.png` |
| `_MHE` | Medium-high + beauty enhancement (second pipeline, step 1) | `FC2_MHE.png` |
| `_HEM` | High + enhanced + **mediumized** (second pipeline, step 2) | `FC2_HEM.png` |
| `_MHEM` | Medium-high + enhanced + **mediumized** (second pipeline, step 2) | `FC2_MHEM.png` |

Subject codes: the first letter encodes gender (`F`/`M`), the second the attractiveness group (`C` = low, `T` = high). Sixteen subjects, four per cell: `FC1`–`FC4`, `FT1`–`FT4`, `MC1`–`MC4`, `MT1`–`MT4`.

---

## Section 1 — Face Research Lab London Set

**Source images:** 1350 × 1350 px, 1:1 aspect ratio, RGB.
**Background:** mid-grey studio backdrop. It is **not flat**: measured on the standardized `FC1`, it reaches ≈ RGB (201, 205, 206) at the mid-left edge and (204, 208, 209) at the mid-right edge, falling to ≈ (161, 167, 167) in the top corners — a pronounced vignette. It also carries a slight cool cast: averaged over the 16 subjects the top-centre patch is (196.4, 200.4, 199.7), i.e. green and blue exceed red by ≈ 3–4 levels. The `#C8C8C8` value quoted in the prompts is a nominal descriptor of the brightest region only; the operative instruction in the prompt is the adjacent *"identical to the base image"* clause.
**Scripts:** `main-generating-v5London.py`, `second-generating-female-London.py`, `second-generating-male-London.py`.
**Standardized / saved resolution:** 1024 × 1024 px (Gemini 1:1 native 1K), obtained from the source by `ImageOps.fit()`, which crops to the target aspect ratio *and* downscales in a single Lanczos pass.

### 1.1 First Pipeline — `main-generating-v5London.py`

**Purpose:** Converts each original London photograph into three CGI-rendered versions at different anthropomorphism levels (High, Medium-High, Medium).

#### Step-by-step process

**1. Input scanning**
`scan_input_images(EXPERIMENT_INPUT_DIR, MAX_IMAGES)` iterates `Images/LondonDataset/ExperimentalDataset/` alphabetically and collects up to `MAX_IMAGES = 16` valid image files (`.png`, `.jpg`, `.jpeg`). Sub-directories are skipped (`item.is_file()`), so the `ExperimentalDataset_origin/` archive — which holds the same 16 photographs under their original London filenames — is not processed. The folder contains exactly 16 selected subjects, four per group.

**2. Standardization**
For each input image, `standardize_input_image(image_path, INPUT_RESOLUTION)` is called:
- If the image already matches the target resolution, it is returned unchanged.
- Otherwise `PIL.ImageOps.fit()` crops the image to the target aspect ratio with centred framing (`centering=(0.5, 0.5)`) and resamples it to the target resolution with LANCZOS, saving the result as `Images/StandardizedImages/{stem}.png`.

The standardized image is the actual input sent to the API. Because London images are exactly 1350 × 1350 while `INPUT_RESOLUTION = (1024, 1024)`, every image is cropped-and-downscaled and archived. The aspect ratio label passed to the API is `"1:1"` (from `get_supported_aspect_ratio(1024, 1024)`).

**Why standardize at all.** The purpose of this step is to fix a **single common resolution for the whole experiment** — the standardized originals and every generated variant alike. Without it, the originals would remain at 1350 × 1350 while the model returned 1024 × 1024, so the stimulus set would mix two sizes and any comparison involving the originals would carry a resolution difference confounded with the manipulation. Verified on disk: the 16 standardized originals, the 48 first-pipeline outputs and the 64 second-pipeline outputs are **all 1024 × 1024 — 128 files, one single size across the entire set**.

That common resolution is the constant `INPUT_RESOLUTION`, and its value is not arbitrary: `compute_gemini_1k_for_input(1350, 1350)` returns **1024 × 1024**, which is the size the model itself produces natively for a 1:1 request (`GEMINI_1K_OUTPUTS["1:1"]`).

Because `INPUT_RESOLUTION` is the model's own native output size, the generated image comes back already at 1024 × 1024 and the resolution check at step 7 has nothing to change. This step is therefore the only point at which the source photograph is resampled.

**3. Prompt construction**
`build_enhanced_prompt(level)` builds the instruction text for the requested anthropomorphism level. All levels share a common `locked_context` preamble that instructs the model to:
- Treat the subject as a 3D mesh and re-surface it with a synthetic rendering engine, using the input solely as a geometric and photometric reference.
- Preserve identity, skin marks, hair, accessories, pose, framing, lighting, shadow geometry, exposure value, white balance and the neutral grey background — stated as four explicit *locks* (identity, composition, photometric, background).
- Change nothing but the surface shader.

> **Why the prompt is framed as 3D-asset production.** The preamble deliberately casts the task as re-surfacing a synthetic 3D character asset rather than as editing a photograph. Requests phrased as a direct modification of a photograph of a real person are liable to be refused by the model's content-safety layer, which returns a moderation signal instead of an image — `prompt_feedback` at the prompt level, or a `finish_reason` such as `SAFETY` / `IMAGE_SAFETY` on the candidate. The 3D-asset framing describes the intended output accurately (the stimuli *are* synthetic renders) while avoiding the formulation that triggers refusal. `generate_with_retry()` still inspects both signals on every response and skips a blocked generation cleanly instead of crashing the run.

The level-specific section then specifies the target rendering style:

| Level | Rendering style description |
|---|---|
| `high` | Hyperreal generative-AI / Midjourney-v5 look: ultra-sharp algorithmically over-traced micro-relief, synthetic sheen, unnaturally even local contrast, glassy over-specular eyes, over-sharpened hair and lip edges. |
| `medium_high` | AAA real-time game character (*Uncharted 4* skin aesthetics): synthetic PBR matte-plastic skin, diffuse-dominant albedo and normal maps, hard-clamped subsurface scattering, game-engine particle-system hair with baked specular highlights, static pre-rendered eye reflections, directional rim lighting. |
| `medium` | Early-2000s cinematic CGI / uncanny valley (*The Polar Express*, 2004): waxy candle-wax skin, one continuous slightly-too-smooth mesh, flat diffuse pass making imperfections read as painted on, old-game-engine hair particles, flat lighting with no bounce and slightly-too-soft shadows. |

**4. Style reference images**
`get_style_reference_image(level)` checks `Images/StyleRefImages/` for an optional second image whose stem is **exactly** `reference_{level}` — i.e. `reference_high`, `reference_medium_high`, `reference_medium` — with a `.png`, `.jpg` or `.jpeg` extension.

The folder does contain ten candidate files (`referenceH.jpg`, `referenceH2.png`, `referenceL.jpeg`, `referenceM.jpeg`, `referenceMH.avif`, `referenceMH.png`, `referenceMH2.jpg`, `referenceMH2.png`, `referenceMH3.png`, `referenzeML.jpg`), but **none of them matches the required naming pattern**, so the function returns `None` for every level and each request carries the standardized input image alone. Style transfer is therefore driven entirely by the textual prompt. This is the intended production condition — but note the mechanism is a naming mismatch, not an empty folder: renaming a file to `reference_high.png` would silently activate a second image in the API call.

**5. Skip-if-exists check**
Before each API call, the pipeline checks whether `Output_images/{stem}_{SIGLE}.png` already exists. If it does, the level is skipped. This makes every run resumable after interruption and prevents redundant billing.

**6. API call**
`generate_with_retry(client, model, standardized_image_path, prompt, "1:1")` calls:
```python
client.models.generate_content(
    model="gemini-3-pro-image-preview",   # gemini-3.1-flash-image-preview for the 4 exception images
    contents=[prompt, input_pil_image],
    config=GenerateContentConfig(
        response_modalities=[Modality.TEXT, Modality.IMAGE],
        image_config=ImageConfig(
            aspect_ratio="1:1",
            image_size="2K"               # only for images affected by graininess — see note below
        )
    )
)
```
The order of `contents` is significant: `[prompt, identity image, optional style image]`.

The generated image comes back as an inline binary payload — the raw PNG/JPEG bytes of `part.inline_data.data` — not as a decoded image object, so `extract_pil_image()` walks both possible response layouts (`response.parts` and `response.candidates[*].content.parts[*]`) and decodes the first inline payload it finds with PIL.

Retries: `for attempt in range(1, MAX_RETRIES + 1)` gives **3 attempts in total** — the initial call plus two retries — with exponential back-off (1.5 s after the first failure, 3.0 s after the second; no sleep after the final attempt).

Moderation is handled separately from failure: `prompt_feedback` is logged when present, and a `finish_reason` matching a safety or image-level block makes `generate_with_retry()` return without an image. The caller's `except Exception` handler then catches the resulting condition and reports the failure for that level, so a blocked stimulus is simply not produced and the run continues. Note this means a block surfaces as two log lines — the explicit `Blocked — finish reason: …` from inside the retry wrapper, followed by a less informative `Failed for … at level …` from the caller.

> **Note on `image_size="2K"`.** In production this parameter was used **only for the images that came back grainy** from the model's post-generation sharpening; those were regenerated at 2K and downscaled to 1024 × 1024 at save time. Every other image was generated at the model's native 1K. The repository history is consistent with this: the parameter appears only in the final commit, `266645a` *"Final Generation: added image_size = '2K'"* (2026-05-22), after the bulk of the set had been produced (`efc1f5a`, *"Finish generation (London Dataset)"*, 2026-05-20), and it is **absent from all three CFD scripts**.
>
> **Caveat for anyone re-running the pipeline.** The line was left in place rather than made conditional, so in the current source it is an unconditional literal in all three London scripts (`main-generating-v5London.py:287`, `second-generating-female-London.py:191`, `second-generating-male-London.py:191`). A fresh run from scratch would therefore request 2K for *every* call — which is not what was done, and which also raises the billed output token count above the 1290 tokens / ≈ $0.039 quoted for ≤ 1024 × 1024 outputs. Comment the line out, or gate it, before re-running.

**7. Resolution enforcement and save**
If the returned image differs from 1024 × 1024 — which happens when `image_size = "2K"` was requested — it is resized back with LANCZOS. It is then saved to `Output_images/{stem}_{SIGLE}.png` as PNG (lossless, to avoid compounding compression artefacts across stages) and validated with `PIL.Image.verify()`.

**Outputs per input image (3 files):**
```
FC2_H.png    ← high
FC2_MH.png   ← medium_high
FC2_M.png    ← medium
```

**Total stimuli from first pipeline (London):** 16 subjects × 3 levels = **48 images**, all 1024 × 1024, verified on disk.

---

### 1.2 Manual curation stage

The first pipeline's raw output is not fed directly to the second pipeline. Three folders under `Output_images/` materialise the curation step:

| Folder | Files | Role |
|---|---|---|
| `Output_images/` | 48 | Raw first-pipeline output |
| `Output_images/ReadyToEdit/` | 48 | Working copies; inspected and colorimetrically corrected by hand |
| `Output_images/ReadyToEnhance/Female/` | 16 | 8 female subjects × `_H`, `_MH` — second-pipeline input |
| `Output_images/ReadyToEnhance/Male/` | 16 | 8 male subjects × `_H`, `_MH` — second-pipeline input |

**Why the correction is needed.** Despite the photometric lock in the prompt, the model does not reproduce the source exposure exactly. Measured on the background plate across all 16 subjects, the generated renders are systematically darker than their standardized inputs: mean −18.4 grey levels (8-bit) for `_H`, −23.6 for `_MH`, −13.3 for `_M`, with a per-image range from +4.2 to −57.2. The model also neutralises the source backdrop's slight cool cast into an essentially achromatic grey. Uncorrected, this drift would be confounded with the anthropomorphism manipulation.

**What was actually changed.** The corrections applied are global and low-amplitude — full-frame tonal adjustments, not local retouching. Of the 48 renders, 3 differ in pixel content from their raw counterparts (`MC2_M`, `MT3_MH`, `MT4_M`), with maximum per-channel deltas of 3, 1 and 8 levels out of 255 respectively, spread across the whole frame. The remaining 45 were judged to need no correction and were carried forward byte-identical. One file, `FC3_M.png`, carries an alpha channel in `Output_images/`, indicating it was round-tripped through the image editor and copied back.

**Selection for the second pipeline.** Only `_H` and `_MH` renders are enhanced; `_M` renders are not. The Medium level in the enhanced branch is instead reached by *mediumizing* an already-enhanced High or Medium-High image (step 2 below), which confines the enhancement operation to the two higher-fidelity levels where facial detail is sufficient for it to be meaningful. The split into `Female/` and `Male/` is the mechanism that selects which of the two second-pipeline scripts applies, since the enhancement prompt is gender-specific.

All 32 files in `ReadyToEnhance/` are byte-identical to their `ReadyToEdit/` counterparts — i.e. the second pipeline consumes the *curated* renders, not the raw ones.

---

### 1.3 Second Pipeline — `second-generating-female-London.py` and `second-generating-male-London.py`

**Purpose:** Takes the curated `_H` and `_MH` renders, applies a beauty-enhancement pass to produce `_HE` / `_MHE`, then applies the Medium anthropomorphism style to the enhanced image to produce `_HEM` / `_MHEM`.

The two scripts are identical in logic and differ only in:
- The input directory (`INPUT_ENHANCED_FEMALE_DIR` vs `INPUT_ENHANCED_MALE_DIR`).
- The `ENHANCEMENT_PROMPT` — female version targets the Western female attractiveness canon; male version targets the Western male canon.

`ENHANCED_MEDIUM_PROMPT1` is byte-identical in both scripts, so only the beauty optimisation is sex-differentiated, not the rendering. Outside the `ENHANCEMENT_PROMPT` block, a line-by-line comparison of the two files returns exactly one substantive difference — the input directory named in `main()` — plus one whitespace-only line. The API wrapper, retry policy, moderation handling, response decoding, resolution enforcement and verification are the same as in the first pipeline, including the two non-uniform elements noted at step 6: the four model-exception stimuli are all outputs of this pipeline, and `image_size = "2K"` was likewise applied here only to images affected by graininess.

#### Input scanning
`scan_enhancement_input_images(INPUT_ENHANCED_FEMALE_DIR)` (or `MALE_DIR`) iterates the directory and collects files whose stem ends exactly with `_H` or `_MH` (derived from `ENHANCED_LEVELS_SIGLE`). The exact-suffix check excludes numbered attempt files (e.g. `FC2_H-3.png`). No `MAX_IMAGES` cap — all eligible files are processed.

#### Resolution handling
Both steps call `standardize_input_image(image_path, None)`. Passing `None` makes the function preserve the file untouched and merely report its size and aspect-ratio label; no crop, no resampling, and no copy written to `StandardizedImages/`. This is correct by construction: the inputs are first-pipeline outputs, already at 1024 × 1024 and already aligned to the model's native 1:1 grid. The label forwarded to the API is `"1:1"`.

#### Step 1 — Beauty Enhancement (`process_image_enhancement`)

For each input file (e.g. `FC2_H.png`):

1. `standardize_input_image(image_path, None)` — returned unchanged.
2. Skip check: if `Output_images/Enhanced/{stem}E.png` already exists, skip.
3. API call with `ENHANCEMENT_PROMPT` and aspect ratio `"1:1"`.
4. Save as `Output_images/Enhanced/{stem}E.png`.

**`ENHANCEMENT_PROMPT` (female version):** Produce a hyper-beautified version of the same person — an idealised representation pushing beauty optimisation beyond what is typically achievable in ordinary humans, explicitly benchmarked against top-tier AI virtual influencers (Aitana Lopez, Lil Miquela aesthetic logic), while remaining credible and avoiding any uncanny-valley, plastic, doll-like or grotesque appearance. Feature-level targets follow the Western female canon: maximise facial symmetry; slim the jawline into a soft V-shape; elevate cheekbones; refine the nose and its tip; enlarge and brighten the eyes with long full lashes; lift the eyebrows into a harmonious arch; fuller lips with a clear cupid's bow; flawless, poreless yet natural-looking skin — invoking averageness, sexual dimorphism and neoteny cues applied with restraint.

**`ENHANCEMENT_PROMPT` (male version):** Same structure, Western male canon: strong angular jawline with a defined gonial angle; refined chin projection; masculine cheekbone hollows; well-proportioned nasal bridge and defined tip; emphasised brow ridge; brightened eyes *without* enlargement or lash emphasis; fuller, straighter brows; lips defined but not enlarged; credible male skin micro-texture retained; existing facial hair groomed but neither added nor removed; slightly higher facial width-to-height ratio. A dedicated negative-constraint block prohibits feminised features (soft V-shaped jaw, enlarged eyes, visible lashes, fuller-than-natural lips, over-arched brows, neotenous proportions).

Both variants impose the same preservation block: identity clearly recognisable as the same individual; head pose, gaze direction, framing, crop, neutral grey background, lighting setup, clothing, hairstyle, hair colour and hair length identical to the source; and — critically — **the exact same rendering style and level of photorealism/anthropomorphism as the source**, with an explicit instruction not to shift it in either direction. This requirement is what keeps anthropomorphism and beauty optimisation orthogonal in the resulting stimulus set.

**Outputs from step 1 (per subject):**
```
FC2_HE.png    ← FC2_H.png enhanced
FC2_MHE.png   ← FC2_MH.png enhanced
```

#### Step 2 — Mediumization (`process_medium_style`)

Immediately after step 1, within the same loop iteration, `process_medium_style` is called with the same `image_path`:

1. Computes the enhanced image path: `Output_images/Enhanced/{stem}E.png` (e.g. `FC2_HE.png`).
2. `standardize_input_image(enhanced_image_path, None)` — returns unchanged.
3. Skip check: if `Output_images/Enhanced/{stem}EM.png` already exists, skip.
4. API call with `ENHANCED_MEDIUM_PROMPT1` and aspect ratio `"1:1"`.
5. Save as `Output_images/Enhanced/{stem}EM.png`.

Because step 2 reads the file step 1 has just written, a failure in step 1 leaves step 2 with a missing input; `Image.open` then raises `FileNotFoundError`, which is caught by the `except (UnidentifiedImageError, OSError)` handler and skipped cleanly.

**`ENHANCED_MEDIUM_PROMPT1`:** Re-shades the beauty-enhanced synthetic asset into the Level MEDIUM rendering style, referencing *The Polar Express* (2004) as the definitive benchmark. Key instructions:
- Skin: continuous, slightly-too-smooth 3D mesh with flat diffuse albedo — matte, waxy like polished candle wax, no specular highlights, no subsurface glow. Albedo brightness **calibrated so the face reads at the same overall exposure level as the attached image**.
- Skin marks: re-expressed as flat painted decals with no geometric relief; no visible pore structure or micro-normal variation.
- Hair, eyebrows and facial hair: geometrically thin old-game-engine particle systems.
- Preserve from source: identity and all facial features; apparent age, gender, ethnicity; **the subject's facial attractiveness as it appears in the source** (i.e. carry the enhancement forward rather than re-deriving it); hairline, parting, length, density and colour; all accessories and clothing in their exact coordinates and colours; head pose, head tilt, gaze direction, neutral closed-mouth expression; camera framing, crop, distance and aspect ratio.
- Photometric lock (stated as overriding all shader instructions): light direction, shadow positions, shadow softness, exposure value and white balance reproduced exactly; background a uniform neutral grey (#C8C8C8), flat and edge-to-edge.

**Outputs from step 2 (per subject):**
```
FC2_HEM.png    ← FC2_HE.png mediumized
FC2_MHEM.png   ← FC2_MHE.png mediumized
```

**Total stimuli from second pipeline (London):** 8 subjects × 2 input levels × 2 steps = **32 images per gender group**, **64 images total**, all 1024 × 1024, verified on disk.

**Complete London stimulus set:** 48 (first pipeline) + 64 (second pipeline) = **112 generated images**, plus the 16 standardized originals = **128 images** available. Regenerating the set from scratch requires a minimum of **112 billable API calls**, excluding retries and rejected outputs.

---

## Section 2 — Chicago Face Dataset (CFD)

> **This branch was piloted and abandoned.** It was never carried to a complete stimulus set. Its partial output is archived under `Output_images/CFD_PROBLEM/` (whose name records the outcome) and `Images/StandardizedImages/CFD/`. The section below documents what the CFD scripts do and how far the run actually got, for the record.

**Source images:** 2444 × 1718 px (ratio 1.4226, nearest supported label `3:2`), plain white background — verified flat `#FFFFFF` edge-to-edge, unlike the London backdrop.
**Scripts:** `main-generating-v5CFD.py`, `second-generating-female-CFD.py`, `second-generating-male-CFD.py`.
**Standardized / saved resolution:** 1264 × 848 px (Gemini 3:2 native 1K — `compute_gemini_1k_for_input(2444, 1718)`).

To switch from London to CFD in `constants.py`: comment out the London path block, uncomment the CFD block, set `INPUT_RESOLUTION = compute_gemini_1k_for_input(2444, 1718)`, and **manually archive any existing output** (see the note in *Shared Configuration* — the output folders are not dataset-specific).

### 2.1 First Pipeline — `main-generating-v5CFD.py`

The logic is identical to the London version, with these differences:

| Parameter | London | CFD |
|---|---|---|
| Input directory | `LondonDataset/ExperimentalDataset/` | `ChicagoFaceDataset/ExperimentalDataset/` |
| Source image size | 1350 × 1350 (1:1) | 2444 × 1718 (≈ 3:2) |
| Standardized size | 1024 × 1024 | 1264 × 848 |
| API aspect ratio | `"1:1"` | `"3:2"` |
| `image_size` parameter | `"2K"` | **not set** — `ImageConfig` carries only `aspect_ratio` |
| Background in prompts | Neutral grey #C8C8C8 | Pure white #FFFFFF |

`standardize_input_image` converts 2444 × 1718 → 1264 × 848 via `ImageOps.fit()` in a single centred LANCZOS pass that both crops to the target aspect ratio and downscales, saving the result as `Images/StandardizedImages/{stem}.png`. Matching the model's *real* 3:2 output dimensions (1264/848 = 1.49057, not exactly 1.5) means the final resize step is uniform on both axes, so no distortion is introduced.

> A second helper, `compute_crop_for_input(2444, 1718)`, exists in `constants.py` and returns `(2444, 1640)` — a 78 px height crop that matches the ratio while preserving full source resolution. It is **commented out** and was not used; the active path is `compute_gemini_1k_for_input`, which targets the model's native 1K grid directly.

The `locked_context` in `build_enhanced_prompt` specifies a `pure white #FFFFFF` background, matching the CFD photographic conditions.

**Outputs per input image (3 files):**
```
MC1_H.png    ← high
MC1_MH.png   ← medium_high
MC1_M.png    ← medium
```

**Actually produced:** 21 files at 1264 × 848 — 7 subjects × 3 levels (`FC1`–`FC4`, `FT1`, `FT2`, `MC1`), out of the 48 a complete run would yield. `Images/StandardizedImages/CFD/` correspondingly holds 7 standardized inputs.

### 2.2 Second Pipeline — `second-generating-female-CFD.py` and `second-generating-male-CFD.py`

Identical in structure to the London second pipeline. Differences:

| Parameter | London | CFD |
|---|---|---|
| Input image size | 1024 × 1024 | 1264 × 848 |
| API aspect ratio | `"1:1"` | `"3:2"` |
| `image_size` parameter | `"2K"` | **not set** |
| Background in prompts | Neutral grey #C8C8C8 | Pure white #FFFFFF |

`standardize_input_image` is called with `None` in both steps (inputs are already at the correct Gemini-native resolution from the first pipeline), so no resize or crop is applied and no copy is written to `StandardizedImages/`.

`ENHANCED_MEDIUM_PROMPT1` for CFD specifies a `pure white (#FFFFFF)` background instead of neutral grey.

**Outputs follow the same naming convention:**
```
MC1_HE.png    ← MC1_H.png enhanced
MC1_MHE.png   ← MC1_MH.png enhanced
MC1_HEM.png   ← MC1_HE.png mediumized
MC1_MHEM.png  ← MC1_MHE.png mediumized
```

**Actually produced:** 8 files — 2 subjects (`FT1`, `MC1`) × 4 variants, out of the 64 a complete run would yield.

---

## Complete Stimulus Taxonomy

For each subject, the full set of stimuli a complete run generates is:

```
{ID}        Original photo, standardized (1024 × 1024 for London)
{ID}_H      Original photo → High CGI
{ID}_MH     Original photo → Medium-High CGI
{ID}_M      Original photo → Medium CGI
{ID}_HE     _H → Beauty enhanced (same rendering style preserved)
{ID}_MHE    _MH → Beauty enhanced (same rendering style preserved)
{ID}_HEM    _HE → mediumized
{ID}_MHEM   _MHE → mediumized
```

Every transformation preserves, by prompt construction: **identity, head pose, gaze direction, facial expression, camera framing, crop, lighting setup, clothing, hairstyle and background**. The only manipulated variables are (1) the surface rendering style, which operationalises anthropomorphism, and (2) the degree of beauty optimisation.

**Verified folder inventory (London production):**

| Folder | Files | Resolution |
|---|---|---|
| `Images/LondonDataset/ExperimentalDataset/` | 16 | 1350 × 1350 |
| `…/ExperimentalDataset/ExperimentalDataset_origin/` | 16 | 1350 × 1350 |
| `Images/StandardizedImages/` | 16 | 1024 × 1024 |
| `Output_images/` | 48 | 1024 × 1024 |
| `Output_images/ReadyToEdit/` | 48 | 1024 × 1024 |
| `Output_images/ReadyToEnhance/Female/` | 16 | 1024 × 1024 |
| `Output_images/ReadyToEnhance/Male/` | 16 | 1024 × 1024 |
| `Output_images/Enhanced/` | 64 | 1024 × 1024 |

---

## Appendix — Known code drift

Items that do not affect the delivered stimuli but are misleading when reading the source.

- **`image_size="2K"` is unconditional** in the three London scripts and absent from the three CFD scripts. See the note in §1.1 step 6.
- **`process_one_image()` docstring** still reads *"Generate all five anthropomorphism variants"*; the loop iterates `LEVELS_3` (three).
- **`get_test_enhanced_images()`** in both second-pipeline scripts hard-codes Chicago Face Dataset stems (`CFD-WF-233-112-N_high`, `CFD-WM-201-063-N_high`). In the London scripts it is dead code — `main()` never calls it. In the CFD scripts it is reachable via the `isTest` flag (currently `False`).
- **`get_supported_aspect_ratio()` is recomputed per image, but its value is invariant.** `standardize_input_image()` contains four call sites. When `target_resolution` is given (first pipeline), only the last two are reachable for London — the `target_resolution is None` branch cannot be taken, and the `source_image.size == target_resolution` branch cannot either, since every source is 1350 × 1350 and the target is 1024 × 1024. Both reachable sites pass exactly `target_resolution`, so the returned label is always `get_supported_aspect_ratio(*INPUT_RESOLUTION)` — a constant that could be computed once at module level. When `target_resolution is None` (second pipeline) the label is read from the actual file, which is a genuine safety net, though in practice every input is a 1024 × 1024 first-pipeline output. **Verified:** the label sent to the API is `"1:1"` on all 48 first-pipeline calls and all 64 second-pipeline calls — 112 identical computations.

  The function itself is **not** eliminable: `ImageConfig.aspect_ratio` accepts only the ten label strings, never a pixel pair, so something must translate `(1024, 1024)` → `"1:1"`. The redundancy is in *when* it is called, not in *whether* it exists. Note also that deriving the label from `INPUT_RESOLUTION` rather than from the source dimensions is the more robust choice, because the standardized image — not the original — is what is actually sent. For London the two agree exactly (both are 1.00000 → `1:1`). For CFD they agree but by a thin margin: the source ratio 2444/1718 = 1.42258 sits at distance 0.07742 from `3:2` and 0.08925 from `4:3`, whereas the standardized 1264/848 = 1.49057 sits at 0.00943 from `3:2` and 0.15723 from `4:3`.

- **`RETRY_BASE_DELAY = 5`** is defined in `constants.py` but never used; the scripts read `RETRY_BASE_DELAY_SECONDS = 1.5`.
- **Operator precedence in block detection:** `if reason and "IMAGE" in str(reason) or "SAFETY" in str(reason)` parses as `(reason and "IMAGE" in …) or ("SAFETY" in …)`, because `and` binds tighter than `or`. The second operand is evaluated even when `reason` is `None`. It happens not to crash, but it is not what the surrounding comment describes.
- **`get_supported_aspect_ratio()`** is defined locally in each pipeline script (and also exists in `ProveImg.py`). `CLAUDE.md` points to `ProveImg.py` as its home, which is misleading — the pipelines use their own copies.
- **`clean-background.py`** (rembg segmentation compositing onto a flat RGB (200, 200, 200) plate) exists but was **not used** in either production run: its destination folder `Output_images_clean/` does not exist. It is not part of the pipeline.
- **`Old/`, `Variants/`, `OtherModels/`, `main-generating-v5.py`, `-v5b.py`, `-v5cClaude.py`, `prompt.py`, `Claude_build_prompt.py`** are earlier iterations retained for provenance. The production scripts are the three London files listed in §1.
