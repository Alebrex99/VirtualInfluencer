# PAPER.md — Section 3.1.3 *Stimulus Development* (continuation)

**Scope.** This file continues the section you have already written, from the point where you
stop (*"…only specific stimuli were generated using the Gemini 3.1 Flash Image Preview model…"*)
through the complete description of the **First Pipeline**, the **intermediate curation stage**,
and the **Second Pipeline**.

Everything below was re-derived directly from the code and from the contents of the image
folders on disk, **not** from the README. Where the README (or the current draft) is imprecise,
the correction is applied silently in the paste-ready prose and listed explicitly in
[Part D — Discrepancies found](#part-d--discrepancies-found-not-for-the-word-document).

**Files audited:** `main-generating-v5London.py`, `second-generating-female-London.py`,
`second-generating-male-London.py`, `constants.py`, `.env`, `clean-background.py`. The three CFD
scripts (`main-generating-v5CFD.py`, `second-generating-{female,male}-CFD.py`) were audited only
as a control, to establish which parameters are London-specific.
**Folders audited:** `Images/LondonDataset/ExperimentalDataset/`, `Images/StandardizedImages/`,
`Output_images/`, `Output_images/ReadyToEdit/`, `Output_images/ReadyToEnhance/{Female,Male}/`,
`Output_images/Enhanced/`, `Images/StyleRefImages/`.

---

## Part A — Corrections to the text you have already written

Apply these three edits before appending the new material.

| # | Where | Current text | Correction | Why |
|---|---|---|---|---|
| A1 | §3.1.3, second bullet | "The **medium-high and low** anthropomorphism conditions retain recognizable human features with artificial cues." | "The **medium-high and medium** anthropomorphism conditions retain recognizable human features with progressively stronger artificial cues." | The London production generates only three levels (`LEVELS_3 = ["high", "medium_high", "medium"]`). No *low* (or *medium-low*) condition was produced. Those two levels exist in `constants.py` (`LEVELS`) but are never iterated by `main-generating-v5London.py`. |
| A2 | §3.1.3, bullet list on API platforms | — (add) | Add after the two bullets: "The model identifier is read from the `.env` configuration file at run time, which is how the four model-exception stimuli were produced: the run was repeated for those four images with the alternative model set in `.env`." | The model switch is **not** encoded in the scripts; it is an environment-level substitution. Stating this makes the exception reproducible. |
| A3 | §3.1.3, opening of the two-stage description | "…it renders each original face photograph into three levels of anthropomorphism." | Keep, but add: "A manual curation stage is interposed between the two pipelines (Section 3.1.3.3)." | The two pipelines are **not** directly chained: the second pipeline reads from a folder that is populated by hand, not from the first pipeline's output folder. Omitting this makes the file paths in the second pipeline unintelligible. |

Also note (for the part of the chapter you said you will redefine): the sentence *"All images
will be standardized for resolution (1080 × 1080 pixels)"* and the bullet block quoting
*"Input image size: 2444 × 1718 / Output image size (filtered resize): 2444 × 1718"* describe
the **Chicago Face Dataset** pipeline, not the London one. For London the figures are
**1350 × 1350 → 1024 × 1024**.

---

## Part B — Paste-ready prose

> Numbering below assumes the new material is nested inside §3.1.3. Renumber to 3.1.4 / 3.1.5 /
> 3.1.6 if you prefer to promote the pipelines to their own subsections; in that case §3.1.4
> *Participants* becomes §3.1.7.

---

### B.0 Summary paragraphs — the two pipelines

> **Placement.** These two paragraphs go together, immediately before the detailed descriptions
> begin. They share the same structure — what the stage does, how resolution is handled,
> idempotency — so they read as a pair.

#### First Pipeline

> **What changed from your draft.** Everything your version asserted is accurate; the revision adds
> what it omitted. Your text refers to *"the standardized input resolution"* without ever saying
> that the inputs are standardized, so the reader meets the figure 1024 × 1024 with no account of
> where it comes from, why it was chosen, or that the original photographs were themselves brought
> to it. That omission also leaves the two sentences on sampling filters unanchored: Lanczos is
> introduced before the operation that uses it. The revision supplies the standardization step and
> its rationale, and turns *"if the model returns a different size"* — which reads as the common
> case — into what it actually is: the exception, essentially confined to the 2K regenerations.

The first pipeline converts each original London dataset photograph into three CGI-rendered
versions at different anthropomorphism levels (High, Medium-High, Medium). Before any request is
issued, each source photograph is standardized to a common resolution of 1024 × 1024. The value is
not arbitrary: it is the size the model itself produces natively for a square request, and fixing
it in advance means that the original photographs and every generated variant enter the experiment
at the same size, so that image size cannot be confounded with the manipulation. The crop and
downscale are performed with the Lanczos resampling filter. Sampling filters, provided by the
Python Imaging Library (PIL), are used for geometry operations that may map multiple input pixels
to a single output pixel; the high-quality Lanczos resampling filter calculates the output pixel
value using a truncated mathematical sinc function. Every output is then saved at that same
resolution. Because the target coincides with the model's native output size, the generated image
normally comes back already at 1024 × 1024 and is saved unchanged; if it returns at a different
size it is resized back with Lanczos before saving. That is the case for the subset of images that
showed graininess (artefacts) from the model's post-generation sharpening, for which
`image_size = "2K"` was requested and the 2K result downscaled at save time. The pipeline is
idempotent: if an output file already exists, it is skipped without an API call.

#### Second Pipeline

The second pipeline takes the High and Medium-High renders produced by the first pipeline and
applies two chained transformations to each of them: a beauty-enhancement pass, which produces a
hyper-optimized version of the same subject while holding the rendering style constant, and a
subsequent pass — referred to throughout as **mediumization** — which re-shades that enhanced image
into the Medium anthropomorphism style while retaining the beauty optimization it has just
received. An image that has undergone this second pass is described as **mediumized** and carries a
terminal `M` in its filename suffix (`_HEM`, `_MHEM`). The second pipeline is executed
twice, once for the female and once for the male subjects, because the enhancement prompt is
gender-specific; the two runs are identical in every other respect. Medium-level renders are not
enhanced directly: within the enhanced branch the Medium level is reached only by mediumizing an
already-enhanced image, which confines beauty optimization to the two higher-fidelity levels, where
facial detail is sufficient for the operation to be meaningful. Unlike the first pipeline, this
stage performs no standardization: its inputs are first-pipeline outputs, already at 1024 × 1024
and already aligned to the resolution the model natively returns for a 1:1 image, so they are
passed to the API untouched and the outputs inherit the same resolution — with the same Lanczos
resize applied at save time should the model return a different size, and the same `image_size =
"2K"` provision available for images affected by graininess. Both transformations are individually
idempotent: each verifies the existence of its own output file before issuing a call, so an
interrupted run resumes without repeating work already paid for. Each subject therefore yields four
additional stimuli; the four images for which the Gemini 3.1 Flash Image Preview model was preferred
(FT1_HEM, MC1_HE, MC1_HEM, FC3_MHEM) all belong to this stage.

> **One dependency to declare.** The sentence *"takes the High and Medium-High renders produced by
> the first pipeline"* is true but elliptical: the second pipeline does not read the first
> pipeline's output folder, it reads a folder populated by hand after the renders have been
> reviewed and, where necessary, colorimetrically corrected (§3.1.3.3). If you prefer to keep the
> summary paragraph free of that detail, add a single clause — *"…produced by the first pipeline
> and subsequently reviewed (Section 3.1.3.3)…"* — so the reader is not surprised by the file
> paths later on. Two verified facts back this up: all 32 files in `ReadyToEnhance/` are
> byte-identical to their `ReadyToEdit/` counterparts, and one of them (`MT3_MH`) is *not*
> identical to the corresponding raw first-pipeline output.

---

### 3.1.3.1 First Pipeline — anthropomorphism rendering

The first pipeline (`main-generating-v5London.py`) converts each original London photograph into
three CGI-rendered variants at decreasing levels of anthropomorphism (High, Medium-High, Medium).
It is executed once over the whole experimental set and constitutes the base stimulus generator;
all subsequent material derives from its outputs. Every source photograph is processed through the
same seven-stage sequence.

**1. Input scanning.** The `scan_input_images(EXPERIMENT_INPUT_DIR, MAX_IMAGES)` function traverses
the `Images/LondonDataset/ExperimentalDataset/` folder in alphabetical order and collects up to
`MAX_IMAGES = 16` valid image files, accepting the `.png`, `.jpg` and `.jpeg` extensions
(`ALLOWED_EXTENSIONS`). Sub-directories are ignored, so the archival folder holding the original
London filenames is not processed. This folder contains the sixteen experimental subjects,
organised into four balanced groups of four — FC1–FC4 (low-attractiveness females), FT1–FT4
(high-attractiveness females), MC1–MC4 (low-attractiveness males) and MT1–MT4 (high-attractiveness
males) — so that gender and attractiveness are crossed evenly across the stimulus set. In the
subject code, the first letter encodes gender (F/M) and the second the attractiveness group
(C = control/low, T = treatment/high). The correspondence between the experimental codes and the
original Face Research Lab London Set filenames is reported in Table X.

**2. Standardization.** Each retrieved image is passed to
`standardize_input_image(image_path, INPUT_RESOLUTION)`. The purpose of this stage is to impose a
**single common resolution on the entire stimulus set** — the standardized originals and every
generated variant alike — so that the experiment is not confounded by image size. Left
unstandardized, the original photographs would remain at 1350 × 1350 while the model returns
1024 × 1024, and any judgement involving an original would be made on a stimulus that differs from
the synthetic ones in resolution as well as in rendering. Fixing the resolution up front removes
that difference by construction rather than post hoc.

That common resolution is the constant `INPUT_RESOLUTION`, and its value is not arbitrary:
`compute_gemini_1k_for_input(1350, 1350)` returns **1024 × 1024**, which is the size the model
itself produces natively for a 1:1 request.

The operation is a single pass. If an image already matches `INPUT_RESOLUTION` it is passed
through untouched; otherwise the function calls `PIL.ImageOps.fit()`, which crops the image to the
target aspect ratio with centred framing (`centering = (0.5, 0.5)`) and resamples it to
1024 × 1024 with Lanczos, archiving the result as `Images/StandardizedImages/{stem}.png`. Sampling
filters, provided by the Python Imaging Library, are used for geometry operations that may map
multiple input pixels onto a single output pixel; the high-quality Lanczos filter computes the
output pixel value from a truncated sinc function. Because every London image measures exactly
1350 × 1350 while the target is 1024 × 1024, all sixteen subjects are cropped and archived. This
standardized file — not the original photograph — is the image actually transmitted to the API,
together with the aspect-ratio label `"1:1"`, derived by `get_supported_aspect_ratio(1024, 1024)`
from the ten ratios the model accepts (1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9).

Because `INPUT_RESOLUTION` is the model's own native output size, the generated image will come
back already at 1024 × 1024 and the resolution check at stage 7 will have nothing to change. This
stage is therefore the only point at which the source photograph is resampled.

**3. Prompt construction.** The `build_enhanced_prompt(level)` function assembles the instruction
text for the requested anthropomorphism level. Every level inherits a shared `locked_context`
preamble that frames the task as 3D-asset production: the model is instructed to treat the subject
in the base image as a 3D digital mesh and to re-surface that mesh with a synthetic rendering
engine. This framing is deliberate. Requests phrased as the direct modification of a photograph of
a real person are liable to be refused by the model's content-safety layer, which returns a
moderation signal — `prompt_feedback`, or a `finish_reason` such as `SAFETY` or `IMAGE_SAFETY` —
in place of an image; describing the same operation as the production of a synthetic character
asset is both accurate, since the stimuli are synthetic renders, and not subject to that refusal.
The input therefore serves solely as (a) a *geometric* reference — facial structure, hair,
accessories, clothing, pose, framing — and (b) a *photometric* blueprint — light direction, shadow
positions and softness, exposure value, white balance and background. The preamble then states four
explicit constraints, formulated as locks: an **identity lock** (facial geometry, skin marks,
hair and eyebrow geometry, accessories, and apparent age, gender, ethnicity and inherent facial
attractiveness must be preserved and merely re-rendered through the target shader); a
**composition lock** (pose, head tilt, gaze direction, expression, camera framing, crop, aspect
ratio, clothing); a **photometric lock** (light direction and angle, shadow geometry, exposure
value and white balance must be identical to the base image, so that the output histogram matches
the input in mid-tone placement and highlight roll-off); and a **background lock** (a flat neutral
grey backdrop identical to the base image). The preamble closes by declaring the single permitted
degree of freedom: only the shading model and surface rendering may change between levels, while
the lighting rig itself does not move, soften, harden, brighten or darken. On top of this common
foundation, a level-specific section dictates the target rendering style (Table Y). This
architecture — one invariant block plus one short variable block — is what operationalises the
experimental requirement that anthropomorphism be manipulated while every other visual attribute
is held constant. The three prompts are reproduced in full in Appendix A.

> **What to cite for the moderation signals.** Do not cite the `laozhang.ai` blog post: it gives no
> primary source (it references a GitHub issue and "Vertex AI documentation" without links), and its
> enumeration is incomplete — it lists five `FinishReason` values where the SDK defines fifteen, and
> its "Layer 1 / Layer 2" taxonomy appears nowhere in the official types. Cite the SDK instead. Both
> enums are public, documented types in `google-genai` (verified in the version installed for this
> project, **1.74.0**, at `google/genai/types.py`):
>
> - `types.FinishReason` — `FINISH_REASON_UNSPECIFIED`, `STOP`, `MAX_TOKENS`, `SAFETY`, `RECITATION`,
>   `LANGUAGE`, `OTHER`, `BLOCKLIST`, `PROHIBITED_CONTENT`, `SPII`, `MALFORMED_FUNCTION_CALL`,
>   `IMAGE_SAFETY`, `UNEXPECTED_TOOL_CALL`, `IMAGE_PROHIBITED_CONTENT`, `NO_IMAGE`. The docstring for
>   `IMAGE_SAFETY` reads *"Token generation stopped because generated images have safety violations."*
> - `types.BlockedReason` — `BLOCKED_REASON_UNSPECIFIED`, `SAFETY`, `OTHER`, `BLOCKLIST`,
>   `PROHIBITED_CONTENT`, `IMAGE_SAFETY`, `MODEL_ARMOR`, `JAILBREAK`. The docstring for `IMAGE_SAFETY`
>   reads *"The prompt was blocked because it contains content that is unsafe for image generation."*
>
> The two values named in the paragraph above, `SAFETY` and `IMAGE_SAFETY`, are therefore both
> official and are exactly what the pipeline's block-detection matches on.

**4. Optional style-reference images.** The pipeline supports a second, style-guiding image.
`get_style_reference_image(level)` inspects `Images/StyleRefImages/` for a file named exactly
`reference_{level}` (`.png`, `.jpg` or `.jpeg`) and, when one is found, appends it to the request
as a second image, after the identity image. For the production of the present stimuli this
mechanism was deliberately left inactive: no file matching the expected naming pattern is present,
the function returns `None`, and each request therefore carries the standardized input image alone.
Style transfer is thus driven entirely by the textual prompt, which avoids introducing a second,
uncontrolled source of visual variance across levels.

**5. Skip-if-exists check.** Before any call is issued, the pipeline tests whether
`Output_images/{stem}_{SIGLE}.png` already exists and, if so, skips that level entirely. This
guards against redundant API expenditure and makes every run idempotent and fully resumable after
an interruption — a practical requirement given that a complete run issues several dozen billable
requests.

**6. API call.** When generation is required, the request is issued through
`generate_with_retry(client, model, standardized_image_path, prompt, aspect_ratio)`, which wraps
the underlying SDK call. With the aspect-ratio label resolved to `"1:1"` (stage 2), the request is:

```python
client.models.generate_content(
    model="gemini-3-pro-image-preview",   # gemini-3.1-flash-image-preview for four stimuli
    contents=[prompt, input_pil_image],
    config=GenerateContentConfig(
        response_modalities=[Modality.TEXT, Modality.IMAGE],
        image_config=ImageConfig(
            aspect_ratio="1:1",
            image_size="2K"               # only for images affected by graininess
        )
    )
)
```

Two elements of this call were not applied uniformly across the production run, and the listing
above shows the configuration used for the affected images rather than the default one. The model
was `gemini-3-pro-image-preview` throughout, except for the four stimuli named in §3.1.3, which
were re-run with `gemini-3.1-flash-image-preview`. The `image_size` field was set to `"2K"` **only
for the images that came back grainy** — an artefact of the model's post-generation sharpening
pass, which in some outputs produced a visibly degraded, noisy surface. Those images were
regenerated at 2K and downscaled to 1024 × 1024 at save time, which resolved the artefact; every
other image was generated at the model's native 1K output, where `image_size` is left unset. In
both cases the variation was operational — applied to specific images during production by
adjusting the configuration and re-running them — and is not a per-image branch inside the code.

The ordering of `contents` is significant: the textual instruction precedes the identity image, and
the optional style image, when present, follows it. The generated image is not returned as a
decoded image object but as an inline binary payload — the raw PNG/JPEG bytes of
`part.inline_data.data` — so a dedicated extraction routine (`extract_pil_image`) walks both
possible response layouts, the flat `response.parts` list and the nested
`response.candidates[*].content.parts[*]` structure, and decodes the first inline payload it finds.

Should a call raise, it is re-issued up to `MAX_RETRIES = 3` attempts in total (the initial attempt
plus two retries) with exponential back-off, the base delay of 1.5 seconds doubling at each
successive attempt, so that the waits are 1.5 s and 3.0 s. A refusal by the content-safety layer —
the case described at stage 3 — is treated differently from a failed call, since retrying it would
not help. The reason the API returns is logged (`prompt_feedback` when the prompt itself was
rejected, `finish_reason` when the block arose during generation), no image is produced for that
stimulus, and the run continues with the next level rather than aborting.

**7. Resolution enforcement, saving and verification.** If the returned image differs from the
standardized input size — which is the case for the images regenerated at 2K — it is resampled to
1024 × 1024 with the Lanczos filter; otherwise it is saved unchanged. The file is written to
`Output_images/{stem}_{SIGLE}.png` and validated with `PIL.Image.verify()` to confirm that it is a
complete, readable image. All outputs are stored as PNG (lossless) to avoid compounding compression
artefacts across the subsequent generation stages.

The net result is three rendered files per input subject, one per anthropomorphism level:

```
FC2_H.png    ← high
FC2_MH.png   ← medium_high
FC2_M.png    ← medium
```

Across the full set the first pipeline therefore yields **16 subjects × 3 levels = 48 images**,
all at 1024 × 1024 pixels.

---

**Table Y — Level-specific rendering styles (first pipeline).**

| Level | Suffix | Rendering style |
|---|---|---|
| `high` | `_H` | Hyperreal generative-AI portrait / Midjourney-v5 signature: pores, freckles and marks re-rendered as ultra-sharp, algorithmically over-traced micro-relief; synthetic sheen on the highlight side; unnaturally even local contrast; glassy, over-specular eyes with mathematically circular irises; algorithmically over-sharpened hair strands, eyelashes and lip line. The surface reads as "too perfectly detailed to be a photograph". |
| `medium_high` | `_MH` | AAA real-time game character (skin aesthetics of *Uncharted 4*): skin treated as a synthetic PBR material with an opaque matte-plastic response; diffuse-dominant albedo and normal maps; detail rendered as mathematically generated digital noise rather than organic texture; hard-clamped subsurface scattering; hair and facial hair as game-engine particle systems with clean alpha cards and baked specular highlights; static pre-rendered eye reflections; directional rim lighting expressing mesh topology. |
| `medium` | `_M` | Early-2000s cinematic CGI / uncanny valley (*The Polar Express*, 2004): waxy skin resembling a soft silicone mask or polished candle wax; the face as one continuous, slightly-too-smooth mesh; imperfections applied as a flat diffuse pass that reads as painted onto the surface rather than emerging from it; hair as old-game-engine particle systems; flat lighting lacking realistic bounce, with shadows falling slightly too softly. |

---

**Table X — Mapping between experimental subject codes and Face Research Lab London Set source files.**

| Code | Group | Source file | | Code | Group | Source file |
|---|---|---|---|---|---|---|
| FC1 | Female, low attractiveness | `020_03.jpg` | | MC1 | Male, low attractiveness | `125_03.jpg` |
| FC2 | Female, low attractiveness | `120_03.jpg` | | MC2 | Male, low attractiveness | `172_03.jpg` |
| FC3 | Female, low attractiveness | `102_03.jpg` | | MC3 | Male, low attractiveness | `143_03.jpg` |
| FC4 | Female, low attractiveness | `013_03.jpg` | | MC4 | Male, low attractiveness | `031_03.jpg` |
| FT1 | Female, high attractiveness | `124_03.jpg` | | MT1 | Male, high attractiveness | `108_03.jpg` |
| FT2 | Female, high attractiveness | `027_03.jpg` | | MT2 | Male, high attractiveness | `033_03.jpg` |
| FT3 | Female, high attractiveness | `009_03.jpg` | | MT3 | Male, high attractiveness | `101_03.jpg` |
| FT4 | Female, high attractiveness | `112_03.jpg` | | MT4 | Male, high attractiveness | `041_03.jpg` |

*Note.* The mapping was verified by content hashing of the renamed files against the archived
originals. The `_03` suffix is the London Set code for the neutral-front view. **You still need to
add a column with each subject's mean attractiveness rating** from `london_faces_ratings.csv` —
the norming CSVs are not stored in the repository, so the code-to-rating assignment could not be
verified here.

---

### 3.1.3.2 Colorimetric drift and its correction

Although the prompt imposes an explicit photometric lock, the generative model does not reproduce
the exposure of the source plate exactly. A direct measurement of the background plate across all
sixteen subjects shows a systematic negative luminance drift in the generated renders relative to
their standardized inputs: on average −18.4 grey levels (8-bit scale) for the High condition,
−23.6 for Medium-High and −13.3 for Medium, with a per-image range spanning +4.2 to −57.2 levels.
The model also neutralises the slight cool cast of the original studio backdrop — whose green and
blue channels exceed the red by approximately three to four levels — into an essentially
achromatic grey.

This drift is consequential for the present design, because the experimental stimuli must be
comparable to the original photographs — and to one another — on every dimension except rendering
style and beauty optimisation. Uncorrected exposure or white-balance differences would introduce a
confound perfectly aligned with the manipulation. A manual correction stage was therefore
interposed between the two pipelines.

### 3.1.3.3 Intermediate curation stage (manual)

The two pipelines are not directly chained; a curation stage separates them, materialised as a set
of staging folders under `Output_images/`.

1. **`Output_images/`** holds the 48 raw outputs of the first pipeline.
2. **`Output_images/ReadyToEdit/`** holds a working copy of all 48 renders. Each render was
   inspected against its source photograph and, where the automated output deviated in exposure,
   tonal distribution or colour cast, corrected by hand in an image editor. The corrections applied
   are global and low-amplitude — full-frame tonal adjustments with maximum per-channel deltas of
   between 1 and 8 levels out of 255 — consistent with exposure and tint curves rather than local
   retouching; no facial content was altered at this stage. Renders that already matched their
   source were carried forward unchanged. The curated version of each render is the one retained
   for the experiment.
3. **`Output_images/ReadyToEnhance/Female/`** and **`Output_images/ReadyToEnhance/Male/`** hold the
   subset that feeds the second pipeline: only the `_H` and `_MH` renders, split by gender because
   the beauty-enhancement prompt is gender-specific. Each folder contains 8 subjects × 2 levels =
   **16 files**, 32 in total. The `_M` renders are not enhanced: the Medium level is reached, in
   the enhanced branch, by re-rendering an already-enhanced High or Medium-High image
   (Section 3.1.3.4), which keeps the enhancement operation itself confined to the two
   higher-fidelity levels where facial detail is sufficient for it to be meaningful.

Splitting the input by gender is the mechanism by which the two second-pipeline scripts are
selected, each reading only its own folder.

### 3.1.3.4 Second Pipeline — beauty enhancement and mediumization

The second pipeline (`second-generating-female-London.py` and `second-generating-male-London.py`)
is executed after the first pipeline and after the curation stage. It takes the curated `_H` and
`_MH` renders and applies two chained transformations, producing four stimuli per subject. The two
scripts differ only in their input directory and in the wording of the enhancement prompt: outside
the `ENHANCEMENT_PROMPT` block, a line-by-line comparison of the two files returns exactly one
substantive difference, the input directory named in `main()`. The mediumization prompt,
`ENHANCED_MEDIUM_PROMPT1`, is byte-identical in both, so only the beauty optimisation is
sex-differentiated, not the rendering. All remaining logic — the API wrapper, the
retry and back-off policy, the moderation handling, the response decoding, the resolution
enforcement, the verification step — is the same as in the first pipeline, including the two
non-uniform elements described at stage 6: the four model-exception stimuli (`FT1_HEM`, `MC1_HE`,
`MC1_HEM`, `FC3_MHEM`) are all outputs of this pipeline, and `image_size = "2K"` was likewise
applied here only to images affected by graininess.

**Input scanning.** `scan_enhancement_input_images()` iterates over the gender folder assigned to
the run and retains only those files whose stem terminates exactly with one of the suffixes
declared in `ENHANCED_LEVELS_SIGLE = {"high": "H", "medium_high": "MH"}`. The test is one of exact
termination rather than of containment, and this is deliberate: prompt iteration during development
left behind intermediate attempt files carrying a numeric discriminator, such as `FC2_H-3.png`,
which the test excludes without any further filtering being necessary. Unlike the first pipeline,
no `MAX_IMAGES` cap applies here, so every eligible file present in the folder is processed.

**Resolution handling.** Both steps call `standardize_input_image(..., None)`, the first on the file
read from `ReadyToEnhance/` and the second on the enhanced file it has just written. Passing `None`
as the target resolution instructs the function to leave the file untouched and merely report its
size and aspect-ratio label, so that no crop, no resampling and no archival copy are produced. This
is correct by construction rather than by coincidence, since every input to this pipeline is a
first-pipeline output and is therefore already at 1024 × 1024, already aligned to the resolution the
model returns natively for a square request. The label forwarded to the API is again `"1:1"`, and,
exactly as in the first pipeline, the generated image is resampled to 1024 × 1024 at save time only
in the event that it comes back at a different size.

**Step 1 — Beauty enhancement (`process_image_enhancement`).** For each input file the pipeline
issues a single API call carrying the `ENHANCEMENT_PROMPT` and saves the result as
`Output_images/Enhanced/{stem}E.png` — so `FC2_H.png` yields `FC2_HE.png` and `FC2_MH.png` yields
`FC2_MHE.png`. The prompt instructs the model to produce a hyper-beautified version of the same
person: an idealised representation pushing beauty optimisation beyond what is typically
attainable in ordinary humans, explicitly benchmarked against the aesthetic logic of top-tier AI
virtual influencers, while remaining credible and avoiding any uncanny, plastic, doll-like or
grotesque appearance. The optimisation targets are not left to the model's discretion but are
specified feature by feature against the Western beauty canon, and they are sex-differentiated.

In the female variant the prompt maximises facial symmetry, refines and slims the jawline into a
soft V-shape, elevates and defines the cheekbones, refines the nose and its tip, enlarges and
brightens the eyes with long full lashes, lifts the eyebrows into a harmonious arch, produces
fuller lips with a clear cupid's bow, and renders flawless, poreless yet natural-looking skin;
these targets are framed explicitly as an application of averageness, sexual dimorphism and neoteny
cues, applied with restraint so as to remain believable. The male variant pursues the same logic
against the corresponding canon: it sharpens the jawline into a strong angular shape with a defined
gonial angle, refines the chin projection, defines masculine cheekbone hollows, refines the nasal
bridge and tip, emphasises the brow ridge, brightens the eyes without enlarging them or drawing
attention to the lashes, shapes fuller and straighter brows, defines the lips without enlarging
them, retains a credible level of male skin micro-texture, and grooms any existing facial hair
without adding or removing it, invoking averageness, masculine dimorphism cues and a slightly
higher facial width-to-height ratio. Because several of the female targets would read as
feminisation if applied to a male face, the male prompt closes with a dedicated block of negative
constraints prohibiting precisely those features: a soft V-shaped jaw, enlarged eyes, visible
lashes, fuller-than-natural lips, over-arched brows and neotenous proportions.

Beyond these differences the two variants impose an identical preservation block. Identity must
remain clearly recognisable as the same individual, and head pose, gaze direction, framing, crop,
background, lighting setup, clothing, hairstyle, hair colour and hair length must be identical to
the source, the male variant additionally fixing facial-hair style and length. Most consequential
for the design, both prompts require the rendering style to be held constant: if the source is a
photorealistic render the output must remain photorealistic, and if the source carries a stylised
CGI rendering the output must retain exactly that rendering, with an explicit instruction not to
shift it in either direction. It is this requirement that keeps anthropomorphism and beauty
optimisation orthogonal in the resulting stimulus set rather than confounded, since it prevents the
enhancement pass from silently raising or lowering the realism of the image it beautifies.

**Step 2 — Mediumization (`process_medium_style`).** Immediately after step 1, and within the
same loop iteration, the pipeline re-reads the file it has just written
(`Output_images/Enhanced/{stem}E.png`) and issues a second API call carrying
`ENHANCED_MEDIUM_PROMPT1`, saving the result as `Output_images/Enhanced/{stem}EM.png` — so
`FC2_HE.png` yields `FC2_HEM.png` and `FC2_MHE.png` yields `FC2_MHEM.png`. The prompt re-shades
the beauty-enhanced synthetic asset into the Level MEDIUM rendering style, again referencing
*The Polar Express* (2004) as the definitive visual benchmark: skin as a continuous,
slightly-too-smooth mesh with a flat matte-diffuse albedo, no specular highlights and no
subsurface glow, with albedo brightness calibrated so that the face reads at the same overall
exposure level as the source; skin marks re-expressed as flat painted decals with no geometric
relief; hair, eyebrows and facial hair as geometrically thin old-game-engine particle systems.
Its preservation block explicitly includes *the subject's facial attractiveness as it appears in
the source*, which instructs the model to carry the enhancement forward rather than to re-derive
or attenuate it, and it closes with a photometric lock overriding all shader instructions.
Because this stage re-renders an already-enhanced image, it isolates the anthropomorphism factor
at a fixed, elevated level of beauty optimisation.

Each of the two steps verifies the existence of its own destination file before issuing a request,
so the second pipeline is idempotent and resumable in the same way as the first, though at a finer
granularity: an interrupted run resumes at the individual transformation rather than at the subject,
and an enhancement already paid for is never repeated merely in order to obtain the mediumized
version that follows it. The chaining does introduce one dependency, in that step 2 consumes the
file step 1 has just produced; should the enhancement fail, the mediumization finds no input, and
the resulting error is caught so that the subject is skipped and the run proceeds.

**Outputs per subject (4 files):**

```
FC2_HE.png      ← FC2_H.png   beauty-enhanced
FC2_MHE.png     ← FC2_MH.png  beauty-enhanced
FC2_HEM.png     ← FC2_HE.png  mediumized
FC2_MHEM.png    ← FC2_MHE.png mediumized
```

The second pipeline therefore yields 8 subjects × 2 input levels × 2 steps = **32 images per
gender group**, **64 images in total**, all at 1024 × 1024 pixels.

### 3.1.3.5 Complete stimulus set

Every generated filename encodes the full transformation chain applied to its source, so that the
provenance of any stimulus is recoverable from its name alone (Table Z).

**Table Z — Filename suffix taxonomy.**

| Suffix | Meaning | Produced by | Example | *n* |
|---|---|---|---|---|
| *(none)* | Original photograph, standardized to 1024 × 1024 | Standardization stage | `FC2.png` | 16 |
| `_H` | High anthropomorphism | First pipeline | `FC2_H.png` | 16 |
| `_MH` | Medium-high anthropomorphism | First pipeline | `FC2_MH.png` | 16 |
| `_M` | Medium anthropomorphism | First pipeline | `FC2_M.png` | 16 |
| `_HE` | High + beauty enhancement | Second pipeline, step 1 | `FC2_HE.png` | 16 |
| `_MHE` | Medium-high + beauty enhancement | Second pipeline, step 1 | `FC2_MHE.png` | 16 |
| `_HEM` | High + enhanced + **mediumized** | Second pipeline, step 2 | `FC2_HEM.png` | 16 |
| `_MHEM` | Medium-high + enhanced + **mediumized** | Second pipeline, step 2 | `FC2_MHEM.png` | 16 |

All seven generated categories are retained in the final stimulus set; none is discarded. The
complete pool therefore comprises **112 generated stimuli** — seven categories × 16 subjects, each
category complete for every subject — that is, 48 from the first pipeline and 64 from the second,
plus the **16 standardized originals**, for **128 images** available for the pretest, all
at 1024 × 1024 pixels, PNG, on the neutral grey background of the source dataset. Across every
transformation the following attributes are held constant by prompt construction: identity, head
pose, gaze direction, facial expression, camera framing and crop, lighting setup, clothing,
hairstyle and background. The only manipulated variables are (i) the surface rendering style, which
operationalises anthropomorphism, and (ii) the degree of beauty optimisation.

A minimum of 112 billable API calls is required to regenerate the set from the original
photographs, excluding retries and the regeneration of rejected outputs.

---

## Part C — Appendix A: verbatim prompts

*(This is the material flagged as "INSERIRE ANCHE I PROMPTS" in the draft.)*

**Fidelity.** Every string below was extracted programmatically from the source files by parsing
them and evaluating the concatenated literals, then compared word-for-word against this appendix.
A.1–A.5 and A.7 are **identical to the strings actually sent to the API**. A.6 differs in exactly
two places, both editorial and both flagged in the note under that heading. Paragraph breaks
reproduce the `\n\n` separators present in the source literals, with the single exception noted at
A.6.

### A.1 Shared preamble — `locked_context` (first pipeline)

> ROLE: You are an expert image producer specializing in 3D character asset generation.
>
> TASK: Produce a synthetic 3D character asset by re-surfacing a given geometric reference (the base image) with a specified target rendering style — high, medium-high, medium, medium-low, or low anthropomorphism.
>
> BASE INPUT IMAGE: The base image is the canonical source of TWO things and only the SHADER is allowed to change:
> (a) GEOMETRIC IDENTITY — facial structure, hair, accessories, clothing, pose, framing.
> (b) PHOTOMETRIC BLUEPRINT — light direction, shadow positions and shadow softness, exposure value (EV), white balance, and the neutral grey background.
> The transformation re-renders the SURFACE SHADER on top of this blueprint. The shader is the only variable.
>
> IDENTITY LOCK: The following attributes must be preserved exactly and never altered, only re-rendered through the target shader:
> - Facial geometry: every feature's spatial coordinates, proportions, asymmetries, and bone structure.
> - Skin character: every freckle, mole, scar, pimple, abrasion, uneven pigmentation – these must be preserved as micro-features in the new shader.
> - Hair: exact hairline, parting, length, density, color, eyebrow shape and density, eyelashes, beard/stubble pattern, fine peach fuzz. The original pixels for hair must be re-rendered with digital shaders.
> - Accessories: every earring, piercing, hair clip, glasses, necklace, garment item – maintain the same geometry, placement, and color.
> - Identity attributes: apparent age, gender, ethnicity, and the subject's inherent facial attractiveness – these must be held constant across all levels.
>
> COMPOSITION LOCK: The following aspects must be preserved exactly:
> - Pose, head tilt, gaze direction, facial expression.
> - Camera framing, crop, distance, aspect ratio.
> - Clothing geometry, color, and spatial arrangement.
>
> PHOTOMETRIC LOCK — preserve exactly (no level may override this):
> - Light direction and angle: identical to the base image.
> - Shadow positions, shapes, edges, and softness: identical to the base image.
> - Exposure Value (EV) and overall brightness: identical to the base image — the output histogram should match the input histogram in mid-tone placement and highlight roll-off.
> - White balance and color temperature: identical to the base image.
> Only the SHADER's *response* to this fixed lighting is allowed to change between levels. The lighting rig itself does not move, soften, harden, brighten, or darken.
>
> BACKGROUND LOCK — uniform neutral grey background #C8C8C8, perfectly flat, edge-to-edge, identical to the base image.
>
> VARIABLE: only the SHADING MODEL and SURFACE RENDERING are allowed to change between levels. Light direction is locked; how that light interacts with the skin is dictated by the target style.
>
> INSTRUCTION:
> 1. Treat the subject in the provided base image as a 3D digital mesh.
> 2. You MUST re-surface this mesh using a synthetic-digital rendering engine.
> 3. SURFACE PROTOCOL: Re-render every surface (skin, hair, fabric) using digital shaders. The final result must be a synthetic-digital reconstruction.
>
> TARGET RENDER STYLE:

### A.2 Level HIGH (`_H`)

> RENDER STYLE — Level HIGH (Midjourney-v5 signature / AI-generated virtual-influencer asset):
> Render as a hyper-detailed virtual-influencer asset in the signature look of high-end generative AI portraits. Every pore, freckle, mole, and skin imperfection from the base image is RE-RENDERED into ultra-sharp, algorithmically over-traced micro-relief - the way raw generative-AI portraits exhibit impossible micro-clarity. Skin carries a synthetic sheen on the highlight side, with unnaturally even local contrast across mid-tones and a noticeable plasticity. Eyes are glassy and over-specular, irises mathematically circular and over-detailed, original eye color preserved. All natural edges — hair strands, eyelashes, lip line — are algorithmically over-sharpened, detailed and shiny, preserving the original constraints. The surface reads as 'too perfectly detailed to be a photograph': the fingerprint of a high-end synthetic asset.

### A.3 Level MEDIUM-HIGH (`_MH`)

> RENDER STYLE — Level MEDIUM-HIGH (AAA Video Game Asset Reconstruction):
> Render the subject as a 3D playable character for a real-time engine (skin aesthetics of Uncharted 4 characters). Replicate the exact Exposure Value (EV) of the base image. SURFACE PROTOCOL: Treat the skin as a 'Synthetic PBR Material'. The skin is rendered as a opaque 'Matte-Plastic' texture, rejecting biological softness. TEXTURE MAPS: Render the surface using evident diffuse-dominant albedo and normal maps. Details must be rendered as mathematically generated digital noise, not organic skin. SHADING: Apply a 'Hard-Clamped Subsurface Scattering' effect to create an opaque, waxy appearance typical of sculpted digital assets. HAIR & EYES: Render hair, eyebrows, and any facial hair as geometrically thin high-end Game-Engine Particle Systems: distinct, geometrically clean alpha cards with baked specular highlights. Eyes must have static, pre-rendered reflections. LIGHTING: Use 'Directional Rim Lighting' to express the 3D topology and volume of the mesh. The result must be an unmistakable, high-poly real-time game character render.

### A.4 Level MEDIUM (`_M`)

> RENDER STYLE — Level MEDIUM (Early-2000s Cinematic CGI / Uncanny Valley):
> Render in the aesthetic of The Polar Express (2004) or early performance-capture cinema, but replicate the exact Exposure Value (EV) of the base image. Skin is waxy like a soft silicone mask or polished candle wax. The face is one continuous, slightly-too-smooth 3D mesh with a flat diffuse texture pass for marks and imperfections — they read as painted onto the surface rather than emerging from it. Render hair, eyebrows, and any facial hair as geometrically thin Old-Game-Engine Particle Systems. Lighting is flat, lacks realistic bounce-light, and produces shadows that fall slightly too softly. The result sits in the uncanny valley: clearly synthetic, clearly attempting realism, clearly not alive.

### A.5 Beauty enhancement — FEMALE (`ENHANCEMENT_PROMPT`, `second-generating-female-London.py`)

> Using the attached image as the exact source, generate a hyper-beautified version of the same person — an idealized representation that pushes beauty optimization to a level beyond what is typically achievable in ordinary humans, comparable to top-tier AI virtual influencers (e.g., Aitana Lopez, Lil Miquela aesthetic logic). The result must remain credible and avoid any uncanny-valley, plastic, doll-like, or grotesque appearance.
>
> Beauty optimization (Western beauty canon): maximize facial symmetry; refine and slim the jawline into a soft V-shape; elevate and define cheekbones with subtle hollows; straighten and refine the nose with a delicate, well-defined tip; enlarge and brighten the eyes with crisp iris definition, long full lashes, and an alert, captivating gaze; lift and shape the eyebrows into a clean, harmonious arch; fuller, well-defined lips with a clear cupid's bow; flawless, poreless yet natural-looking skin with even tone, healthy radiance and a subtle glow; remove any blemish, asymmetry, or imperfection; idealize overall facial proportions following the canonical Western standard of female attractiveness (averageness + sexual dimorphism + neoteny cues, applied with restraint to stay believable).
>
> Strict preservation (do NOT change): identity must remain clearly recognizable as the same individual; head pose, gaze direction, framing, crop, background (neutral grey, identical to the source), lighting setup, clothing, hairstyle, hair color, hair length must be identical to the source; critically, preserve the exact same rendering style and level of photorealism/anthropomorphism as the source image — if the source looks photorealistic, the output must look photorealistic; if the source has a stylized/CGI/synthetic rendering, the output must keep that exact same stylized/CGI/synthetic rendering. Do not shift the rendering style in either direction.
>
> Negative constraints: no plastic skin, no doll-like or mannequin appearance, no exaggerated anime-like eyes, no over-smoothed wax texture, no facial distortion, no change of ethnicity, no change of age range, no different person.
>
> Output: a hyper-optimized but credible 'more beautiful version of the same person in the same photo, in the same rendering style'.

### A.6 Beauty enhancement — MALE (`ENHANCEMENT_PROMPT`, `second-generating-male-London.py`)

> **Note on two junctions.** Unlike the female prompt, the male prompt carries **no separator at
> all** at two sentence boundaries: adjacent Python literals concatenate directly, so the string
> actually sent to the API reads `…in either direction.Negative constraints:…` and
> `…relative to the source.Output:…`, with no space or line break. The female prompt (A.5) has
> `\n\n` at both equivalent points. The paragraph breaks shown below are editorial, inserted for
> legibility; everything else is verbatim.

> Using the attached image as the exact source, generate a hyper-beautified version of the same person — an idealized representation that pushes beauty optimization to a level beyond what is typically achievable in ordinary men, comparable to top-tier male AI virtual influencers and to the aesthetic logic of hyper-optimized male synthetic models. The result must remain credible and avoid any uncanny-valley, plastic, doll-like, mannequin, or grotesque appearance.
>
> Beauty optimization (Western male beauty canon): maximize facial symmetry; sharpen and define the jawline into a strong, angular, well-defined shape with a clean mandibular line and a defined gonial angle; refine the chin with subtle prominence and a balanced projection; elevate and define cheekbones with clean, masculine hollows; straighten and refine the nose with a well-proportioned bridge and a clean, defined tip (no delicate or upturned tip); subtly emphasize a refined brow ridge consistent with masculine sexual dimorphism; brighten the eyes with crisp iris definition, clear whites, and an alert, confident gaze (no lash emphasis, no enlargement); shape the eyebrows into a clean, well-groomed, naturally masculine line — fuller, straighter, not over-arched; define the lips with clear, balanced contours and a well-formed shape — proportionate to the face, not enlarged and without an exaggerated cupid's bow; clear, healthy skin with even tone, natural radiance, and a subtle, credible male skin texture (not waxy, not over-smoothed, retaining a believable level of micro-texture); preserve any existing facial hair (stubble, beard, mustache) exactly as in the source but groom it to appear cleaner, denser where present, and more defined in its outline; idealize overall facial proportions following the canonical Western standard of male attractiveness (averageness + masculine sexual dimorphism cues — pronounced jaw, chin, cheekbones, refined brow — and a slightly higher facial width-to-height ratio, all applied with restraint to stay believable).
>
> Strict preservation (do NOT change): identity must remain clearly recognizable as the same individual; head pose, gaze direction, framing, crop, background (neutral grey, identical to the source), lighting setup, clothing, hairstyle, hair color, hair length, facial hair style and length must be identical to the source; critically, preserve the exact same rendering style and level of photorealism/anthropomorphism as the source image — if the source looks photorealistic, the output must look photorealistic; if the source has a stylized/CGI/synthetic rendering, the output must keep that exact same stylized/CGI/synthetic rendering. Do not shift the rendering style in either direction.
>
> Negative constraints: no plastic or waxy skin, no doll-like or mannequin appearance, no feminized features (no soft V-shape jawline, no enlarged eyes, no exaggerated or visible lashes, no fuller-than-natural lips, no over-arched or thinned brows, no neotenous proportions), no facial distortion, no change of ethnicity, no change of age range, no different person, no removal or addition of facial hair relative to the source.
>
> Output: a hyper-optimized but credible "more handsome version of the same person in the same photo, in the same rendering style."

### A.7 Mediumization (`ENHANCED_MEDIUM_PROMPT1`, identical in both second-pipeline scripts)

> Using the attached image as the exact source, re-shade this synthetic character asset into the Level MEDIUM rendering style: mid-2000s cinematic CGI in the exact visual aesthetic of The Polar Express (2004) — the definitive reference for this style.
>
> SURFACE SHADER: the skin is rendered as a continuous, slightly-too-smooth 3D mesh surface with a flat diffuse albedo — soft, uniform, and waxy like polished candle wax. The surface is matte and diffuse, carrying no specular highlights and no sub-surface glow. The albedo brightness is calibrated so that the face reads at the same overall exposure level as the attached image. Any skin marks visible in the source are re-expressed as flat painted decals with no geometric relief. The skin reads as one continuous poured surface with no visible pore structure or micro-normal variation. Hair, eyebrows, and any facial hair are rendered as geometrically thin Old-Game-Engine Particle Systems. The overall result sits in the uncanny valley: clearly synthetic, clearly attempting human realism, clearly not alive.
>
> PRESERVE FROM SOURCE (keep exactly as in the attached image): the subject's identity and all facial features — facial geometry, proportions, jawline, cheekbones, nose, eyes, eyebrows, and lips; apparent age, gender, and ethnicity; the subject's facial attractiveness as it appears in the source; hairline, parting, length, density, and color; all accessories and clothing in their exact spatial coordinates and colors; head pose, head tilt, gaze direction, neutral closed-mouth expression; camera framing, crop, distance, and aspect ratio.
>
> PHOTOMETRIC LOCK (overrides all shader instructions): the light direction, shadow positions, shadow softness, exposure value, and white balance of the attached image are reproduced exactly. Shadow intensity, coverage, and spread remain within the bounds visible in the source. The background is a uniform neutral grey (#C8C8C8), perfectly flat and edge-to-edge, identical to the source.

---

## Appendix B — Verified technical parameters

| Parameter | Value | Source |
|---|---|---|
| SDK | `google-genai` (Google AI Python SDK), imported as `from google import genai` | all scripts |
| Client | `genai.Client(vertexai=True, api_key=api_key)` | all scripts |
| Production model | `gemini-3-pro-image-preview` (read from `.env` as `GEMINI_MODEL`) | `.env`, `load_config()` |
| Exception model | `gemini-3.1-flash-image-preview` for `FT1_HEM`, `MC1_HE`, `MC1_HEM`, `FC3_MHEM` | README; applied by editing `.env` |
| Fallback model | `DEFAULT_MODEL = "gemini-2.5-flash-image-preview"` — used only if `GEMINI_MODEL` is unset; never active in production | `constants.py:29` |
| Response modalities | `[Modality.TEXT, Modality.IMAGE]` | all scripts |
| Aspect ratio | `"1:1"`, derived from `get_supported_aspect_ratio(1024, 1024)` | all three London scripts |
| `image_size` | In production, `"2K"` only for images affected by graininess; native 1K otherwise. In the current source the literal is unconditional (see D1); **absent from the CFD scripts** | all three London scripts |
| Source resolution | 1350 × 1350 px, RGB (verified on all 16 files) | disk |
| `INPUT_RESOLUTION` | `compute_gemini_1k_for_input(1350, 1350)` → **(1024, 1024)** | `constants.py:84` |
| Crop method | `PIL.ImageOps.fit()`, `centering=(0.5, 0.5)`, `Image.Resampling.LANCZOS` | `standardize_input_image()` |
| Output resolution | 1024 × 1024 px, PNG (verified on all 112 generated files) | disk |
| Down-resample method | `Image.resize(..., Image.Resampling.LANCZOS)` | all scripts |
| `MAX_IMAGES` | 16 (first pipeline only; no cap in second pipeline) | `constants.py:23` |
| `MAX_RETRIES` | 3 total attempts (initial + 2 retries) | `constants.py:24` |
| Back-off | `RETRY_BASE_DELAY_SECONDS = 1.5`, doubling → waits of 1.5 s and 3.0 s | `constants.py:27` |
| Accepted extensions | `.png`, `.jpg`, `.jpeg` | `constants.py:26` |
| Levels generated | `LEVELS_3 = ["high", "medium_high", "medium"]` | `constants.py:32` |
| Levels enhanced | `ENHANCED_LEVELS_SIGLE = {"high": "H", "medium_high": "MH"}` | `constants.py:93` |
| Integrity check | `PIL.Image.verify()` on every saved file | `verify_saved_image()` |
| Style references | Inactive — no file matches the `reference_{level}` pattern | `Images/StyleRefImages/` |
| Minimum API calls | 48 (first pipeline) + 64 (second pipeline) = **112** | derived |

**Folder inventory as verified on disk:**

| Folder | Files | Resolution | Role |
|---|---|---|---|
| `Images/LondonDataset/ExperimentalDataset/` | 16 | 1350 × 1350 | First-pipeline input (renamed subjects) |
| `…/ExperimentalDataset/ExperimentalDataset_origin/` | 16 | 1350 × 1350 | Archive of the original London filenames |
| `Images/StandardizedImages/` | 16 | 1024 × 1024 | Cropped inputs actually sent to the API |
| `Output_images/` | 48 | 1024 × 1024 | First-pipeline outputs (`_H`, `_MH`, `_M`) |
| `Output_images/ReadyToEdit/` | 48 | 1024 × 1024 | Manual colorimetric correction stage |
| `Output_images/ReadyToEnhance/Female/` | 16 | 1024 × 1024 | Second-pipeline input, 8 female subjects × 2 levels |
| `Output_images/ReadyToEnhance/Male/` | 16 | 1024 × 1024 | Second-pipeline input, 8 male subjects × 2 levels |
| `Output_images/Enhanced/` | 64 | 1024 × 1024 | Second-pipeline outputs (`_HE`, `_MHE`, `_HEM`, `_MHEM`) |

---

## Part D — Discrepancies found (NOT for the Word document)

These are the points where the README, the current draft, or `CLAUDE.md` did not match the code or
the files on disk. Each is already corrected in Part B.

> **Status of `README.md`:** all items below have since been **corrected in `README.md`**, which
> was rewritten against the code and the folder contents. Where an item quotes the README, the
> quotation is the *former* wording, retained here so the change is traceable. What remains open
> is D1 (a decision about the code, not the documentation), D2 (a figure to recompute) and D7
> (a design decision about the pretest). `CLAUDE.md` has **not** been updated — see D8.

### D1 — 2K was applied selectively in production, but the line was left unconditional in the code

**The production history is as stated in the draft:** `image_size = "2K"` was requested only for
the images that came back grainy from the model's post-generation sharpening; everything else was
generated at native 1K. Nothing below contradicts that — the point is only that the code no longer
records it, so the paper cannot cite the source as evidence for the claim.

In the committed code, `image_size = "2K"`
is a hard-coded literal inside `generate_with_retry` in **all three** London scripts
(`main-generating-v5London.py:287`, `second-generating-female-London.py:191`,
`second-generating-male-London.py:191`). There is no conditional branch. It is also **absent from
all three CFD scripts**, whose `ImageConfig` carries only `aspect_ratio` — corroborating that the
parameter was a late, London-only addition rather than a designed feature of the pipeline.

The git history corroborates the selective use: the flag appears only in the **final** commit,
`266645a` "Final Generation: added image_size = '2K' for image generation (Gemini)" (2026-05-22),
*after* the bulk of the set had already been produced (commit `efc1f5a`, "Finish generation
(London Dataset)", 2026-05-20). File modification times agree: 46 of the 48 first-pipeline outputs
and 63 of the 64 enhanced outputs pre-date 22 May.

**What this means for the paper.** The claim is safe to make — it is the author's account of what
was done, and the history is consistent with it. What the repository cannot supply is the *list* of
which stimuli were regenerated at 2K: the parameter was left unconditional, so the source no longer
distinguishes them, and file timestamps only narrow the candidates to three (`FC1_M.png`,
`FC2_M.png`, `Enhanced/MC4_MHEM.png`, all 2026-05-22). If a reviewer asks which images those were,
the answer has to come from your own records, not from the code. Two practical follow-ups:
comment out or gate the line before any future re-run, and recompute the cost figure (D2) if the
2K images are numerous enough to matter.

### D2 — Cost per image

`CLAUDE.md` and the pipeline docstrings state ≈ **$0.039 per generated image**, which is the
published rate for outputs up to 1024 × 1024 (1290 tokens). With `image_size="2K"` requested the
billed output token count is higher, so the figure understates the cost of any image generated
after commit `266645a`. Recompute before quoting a total budget in the paper.

### D3 — The `#C8C8C8` background is nominal, not measured

Both the `locked_context` and `ENHANCED_MEDIUM_PROMPT1` specify a *"uniform neutral grey
background #C8C8C8, perfectly flat, edge-to-edge"*. The actual London backdrop is neither flat nor
#C8C8C8: measured on the standardized `FC1`, it reaches ≈ (201, 205, 206) at the mid-left edge and
(204, 208, 209) at the mid-right edge — close to #C8C8C8 — but falls to ≈ (161, 167, 167) in the
top corners, i.e. it carries a pronounced vignette. It also has a slight cool cast: averaged over
the 16 subjects the top-centre patch measures (196.4, 200.4, 199.7), with green and blue exceeding
red by ≈ 3–4 levels. The instruction that actually governs is the
adjacent *"identical to the base image"* clause; the hex value is a nominal descriptor of the
brightest region only. This does not invalidate anything — but do not write in the paper that the
source background *is* #C8C8C8.

### D4 — The README omits the `ReadyToEdit` curation stage

The README's "Preparation step (manual)" says only that the researcher moves `_H`/`_MH` outputs
into `ReadyToEnhance/`. It never mentions `Output_images/ReadyToEdit/`, which is where the manual
exposure/tint correction happens and which is the actual provenance of every file in
`ReadyToEnhance/`. This is verifiable: all 32 files in `ReadyToEnhance/` are byte-identical to
their `ReadyToEdit/` counterparts. Since this stage is a genuine methodological step (it is the
control for the colorimetric drift documented in §3.1.3.2), it belongs in both the README and the
paper. Section 3.1.3.3 of Part B supplies the text.

Scale of the intervention, for the record: 3 of the 48 renders (`MC2_M`, `MT3_MH`, `MT4_M`)
differ in pixel content from their raw counterparts, with maximum full-frame per-channel deltas of
3, 1 and 8 levels out of 255 respectively — global tonal curves, not local retouching. One file,
`FC3_M`, carries an alpha channel in `Output_images/`, indicating it was round-tripped through
the editor and copied back.

### D5 — Style reference images: right conclusion, wrong reason

The README says the style-reference path returns `None` because *"no reference images are
present"*. `Images/StyleRefImages/` in fact contains ten files (`referenceH.jpg`, `referenceH2.png`,
`referenceL.jpeg`, `referenceM.jpeg`, `referenceMH.avif`, `referenceMH.png`, `referenceMH2.jpg`,
`referenceMH2.png`, `referenceMH3.png`, `referenzeML.jpg`). None of them matches the pattern the
code looks for — `get_style_reference_image()` requires the stem to equal exactly
`reference_{level}`, i.e. `reference_high`, `reference_medium_high`, `reference_medium`. The
outcome is the same (no style image is ever attached), but the mechanism is a naming mismatch,
not an empty folder. Part B is worded accordingly.

### D6 — Retry count

The README says *"Retries up to `MAX_RETRIES = 3` times"*. `for attempt in range(1, MAX_RETRIES + 1)`
gives **3 attempts in total** — the initial call plus two retries — with sleeps of 1.5 s and 3.0 s.
The final attempt is followed by no sleep. Minor, but stated correctly in Part B.

### D7 — Stimulus counts: production (128) vs. pretest design (96)

§3.1.5 of the proposal budgets *"16 (original) + 16 × 3 (3 levels of Anthrop) + 16 × 2 (two levels
of enhancement) = 96 images"* to be rated. Production actually yielded **128** distinct images
(16 originals + 48 + 64), because the enhancement branch produces **four** variants per subject
(`_HE`, `_MHE`, `_HEM`, `_MHEM`), not two.

**Resolved.** The retained stimulus set has since been confirmed as **all seven generated
categories** — `H`, `HE`, `HEM`, `M`, `MH`, `MHE`, `MHEM` — with nothing discarded. This was
verified against disk: each of the seven categories is present for all 16 subjects, with no
missing subject and no additional category, giving exactly 7 × 16 = **112 generated stimuli**,
plus the 16 standardized originals = **128**.

The `= 96` arithmetic in §3.1.5 is therefore **superseded and must be corrected**, along with
everything downstream of it. Recomputed on the same assumptions the proposal uses (20 ratings per
image, 12 images per participant):

| | Proposal §3.1.5 | Actual production |
|---|---|---|
| Images to rate | 96 | **128** |
| Evaluations required (× 20) | 1 920 | **2 560** |
| Participants (÷ 12) | 160 | **≈ 214** |

If the participant budget is fixed at 160, the alternative levers are to raise the number of images
each participant rates (2 560 ÷ 160 = **16 images per participant**) or to lower the target of 20
ratings per image. Both are design decisions; the image count itself is now settled.

### D8 — Minor code/documentation drift (no impact on the paper)

- `process_one_image()`'s docstring still says *"Generate all five anthropomorphism variants"*;
  the loop iterates `LEVELS_3` (three).
- `get_test_enhanced_images()` in both second-pipeline scripts still hard-codes Chicago Face
  Dataset stems (`CFD-WF-233-112-N_high`); it is dead code in the London runs — `main()` never
  calls it.
- `constants.py` defines both `RETRY_BASE_DELAY = 5` (unused) and
  `RETRY_BASE_DELAY_SECONDS = 1.5` (used).
- The block-detection line `if reason and "IMAGE" in str(reason) or "SAFETY" in str(reason)`
  parses as `(reason and "IMAGE" in …) or ("SAFETY" in …)` because `and` binds tighter than `or`.
  It happens to behave acceptably, but it is not what the comment describes. Note also that the
  substring test is broader than the two values it appears to target: against the real
  `types.FinishReason` members, `"IMAGE"` also matches `IMAGE_PROHIBITED_CONTENT` and `NO_IMAGE`.
  That is benign — all three are cases where no usable image was returned — but it is incidental,
  not designed.
- `clean-background.py` (rembg-based segmentation onto a flat (200, 200, 200) plate) exists in the
  repository but was **not** used for the London production: its destination folder
  `Output_images_clean/` does not exist. Do not describe it as part of the pipeline.
- `CLAUDE.md` states that `get_supported_aspect_ratio()` lives in `ProveImg.py`; the London scripts
  each define their own local copy.

### D9 — `get_supported_aspect_ratio()` is recomputed per image, but is invariant

Not an error, and no impact on the stimuli — recorded because the paper prose (Part B, stage 2)
describes the label as "derived by `get_supported_aspect_ratio(1024, 1024)`", and it is worth
knowing that this is a constant rather than a per-image decision.

`standardize_input_image()` contains four call sites. With `target_resolution` supplied (first
pipeline) only the last two are reachable for London: the `target_resolution is None` branch cannot
be taken, and neither can the `source_image.size == target_resolution` branch, since every source
is 1350 × 1350 against a 1024 × 1024 target. Both reachable sites pass exactly `target_resolution`,
so the value returned is always `get_supported_aspect_ratio(*INPUT_RESOLUTION)`. With
`target_resolution = None` (second pipeline) the label is read from the actual file. **Verified:**
the label is `"1:1"` on all 48 first-pipeline calls and all 64 second-pipeline calls.

The function is not eliminable — `ImageConfig.aspect_ratio` accepts only the ten label strings,
never a pixel pair — so the observation concerns *when* it is called, not *whether* it is needed.
Deriving it from `INPUT_RESOLUTION` rather than from the source is also the more robust choice,
since the standardized image is what is actually transmitted: for London the two agree exactly
(1.00000 → `1:1`), while for CFD the source ratio 1.42258 separates `3:2` from `4:3` by only
0.012, against 0.148 for the standardized 1.49057.

### D10 — The male enhancement prompt is missing two separators the female one has

Verified by parsing both files and evaluating the literals. At two sentence boundaries the male
`ENHANCEMENT_PROMPT` concatenates adjacent Python string literals with no whitespace between them,
so the text transmitted to the API contains `direction.Negative constraints:` and
`source.Output:` — words run together across a full stop. The female prompt has an explicit `\n\n`
at both equivalent points (`…in either direction.\n\n"` and `…no different person.\n\n"`).

The consequence is presentational rather than semantic, and there is no evidence in the outputs
that it changed anything — the male stimuli are complete and were accepted. But it is a real
asymmetry between two prompts that the design otherwise treats as parallel instruments differing
only in beauty canon, and it is the kind of detail a reviewer reading Appendix A will notice.
Two one-character fixes in `second-generating-male-London.py` (adding `\n\n` before `"Negative`
and before `"Output:`) would remove it; note that doing so changes the prompt string and therefore
would not reproduce the delivered stimuli byte-for-byte.
