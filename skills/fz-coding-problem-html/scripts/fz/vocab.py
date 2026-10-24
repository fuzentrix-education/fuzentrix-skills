"""The fixed vocabulary of Video and Topic Bundles: Line Roles, Finding kinds, Video Sections, slide layouts, Visual
Events, animation entrances and quiz choices. One place, so modules (and the schemas the Host App reads) agree
without importing each other."""

LINE_ROLES = ("spoken", "heading", "speaker_label", "stage_direction", "note_to_team", "slide_only", "duplicate")
CATEGORIES = ("technical", "flow", "guideline", "hygiene", "code")
SEVERITIES = ("critical", "major", "minor")
CODE_STATUS = ("run", "read_only")

VIDEO_SECTIONS = ("hook", "intro", "recap", "agenda", "explanation", "summary", "teaser", "outro")
SLIDE_LAYOUTS = ("title", "agenda", "bullets", "definition", "code", "comparison", "diagram", "quote", "image", "summary")
EVENT_KINDS = ("animation", "image", "diagram", "code", "broll", "direction")  # direction: camera, music or sound cue
EVENT_LAYOUTS = ("fullscreen_cutaway", "beside_instructor", "overlay", "slide_bg")

# How an element can enter: the Brand Kit picks one per kind of element (motion.entrances), the motion workflow
# animates it, and the step sheet tells the Video Editor how to do it by hand in Premiere.
ENTRANCES = {
    "cut": "Cut in",
    "fade": "Opacity 0 → 100 %",
    "fade_up": "Opacity 0 → 100 % while rising 20 px",
    "pop": "Scale 85 → 100 % with Opacity 0 → 100 %",
    "draw": "Linear Wipe in the direction it points",
    "wipe": "Linear Wipe left to right",
    "type": "Linear Wipe left to right, one line at a time",
    "slide_in": "Position in from the nearest frame edge",
}

QUESTION_TYPES = ("SINGLE_SELECT", "MULTI_SELECT", "TRUE_FALSE")
DIFFICULTIES = ("easy", "medium", "hard")
EXPLANATIONS = ("correct_only", "all_options")
CODE_QUESTIONS = ("auto", "include", "none")
