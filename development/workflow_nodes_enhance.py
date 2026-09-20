"""Prompt-enhance and music encyclopedia rows.

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_lib import _n, _s, _w

def enhance_nodes() -> dict[str, Any]:
    """Prompt-enhance, join, cinema, sample, lyrics, album.

    Returns:
        Node specs keyed by type.
    """
    nodes: dict[str, Any] = {}
    # ez_prompt_enhance
    nodes["EZKleinPromptEnhance"] = _n(
        "Klein Prompt Enhance",
        "Rewrite a lazy still/edit prompt for Klein 4B with on-box Qwen3-4B-Instruct.",
        origin="ez_prompt_enhance",
        lab="Enhance on for lazy CLIP printers; off for authored recipes. Style ignored when it would fight an I2V start frame (not used here). Occupancy llm for the GGUF, then klein for the UNET.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional override of the widget (usually unwired)."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "String CLIP actually encodes."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Lab sample prompt or Custom.", gen="Custom keeps the textarea. Picking a sample fills and locks the Prompt. The App dropdown lists this graph's 20 recipes plus Custom (place recipes such as Cliff villa on stills/dream-house)."),
            _w("prompt", index=1, desc="Lazy sentence or authored still prompt.", gen="When Enhance is on, the GGUF expands this into Klein-native sentences."),
            _w("enhance", index=2, typ="BOOLEAN", rng="on for lazy printers", desc="Run the rewriter.", gen="Off = encode the widget as-is (plus style suffix if set)."),
            _w("mode", index=3, typ="COMBO", rng="t2i / edit / identity / text_swap", desc="System prompt flavor.", gen="t2i = new still. edit = change an existing still. identity = camera-free bible (identity-sheet). text_swap = glyph-lock lettering on a source still.", choices=[("t2i", "New still."), ("edit", "Klein-edit / clay / tweak."), ("identity", "Camera-free identity bible."), ("text_swap", "Replace lettering; source still owns look and size.")]),
            _w("duration_hint", index=4, desc="Framing hint (YouTube 16:9 still, Instagram 4:5, …).", gen="Steers aspect language in the rewrite. Does not set the latent size — EmptyFlux2LatentImage does."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference woven into the CLIP prompt.", gen="none = off. Dropdown wins over style words already in the source. Hidden on I2V graphs.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id (graph stem).", gen="Internal. Leave as stamped so sample dropdowns resolve."),
        ],
    )
    nodes["EZWanPromptEnhance"] = _n(
        "Wan Prompt Enhance",
        "Rewrite a lazy prompt for Wan 2.2 TI2V-5B (silent).",
        origin="ez_prompt_enhance",
        sockets=[
            _s("prompt", "STRING", "in", "Optional."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "Motion string for CLIP."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy motion sentence.", gen="I2V rewrites to motion + one camera only. Do not prompt audio — Wan is silent."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off on authored camera-verb graphs (orbit, push-in, gif-loop)."),
            _w("mode", index=3, typ="COMBO", desc="System flavor.", gen="i2v is the smoke. t2v when LoadImage is bypassed. flf / vace / s2v for those opt-in graphs.", choices=[("t2v", "Text to silent video."), ("i2v", "Start image owns look; prompt is motion."), ("flf", "First-last-frame."), ("vace", "VACE join."), ("s2v", "Speech-to-video; wav owns lip-sync.")]),
            _w("duration_hint", index=4, rng="5 seconds, 24 fps", desc="Duration/fps hint for the rewriter.", gen="Does not change latent length — Wan22ImageToVideoLatent does."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference. Ignored on I2V.", gen="Start frame owns look on I2V.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZLTXPromptEnhance"] = _n(
        "LTX Prompt Enhance",
        "Rewrite a lazy prompt for LTX-2.5 (present-tense paragraph, audio interleaved).",
        origin="ez_prompt_enhance",
        lab="Off on 90s films, talking-head, authored showcase. On for generic 5 s printers.",
        sockets=[_s("prompt", "STRING", "out", "Paragraph CLIP encodes.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy sentence or authored LTX paragraph.", gen="I2V: start image holds look; prompt is motion + world SFX. Dialogue belongs in \"quotes\" only if you asked for speech."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off keeps authored film/shot text pinned."),
            _w("mode", index=3, typ="COMBO", desc="t2v vs i2v vs iclora system prompt.", gen="i2v when a start still is wired. iclora describes look, not the control type.", choices=[("t2v", "Text to AV."), ("i2v", "Start still owns look."), ("iclora", "Union Control look/materials; guide owns blocking.")]),
            _w("duration_hint", index=4, rng="5 seconds, 24 fps", desc="Duration hint.", gen="Does not set 121 frames — LTXVImgToVideo does."),
            _w("audio_notes", index=5, desc="World SFX / no-score policy.", gen="Lab 5 s printers ask for world SFX matching the start image, no score."),
            _w("style", index=6, typ="COMBO", rng="none", desc="Look reference. Ignored on I2V.", gen="Start frame owns look.", choices_from="styles"),
            _w("catalog", index=7, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZNegativePromptEnhance"] = _n(
        "Negative Prompt Enhance",
        "Rewrite a negative CLIP seed so it does not fight the positive.",
        origin="ez_prompt_enhance",
        sockets=[
            _s("positive", "STRING", "in", "Positive CLIP string as context."),
            _s("prompt", "STRING", "out", "Negative string."),
        ],
        widgets=[
            _w("prompt", index=0, desc="Negative seed (artifacts, not style).", gen="FLUX-family models do not use negatives well. Keep this short; put constraints in the positive."),
            _w("enhance", index=1, typ="BOOLEAN", desc="Rewrite using the positive as context.", gen="Stops canned 'illustration / Pixar' terms from fighting a cartoon-positive."),
            _w("family", index=2, typ="COMBO", desc="Which negative family.", gen="Must match the UNET on the canvas.", choices=[("klein", "Klein stills."), ("wan", "Wan silent."), ("ltx", "LTX AV."), ("zimage", "Z-Image Turbo (CFG 1; list is documentation)."), ("longcat", "LongCat-Video."), ("dreamx", "DreamX-Creator AV."), ("s2v", "Wan S2V; wav owns speech.")]),
        ],
    )
    nodes["EZZimagePromptEnhance"] = _n(
        "Z-Image Prompt Enhance",
        "Rewrite a lazy still prompt for Z-Image Turbo (Qwen3-4B chat wrap).",
        origin="ez_prompt_enhance",
        lab="Turbo ignores a separate negative CLIP. Exclusions stay in the positive. No z_image_turbo UNET on lab graphs.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional override of the widget."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "String CLIP actually encodes."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Lab sample prompt or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy sentence or authored still prompt.", gen="When Enhance is on, the GGUF expands this into Z-Image sentences with in-prompt constraints."),
            _w("enhance", index=2, typ="BOOLEAN", rng="on", desc="Run the rewriter.", gen="Off = encode the widget as-is (plus style suffix if set)."),
            _w("duration_hint", index=3, desc="Framing hint (YouTube 16:9 still, …).", gen="Steers aspect language. Does not set the latent size."),
            _w("style", index=4, typ="COMBO", rng="none", desc="Look reference woven into the CLIP prompt.", gen="none = off. Dropdown wins over style words already in the source.", choices_from="styles"),
            _w("catalog", index=5, desc="Sample-catalog id (graph stem).", gen="Internal. Leave as stamped."),
        ],
    )
    nodes["EZLongCatPromptEnhance"] = _n(
        "LongCat Prompt Enhance",
        "Rewrite a lazy prompt for LongCat-Video (T2V / I2V / continuation).",
        origin="ez_prompt_enhance",
        lab="No native audio. Standard CFG ~4; distilled CFG 1 ignores negatives. Optional stub preview on optional/longcat-video.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "Motion string for CLIP."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy motion sentence.", gen="T2V is scene+motion+camera. I2V extends the still. vc continues previous frames."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off pins the widget text."),
            _w("mode", index=3, typ="COMBO", desc="System flavor.", gen="t2v on the stub. i2v / vc when start frames exist.", choices=[("t2v", "Text to video."), ("i2v", "Start image owns look."), ("vc", "Continue previous frames.")]),
            _w("duration_hint", index=4, rng="5 seconds, 30 fps", desc="Duration/fps hint for the rewriter.", gen="Does not change latent length."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference. Ignored on I2V/vc.", gen="Start frames own look on I2V/vc.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZDreamXPromptEnhance"] = _n(
        "DreamX Prompt Enhance",
        "Rewrite a lazy first-frame+text prompt for DreamX-Creator (UMT5, joint AV).",
        origin="ez_prompt_enhance",
        lab="First frame owns look. Paragraph is visual dynamics plus interleaved acoustic events. No DreamX UNET on lab graphs — Prompt Forge preview only.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "AV paragraph."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy sentence or authored AV paragraph.", gen="Do not restate the start-image look. Name motion and sound."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off pins the widget text."),
            _w("duration_hint", index=3, rng="5 seconds, 24 fps", desc="Duration hint.", gen="Lab takes are about 5 s at 24 fps."),
            _w("audio_notes", index=4, desc="World SFX / no-score policy.", gen="Interleave with the action; do not dump a trailer."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference. Ignored (start image owns look).", gen="Start frame owns look.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZAceStepPromptEnhance"] = _n(
        "ACE-Step Prompt Enhance",
        "Rewrite ACE tags (genre first) and lyrics. Instrumental mode forces [inst].",
        origin="ez_prompt_enhance",
        lab="Enhance off on authored album takes. Instrumental sanitizes lyrics into bracket cues.",
        sockets=[
            _s("lyrics", "STRING", "in", "Optional lyrics override (EZRapLyrics)."),
            _s("tags", "STRING", "out", "Tags for the ACE encoder."),
            _s("lyrics", "STRING", "out", "Lyrics / [inst] for the ACE encoder."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps authored tags/lyrics."),
            _w("tags", index=1, desc="Genre-first tags.", gen="Keep vocal identity tags stable across an album. Drive-through is not rap-over-club."),
            _w("lyrics", index=2, desc="Sectioned lyrics.", gen="Enhance off on catalog takes so exclusive verses stay pinned."),
            _w("enhance", index=3, typ="BOOLEAN", rng="false on albums", desc="Run the rewriter.", gen="On only when you typed a lazy hook and want the GGUF to expand it."),
            _w("mode", index=4, typ="COMBO", desc="Vocal vs instrumental sanitizer.", gen="instrumental forces no-vocals tags and [inst] lyrics.", choices=[("vocal", "Nill Bye / rap-draft / rap-full."), ("instrumental", "Drive-through EDM.")]),
            _w("catalog", index=5, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZPromptJoin"] = _n(
        "Prompt Join",
        "Join a shared identity paragraph with a shot-specific camera line.",
        origin="ez_prompt_enhance",
        sockets=[
            _s("identity", "STRING", "in", "World bible / character lock."),
            _s("prompt", "STRING", "out", "Joined prompt for CLIP / Enhance."),
        ],
        widgets=[
            _w("shot", index=0, desc="Shot card (camera, room, action).", gen="lock=view front-loads this so Klein sees a new camera in the same place."),
            _w("inventory", index=1, desc="Locked object list.", gen="Keeps mugs/coats from mutating across a pack."),
            _w("lock", index=2, typ="COMBO", rng="view", desc="What stays pinned.", gen="view = new camera, same place (dream-house, storyboard). state = same camera, new light/grade (time-of-day, color-moods).", choices=[("view", "New camera, same world."), ("state", "Same framing, new light/grade/action.")]),
        ],
    )
    nodes["EZContextJoin"] = _n(
        "Context Join",
        "Pack labeled desk fields into one context STRING for rewriter nodes.",
        origin="ez_prompt_enhance",
        sockets=[
            _s("a", "STRING", "in", "Logline."),
            _s("b", "STRING", "in", "Script."),
            _s("c", "STRING", "in", "Audio policy."),
            _s("d", "STRING", "in", "Score."),
            _s("context", "STRING", "out", "Labeled block for Enhance context."),
        ],
        widgets=[
            _w("label_a", index=0, rng="Logline", desc="Label for field A.", gen="Empty values are omitted."),
            _w("label_b", index=1, rng="Script", desc="Label for field B.", gen="Beat-sheet default Script."),
            _w("label_c", index=2, rng="Audio policy", desc="Label for field C.", gen="Keeps no-score / world-SFX policy in every card rewrite."),
            _w("label_d", index=3, rng="Score", desc="Label for field D.", gen="Optional."),
        ],
    )
    nodes["EZCinemaRack"] = _n(
        "Cinema Rack",
        "Pick one cinematography technique per axis and splice a Klein / Wan / LTX prompt.",
        origin="ez_prompt_enhance",
        lab="Deterministic. No LLM. Recipe fills empty axes. Wan emits one camera verb. I2V drops look. Editing omitted on stills. Style on downstream Enhance stays none.",
        sockets=[
            _s("prompt", "STRING", "out", "Spliced prompt for CLIP / Enhance."),
            _s("notes", "STRING", "out", "Dropped conflicts and Wan camera token."),
        ],
        widgets=[
            _w("subject", index=0, desc="Who or what is in the shot.", gen="Front-loaded except on I2V (start image owns identity)."),
            _w("flavor", index=1, typ="COMBO", rng="klein", desc="Family renderer.", gen="klein stills freeze motion axes. wan_t2v appends one camera token. i2v drops look.", choices=[("klein", "Still sentences."), ("klein_edit", "Edit still."), ("klein_identity", "Camera-free bible."), ("wan_t2v", "Look + one camera."), ("wan_i2v", "Motion + camera only."), ("ltx_t2v", "Present tense + foley."), ("ltx_i2v", "I2V AV; look dropped.")]),
            _w("recipe", index=2, typ="COMBO", rng="none", desc="Named splice.", gen="Fills axes that are still none. Explicit picks win."),
            _w("framing_shot_size", index=3, typ="COMBO", rng="none", desc="Shot size.", gen="How much of the subject fills the frame. Catalog under generated/cinema."),
            _w("camera_angles", index=4, typ="COMBO", rng="none", desc="Camera angle.", gen="Height and subject-relative angle. Catalog under generated/cinema."),
            _w("camera_movement", index=5, typ="COMBO", rng="none", desc="Camera move.", gen="The single Wan camera verb. Catalog under generated/cinema."),
            _w("lenses_optics", index=6, typ="COMBO", rng="none", desc="Lens and optic.", gen="Focal length and optic character. Catalog under generated/cinema."),
            _w("composition", index=7, typ="COMBO", rng="none", desc="Composition.", gen="Where masses sit in the frame. Catalog under generated/cinema."),
            _w("lighting", index=8, typ="COMBO", rng="none", desc="Lighting.", gen="Key quality, direction, and motivation. Catalog under generated/cinema."),
            _w("color_film_look", index=9, typ="COMBO", rng="none", desc="Color and film look.", gen="Grade and photochemical grammar, no stock names. Catalog under generated/cinema."),
            _w("time_motion", index=10, typ="COMBO", rng="none", desc="Time and motion.", gen="Shutter and temporal grammar. Catalog under generated/cinema."),
            _w("in_camera_optical", index=11, typ="COMBO", rng="none", desc="In-camera / optical.", gen="Flare, zoom, and in-camera tricks. Catalog under generated/cinema."),
            _w("editing_transitions", index=12, typ="COMBO", rng="none", desc="Editing.", gen="Named cuts. Omitted on Klein stills. Catalog under generated/cinema."),
            _w("atmosphere_weather", index=13, typ="COMBO", rng="none", desc="Atmosphere.", gen="Air, precip, ground. LTX interleaves foley. Catalog under generated/cinema."),
            _w("genre_looks", index=14, typ="COMBO", rng="none", desc="Genre grammar.", gen="Genre lighting and texture, not a titled film. Catalog under generated/cinema."),
            _w("viral_looks", index=15, typ="COMBO", rng="none", desc="Short-form hook.", gen="Platform-agnostic hook grammar. Catalog under generated/cinema."),
        ],
    )
    nodes["EZAudioRack"] = _n(
        "Audio Rack",
        "Pick one audio/music technique per axis and splice ACE-Step tags and lyrics form.",
        origin="ez_prompt_enhance",
        lab="Deterministic. No LLM. Recipe fills empty axes. Vocal omitted on instrumental/podcast. Instrumental forces no-vocals tags and [inst] form. Exactly one BPM when tempo is picked.",
        sockets=[
            _s("tags", "STRING", "out", "Genre-first ACE tags."),
            _s("lyrics", "STRING", "out", "Lyrics form / [inst] skeleton."),
            _s("notes", "STRING", "out", "Dropped conflicts and BPM token."),
        ],
        widgets=[
            _w("brief", index=0, desc="Optional lyrics seed.", gen="Ignored on instrumental and podcast-bed so ACE does not sing free text."),
            _w("flavor", index=1, typ="COMBO", rng="ace_vocal", desc="Family renderer.", gen="ace_vocal keeps vocal identity. ace_instrumental and podcast_bed omit it and force no-vocals tags.", choices=[("ace_vocal", "Vocal tags + lyrics form."), ("ace_instrumental", "No-vocals tags and [inst]/[drop]."), ("podcast_bed", "Instrumental bed; drop-first EDM dropped.")]),
            _w("recipe", index=2, typ="COMBO", rng="none", desc="Named splice.", gen="Fills axes that are still none. Explicit picks win."),
            _w("genre_style", index=3, typ="COMBO", rng="none", desc="Genre.", gen="Genre-first ACE tags. Catalog under generated/audio."),
            _w("tempo_groove", index=4, typ="COMBO", rng="none", desc="Tempo.", gen="Pocket and BPM token. Match the ACE encoder BPM. Catalog under generated/audio."),
            _w("drums_rhythm", index=5, typ="COMBO", rng="none", desc="Drums.", gen="Kit, hats, and groove. Catalog under generated/audio."),
            _w("bass_low_end", index=6, typ="COMBO", rng="none", desc="Bass.", gen="Upright, 808, sub, walking. Catalog under generated/audio."),
            _w("harmony_mode", index=7, typ="COMBO", rng="none", desc="Harmony.", gen="Mode color in tags. Does not set ACE keyscale. Catalog under generated/audio."),
            _w("instruments_texture", index=8, typ="COMBO", rng="none", desc="Instruments.", gen="Specific instruments and timbre. Catalog under generated/audio."),
            _w("vocal_identity", index=9, typ="COMBO", rng="none", desc="Vocal.", gen="One vocal identity. Omitted on instrumental/podcast. Catalog under generated/audio."),
            _w("arrangement_form", index=10, typ="COMBO", rng="none", desc="Form.", gen="Lyrics skeleton. Instrumental uses [inst]/[drop]. Catalog under generated/audio."),
            _w("mix_production", index=11, typ="COMBO", rng="none", desc="Mix.", gen="Vinyl dirt, dry booth, club loudness, duck. Catalog under generated/audio."),
            _w("space_ambience", index=12, typ="COMBO", rng="none", desc="Space.", gen="Booth dry, hall, mono drums, width. Catalog under generated/audio."),
            _w("sound_design_fx", index=13, typ="COMBO", rng="none", desc="Sound design.", gen="Tape stop, riser, reverse cymbal. Catalog under generated/audio."),
            _w("mood_energy", index=14, typ="COMBO", rng="none", desc="Mood.", gen="Menace, laid-back, civic-serious. Catalog under generated/audio."),
            _w("use_case", index=15, typ="COMBO", rng="none", desc="Use.", gen="Draft, album take, 30 s bed, bumper. Catalog under generated/audio."),
        ],
    )
    nodes["EZSamplePrompt"] = _n(
        "Sample Prompt",
        "STRING source with a sample-prompt combo plus Custom textarea.",
        origin="ez_prompt_enhance",
        sockets=[_s("prompt", "STRING", "out", "Resolved prompt.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom uses the textarea as typed."),
            _w("prompt", index=1, desc="Custom textarea.", gen="Ignored when a sample is selected."),
            _w("catalog", index=2, desc="Catalog id (inspire/prompt-forge).", gen="Leave as stamped."),
        ],
    )
    nodes["EZRapLyrics"] = _n(
        "Rap Lyrics",
        "Draft original rap lyrics via the on-box GGUF. Forbids living-MC names.",
        origin="ez_music",
        sockets=[
            _s("context", "STRING", "in", "Optional. Ignored when Enhance is off."),
            _s("lyrics", "STRING", "out", "Sectioned lyrics for ACE."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps authored bars."),
            _w("lyrics", index=1, desc="Sectioned lyrics.", gen="Human rewrite required before any release. Catalog takes keep Enhance off."),
            _w("enhance", index=2, typ="BOOLEAN", rng="false on albums", desc="Run the lyrics writer.", gen="On only for a lazy draft. Off pins exclusive verses."),
            _w("catalog", index=3, desc="Catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZAudioMetadata"] = _n(
        "Audio Metadata",
        "Stamp artist/album/title tags and optional cover on saved audio.",
        origin="ez_music",
        sockets=[
            _s("audio", "AUDIO", "in", "Pass-through AUDIO."),
            _s("cover", "IMAGE", "in", "Optional. Unwired so App Queue does not require a file."),
            _s("audio", "AUDIO", "out", "Same AUDIO; files on disk get tags."),
        ],
        widgets=[
            _w("artist", index=0, desc="ID3/Vorbis artist.", gen="Nill Bye vs Drive-through."),
            _w("album", index=1, desc="Album title.", gen="Must match the folder album-slug display name."),
            _w("title", index=2, desc="Track title.", gen="Pairs with SaveAudio stem NN - Song Title."),
            _w("track", index=3, typ="INT", rng="1–99", desc="Track number.", gen="Numbered takes 01–20."),
            _w("tracktotal", index=4, typ="INT", desc="Album track count.", gen="15 or 20 depending on the album."),
            _w("year", index=5, typ="INT", rng="2026", desc="Tag year.", gen="Does not affect audio."),
            _w("art_mode", index=6, typ="COMBO", rng="skip", desc="Cover art policy.", gen="skip on every audio Queue (Cover LoadImage is bypassed). generate is klein occupancy — later session. upload: graph view, Ctrl+B Cover image, then wire.", choices=[("skip", "Lab default. No cover required."), ("upload", "Un-bypass Cover image and wire the socket."), ("generate", "Use cover.jpg from the album folder (klein session).")]),
            _w("prefix", index=7, desc="SaveAudio stem to stamp.", gen="Must match SaveAudio / SaveAudioMP3."),
        ],
    )
    nodes["EZAlbumPack"] = _n(
        "Album Pack",
        "Write <Album>.m3u and <Album>.zip under albums/<Artist>/<Album>/.",
        origin="ez_music",
        sockets=[_s("zip_path", "STRING", "out", "Zip path or empty on failure.")],
        widgets=[
            _w("artist", index=0, desc="Artist folder.", gen="Drive-through or Nill Bye."),
            _w("album", index=1, desc="Album folder display name.", gen="Queue tracks first (or album-render). CPU only."),
        ],
    )
    return nodes
