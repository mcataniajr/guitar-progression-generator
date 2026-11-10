"""Guitar Chord Progression Generator: a Drafter web app."""
from dataclasses import dataclass, field
from typing import Any
from drafter import *

# Website settings (these must come before start_server, so they are kept right after the imports)
hide_debug_information()
set_website_title("Guitar Progression Generator")
set_website_style("daub")
set_website_framed(False)
set_page_transition("fade")
set_button_spinners(True)

# ----------------------------------------------------------------------------------------------
# Constants (global constants are allowed; anything that changes lives in State instead)
# ----------------------------------------------------------------------------------------------

# All twelve notes, using sharps inside the program.
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# The five black keys are always written the same way on the screen: C#, Eb, F#, G#, and Bb.
# Only Eb and Bb are flats, so those are the only two that need converting between the program and the screen.
FLAT_TO_SHARP = {"Eb": "D#", "Bb": "A#"}
SHARP_TO_FLAT = {"A#": "Bb", "D#": "Eb"}

# The choices shown in the setup page's dropdown boxes. A key ending in "m" is a minor key.
# The major keys come first, then the minor keys, each group in alphabetical order.
KEY_OPTIONS = [
    "A", "Bb", "B", "C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#",
    "Am", "Bbm", "Bm", "Cm", "C#m", "Dm", "Ebm", "Em", "Fm", "F#m", "Gm", "G#m",
]
MOOD_OPTIONS = ["Joyful", "Peaceful", "Sorrowful", "Mysterious", "Bluesy"]
LENGTH_OPTIONS = ["4", "8"]  # dropdown options are text; the route converts the choice to an int

# How many semitones each note of a major scale is above the starting note.
MAJOR_SCALE_STEPS = [0, 2, 4, 5, 7, 9, 11]

# Roman numerals in order, so the position in this list is the scale degree (I is 0, V is 4).
NUMERALS = ["i", "ii", "iii", "iv", "v", "vi", "vii"]

# The text added after the root note to make the chord name.
QUALITY_SUFFIX = {"major": "", "minor": "m", "dominant7": "7", "major7": "maj7", "minor7": "m7"}

# How many semitones above the root each note of a chord is, and the job each note does in the chord.
CHORD_INTERVALS = {
    "major": [0, 4, 7], "minor": [0, 3, 7],
    "dominant7": [0, 4, 7, 10], "major7": [0, 4, 7, 11], "minor7": [0, 3, 7, 10],
}
CHORD_ROLES = {
    "major": ["root", "3rd", "5th"],
    "minor": ["root", "minor 3rd", "5th"],
    "dominant7": ["root", "3rd", "5th", "minor 7th"],
    "major7": ["root", "3rd", "5th", "major 7th"],
    "minor7": ["root", "minor 3rd", "5th", "minor 7th"],
}
QUALITY_LABEL = {
    "major": "major chord", "minor": "minor chord", "dominant7": "dominant 7th chord",
    "major7": "major 7th chord", "minor7": "minor 7th chord",
}

# The pitch of each open guitar string, low E to high e. Each pitch is a number of semitones above C0, so the
# octave is the number divided by 12 and the note is the remainder (E2 is 28, because 2 * 12 + 4 = 28).
OPEN_STRING_PITCHES = [28, 33, 38, 43, 47, 52]

# Each mood has a list of Roman numeral patterns. Uppercase = major chord, lowercase = minor chord,
# and a 7 on the end means a dominant seventh chord.
MOOD_TEMPLATES = {
    "Joyful": [["I", "V", "vi", "IV"], ["I", "IV", "V", "I"]],
    "Peaceful": [["I", "iii", "IV", "V"], ["I", "vi", "ii", "V"]],
    "Sorrowful": [["vi", "IV", "I", "V"], ["vi", "V", "IV", "V"]],
    "Mysterious": [["vi", "V", "IV", "iii"], ["ii", "vi", "IV", "V"]],
    "Bluesy": [["I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "I7"]],
}

# The key used for every example on the mood guide page.
GUIDE_KEY = "G"

# One accent color for each mood (HTML color names), used on the result page, the saved page, and the mood guide.
MOOD_COLORS = {
    "Joyful": "goldenrod", "Peaceful": "seagreen", "Sorrowful": "steelblue",
    "Mysterious": "rebeccapurple", "Bluesy": "teal",
}
NEUTRAL_COLOR = "gray"  # used for cards that do not belong to a mood

# The look shared by every card (a bordered, padded box with rounded corners).
CARD_RADIUS = "8px"
CARD_PADDING = "10px"
CARD_MARGIN = "8px"

# The highest fret a capo is suggested on in beginner mode (higher than this is uncomfortable for most beginners).
CAPO_MAX = 7

# The width in pixels of the chord diagrams on the result page and on the saved progression page.
RESULT_DIAGRAM_WIDTH = 140
SAVED_DIAGRAM_WIDTH = 120

# A short explanation of each mood, shown on the mood guide page.
MOOD_DESCRIPTIONS = {
    "Joyful": "Bright and upbeat. It uses mostly major chords and keeps coming back toward the home chord (I), "
              "so it feels happy and settled.",
    "Peaceful": "Calm and floating. The soft minor chord iii sits close to the home chord, and the chords "
                "then step gently upward (IV, V) without any big jumps.",
    "Sorrowful": "Sad and heavy. It starts on the minor chord vi, which is the home chord of the relative minor key, "
                 "so the progression feels like it lives in a minor key.",
    "Mysterious": "Unsettled and dark. The chords walk downward from the minor chord vi and never land on the "
                  "home chord (I), so the progression feels like it is not finished.",
    "Bluesy": "Gritty and soulful. This is the classic 12-bar blues: seventh chords on I, IV, and V give it that "
              "blues sound. It always has 12 chords, whatever length you pick.",
}

# The open chords, typed by hand. Fret number for each string from low E to high e.
# 0 means an open string and -1 means a muted string.
# Every other chord is made from the barre shapes below by build_fingering_dictionary.
OPEN_CHORD_FINGERINGS = {
    "C": [-1, 3, 2, 0, 1, 0], "G": [3, 2, 0, 0, 0, 3], "D": [-1, -1, 0, 2, 3, 2],
    "A": [-1, 0, 2, 2, 2, 0], "E": [0, 2, 2, 1, 0, 0],
    "Am": [-1, 0, 2, 2, 1, 0], "Em": [0, 2, 2, 0, 0, 0], "Dm": [-1, -1, 0, 2, 3, 1],
    "C7": [-1, 3, 2, 3, 1, 0], "D7": [-1, -1, 0, 2, 1, 2], "E7": [0, 2, 0, 1, 0, 0],
    "G7": [3, 2, 0, 0, 0, 1], "A7": [-1, 0, 2, 0, 2, 0], "B7": [-1, 2, 1, 2, 0, 2],
    "Cmaj7": [-1, 3, 2, 0, 0, 0], "Dmaj7": [-1, -1, 0, 2, 2, 2], "Fmaj7": [-1, -1, 3, 2, 1, 0],
    "Gmaj7": [3, 2, 0, 0, 0, 2], "Amaj7": [-1, 0, 2, 1, 2, 0], "Emaj7": [0, 2, 1, 1, 0, 0],
    "Am7": [-1, 0, 2, 0, 1, 0], "Dm7": [-1, -1, 0, 2, 1, 1], "Em7": [0, 2, 0, 0, 0, 0],
}

# Barre chord shapes. Each list is the fret for each string when the root note is on fret 0.
# To play the chord higher up the neck, add the same number to every string that is not muted (-1).
# The E shape has its root note on the low E string (like an open E chord). The A shape has it on the A string.
E_SHAPES = {
    "major": [0, 2, 2, 1, 0, 0], "minor": [0, 2, 2, 0, 0, 0], "dominant7": [0, 2, 0, 1, 0, 0],
    "major7": [0, 2, 1, 1, 0, 0], "minor7": [0, 2, 0, 0, 0, 0],
}
A_SHAPES = {
    "major": [-1, 0, 2, 2, 2, 0], "minor": [-1, 0, 2, 2, 1, 0], "dominant7": [-1, 0, 2, 0, 2, 0],
    "major7": [-1, 0, 2, 1, 2, 0], "minor7": [-1, 0, 2, 0, 1, 0],
}


# The CAGED system: every chord can be played in five places on the neck, using the shapes of the open
# C, A, G, E, and D chords slid up the neck. Each list is the fret for each string (low E to high e) when the
# shape's open strings are lined up with the barre, so 0 means "the barre fret" and -1 means a muted string.
# The shapes are listed for each chord quality, so CAGED_SHAPES[quality][letter] is one shape.
CAGED_LETTERS = ["C", "A", "G", "E", "D"]
CAGED_SHAPES = {
    "major": {
        "C": [-1, 3, 2, 0, 1, 0], "A": [-1, 0, 2, 2, 2, 0], "G": [3, 2, 0, 0, 0, 3],
        "E": [0, 2, 2, 1, 0, 0], "D": [-1, -1, 0, 2, 3, 2],
    },
    "minor": {
        "C": [-1, 3, 1, 0, 1, -1], "A": [-1, 0, 2, 2, 1, 0], "G": [3, 1, 0, 0, 3, 3],
        "E": [0, 2, 2, 0, 0, 0], "D": [-1, -1, 0, 2, 3, 1],
    },
    "dominant7": {
        "C": [-1, 3, 2, 3, 1, 0], "A": [-1, 0, 2, 0, 2, 0], "G": [3, 2, 0, 0, 0, 1],
        "E": [0, 2, 0, 1, 0, 0], "D": [-1, -1, 0, 2, 1, 2],
    },
    "major7": {
        "C": [-1, 3, 2, 0, 0, 0], "A": [-1, 0, 2, 1, 2, 0], "G": [3, 2, 0, 0, 0, 2],
        "E": [0, 2, 1, 1, 0, 0], "D": [-1, -1, 0, 2, 2, 2],
    },
    "minor7": {
        "C": [-1, 3, 1, 3, 1, -1], "A": [-1, 0, 2, 0, 1, 0], "G": [3, 1, 0, 0, 3, 1],
        "E": [0, 2, 0, 0, 0, 0], "D": [-1, -1, 0, 2, 1, 1],
    },
}

# The note that each open shape is built on, as a position in NOTES (C is 0, A is 9, G is 7, E is 4, D is 2).
CAGED_ROOT_POSITIONS = {"C": 0, "A": 9, "G": 7, "E": 4, "D": 2}


# ----------------------------------------------------------------------------------------------
# Dataclasses
# ----------------------------------------------------------------------------------------------

@dataclass
class Chord:
    """One guitar chord."""
    name: str          # for example "Am7"
    root: str          # for example "A"
    quality: str       # a key of QUALITY_SUFFIX, such as "minor7"
    frets: list[int]   # six fret numbers, or an empty list if the chord is not in the dictionary yet
    is_barre: bool
    # The Roman numeral the chord was made from, such as "vi" (empty if it was not made from one).
    # compare=False means two chords with the same notes and fingering count as equal even if their numerals differ.
    numeral: str = field(default="", compare=False)


@dataclass
class CagedShape:
    """One way to play a chord: one of the five CAGED shapes, slid to the right place on the neck."""
    letter: str        # "C", "A", "G", "E", or "D"
    start_fret: int    # 0 if the shape is played in open position, otherwise the fret of the barre
    frets: list[int]   # six fret numbers


@dataclass
class Progression:
    """A named, saved chord progression."""
    name: str
    mood: str
    key: str
    chords: list[Chord]
    capo: int = 0  # the capo fret the chords are played with (0 means no capo)


@dataclass
class State:
    """Everything the site remembers between pages."""
    key: str
    mood: str
    length: int
    use_sevenths: bool
    beginner_mode: bool
    transpose_steps: int
    current_progression: list[Chord]
    saved_progressions: list[Progression]
    # The capo fret for the current progression (0 means no capo). With a capo, current_progression holds the shapes
    # the user plays, and they sound that many half steps higher.
    capo: int = 0
    # Which of the mood's patterns the current progression uses (0 is the main one).
    pattern: int = 0
    # The key and mood the current progression was made with. These are kept apart from key and mood above, which
    # only remember what the setup page shows, so visiting another page cannot change how the progression is labeled.
    progression_key: str = ""
    progression_mood: str = ""


# ----------------------------------------------------------------------------------------------
# Note and scale helpers
# ----------------------------------------------------------------------------------------------

def to_internal_name(note: str) -> str:
    """Convert a note name such as 'Bb' to the sharp spelling used inside the program ('A#')."""
    if note in FLAT_TO_SHARP:
        return FLAT_TO_SHARP[note]
    return note


def to_display_name(note: str) -> str:
    """Convert a note name such as 'A#' to the name guitarists expect ('Bb')."""
    if note in SHARP_TO_FLAT:
        return SHARP_TO_FLAT[note]
    return note


def transpose_note(note: str, steps: int) -> str:
    """Move a note up or down by a number of semitones.

    The % 12 wraps the position back into the range 0 to 11, so B up one step is C,
    and C down one step is B.
    """
    new_position = (NOTES.index(note) + steps) % 12
    return NOTES[new_position]


def get_scale(key: str) -> list[str]:
    """Return the seven notes of the major scale that starts on the given key."""
    root_position = NOTES.index(key)
    scale = []
    for step in MAJOR_SCALE_STEPS:
        scale.append(NOTES[(root_position + step) % 12])
    return scale


def relative_major(minor_root: str) -> str:
    """Return the relative major key of a minor key, which is three semitones up (A minor -> C)."""
    return transpose_note(minor_root, 3)


def resolve_key(key: str, is_minor: bool) -> str:
    """Return the major key to build from. Minor keys use their relative major."""
    if is_minor:
        return relative_major(key)
    return key


def parse_key(key_choice: str) -> tuple[str, bool]:
    """Split a dropdown choice such as 'Bbm' into its internal root note ('A#') and whether it is minor (True)."""
    is_minor = False
    root = key_choice
    if key_choice[-1] == "m":
        is_minor = True
        root = key_choice[:-1]
    return to_internal_name(root), is_minor


def key_choice_name(root: str, is_minor: bool) -> str:
    """Return the dropdown name for a key, such as 'Bbm' for the root 'A#' in a minor key."""
    name = to_display_name(root)
    if is_minor:
        name = name + "m"
    return name


def transposed_key_name(key_choice: str, steps: int) -> str:
    """Return the name of a key after moving it up (or down, if steps is negative) by some half steps."""
    root, is_minor = parse_key(key_choice)
    return key_choice_name(transpose_note(root, steps), is_minor)


def describe_transpose(key_choice: str, steps: int) -> str:
    """Return a sentence about how far the progression has been moved from its original key ('' if it has not)."""
    if steps == 0:
        return ""
    direction = "up"
    amount = steps
    if steps < 0:
        direction = "down"
        amount = -steps
    unit = " half steps"
    if amount == 1:
        unit = " half step"
    return "Original key: " + key_choice + " (transposed " + direction + " " + str(amount) + unit + ")"


# ----------------------------------------------------------------------------------------------
# Chord helpers
# ----------------------------------------------------------------------------------------------

def shift_shape(shape: list[int], fret_offset: int) -> list[int]:
    """Slide a chord shape up the neck by adding fret_offset to every string that is not muted."""
    shifted = []
    for fret in shape:
        if fret == -1:
            shifted.append(-1)
        else:
            shifted.append(fret + fret_offset)
    return shifted


def barre_fingering(root: str, quality: str) -> list[int]:
    """Make a barre chord fingering by sliding the E shape or the A shape, whichever sits lower on the neck.

    The E shape's root is on the low E string, so the offset is how many semitones the root is above E.
    The A shape's root is on the A string, so the offset is how many semitones the root is above A.
    """
    e_offset = (NOTES.index(root) - NOTES.index("E")) % 12
    a_offset = (NOTES.index(root) - NOTES.index("A")) % 12
    if e_offset < a_offset:
        return shift_shape(E_SHAPES[quality], e_offset)
    return shift_shape(A_SHAPES[quality], a_offset)


def build_fingering_dictionary() -> dict[str, list[int]]:
    """Make a fingering for every root note and quality: the hand-typed open chords, then barre chords for the rest."""
    fingerings = {}
    for root in NOTES:
        for quality in QUALITY_SUFFIX:
            name = root + QUALITY_SUFFIX[quality]
            if name in OPEN_CHORD_FINGERINGS:
                fingerings[name] = OPEN_CHORD_FINGERINGS[name]
            else:
                fingerings[name] = barre_fingering(root, quality)
    return fingerings


# A constant: filled in once when the program starts and never changed after that.
CHORD_FINGERINGS = build_fingering_dictionary()


def lookup_fingering(chord_name: str) -> list[int]:
    """Return the six fret numbers for a chord, or an empty list if it is not in the dictionary yet."""
    if chord_name in CHORD_FINGERINGS:
        return CHORD_FINGERINGS[chord_name]
    return []


def is_barre_shape(frets: list[int]) -> bool:
    """Guess whether a fingering is a barre chord: no open strings, and the lowest fret used on 2+ strings."""
    lowest = 99
    for fret in frets:
        if fret == 0:
            return False
        if fret > 0 and fret < lowest:
            lowest = fret
    if lowest == 99:
        return False
    count = 0
    for fret in frets:
        if fret == lowest:
            count += 1
    return count >= 2


def caged_start_fret(root: str, letter: str) -> int:
    """Return the fret where a CAGED shape must be played for a chord with this root note.

    The shape's open version has its own root note (the C shape's is C), so the shape has to slide up by the number
    of semitones from that note to the chord's root. The % 12 keeps the answer between 0 and 11.
    """
    return (NOTES.index(root) - CAGED_ROOT_POSITIONS[letter]) % 12


def caged_frets(root: str, quality: str, letter: str) -> list[int]:
    """Return the six fret numbers for one CAGED shape of a chord."""
    return shift_shape(CAGED_SHAPES[quality][letter], caged_start_fret(root, letter))


def caged_shapes(root: str, quality: str) -> list[CagedShape]:
    """Return all five CAGED shapes of a chord, ordered from the lowest place on the neck to the highest.

    Every shape starts at a different fret, so checking the frets 0 to 11 in order puts the shapes in order.
    """
    shapes = []
    for start_fret in range(12):
        for letter in CAGED_LETTERS:
            if caged_start_fret(root, letter) == start_fret:
                shapes.append(CagedShape(letter, start_fret, caged_frets(root, quality, letter)))
    return shapes


def make_chord(root: str, quality: str) -> Chord:
    """Build a Chord from a root note and a quality, looking up its fingering."""
    name = root + QUALITY_SUFFIX[quality]
    frets = lookup_fingering(name)
    return Chord(name, root, quality, frets, is_barre_shape(frets))


def needs_barre(chord: Chord) -> bool:
    """Return True if a beginner could not play the chord with open-string shapes.

    A chord with no fingering in the dictionary has no open-chord shape stored,
    so for now it counts as needing a barre.
    """
    return chord.is_barre or chord.frets == []


def barre_chord_names(chords: list[Chord]) -> list[str]:
    """Return the display names of the chords that need a barre, with no repeats."""
    names = []
    for chord in chords:
        name = display_chord_name(chord)
        if needs_barre(chord) and name not in names:
            names.append(name)
    return names


def join_names(names: list[str]) -> str:
    """Join a list of names into one piece of text with commas, such as 'F, Bm'."""
    text = ""
    for name in names:
        if text != "":
            text = text + ", "
        text = text + name
    return text


def barre_error_message(barre_names: list[str]) -> str:
    """Write the error shown when beginner mode is on but the progression needs barre chords."""
    return ("Beginner mode: this progression would include barre chords (" + join_names(barre_names)
            + ") and no capo position up to fret " + str(CAPO_MAX) + " avoids them. Choose another key or mood, "
            + "or turn off beginner mode.")


def transpose_error_message(barre_names: list[str]) -> str:
    """Write the error shown when beginner mode is on but transposing would need barre chords."""
    return ("Beginner mode: transposing would include barre chords (" + join_names(barre_names)
            + ") and no capo position up to fret " + str(CAPO_MAX) + " avoids them. Turn off beginner mode on the "
            + "setup page to transpose.")


def display_chord_name(chord: Chord) -> str:
    """Return the chord name as a guitarist would write it, such as 'Bbm7'."""
    return to_display_name(chord.root) + QUALITY_SUFFIX[chord.quality]


def choose_quality(degree: int, is_minor: bool, has_seven: bool, use_sevenths: bool) -> str:
    """Pick a chord quality from the numeral's case, a written 7, and the 'include 7ths' option."""
    if is_minor:
        if has_seven or use_sevenths:
            return "minor7"
        return "minor"
    if has_seven:
        return "dominant7"
    if use_sevenths:
        if degree == 4:
            return "dominant7"  # the V chord gets a dominant 7th
        return "major7"
    return "major"


def numeral_to_chord(numeral: str, scale: list[str], use_sevenths: bool) -> Chord:
    """Convert a Roman numeral such as 'vi' or 'V7' into a Chord, using the notes of a major scale."""
    has_seven = False
    base = numeral
    if numeral[-1] == "7":
        has_seven = True
        base = numeral[:-1]
    degree = NUMERALS.index(base.lower())
    is_minor = base == base.lower()
    quality = choose_quality(degree, is_minor, has_seven, use_sevenths)
    chord = make_chord(scale[degree], quality)
    chord.numeral = numeral
    return chord


def build_progression(major_key: str, mood: str, use_sevenths: bool, length: int, pattern: int = 0) -> list[Chord]:
    """Build a chord progression for a major key, a mood, and a length, using one of the mood's patterns."""
    template = MOOD_TEMPLATES[mood][pattern]
    if mood == "Bluesy":
        length = len(template)  # the 12-bar blues always has 12 chords
    scale = get_scale(major_key)
    chords = []
    for position in range(length):
        numeral = template[position % len(template)]  # % repeats the pattern if the length is longer
        chords.append(numeral_to_chord(numeral, scale, use_sevenths))
    return chords


def build_current_progression(key_choice: str, steps: int, mood: str, use_sevenths: bool, length: int,
                              pattern: int = 0) -> list[Chord]:
    """Build the progression for a dropdown key choice that has been transposed by some number of half steps."""
    root, is_minor = parse_key(key_choice)
    new_root = transpose_note(root, steps)
    major_key = resolve_key(new_root, is_minor)
    return build_progression(major_key, mood, use_sevenths, length, pattern)


def shift_chords(chords: list[Chord], steps: int) -> list[Chord]:
    """Return new chords with every chord moved up (or down, if steps is negative) by some half steps.

    Each chord keeps its quality and its Roman numeral. Only the root note, and so the fingering, changes.
    """
    shifted = []
    for chord in chords:
        new_chord = make_chord(transpose_note(chord.root, steps), chord.quality)
        new_chord.numeral = chord.numeral
        shifted.append(new_chord)
    return shifted


def find_capo_for_chords(chords: list[Chord]) -> int:
    """Return the lowest capo fret (0 up to CAPO_MAX) that lets the chords be played with open shapes only.

    A capo on fret N makes every shape sound N half steps higher. So to sound like these chords, the shapes to play
    are these chords moved N half steps lower. Return -1 if no capo fret works.
    """
    for capo in range(CAPO_MAX + 1):
        if len(barre_chord_names(shift_chords(chords, -capo))) == 0:
            return capo
    return -1


def find_beginner_capo(key_choice: str, steps: int, mood: str, use_sevenths: bool, length: int,
                       pattern: int = 0) -> int:
    """Return the lowest capo fret that makes one pattern of a mood playable with open shapes, or -1."""
    chords = build_current_progression(key_choice, steps, mood, use_sevenths, length, pattern)
    return find_capo_for_chords(chords)


def find_beginner_options(key_choice: str, mood: str, use_sevenths: bool, length: int) -> tuple[int, int]:
    """Find a pattern number and a capo fret that make the mood playable with open shapes in beginner mode.

    The mood's main pattern (number 0) is tried first, with every capo fret. Only if it cannot work are the mood's
    other patterns tried, in order. Return (-1, -1) if nothing works.
    """
    for pattern in range(len(MOOD_TEMPLATES[mood])):
        capo = find_beginner_capo(key_choice, 0, mood, use_sevenths, length, pattern)
        if capo != -1:
            return pattern, capo
    return -1, -1


def sounding_chord_name(chord: Chord, capo: int) -> str:
    """Return the name of the chord heard when this shape is played with a capo, such as 'Bb' for G on fret 3."""
    return to_display_name(transpose_note(chord.root, capo)) + QUALITY_SUFFIX[chord.quality]


def sounding_chords_text(chords: list[Chord], capo: int) -> str:
    """Write the chords that are heard when the shapes are played with a capo, such as 'Bb - F - Gm - Eb'."""
    text = ""
    for chord in chords:
        if text != "":
            text = text + " - "
        text = text + sounding_chord_name(chord, capo)
    return text


def capo_suffix(capo: int) -> str:
    """Return ' (capo on fret 3)' for a capo fret, or '' if there is no capo."""
    if capo == 0:
        return ""
    return " (capo on fret " + str(capo) + ")"


def describe_capo(key_name: str, capo: int) -> str:
    """Write the sentence that tells the user where to put the capo ('' if there is no capo)."""
    if capo == 0:
        return ""
    return ("Capo on fret " + str(capo) + ": play the shapes below with the capo on and they will sound in "
            + key_name + ". (Frets are counted from the capo.)")


def chords_text(chords: list[Chord]) -> str:
    """Write a list of chords as one line of text, such as 'C - G - Am - F'."""
    text = ""
    for chord in chords:
        if text != "":
            text = text + " - "
        text = text + display_chord_name(chord)
    return text


def name_is_taken(saved: list[Progression], name: str, skip_position: int) -> bool:
    """Return True if a saved progression already has this name (capital letters are ignored).

    The progression at skip_position is not checked, so a progression can be renamed to a different spelling of its
    own name. Use -1 to check every progression.
    """
    for position in range(len(saved)):
        if position != skip_position and saved[position].name.lower() == name.lower():
            return True
    return False


def find_position(saved: list[Progression], name: str) -> int:
    """Return where the progression with exactly this name is in the saved list, or -1 if there is none.

    Names are unique, so a name always points to one progression. The buttons on the saved page send the name,
    which keeps an old page's buttons from changing the wrong progression after the list has changed.
    """
    for position in range(len(saved)):
        if saved[position].name == name:
            return position
    return -1


# ----------------------------------------------------------------------------------------------
# Diagram helpers (build the shapes of an SVG drawing as text)
# ----------------------------------------------------------------------------------------------

STRING_X_START = 22   # x position of the lowest (thickest) string in the drawing
STRING_GAP = 13       # space between strings
FRET_Y_TOP = 30       # y position of the top fret line (the nut)
FRET_GAP = 18         # space between fret lines
FRETS_SHOWN = 5       # how many frets the diagram covers


def string_x(string_number: int) -> int:
    """Return the x position of a string (0 is the low E string, 5 is the high e string)."""
    return STRING_X_START + string_number * STRING_GAP


def fret_y(row: int) -> int:
    """Return the y position of a fret line (row 0 is the top line)."""
    return FRET_Y_TOP + row * FRET_GAP


def svg_line(x1: int, y1: int, x2: int, y2: int, width: int) -> str:
    """Return the SVG text for one black line."""
    return ('<line x1="' + str(x1) + '" y1="' + str(y1) + '" x2="' + str(x2) + '" y2="' + str(y2)
            + '" stroke="black" stroke-width="' + str(width) + '" stroke-linecap="round" />')


def svg_circle(x: int, y: int, radius: int, filled: bool) -> str:
    """Return the SVG text for one circle, filled in black or just an outline."""
    fill = "none"
    if filled:
        fill = "black"
    return ('<circle cx="' + str(x) + '" cy="' + str(y) + '" r="' + str(radius)
            + '" fill="' + fill + '" stroke="black" stroke-width="1.5" />')


def base_fret_for(frets: list[int]) -> int:
    """Return the fret number shown at the top of the diagram (1 unless the chord is played high up the neck)."""
    highest = 0
    lowest = 99
    for fret in frets:
        if fret > highest:
            highest = fret
        if fret > 0 and fret < lowest:
            lowest = fret
    if highest <= FRETS_SHOWN:
        return 1
    return lowest


def draw_grid(base_fret: int) -> str:
    """Return the strings and fret lines. The top line is thick (the nut) unless the chord is higher up."""
    shapes = ""
    for string_number in range(6):
        shapes += svg_line(string_x(string_number), fret_y(0), string_x(string_number), fret_y(FRETS_SHOWN), 1)
    for row in range(FRETS_SHOWN + 1):
        width = 1
        if row == 0 and base_fret == 1:
            width = 4
        shapes += svg_line(string_x(0), fret_y(row), string_x(5), fret_y(row), width)
    if base_fret > 1:
        shapes += '<text x="1" y="' + str(fret_y(0) + 13) + '" font-size="9">' + str(base_fret) + "fr</text>"
    return shapes


def draw_markers(frets: list[int]) -> str:
    """Return an open circle above each open string and an X above each muted string."""
    shapes = ""
    for string_number in range(len(frets)):
        x = string_x(string_number)
        if frets[string_number] == 0:
            shapes += svg_circle(x, 18, 4, False)
        elif frets[string_number] == -1:
            shapes += svg_line(x - 4, 14, x + 4, 22, 1)
            shapes += svg_line(x - 4, 22, x + 4, 14, 1)
    return shapes


def draw_barre(frets: list[int], base_fret: int) -> str:
    """Return a thick bar across the strings that share the lowest fret, or nothing if there is no barre."""
    if not is_barre_shape(frets):
        return ""
    lowest = 99
    for fret in frets:
        if fret > 0 and fret < lowest:
            lowest = fret
    first = -1
    last = -1
    for string_number in range(len(frets)):
        if frets[string_number] == lowest:
            if first == -1:
                first = string_number
            last = string_number
    y = fret_y(lowest - base_fret) + FRET_GAP // 2
    return svg_line(string_x(first), y, string_x(last), y, 10)


def draw_dots(frets: list[int], base_fret: int) -> str:
    """Return a filled dot on every fretted string."""
    shapes = ""
    for string_number in range(len(frets)):
        if frets[string_number] > 0:
            y = fret_y(frets[string_number] - base_fret) + FRET_GAP // 2
            shapes += svg_circle(string_x(string_number), y, 6, True)
    return shapes


def draw_diagram(frets: list[int]) -> str:
    """Return the SVG shapes for a six-string chord diagram, or an empty string if there are no fret numbers."""
    if len(frets) != 6:
        return ""
    base_fret = base_fret_for(frets)
    return draw_grid(base_fret) + draw_markers(frets) + draw_barre(frets, base_fret) + draw_dots(frets, base_fret)


def mood_color(mood: str) -> str:
    """Return the accent color for a mood, or a neutral gray if the mood has no color."""
    if mood in MOOD_COLORS:
        return MOOD_COLORS[mood]
    return NEUTRAL_COLOR


def card_border(color: str) -> str:
    """Return the border text for a card in the given color, such as '2px solid teal'."""
    return "2px solid " + color


def make_chord_block(chord: Chord, width: int, color: str, capo: int) -> Div:
    """Build the card for one chord: its name, its diagram (width pixels wide), and its Roman numeral below.

    If a capo is used, the card also says which chord the shape sounds as.
    """
    name = display_chord_name(chord)
    sounds_as = ""
    diagram: SVG | str = "(no diagram yet)"
    if capo > 0:
        sounds_as = "sounds as " + sounding_chord_name(chord, capo)
    if len(chord.frets) == 6:
        height = width * 13 // 10  # the diagram is drawn on a 100 by 130 grid, so the height keeps that shape
        diagram = SVG(draw_diagram(chord.frets), width=width, height=height, viewBox="0 0 100 130")
    return Div(Header(name, 3), diagram, "\n", chord.numeral, "\n", sounds_as, style_border=card_border(color),
               style_border_radius=CARD_RADIUS, style_padding=CARD_PADDING, style_margin=CARD_MARGIN,
               style_display="inline-block")


def guitar_body_circle(x: int, y: int, radius: int, stroke: str) -> str:
    """Return one wooden circle for the guitar's body (stroke is a color, or 'none' for no outline)."""
    return ('<circle cx="' + str(x) + '" cy="' + str(y) + '" r="' + str(radius) + '" fill="#c68642" stroke="' + stroke
            + '" stroke-width="4" />')


def draw_guitar() -> str:
    """Return the SVG shapes for a small acoustic guitar lying on its side (body on the left, neck on the right)."""
    dark = "#5a3418"
    # The body is two circles. All the outlines are drawn first and then both circles are filled again with no
    # outline, which hides the outline lines inside the body.
    shapes = guitar_body_circle(70, 50, 38, dark) + guitar_body_circle(118, 50, 28, dark)
    shapes += guitar_body_circle(70, 50, 38, "none") + guitar_body_circle(118, 50, 28, "none")
    shapes += '<circle cx="85" cy="50" r="10" fill="#2b1a0e" />'  # the sound hole
    shapes += '<rect x="45" y="43" width="5" height="14" fill="' + dark + '" />'  # the bridge
    shapes += '<rect x="140" y="44" width="125" height="12" fill="#8b5a2b" stroke="' + dark + '" stroke-width="1.5" />'
    for fret_x in [165, 188, 209, 228, 245]:
        shapes += '<line x1="' + str(fret_x) + '" y1="44" x2="' + str(fret_x) + '" y2="56" stroke="#e8e0d0" />'
    shapes += '<rect x="265" y="40" width="28" height="20" rx="3" fill="#8b5a2b" stroke="' + dark + '" />'
    for peg in [[272, 37], [287, 37], [272, 63], [287, 63]]:
        shapes += '<circle cx="' + str(peg[0]) + '" cy="' + str(peg[1]) + '" r="3" fill="#e8e0d0" stroke="' + dark
        shapes += '" />'
    for string_number in range(6):
        shapes += svg_line(48, 44 + string_number * 2, 266, 45 + string_number * 2, 1)
    return shapes


# ----------------------------------------------------------------------------------------------
# Chord detail helpers: which notes are in a chord, and which notes the guitar strings play
# ----------------------------------------------------------------------------------------------

def chord_note_names(chord: Chord, capo: int = 0) -> list[str]:
    """Return the notes that make up the chord (not counting repeats), such as ['C', 'E', 'G'] for C.

    With a capo the notes are the ones that are heard, which are capo half steps higher than the shape's notes.
    """
    names = []
    for interval in CHORD_INTERVALS[chord.quality]:
        names.append(to_display_name(transpose_note(chord.root, interval + capo)))
    return names


def chord_notes_text(chord: Chord, capo: int = 0) -> str:
    """Write the notes of a chord with the job each one does, such as 'C (root), E (3rd), G (5th)'."""
    names = chord_note_names(chord, capo)
    roles = CHORD_ROLES[chord.quality]
    text = ""
    for position in range(len(names)):
        if text != "":
            text = text + ", "
        text = text + names[position] + " (" + roles[position] + ")"
    return text


def pitch_name(pitch: int) -> str:
    """Turn a pitch number into a note name with its octave, such as 28 into 'E2'. Sharps are used (Tone needs them)."""
    return NOTES[pitch % 12] + str(pitch // 12)


def chord_pitch_names(chord: Chord, capo: int = 0) -> list[str]:
    """Return the note played by each sounding string, low to high, such as ['C3', 'E3', 'G3', 'C4', 'E4'] for C.

    A string is sounding if its fret is 0 or more. The note is the open string's pitch plus the fret number, plus the
    capo fret if there is a capo (the capo raises every string).
    """
    names = []
    for string_number in range(len(chord.frets)):
        if chord.frets[string_number] >= 0:
            names.append(pitch_name(OPEN_STRING_PITCHES[string_number] + chord.frets[string_number] + capo))
    return names


def display_pitch_name(pitch: str) -> str:
    """Write a pitch name the way the screen shows it: 'A#3' becomes 'Bb3'. (The sound itself uses the sharp name.)"""
    return to_display_name(pitch[:-1]) + pitch[-1]


def pitch_labels_text(pitches: list[str]) -> str:
    """Write a list of pitch names as one piece of text, such as 'F2, C3, Eb3', using the on-screen spelling."""
    names = []
    for pitch in pitches:
        names.append(display_pitch_name(pitch))
    return join_names(names)


def fret_text(frets: list[int]) -> str:
    """Write the six fret numbers as text, such as 'x 3 2 0 1 0' (x is a muted string)."""
    text = ""
    for fret in frets:
        if text != "":
            text = text + " "
        if fret == -1:
            text = text + "x"
        else:
            text = text + str(fret)
    return text


def find_chord_position(chords: list[Chord], name: str) -> int:
    """Return where the first chord with this name is in the list, or -1 if there is none."""
    for position in range(len(chords)):
        if chords[position].name == name:
            return position
    return -1


def distinct_chords(chords: list[Chord]) -> list[Chord]:
    """Return the chords in order with repeats removed, so each chord gets only one details button."""
    result: list[Chord] = []
    for chord in chords:
        if find_chord_position(result, chord.name) == -1:
            result.append(chord)
    return result


# ----------------------------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------------------------

def one_argument(name: str, value: str) -> list[Any]:
    """Return the argument list for a Button that sends one value (name) to its route."""
    return [Argument(name, value)]


def make_nav(state: State) -> Row:
    """Build the row of navigation buttons shown at the top of every page that has no inputs.

    Pages with inputs (setup, save, rename) have their own buttons instead, because a button sends every input on its
    page to its route. The "My progression" button only appears once the user has made a progression.
    """
    if len(state.current_progression) > 0:
        return Row(Button("Home", "index"), Button("My progression", "show_result"),
                   Button("Saved progressions", "view_saved"), Button("Mood guide", "view_mood_guide"),
                   style_gap="8px", style_flex_wrap="wrap")
    return Row(Button("Home", "index"), Button("Saved progressions", "view_saved"),
               Button("Mood guide", "view_mood_guide"), style_gap="8px", style_flex_wrap="wrap")


def make_setup_page(state: State, error_message: str) -> Page:
    """Build the setup page (the home page), with an error message at the top if there is one."""
    content: list[Any] = [Header("Chord Progression Generator"),
                          SVG(draw_guitar(), width=300, height=100, viewBox="0 0 300 100")]
    if error_message != "":
        content.append(error_message)
        content.append("\n")
    content.append("Pick a key and a mood, choose your options, and press Generate to get a chord progression ")
    content.append("with guitar fingering diagrams.\n")
    content.append(Header("Key and mood", 2))
    content.append("Key: ")
    content.append(SelectBox("key", KEY_OPTIONS, state.key))
    content.append("\n")
    content.append("Mood: ")
    content.append(SelectBox("mood", MOOD_OPTIONS, state.mood))
    content.append("\n")
    content.append("Not sure what the moods mean? Open the Mood guide below.\n")
    content.append(Header("Options", 2))
    content.append("Number of chords: ")
    content.append(SelectBox("length", LENGTH_OPTIONS, str(state.length)))
    content.append("\n")
    content.append(CheckBox("use_sevenths", state.use_sevenths))
    content.append(" Include 7th chords\n")
    content.append(CheckBox("beginner_mode", state.beginner_mode))
    content.append(" Beginner mode (open chords only; a capo is suggested if the key needs one)\n")
    content.append(HorizontalRule())
    content.append(Button("Generate", "generate"))
    content.append(Header("Explore", 2))
    content.append(Row(Button("Saved progressions", "open_saved"), Button("Mood guide", "open_mood_guide"),
                       style_gap="8px", style_flex_wrap="wrap"))
    return Page(state, content)


@route
def index(state: State) -> Page:
    """Show the setup page."""
    return make_setup_page(state, "")


def remember_choices(state: State, key: str, mood: str, length: int, use_sevenths: bool, beginner_mode: bool) -> None:
    """Store the choices from the setup page in the state, so the page shows them again when the user comes back."""
    state.key = key
    state.mood = mood
    state.length = length
    state.use_sevenths = use_sevenths
    state.beginner_mode = beginner_mode


@route
def generate(state: State, key: str, mood: str, length: int, use_sevenths: bool, beginner_mode: bool) -> Page:
    """Save the user's choices in the state, build a progression from them, and show it.

    Every input on the setup page is sent to this route, so each one needs a parameter with the same name.
    If beginner mode is on and the progression needs barre chords, look for a capo fret that avoids them (the chords
    shown are then the shapes to play with the capo). If the mood's main pattern cannot work with any capo, its other
    patterns are tried. If nothing works, show an error on the setup page instead.
    """
    remember_choices(state, key, mood, length, use_sevenths, beginner_mode)
    chords = build_current_progression(key, 0, mood, use_sevenths, length)
    barre_names = barre_chord_names(chords)
    capo = 0
    pattern = 0
    if beginner_mode and len(barre_names) > 0:
        pattern, capo = find_beginner_options(key, mood, use_sevenths, length)
        if pattern == -1:
            return make_setup_page(state, barre_error_message(barre_names))
        chords = shift_chords(build_current_progression(key, 0, mood, use_sevenths, length, pattern), -capo)
    state.transpose_steps = 0
    state.capo = capo
    state.pattern = pattern
    state.progression_key = key
    state.progression_mood = mood
    state.current_progression = chords
    return show_result(state)


def make_result_page(state: State, message: str) -> Page:
    """Build the result page, with a message (an error or a confirmation) near the top if there is one."""
    content: list[Any] = [make_nav(state)]
    if message != "":
        content.append(message)
        content.append("\n")
    color = mood_color(state.progression_mood)
    current_key = transposed_key_name(state.progression_key, state.transpose_steps)
    transposed = describe_transpose(state.progression_key, state.transpose_steps)
    if transposed != "":
        transposed = transposed + "\n"
    capo_text = ""
    if state.pattern > 0:
        used = pattern_text(MOOD_TEMPLATES[state.progression_mood][state.pattern])
        capo_text = ("Beginner mode used the pattern " + used + ", because the main " + state.progression_mood
                     + " pattern needs barre chords here.\n")
    if state.capo > 0:
        capo_text = capo_text + describe_capo(current_key, state.capo) + "\n"
        capo_text = capo_text + "Sounds like: " + sounding_chords_text(state.current_progression, state.capo) + "\n"
    content.append(Div(Header("Your Progression", style_color=color),
                       state.progression_mood + " progression in " + current_key + "\n", transposed, capo_text,
                       style_border=card_border(color), style_border_radius=CARD_RADIUS,
                       style_padding=CARD_PADDING, style_margin=CARD_MARGIN))
    for chord in state.current_progression:
        content.append(make_chord_block(chord, RESULT_DIAGRAM_WIDTH, color, state.capo))
    content.append("\n")
    content.append(Header("Look closer at a chord", 2))
    for chord in distinct_chords(state.current_progression):
        content.append(Button(display_chord_name(chord), "chord_detail", one_argument("name", chord.name)))
    content.append(Header("Transpose", 2))
    content.append(Button("Down a half step", "transpose_down"))
    content.append(Button("Up a half step", "transpose_up"))
    if state.transpose_steps != 0:
        content.append(Button("Back to original key", "reset_transpose"))
    content.append(Header("Keep it", 2))
    content.append(Button("Save this progression", "save_page"))
    return Page(state, content)


@route
def show_result(state: State) -> Page:
    """Show the current progression."""
    return make_result_page(state, "")


def change_transpose(state: State, change: int) -> Page:
    """Move the progression by some half steps and show it.

    The chords themselves are moved, so this does not depend on the choices on the setup page. If beginner mode is on
    and the new key needs barre chords, a capo fret is looked for again. If there is none, nothing changes and an
    error is shown instead.
    """
    new_steps = state.transpose_steps + change
    # The chords as they sound (the shapes sound state.capo half steps higher), moved by the change
    sounding_chords = shift_chords(state.current_progression, state.capo + change)
    chords = sounding_chords
    barre_names = barre_chord_names(sounding_chords)
    capo = 0
    if state.beginner_mode and len(barre_names) > 0:
        capo = find_capo_for_chords(sounding_chords)
        if capo == -1:
            return make_result_page(state, transpose_error_message(barre_names))
        chords = shift_chords(sounding_chords, -capo)
    state.transpose_steps = new_steps
    state.capo = capo
    state.current_progression = chords
    return show_result(state)


@route
def transpose_up(state: State) -> Page:
    """Move the progression up one half step."""
    return change_transpose(state, 1)


@route
def transpose_down(state: State) -> Page:
    """Move the progression down one half step."""
    return change_transpose(state, -1)


@route
def reset_transpose(state: State) -> Page:
    """Move the progression back to the key the user originally chose."""
    return change_transpose(state, -state.transpose_steps)


def make_save_page(state: State, message: str, typed_name: str) -> Page:
    """Build the page where the user names a progression, with an error message if there is one.

    typed_name is put back in the text box, so the user does not have to retype it after an error.
    """
    current_key = transposed_key_name(state.progression_key, state.transpose_steps)
    content: list[Any] = [Header("Save Progression")]
    if message != "":
        content.append(message)
        content.append("\n")
    content.append("Saving: " + state.progression_mood + " progression in " + current_key + " (" + chords_text(
        state.current_progression) + ")" + capo_suffix(state.capo))
    content.append("\n")
    content.append("Name: ")
    content.append(TextBox("progression_name", typed_name))
    content.append("\n")
    content.append(Button("Save", "save_progression"))
    content.append(Button("Cancel", "cancel_save"))
    return Page(state, content)


@route
def save_page(state: State) -> Page:
    """Show the page where the user names the progression they want to save."""
    return make_save_page(state, "", "")


@route
def save_progression(state: State, progression_name: str) -> Page:
    """Save the current progression under the name the user typed.

    The name must not be empty and must not match a name that is already saved (capital letters are ignored).
    The key is saved as it is shown now, so a transposed progression is saved in its transposed key. The capo fret
    is saved too, because the saved chords are the shapes that are played with it.
    """
    name = progression_name.strip()
    if name == "":
        return make_save_page(state, "Please type a name for your progression.", "")
    if name_is_taken(state.saved_progressions, name, -1):
        message = 'You already have a progression named "' + name + '". Choose a different name.'
        return make_save_page(state, message, name)
    current_key = transposed_key_name(state.progression_key, state.transpose_steps)
    state.saved_progressions.append(
        Progression(name, state.progression_mood, current_key, state.current_progression[:], state.capo))
    return make_result_page(state, 'Saved "' + name + '".')


@route
def cancel_save(state: State, progression_name: str) -> Page:
    """Go back to the result page without saving.

    Every input on a page is sent to the route that a button points to, so this route needs a parameter for the
    text box even though it does not use it.
    """
    return show_result(state)


# ----------------------------------------------------------------------------------------------
# Chord detail page: a big diagram, the notes in the chord, and the sound of the chord
# ----------------------------------------------------------------------------------------------

CHORD_GONE = "That chord is no longer in your progression."


def make_listen_content(chord: Chord, capo: int) -> list:
    """Build the sound part of the detail page: a strum of the whole chord and a button for each string's note.

    Drafter plays one note at a time, so the strum plays the notes quickly one after another, low to high.
    """
    pitches = chord_pitch_names(chord, capo)
    strum_notes: list[Any] = []
    for pitch in pitches:
        strum_notes.append((pitch, 1))
    content: list[Any] = [Header("Listen", 2), "Strum the chord: ",
                          Melody(strum_notes, tempo=300, waveform="triangle"), "\n"]
    content.append("Or listen to one string at a time:\n")
    for pitch in pitches:
        content.append(Div(display_pitch_name(pitch), "\n", Tone(pitch, duration=1000, waveform="triangle"),
                           style_display="inline-block", style_padding="8px"))
    content.append("\n")
    return content


def make_caged_block(shape: CagedShape, chord: Chord) -> Div:
    """Build the block for one CAGED shape: its label, its diagram, and its fret numbers."""
    label = shape.letter + " shape, "
    if shape.start_fret == 0:
        label = label + "open position"
    else:
        label = label + "starts at fret " + str(shape.start_fret)
    if shape.frets == chord.frets:
        label = label + " (the diagram above)"
    diagram = SVG(draw_diagram(shape.frets), width=100, height=130, viewBox="0 0 100 130")
    return Div(label, "\n", diagram, "\n", fret_text(shape.frets), style_border=card_border(NEUTRAL_COLOR),
               style_border_radius=CARD_RADIUS, style_padding=CARD_PADDING, style_margin=CARD_MARGIN,
               style_display="inline-block")


def make_caged_content(chord: Chord, capo: int) -> list:
    """Build the part of the detail page that shows all five CAGED shapes of the chord, lowest on the neck first.

    With a capo, the shapes shown are for the chord that is heard, played without the capo.
    """
    target = chord
    if capo > 0:
        target = Chord(chord.name, transpose_note(chord.root, capo), chord.quality, [], False)
    content: list[Any] = [Header("Five ways to play " + display_chord_name(target) + " (the CAGED system)", 2)]
    if capo > 0:
        content.append("These are the ways to play the sounding chord without a capo.\n")
    content.append("These are the shapes of the open C, A, G, E, and D chords, slid up the neck to the right place. ")
    content.append("They are listed from the lowest place on the neck to the highest.\n")
    for shape in caged_shapes(target.root, target.quality):
        content.append(make_caged_block(shape, target))
    content.append("\n")
    return content


def make_detail_page(chord: Chord, state: State) -> Page:
    """Build the detail page for one chord."""
    name = display_chord_name(chord)
    capo = state.capo
    content: list[Any] = [make_nav(state), Header(name)]
    content.append(name + " is a " + QUALITY_LABEL[chord.quality] + ".\n")
    if capo > 0:
        content.append("With the capo on fret " + str(capo) + ", this shape sounds as "
                       + sounding_chord_name(chord, capo) + ". The notes below are the ones you hear.\n")
    if len(chord.frets) != 6:
        content.append("This chord does not have a fingering in the program yet.\n")
        content.append(Header("Notes", 2))
        content.append("Notes in the chord: " + chord_notes_text(chord, capo) + "\n")
    else:
        if chord.is_barre:
            content.append("It is a barre chord: one finger holds down several strings across the neck.\n")
        else:
            content.append("It is an open chord, so no barre is needed.\n")
        content.append(SVG(draw_diagram(chord.frets), width=200, height=260, viewBox="0 0 100 130"))
        content.append("\n")
        content.append(Header("Notes", 2))
        content.append("Frets, low E string to high e string: " + fret_text(chord.frets))
        content.append(" (x means do not play that string, 0 means an open string)\n")
        content.append("Notes in the chord: " + chord_notes_text(chord, capo) + "\n")
        content.append("Notes the strings play, low to high: " + pitch_labels_text(chord_pitch_names(chord, capo))
                       + "\n")
        content.extend(make_listen_content(chord, capo))
        content.extend(make_caged_content(chord, capo))
    return Page(state, content)


@route
def chord_detail(state: State, name: str) -> Page:
    """Show the detail page for the chord with this name from the current progression.

    The button sends the chord's name instead of a list position, so a chord that appears twice shows the same page.
    If the chord is not in the progression any more (for example after transposing), the result page is shown.
    """
    position = find_chord_position(state.current_progression, name)
    if position == -1:
        return make_result_page(state, CHORD_GONE)
    return make_detail_page(state.current_progression[position], state)


# ----------------------------------------------------------------------------------------------
# Mood guide page: what each mood is, its Roman numeral pattern, and an example in the key of G
# ----------------------------------------------------------------------------------------------

def pattern_text(numerals: list[str]) -> str:
    """Write a list of Roman numerals as one line of text, such as 'I - V - vi - IV'."""
    text = ""
    for numeral in numerals:
        if text != "":
            text = text + " - "
        text = text + numeral
    return text


def make_mood_guide_page(state: State, message: str) -> Page:
    """Build the mood guide page: every mood with its description, pattern, and an example in the key of G."""
    content: list[Any] = [make_nav(state), Header("Mood Guide")]
    if message != "":
        content.append(message)
        content.append("\n")
    content.append("Each mood is a pattern of Roman numerals. The numeral says which note of the key's scale the chord "
                   "starts on (I is the first note, V is the fifth). A capital letter means a major chord, a small "
                   "letter means a minor chord, and a 7 means a seventh chord.\n")
    content.append("The examples are all in the key of " + GUIDE_KEY + " and follow your 7th chord choice.\n")
    for mood in MOOD_OPTIONS:
        color = mood_color(mood)
        example = build_current_progression(GUIDE_KEY, 0, mood, state.use_sevenths, 4)
        barre_note = ""
        barre_names = barre_chord_names(example)
        if len(barre_names) > 0:
            barre_note = "This one needs barre chords: " + join_names(barre_names) + "."
            if state.beginner_mode:
                pattern, capo = find_beginner_options(GUIDE_KEY, mood, state.use_sevenths, 4)
                if pattern == -1:
                    barre_note = barre_note + " Beginner mode would not allow it."
                else:
                    barre_note = barre_note + " Beginner mode would use"
                    if pattern > 0:
                        barre_note = barre_note + " the pattern " + pattern_text(MOOD_TEMPLATES[mood][pattern])
                    if pattern > 0 and capo > 0:
                        barre_note = barre_note + " and"
                    if capo > 0:
                        barre_note = barre_note + " a capo on fret " + str(capo)
                    barre_note = barre_note + "."
            barre_note = barre_note + "\n"
        content.append(Div(Header(mood, 2, style_color=color), MOOD_DESCRIPTIONS[mood] + "\n",
                           "Pattern: " + pattern_text(MOOD_TEMPLATES[mood][0]) + "\n",
                           "In " + GUIDE_KEY + ": " + chords_text(example) + "\n", barre_note,
                           Button("Use " + mood, "choose_mood", one_argument("mood", mood)),
                           style_border=card_border(color), style_border_radius=CARD_RADIUS,
                           style_padding=CARD_PADDING, style_margin=CARD_MARGIN))
    return Page(state, content)


@route
def open_mood_guide(state: State, key: str, mood: str, length: int, use_sevenths: bool, beginner_mode: bool) -> Page:
    """Show the mood guide from the setup page, keeping the choices the user has made there.

    Every input on the setup page is sent to this route, so it needs a parameter for each one.
    """
    remember_choices(state, key, mood, length, use_sevenths, beginner_mode)
    return make_mood_guide_page(state, "")


@route
def view_mood_guide(state: State) -> Page:
    """Show the mood guide (from the result page, which has no inputs)."""
    return make_mood_guide_page(state, "")


@route
def choose_mood(state: State, mood: str) -> Page:
    """Make the chosen mood the current mood and go back to the setup page, which shows it in the mood dropdown."""
    if mood not in MOOD_OPTIONS:
        return make_mood_guide_page(state, "That mood does not exist.")
    state.mood = mood
    return make_setup_page(state, "Mood set to " + mood + ". Press Generate to make a progression.")


# ----------------------------------------------------------------------------------------------
# Saved progressions: list, view, rename, and delete
# ----------------------------------------------------------------------------------------------

NO_LONGER_EXISTS = "That progression no longer exists."


def make_saved_page(state: State, message: str) -> Page:
    """Build the page that lists every saved progression, with a message near the top if there is one."""
    content: list[Any] = [make_nav(state), Header("Saved Progressions")]
    if message != "":
        content.append(message)
        content.append("\n")
    if len(state.saved_progressions) == 0:
        content.append("Nothing saved yet. Make a progression and press 'Save this progression'.")
        content.append("\n")
    for progression in state.saved_progressions:
        color = mood_color(progression.mood)
        title = progression.name + " (" + progression.mood + " in " + progression.key + ")"
        content.append(Div(Header(title, 2, style_color=color),
                           chords_text(progression.chords) + capo_suffix(progression.capo) + "\n",
                           Row(Button("View", "view_progression", one_argument("name", progression.name)),
                               Button("Rename", "rename_page", one_argument("name", progression.name)),
                               Button("Delete", "confirm_delete", one_argument("name", progression.name)),
                               style_gap="8px", style_flex_wrap="wrap"),
                           style_border=card_border(color), style_border_radius=CARD_RADIUS,
                           style_padding=CARD_PADDING, style_margin=CARD_MARGIN))
    return Page(state, content)


@route
def open_saved(state: State, key: str, mood: str, length: int, use_sevenths: bool, beginner_mode: bool) -> Page:
    """Show the saved progressions from the setup page, keeping the choices the user has made there.

    Every input on the setup page is sent to this route, so it needs a parameter for each one.
    """
    remember_choices(state, key, mood, length, use_sevenths, beginner_mode)
    return make_saved_page(state, "")


@route
def view_saved(state: State) -> Page:
    """Show the list of saved progressions."""
    return make_saved_page(state, "")


@route
def view_progression(state: State, name: str) -> Page:
    """Show one saved progression, picked by its name, with a diagram for each chord."""
    position = find_position(state.saved_progressions, name)
    if position == -1:
        return make_saved_page(state, NO_LONGER_EXISTS)
    progression = state.saved_progressions[position]
    color = mood_color(progression.mood)
    content: list[Any] = [make_nav(state), Header(progression.name, style_color=color)]
    content.append(progression.mood + " progression in " + progression.key)
    content.append("\n")
    if progression.capo > 0:
        content.append(describe_capo(progression.key, progression.capo) + "\n")
        content.append("Sounds like: " + sounding_chords_text(progression.chords, progression.capo) + "\n")
    for chord in progression.chords:
        content.append(make_chord_block(chord, SAVED_DIAGRAM_WIDTH, color, progression.capo))
    content.append("\n")
    content.append(Row(Button("Rename", "rename_page", one_argument("name", progression.name)),
                       Button("Delete", "confirm_delete", one_argument("name", progression.name)),
                       style_gap="8px", style_flex_wrap="wrap"))
    return Page(state, content)


@route
def confirm_delete(state: State, name: str) -> Page:
    """Ask the user to confirm before the saved progression with this name is deleted.

    Nothing is deleted here. The "Yes, delete it" button goes to delete_progression, which does the deleting.
    """
    if find_position(state.saved_progressions, name) == -1:
        return make_saved_page(state, NO_LONGER_EXISTS)
    content: list[Any] = [Header("Delete Progression?")]
    content.append('Are you sure you want to delete "' + name + '"? This cannot be undone.\n')
    content.append(Row(Button("Yes, delete it", "delete_progression", one_argument("name", name)),
                       Button("No, keep it", "view_saved"), style_gap="8px", style_flex_wrap="wrap"))
    return Page(state, content)


@route
def delete_progression(state: State, name: str) -> Page:
    """Remove the saved progression with this name from the saved list."""
    position = find_position(state.saved_progressions, name)
    if position == -1:
        return make_saved_page(state, NO_LONGER_EXISTS)
    state.saved_progressions.pop(position)
    return make_saved_page(state, 'Deleted "' + name + '".')


def make_rename_page(state: State, name: str, message: str, typed_name: str) -> Page:
    """Build the page where the user types a new name for the saved progression called name."""
    content: list[Any] = [Header("Rename Progression")]
    if message != "":
        content.append(message)
        content.append("\n")
    content.append("Current name: " + name)
    content.append("\n")
    content.append("New name: ")
    content.append(TextBox("new_name", typed_name))
    content.append("\n")
    content.append(Button("Rename", "rename_progression", one_argument("name", name)))
    content.append(Button("Cancel", "cancel_rename", one_argument("name", name)))
    return Page(state, content)


@route
def rename_page(state: State, name: str) -> Page:
    """Show the page where the user types a new name for the saved progression called name."""
    if find_position(state.saved_progressions, name) == -1:
        return make_saved_page(state, NO_LONGER_EXISTS)
    return make_rename_page(state, name, "", name)


@route
def rename_progression(state: State, name: str, new_name: str) -> Page:
    """Give the saved progression called name the new name the user typed.

    The new name must not be empty and must not match the name of a different saved progression (capital letters are
    ignored, so a progression can be renamed to a different spelling of its own name).
    """
    position = find_position(state.saved_progressions, name)
    if position == -1:
        return make_saved_page(state, NO_LONGER_EXISTS)
    typed = new_name.strip()
    if typed == "":
        return make_rename_page(state, name, "Please type a name for your progression.", "")
    if name_is_taken(state.saved_progressions, typed, position):
        message = 'You already have a progression named "' + typed + '". Choose a different name.'
        return make_rename_page(state, name, message, typed)
    state.saved_progressions[position].name = typed
    return make_saved_page(state, 'Renamed to "' + typed + '".')


@route
def cancel_rename(state: State, name: str, new_name: str) -> Page:
    """Go back to the saved progressions without renaming.

    Every input on a page is sent to the route that a button points to, so this route needs a parameter for the
    text box even though it does not use it.
    """
    return make_saved_page(state, "")


# ----------------------------------------------------------------------------------------------
# Unit tests (assert_equal compares the actual result first and the expected result second)
# ----------------------------------------------------------------------------------------------

def chord_names(chords: list[Chord]) -> list[str]:
    """Return just the names of a list of chords, to keep the tests short."""
    names = []
    for chord in chords:
        names.append(chord.name)
    return names


# Note helpers
assert_equal(to_internal_name("Bb"), "A#")
assert_equal(to_internal_name("C"), "C")
assert_equal(to_display_name("A#"), "Bb")
assert_equal(to_display_name("F#"), "F#")
assert_equal(transpose_note("C", 2), "D")
assert_equal(transpose_note("B", 1), "C")
assert_equal(transpose_note("C", -1), "B")
assert_equal(get_scale("C"), ["C", "D", "E", "F", "G", "A", "B"])
assert_equal(get_scale("F"), ["F", "G", "A", "A#", "C", "D", "E"])
assert_equal(relative_major("A"), "C")
assert_equal(resolve_key("A", True), "C")
assert_equal(resolve_key("A", False), "A")
assert_equal(parse_key("C"), ("C", False))
assert_equal(parse_key("Am"), ("A", True))
assert_equal(parse_key("Bb"), ("A#", False))
assert_equal(parse_key("Bbm"), ("A#", True))
assert_equal(parse_key("F#m"), ("F#", True))
assert_equal(key_choice_name("A#", True), "Bbm")
assert_equal(key_choice_name("C#", False), "C#")
assert_equal(key_choice_name("G#", False), "G#")
assert_equal(key_choice_name("D#", False), "Eb")
assert_equal(key_choice_name("A#", False), "Bb")
assert_equal(key_choice_name("F#", False), "F#")
assert_equal(key_choice_name("G#", True), "G#m")
assert_equal(key_choice_name("C", False), "C")


def check_key_names() -> list[str]:
    """Return any keys whose dropdown name does not turn back into the same root note and major/minor choice."""
    problems = []
    for root in NOTES:
        for is_minor in [False, True]:
            if parse_key(key_choice_name(root, is_minor)) != (root, is_minor):
                problems.append(root)
    return problems


assert_equal(check_key_names(), [])
assert_equal(transposed_key_name("C", 2), "D")
assert_equal(transposed_key_name("G", 5), "C")
assert_equal(transposed_key_name("Am", 3), "Cm")
assert_equal(transposed_key_name("Bbm", 1), "Bm")
assert_equal(transposed_key_name("C", -1), "B")
assert_equal(transposed_key_name("A", 1), "Bb")
assert_equal(transposed_key_name("C#", 0), "C#")
assert_equal(transposed_key_name("G", 1), "G#")
assert_equal(transposed_key_name("F", 1), "F#")
assert_equal(transposed_key_name("C", 3), "Eb")
assert_equal(transposed_key_name("C", 12), "C")
assert_equal(describe_transpose("Am", 0), "")
assert_equal(describe_transpose("Am", 3), "Original key: Am (transposed up 3 half steps)")
assert_equal(describe_transpose("C", -1), "Original key: C (transposed down 1 half step)")

# Chord helpers
assert_equal(lookup_fingering("G"), [3, 2, 0, 0, 0, 3])
assert_equal(lookup_fingering("A#"), [-1, 1, 3, 3, 3, 1])  # B-flat major: the A shape slid up to fret 1
assert_equal(lookup_fingering("not a chord"), [])
assert_equal(shift_shape([-1, 0, 2, 2, 2, 0], 3), [-1, 3, 5, 5, 5, 3])  # muted strings stay muted
assert_equal(barre_fingering("F", "major"), [1, 3, 3, 2, 1, 1])  # E shape at fret 1
assert_equal(barre_fingering("F", "minor7"), [1, 3, 1, 1, 1, 1])
assert_equal(barre_fingering("G", "minor"), [3, 5, 5, 3, 3, 3])  # E shape at fret 3
assert_equal(barre_fingering("C", "minor"), [-1, 3, 5, 5, 4, 3])  # A shape at fret 3
assert_equal(barre_fingering("B", "major"), [-1, 2, 4, 4, 4, 2])  # A shape at fret 2
assert_equal(barre_fingering("D#", "major"), [-1, 6, 8, 8, 8, 6])  # E-flat major: A shape at fret 6
assert_equal(lookup_fingering("Bm"), [-1, 2, 4, 4, 3, 2])
assert_equal(lookup_fingering("F#7"), [2, 4, 2, 3, 2, 2])
assert_equal(is_barre_shape(lookup_fingering("F")), True)
assert_equal(is_barre_shape(lookup_fingering("C")), False)
assert_equal(is_barre_shape([]), False)
assert_equal(numeral_to_chord("vi", get_scale("C"), False).name, "Am")
assert_equal(numeral_to_chord("V", get_scale("C"), True).name, "G7")
assert_equal(numeral_to_chord("IV", get_scale("C"), True).name, "Fmaj7")
assert_equal(numeral_to_chord("I7", get_scale("C"), False).name, "C7")
assert_equal(display_chord_name(make_chord("A#", "minor7")), "Bbm7")
assert_equal(needs_barre(make_chord("F", "major")), True)
assert_equal(needs_barre(make_chord("C", "major")), False)
assert_equal(needs_barre(make_chord("A#", "major")), True)  # B-flat major is a barre chord
assert_equal(needs_barre(make_chord("G", "minor")), True)
assert_equal(needs_barre(make_chord("E", "minor7")), False)
assert_equal(barre_chord_names(build_progression("C", "Joyful", False, 4)), ["F"])
assert_equal(barre_chord_names(build_progression("G", "Joyful", False, 4)), [])
assert_equal(barre_chord_names(build_progression("E", "Joyful", False, 4)), ["B", "C#m"])
assert_equal(barre_chord_names(build_progression("C", "Bluesy", False, 12)), ["F7"])  # F7 is a barre chord
assert_equal(barre_chord_names(build_progression("A", "Bluesy", False, 12)), [])  # A7, D7, E7 are all open
assert_equal(
    barre_error_message(["F", "Bm"]),
    "Beginner mode: this progression would include barre chords (F, Bm) and no capo position up to fret 7 avoids "
    "them. Choose another key or mood, or turn off beginner mode.")

# Diagrams
assert_equal(base_fret_for([3, 2, 0, 0, 0, 3]), 1)
assert_equal(base_fret_for([1, 3, 3, 2, 1, 1]), 1)
assert_equal(base_fret_for([-1, 7, 9, 9, 8, 7]), 7)  # played high up the neck, so the diagram starts at fret 7
assert_equal(base_fret_for([]), 1)
assert_equal(draw_diagram([]), "")
assert_equal(draw_diagram(CHORD_FINGERINGS["G"]).count("<circle"), 6)  # 3 fretted dots and 3 open-string circles
assert_equal(draw_diagram(CHORD_FINGERINGS["C"]).count("<circle"), 5)  # 3 fretted dots and 2 open-string circles
assert_equal(draw_diagram(CHORD_FINGERINGS["F"]).count('stroke-width="10"'), 1)  # the barre bar
assert_equal(draw_diagram(CHORD_FINGERINGS["C"]).count('stroke-width="10"'), 0)  # no barre in C
assert_equal("7fr" in draw_diagram([-1, 7, 9, 9, 8, 7]), True)
assert_equal("fr</text>" in draw_diagram(CHORD_FINGERINGS["G"]), False)  # no fret label near the nut


def check_every_chord() -> list[str]:
    """Return the names of any chords that are missing a fingering or would not fit in the diagram."""
    problems = []
    for root in NOTES:
        for quality in QUALITY_SUFFIX:
            name = root + QUALITY_SUFFIX[quality]
            frets = lookup_fingering(name)
            if len(frets) != 6:
                problems.append(name + " has no fingering")
            elif max(frets) - base_fret_for(frets) >= FRETS_SHOWN:
                problems.append(name + " does not fit in the diagram")
    return problems


assert_equal(check_every_chord(), [])  # all 60 chords (12 roots x 5 qualities) have a diagram that fits
assert_equal(len(CHORD_FINGERINGS), 60)

# Building progressions
assert_equal(chord_names(build_progression("C", "Joyful", False, 4)), ["C", "G", "Am", "F"])
assert_equal(chord_names(build_progression("G", "Joyful", False, 4)), ["G", "D", "Em", "C"])
assert_equal(chord_names(build_progression("C", "Sorrowful", False, 4))[0], "Am")
assert_equal(len(build_progression("C", "Joyful", False, 8)), 8)
assert_equal(len(build_progression("C", "Bluesy", False, 4)), 12)
assert_equal(chord_names(build_progression("C", "Joyful", True, 4)), ["Cmaj7", "G7", "Am7", "Fmaj7"])


def chord_display_names(chords: list[Chord]) -> list[str]:
    """Return the names of a list of chords as a guitarist would write them, to keep the tests short."""
    names = []
    for chord in chords:
        names.append(display_chord_name(chord))
    return names


assert_equal(chord_names(build_current_progression("G", 0, "Joyful", False, 4)), ["G", "D", "Em", "C"])
assert_equal(chord_display_names(build_current_progression("C", 2, "Joyful", False, 4)), ["D", "A", "Bm", "G"])
assert_equal(chord_names(build_current_progression("C", -1, "Joyful", False, 4)), ["B", "F#", "G#m", "E"])
assert_equal(chord_display_names(build_current_progression("Am", 3, "Sorrowful", False, 4)), ["Cm", "G#", "Eb", "Bb"])

# Routes
assert_has(index(State("C", "Joyful", 4, False, False, 0, [], [])), "Chord Progression Generator")
def made_state(key: str, mood: str, steps: int, chords: list[Chord], saved: list[Progression]) -> State:
    """Make a state as it is after a progression is generated (setup choices and the progression's own key and mood)."""
    return State(key, mood, 4, False, False, steps, chords, saved, 0, 0, key, mood)


assert_state(
    generate(State("C", "Peaceful", 8, True, False, 3, [], []), "C", "Joyful", 4, False, False),
    made_state("C", "Joyful", 0, [
        Chord("C", "C", "major", [-1, 3, 2, 0, 1, 0], False),
        Chord("G", "G", "major", [3, 2, 0, 0, 0, 3], False),
        Chord("Am", "A", "minor", [-1, 0, 2, 2, 1, 0], False),
        Chord("F", "F", "major", [1, 3, 3, 2, 1, 1], True),
    ], []))
assert_state(  # a minor key builds from its relative major, so A minor Sorrowful starts on Am
    generate(State("C", "Joyful", 4, False, False, 0, [], []), "Am", "Sorrowful", 4, False, False),
    made_state("Am", "Sorrowful", 0, [
        Chord("Am", "A", "minor", [-1, 0, 2, 2, 1, 0], False),
        Chord("F", "F", "major", [1, 3, 3, 2, 1, 1], True),
        Chord("C", "C", "major", [-1, 3, 2, 0, 1, 0], False),
        Chord("G", "G", "major", [3, 2, 0, 0, 0, 3], False),
    ], []))
assert_has(show_result(made_state("Am", "Sorrowful", 0, [make_chord("A", "minor")], [])), "Sorrowful progression in Am")
assert_state(  # beginner mode with only open chords works normally
    generate(State("C", "Joyful", 4, False, False, 0, [], []), "G", "Joyful", 4, False, True),
    State("G", "Joyful", 4, False, True, 0, [
        Chord("G", "G", "major", [3, 2, 0, 0, 0, 3], False),
        Chord("D", "D", "major", [-1, -1, 0, 2, 3, 2], False),
        Chord("Em", "E", "minor", [0, 2, 2, 0, 0, 0], False),
        Chord("C", "C", "major", [-1, 3, 2, 0, 1, 0], False),
    ], [], 0, 0, "G", "Joyful"))
assert_state(  # beginner mode where nothing works (Sorrowful in F): the choices are kept but there is no progression
    generate(State("G", "Joyful", 4, False, False, 0, [], []), "F", "Sorrowful", 4, False, True),
    State("F", "Sorrowful", 4, False, True, 0, [], []))
assert_has(
    generate(State("G", "Joyful", 4, False, False, 0, [], []), "F", "Sorrowful", 4, False, True),
    "Beginner mode: this progression would include barre chords (Bb, F) and no capo position up to fret 7 avoids "
    "them. Choose another key or mood, or turn off beginner mode.")
assert_state(  # beginner mode with a barre chord (F): a capo on fret 5 turns it into the open G shapes
    generate(State("G", "Joyful", 4, False, False, 0, [], []), "C", "Joyful", 4, False, True),
    State("C", "Joyful", 4, False, True, 0, build_progression("G", "Joyful", False, 4), [], 5, 0, "C", "Joyful"))
assert_state(  # Peaceful in C has no capo that helps, so beginner mode uses the alternate pattern I - vi - ii - V
    generate(State("G", "Joyful", 4, False, False, 0, [], []), "C", "Peaceful", 4, False, True),
    State("C", "Peaceful", 4, False, True, 0, build_progression("C", "Peaceful", False, 4, 1), [], 0, 1, "C",
          "Peaceful"))

# Transpose routes (the progression's own key stays the original key; transpose_steps tracks the shift)
assert_state(  # up one half step: G major becomes G-sharp (A-flat) major
    transpose_up(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), [])),
    made_state("G", "Joyful", 1, [
        make_chord("G#", "major"), make_chord("D#", "major"), make_chord("F", "minor"), make_chord("C#", "major"),
    ], []))
assert_state(  # down one half step: G major becomes F-sharp major
    transpose_down(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), [])),
    made_state("G", "Joyful", -1, [
        make_chord("F#", "major"), make_chord("C#", "major"), make_chord("D#", "minor"), make_chord("B", "major"),
    ], []))
assert_state(  # reset goes back to the original key
    reset_transpose(made_state("G", "Joyful", 3, build_progression("A#", "Joyful", False, 4), [])),
    made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []))
assert_has(
    show_result(made_state("Am", "Sorrowful", 3, [make_chord("C", "minor")], [])), "Sorrowful progression in Cm")
assert_has(
    show_result(made_state("Am", "Sorrowful", 3, [make_chord("C", "minor")], [])),
    "Original key: Am (transposed up 3 half steps)")
assert_state(  # beginner mode: transposing G up would need barre chords, so a capo on fret 1 keeps the open shapes
    transpose_up(State("G", "Joyful", 4, False, True, 0, build_progression("G", "Joyful", False, 4), [], 0, 0, "G",
                       "Joyful")),
    State("G", "Joyful", 4, False, True, 1, build_progression("G", "Joyful", False, 4), [], 1, 0, "G", "Joyful"))
assert_state(  # beginner mode with no capo that helps (Sorrowful in G moved down to F-sharp): nothing changes
    transpose_down(State("G", "Sorrowful", 4, False, True, 0, build_progression("G", "Sorrowful", False, 4), [], 0, 0,
                         "G", "Sorrowful")),
    State("G", "Sorrowful", 4, False, True, 0, build_progression("G", "Sorrowful", False, 4), [], 0, 0, "G",
          "Sorrowful"))
assert_has(
    transpose_down(State("G", "Sorrowful", 4, False, True, 0, build_progression("G", "Sorrowful", False, 4), [], 0, 0,
                         "G", "Sorrowful")),
    "Beginner mode: transposing would include barre chords (Ebm, B, F#, C#) and no capo position up to fret 7 "
    "avoids them. Turn off beginner mode on the setup page to transpose.")


def check_beginner_blues_transpose() -> list[str]:
    """Move an A blues down two half steps in beginner mode and return the new chord names and steps."""
    state = State("A", "Bluesy", 4, False, True, 0, build_progression("A", "Bluesy", False, 4), [], 0, 0, "A", "Bluesy")
    change_transpose(state, -2)  # G blues is G7, C7, D7, all open chords, so it is allowed
    return chord_names(state.current_progression) + [str(state.transpose_steps)]


assert_equal(check_beginner_blues_transpose(),
             ["G7", "G7", "G7", "G7", "C7", "C7", "G7", "G7", "D7", "C7", "G7", "G7", "-2"])

# Saving progressions
assert_equal(chords_text(build_progression("C", "Joyful", False, 4)), "C - G - Am - F")
assert_equal(chords_text(build_progression("A#", "Joyful", False, 4)), "Bb - F - Gm - Eb")
assert_equal(chords_text([]), "")
assert_equal(name_is_taken([Progression("Campfire", "Joyful", "G", [])], "campfire", -1), True)
assert_equal(name_is_taken([Progression("Campfire", "Joyful", "G", [])], "Beach", -1), False)
assert_equal(name_is_taken([], "Beach", -1), False)
assert_equal(name_is_taken([Progression("Campfire", "Joyful", "G", [])], "campfire", 0), False)  # its own name
assert_equal(name_is_taken([Progression("A", "Joyful", "G", []), Progression("B", "Joyful", "G", [])], "a", 1), True)
assert_has(
    save_page(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), [])),
    "Saving: Joyful progression in G (G - D - Em - C)")
assert_state(  # the progression is saved under the typed name, with the chords as they are now
    save_progression(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []), "Campfire"),
    made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), [
        Progression("Campfire", "Joyful", "G", [
            make_chord("G", "major"), make_chord("D", "major"), make_chord("E", "minor"), make_chord("C", "major"),
        ]),
    ]))
assert_state(  # spaces around the name are removed
    save_progression(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []), "  Campfire  "),
    made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), [
        Progression("Campfire", "Joyful", "G", build_progression("G", "Joyful", False, 4)),
    ]))
assert_state(  # a transposed progression is saved in the key it is shown in (G up 2 half steps is A)
    save_progression(made_state("G", "Joyful", 2, build_progression("A", "Joyful", False, 4), []), "Beach"),
    made_state("G", "Joyful", 2, build_progression("A", "Joyful", False, 4), [
        Progression("Beach", "Joyful", "A", build_progression("A", "Joyful", False, 4)),
    ]))
assert_has(
    save_progression(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []), "Campfire"),
    'Saved "Campfire".')
assert_state(  # a name that is only spaces is not saved
    save_progression(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []), "   "),
    made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []))
assert_has(
    save_progression(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []), "   "),
    "Please type a name for your progression.")
assert_state(  # a name that is already saved is not saved again (capital letters do not matter)
    save_progression(
        made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4),
                   [Progression("Campfire", "Joyful", "G", [])]),
        "campfire"),
    made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4),
               [Progression("Campfire", "Joyful", "G", [])]))
assert_has(
    save_progression(
        made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4),
                   [Progression("Campfire", "Joyful", "G", [])]),
        "campfire"),
    'You already have a progression named "campfire". Choose a different name.')
assert_has(
    cancel_save(made_state("G", "Joyful", 0, build_progression("G", "Joyful", False, 4), []), "abc"),
    "Joyful progression in G")


# CAGED shapes
def caged_shape_is_valid(root: str, quality: str, frets: list[int]) -> bool:
    """Check that a shape spells its chord: only chord notes, the root lowest, and the 3rd (and 7th) included.

    The 5th is allowed to be missing, because some of the C and G shapes for seventh chords leave it out.
    """
    chord_notes = []
    for interval in CHORD_INTERVALS[quality]:
        chord_notes.append(transpose_note(root, interval))
    played = chord_pitch_names(Chord("test", root, quality, frets, False))
    played_notes = []
    for pitch in played:
        played_notes.append(pitch[:-1])  # drop the octave number
    for note in played_notes:
        if note not in chord_notes:
            return False
    if played_notes[0] != root or chord_notes[1] not in played_notes:
        return False
    if len(chord_notes) == 4 and chord_notes[3] not in played_notes:
        return False
    return True


def all_caged_shapes_are_valid() -> bool:
    """Check every shape of every chord (12 roots, 5 qualities, 5 shapes each), and that none goes past fret 15."""
    for root in NOTES:
        for quality in QUALITY_SUFFIX:
            for shape in caged_shapes(root, quality):
                if not caged_shape_is_valid(root, quality, shape.frets):
                    return False
                if max(shape.frets) > 15 or len(shape.frets) != 6:
                    return False
    return True


assert_equal(caged_start_fret("C", "C"), 0)
assert_equal(caged_start_fret("C", "A"), 3)
assert_equal(caged_start_fret("C", "G"), 5)
assert_equal(caged_start_fret("C", "E"), 8)
assert_equal(caged_start_fret("C", "D"), 10)
assert_equal(caged_start_fret("G", "G"), 0)
assert_equal(caged_start_fret("A#", "E"), 6)
assert_equal(caged_frets("C", "major", "C"), [-1, 3, 2, 0, 1, 0])  # the open C chord
assert_equal(caged_frets("C", "major", "A"), [-1, 3, 5, 5, 5, 3])
assert_equal(caged_frets("C", "major", "G"), [8, 7, 5, 5, 5, 8])
assert_equal(caged_frets("C", "major", "E"), [8, 10, 10, 9, 8, 8])
assert_equal(caged_frets("C", "major", "D"), [-1, -1, 10, 12, 13, 12])
assert_equal(caged_frets("A", "minor7", "E"), [5, 7, 5, 5, 5, 5])
assert_equal(caged_frets("A#", "major", "G"), [6, 5, 3, 3, 3, 6])
assert_equal(len(caged_shapes("C", "major")), 5)
assert_equal(caged_shapes("C", "major")[1], CagedShape("A", 3, [-1, 3, 5, 5, 5, 3]))
assert_equal(  # for C the shapes go up the neck in the order C A G E D
    [caged_shapes("C", "major")[0].letter, caged_shapes("C", "major")[1].letter, caged_shapes("C", "major")[2].letter,
     caged_shapes("C", "major")[3].letter, caged_shapes("C", "major")[4].letter], ["C", "A", "G", "E", "D"])
assert_equal(  # for G the order is different: G E D C A
    [caged_shapes("G", "major")[0].letter, caged_shapes("G", "major")[1].letter, caged_shapes("G", "major")[2].letter,
     caged_shapes("G", "major")[3].letter, caged_shapes("G", "major")[4].letter], ["G", "E", "D", "C", "A"])
assert_equal(sorted(CAGED_SHAPES.keys()), sorted(QUALITY_SUFFIX.keys()))  # a set of shapes for every quality
assert_equal(sorted(CAGED_SHAPES["minor"].keys()), ["A", "C", "D", "E", "G"])
assert_equal(caged_shape_is_valid("C", "major", [-1, 3, 5, 5, 5, 3]), True)
assert_equal(caged_shape_is_valid("C", "major", [-1, 3, 5, 5, 5, 4]), False)  # a wrong note
assert_equal(all_caged_shapes_are_valid(), True)
# Chord detail page
def state_with_progression(key: str, mood: str) -> State:
    """Make a state that has just generated a progression, as the result page would have it."""
    state = State("C", "Joyful", 4, False, False, 0, [], [])
    generate(state, key, mood, 4, False, False)
    return state


assert_equal(chord_note_names(make_chord("C", "major")), ["C", "E", "G"])
assert_equal(chord_note_names(make_chord("A", "minor7")), ["A", "C", "E", "G"])
assert_equal(chord_note_names(make_chord("A#", "major")), ["Bb", "D", "F"])  # A# is shown as Bb
assert_equal(chord_note_names(make_chord("G", "dominant7")), ["G", "B", "D", "F"])
assert_equal(chord_note_names(make_chord("F", "major7")), ["F", "A", "C", "E"])
assert_equal(chord_note_names(make_chord("B", "minor")), ["B", "D", "F#"])
assert_equal(chord_notes_text(make_chord("C", "major")), "C (root), E (3rd), G (5th)")
assert_equal(chord_notes_text(make_chord("A", "minor")), "A (root), C (minor 3rd), E (5th)")
assert_equal(chord_notes_text(make_chord("G", "dominant7")), "G (root), B (3rd), D (5th), F (minor 7th)")
assert_equal(pitch_name(28), "E2")
assert_equal(pitch_name(52), "E4")
assert_equal(pitch_name(36), "C3")
assert_equal(pitch_name(30), "F#2")
assert_equal(chord_pitch_names(make_chord("C", "major")), ["C3", "E3", "G3", "C4", "E4"])  # the low E is muted
assert_equal(chord_pitch_names(make_chord("G", "dominant7")), ["G2", "B2", "D3", "G3", "B3", "F4"])
assert_equal(chord_pitch_names(make_chord("E", "major")), ["E2", "B2", "E3", "G#3", "B3", "E4"])
assert_equal(chord_pitch_names(Chord("Xyz", "C", "major", [], False)), [])
assert_equal(display_pitch_name("A#3"), "Bb3")
assert_equal(display_pitch_name("D#2"), "Eb2")
assert_equal(display_pitch_name("F#3"), "F#3")
assert_equal(display_pitch_name("C4"), "C4")
assert_equal(pitch_labels_text(chord_pitch_names(make_chord("F", "dominant7"))), "F2, C3, Eb3, A3, C4, F4")
assert_equal(pitch_labels_text([]), "")
assert_has(chord_detail(state_with_progression("C", "Bluesy"), "F7"), "F2, C3, Eb3, A3, C4, F4")
assert_equal(fret_text([-1, 3, 2, 0, 1, 0]), "x 3 2 0 1 0")
assert_equal(fret_text([1, 3, 3, 2, 1, 1]), "1 3 3 2 1 1")
assert_equal(fret_text([]), "")
assert_equal(find_chord_position(state_with_progression("C", "Joyful").current_progression, "G"), 1)
assert_equal(find_chord_position(state_with_progression("C", "Joyful").current_progression, "F#"), -1)
assert_equal(find_chord_position([], "C"), -1)
assert_equal(  # C appears twice, but gets only one details button
    chords_text(distinct_chords([make_chord("C", "major"), make_chord("G", "major"), make_chord("C", "major")])),
    "C - G")
assert_equal(len(distinct_chords(build_progression("C", "Bluesy", False, 12))), 3)  # C7, F7, G7
assert_equal(distinct_chords([]), [])
assert_has(show_result(state_with_progression("C", "Joyful")), "Look closer at a chord")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "C is a major chord.")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "It is an open chord, so no barre is needed.")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "high e string: x 3 2 0 1 0")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "Notes in the chord: C (root), E (3rd), G (5th)")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "C3, E3, G3, C4, E4")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "G"), "G is a major chord.")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "Am"), "Am is a minor chord.")
assert_has(chord_detail(state_with_progression("C", "Bluesy"), "F7"), "F7 is a dominant 7th chord.")
assert_has(chord_detail(state_with_progression("C", "Bluesy"), "F7"), "It is a barre chord")
assert_has(chord_detail(state_with_progression("Eb", "Joyful"), "A#"), "Bb is a major chord.")
assert_has(chord_detail(state_with_progression("Eb", "Joyful"), "A#"), "Bb (root), D (3rd), F (5th)")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "F#"), CHORD_GONE)  # the chord is not in the progression
assert_has(chord_detail(state_with_progression("C", "Joyful"), "F#"), "Your Progression")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "My progression")  # the nav row
assert_state(  # looking at a chord does not change anything in the state
    chord_detail(state_with_progression("C", "Joyful"), "C"), state_with_progression("C", "Joyful"))
assert_has(  # a chord with no fingering still gets a page, without a diagram or sound
    make_detail_page(Chord("C", "C", "major", [], False), state_with_progression("C", "Joyful")),
    "This chord does not have a fingering in the program yet.")

# CAGED shapes on the chord detail page
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "Five ways to play C (the CAGED system)")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "C shape, open position (the diagram above)")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "A shape, starts at fret 3")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "D shape, starts at fret 10")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "8 10 10 9 8 8")
assert_has(chord_detail(state_with_progression("Eb", "Joyful"), "A#"), "Five ways to play Bb (the CAGED system)")

# Key dropdown order: major keys first, then minor keys, each in alphabetical order
assert_equal(KEY_OPTIONS[:4], ["A", "Bb", "B", "C"])
assert_equal(KEY_OPTIONS[12:16], ["Am", "Bbm", "Bm", "Cm"])
assert_equal(KEY_OPTIONS[11], "G#")
assert_equal(KEY_OPTIONS[23], "G#m")
assert_equal(len(KEY_OPTIONS), 24)


def every_key_round_trips() -> bool:
    """Check that splitting each dropdown key into a root and back gives the same key name."""
    for key_choice in KEY_OPTIONS:
        root, is_minor = parse_key(key_choice)
        if key_choice_name(root, is_minor) != key_choice:
            return False
    return True


assert_equal(every_key_round_trips(), True)

# Mood guide page
def fresh_state() -> State:
    """Make a fresh state with the default choices and nothing saved, for the tests below."""
    return State("C", "Joyful", 4, False, False, 0, [], [])


assert_equal(pattern_text(["I", "V", "vi", "IV"]), "I - V - vi - IV")
assert_equal(pattern_text(["I7"]), "I7")
assert_equal(pattern_text([]), "")
assert_equal(sorted(MOOD_DESCRIPTIONS.keys()), sorted(MOOD_OPTIONS))  # every mood has a description
assert_has(view_mood_guide(fresh_state()), "Mood Guide")
for guide_mood in MOOD_OPTIONS:
    assert_has(view_mood_guide(fresh_state()), MOOD_DESCRIPTIONS[guide_mood])
    assert_has(view_mood_guide(fresh_state()), "Pattern: " + pattern_text(MOOD_TEMPLATES[guide_mood][0]))
assert_has(view_mood_guide(fresh_state()), "The examples are all in the key of G")
assert_has(view_mood_guide(fresh_state()), "In G: G - D - Em - C")  # Joyful in G
assert_has(view_mood_guide(fresh_state()), "In G: G - Bm - C - D")  # Peaceful in G
assert_has(view_mood_guide(fresh_state()), "In G: Em - C - G - D")  # Sorrowful in G
assert_has(view_mood_guide(fresh_state()), "In G: Em - D - C - Bm")  # Mysterious in G
assert_has(view_mood_guide(fresh_state()), "In G: G7 - G7 - G7 - G7 - C7 - C7 - G7 - G7 - D7 - C7 - G7 - G7")
assert_has(  # the examples stay in G whatever key the user picked
    view_mood_guide(State("Eb", "Joyful", 4, False, False, 0, [], [])), "In G: G - D - Em - C")
assert_has(  # 7th chords follow the user's choice
    view_mood_guide(State("C", "Joyful", 4, True, False, 0, [], [])), "In G: Gmaj7 - D7 - Em7 - Cmaj7")
assert_has(view_mood_guide(fresh_state()), "This one needs barre chords: Bm.")  # Peaceful and Mysterious use Bm
assert_has(
    view_mood_guide(State("C", "Joyful", 4, False, True, 0, [], [])),
    "This one needs barre chords: Bm. Beginner mode would use the pattern I - vi - ii - V.")
assert_has(  # Mysterious in G uses its alternate pattern too
    view_mood_guide(State("C", "Joyful", 4, False, True, 0, [], [])),
    "This one needs barre chords: Bm. Beginner mode would use the pattern ii - vi - IV - V.")
assert_has(open_mood_guide(fresh_state(), "D", "Peaceful", 8, True, False), "In G: Gmaj7 - Bm7 - Cmaj7 - D7")
assert_state(
    open_mood_guide(fresh_state(), "D", "Peaceful", 8, True, False), State("D", "Peaceful", 8, True, False, 0, [], []))
assert_state(choose_mood(fresh_state(), "Bluesy"), State("C", "Bluesy", 4, False, False, 0, [], []))
assert_has(choose_mood(fresh_state(), "Bluesy"), "Mood set to Bluesy. Press Generate to make a progression.")
assert_has(choose_mood(fresh_state(), "Bluesy"), "Chord Progression Generator")  # it goes back to the setup page
assert_state(choose_mood(fresh_state(), "Nope"), fresh_state())  # an unknown mood changes nothing
assert_has(choose_mood(fresh_state(), "Nope"), "That mood does not exist.")
assert_has(show_result(state_with_progression("C", "Joyful")), "Your Progression")

# Saved progressions page: view, rename, and delete
def state_with_two_saved() -> State:
    """Make a fresh state with two saved progressions (Campfire and Rainy day), for the tests below."""
    return State("C", "Joyful", 4, False, False, 0, [], [
        Progression("Campfire", "Joyful", "G", build_progression("G", "Joyful", False, 4)),
        Progression("Rainy day", "Sorrowful", "Am", build_progression("C", "Sorrowful", False, 4)),
    ])


def names_of_saved(state: State) -> list[str]:
    """Return the names of the saved progressions in a state, to keep the tests short."""
    names = []
    for progression in state.saved_progressions:
        names.append(progression.name)
    return names


def delete_the_same_one_twice() -> list[str]:
    """Press Delete twice for Campfire (as an old page's button could) and return the names left."""
    state = state_with_two_saved()
    delete_progression(state, "Campfire")
    delete_progression(state, "Campfire")
    return names_of_saved(state)


assert_equal(find_position(state_with_two_saved().saved_progressions, "Campfire"), 0)
assert_equal(find_position(state_with_two_saved().saved_progressions, "Rainy day"), 1)
assert_equal(find_position(state_with_two_saved().saved_progressions, "rainy day"), -1)  # the exact name is needed
assert_equal(find_position([], "Campfire"), -1)
assert_has(view_saved(state_with_two_saved()), "Campfire (Joyful in G)")
assert_has(view_saved(state_with_two_saved()), "G - D - Em - C")
assert_has(view_saved(state_with_two_saved()), "Rainy day (Sorrowful in Am)")
assert_has(view_saved(state_with_two_saved()), "Am - F - C - G")
assert_has(
    view_saved(State("C", "Joyful", 4, False, False, 0, [], [])),
    "Nothing saved yet. Make a progression and press 'Save this progression'.")
assert_has(  # the setup page's saved button keeps the choices the user made
    open_saved(State("C", "Joyful", 4, False, False, 0, [], []), "G", "Peaceful", 8, True, False),
    "Nothing saved yet. Make a progression and press 'Save this progression'.")
assert_state(
    open_saved(State("C", "Joyful", 4, False, False, 0, [], []), "G", "Peaceful", 8, True, False),
    State("G", "Peaceful", 8, True, False, 0, [], []))
assert_has(view_progression(state_with_two_saved(), "Rainy day"), "Sorrowful progression in Am")
assert_has(view_progression(state_with_two_saved(), "Nope"), NO_LONGER_EXISTS)

# Deleting
assert_equal(names_of_saved(delete_progression(state_with_two_saved(), "Campfire").state), ["Rainy day"])
assert_equal(names_of_saved(delete_progression(state_with_two_saved(), "Rainy day").state), ["Campfire"])
assert_has(delete_progression(state_with_two_saved(), "Campfire"), 'Deleted "Campfire".')
assert_equal(names_of_saved(delete_progression(state_with_two_saved(), "Nope").state), ["Campfire", "Rainy day"])
assert_has(delete_progression(state_with_two_saved(), "Nope"), NO_LONGER_EXISTS)
assert_equal(delete_the_same_one_twice(), ["Rainy day"])  # the second press does not delete a different progression

# Renaming
assert_has(rename_page(state_with_two_saved(), "Rainy day"), "Current name: Rainy day")
assert_has(rename_page(state_with_two_saved(), "Nope"), NO_LONGER_EXISTS)
assert_equal(
    names_of_saved(rename_progression(state_with_two_saved(), "Campfire", "Beach").state), ["Beach", "Rainy day"])
assert_equal(
    names_of_saved(rename_progression(state_with_two_saved(), "Campfire", "  Beach  ").state), ["Beach", "Rainy day"])
assert_has(rename_progression(state_with_two_saved(), "Campfire", "Beach"), 'Renamed to "Beach".')
assert_equal(  # a progression can be renamed to a different spelling of its own name
    names_of_saved(rename_progression(state_with_two_saved(), "Campfire", "campfire").state),
    ["campfire", "Rainy day"])
assert_equal(  # but not to the name of a different progression, even with different capital letters
    names_of_saved(rename_progression(state_with_two_saved(), "Campfire", "rainy DAY").state),
    ["Campfire", "Rainy day"])
assert_has(
    rename_progression(state_with_two_saved(), "Campfire", "rainy DAY"),
    'You already have a progression named "rainy DAY". Choose a different name.')
assert_equal(
    names_of_saved(rename_progression(state_with_two_saved(), "Campfire", "   ").state), ["Campfire", "Rainy day"])
assert_has(rename_progression(state_with_two_saved(), "Campfire", "   "), "Please type a name for your progression.")
assert_equal(
    names_of_saved(rename_progression(state_with_two_saved(), "Nope", "Beach").state), ["Campfire", "Rainy day"])
assert_has(rename_progression(state_with_two_saved(), "Nope", "Beach"), NO_LONGER_EXISTS)
assert_has(cancel_rename(state_with_two_saved(), "Campfire", "anything"), "Campfire (Joyful in G)")
assert_equal(
    names_of_saved(cancel_rename(state_with_two_saved(), "Campfire", "anything").state), ["Campfire", "Rainy day"])

# Navigation row, section headings, and the delete confirmation
assert_has(show_result(state_with_progression("C", "Joyful")), "Home")
assert_has(show_result(state_with_progression("C", "Joyful")), "My progression")
assert_has(show_result(state_with_progression("C", "Joyful")), "Saved progressions")
assert_has(show_result(state_with_progression("C", "Joyful")), "Mood guide")
assert_has(view_saved(fresh_state()), "Home")  # the nav is on the saved page too
assert_has(view_saved(fresh_state()), "Mood guide")
assert_has(view_mood_guide(fresh_state()), "Saved progressions")
assert_has(view_mood_guide(state_with_progression("C", "Joyful")), "My progression")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "G"), "Saved progressions")
assert_has(view_progression(state_with_two_saved(), "Campfire"), "Home")
assert_has(show_result(state_with_progression("C", "Joyful")), "Transpose")
assert_has(show_result(state_with_progression("C", "Joyful")), "Keep it")
assert_has(make_setup_page(fresh_state(), ""), "Key and mood")
assert_has(make_setup_page(fresh_state(), ""), "Options")
assert_has(make_setup_page(fresh_state(), ""), "Not sure what the moods mean? Open the Mood guide below.")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "Listen")
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "Notes")
assert_has(view_saved(state_with_two_saved()), "confirm_delete")  # Delete asks first
assert_has(view_progression(state_with_two_saved(), "Campfire"), "confirm_delete")
assert_has(
    confirm_delete(state_with_two_saved(), "Campfire"),
    'Are you sure you want to delete "Campfire"? This cannot be undone.')
assert_has(confirm_delete(state_with_two_saved(), "Campfire"), "Yes, delete it")
assert_has(confirm_delete(state_with_two_saved(), "Campfire"), "No, keep it")
assert_equal(  # asking does not delete anything
    names_of_saved(confirm_delete(state_with_two_saved(), "Campfire").state), ["Campfire", "Rainy day"])
assert_has(confirm_delete(state_with_two_saved(), "Nope"), NO_LONGER_EXISTS)
assert_equal(
    names_of_saved(confirm_delete(state_with_two_saved(), "Nope").state), ["Campfire", "Rainy day"])

# Visual polish: colors, Roman numerals, the guitar drawing
assert_equal(mood_color("Joyful"), "goldenrod")
assert_equal(mood_color("Sorrowful"), "steelblue")
assert_equal(mood_color("Bluesy"), "teal")
assert_equal(mood_color("Nope"), NEUTRAL_COLOR)
assert_equal(sorted(MOOD_COLORS.keys()), sorted(MOOD_OPTIONS))  # every mood has a color
assert_equal(card_border("teal"), "2px solid teal")


def numerals_of(chords: list[Chord]) -> list[str]:
    """Return just the Roman numerals of a list of chords, to keep the tests short."""
    numerals = []
    for chord in chords:
        numerals.append(chord.numeral)
    return numerals


assert_equal(numerals_of(build_progression("C", "Joyful", False, 4)), ["I", "V", "vi", "IV"])
assert_equal(numerals_of(build_progression("C", "Sorrowful", True, 4)), ["vi", "IV", "I", "V"])  # 7ths keep the numeral
assert_equal(numerals_of(build_progression("C", "Bluesy", False, 12))[4], "IV7")
assert_equal(numerals_of(build_progression("C", "Joyful", False, 8)), ["I", "V", "vi", "IV", "I", "V", "vi", "IV"])
assert_equal(numeral_to_chord("vi", get_scale("C"), False).numeral, "vi")
assert_equal(make_chord("C", "major").numeral, "")  # a chord made without a numeral has none
assert_equal(  # the numeral is not part of what makes two chords equal
    numeral_to_chord("I", get_scale("C"), False) == make_chord("C", "major"), True)
assert_equal(numerals_of(state_with_progression("G", "Peaceful").current_progression), ["I", "iii", "IV", "V"])
assert_has(show_result(state_with_progression("C", "Joyful")), "IV")
assert_equal(  # a saved progression keeps its numerals
    numerals_of(save_progression(state_with_progression("C", "Joyful"), "Mine").state.saved_progressions[0].chords),
    ["I", "V", "vi", "IV"])
assert_equal(  # and so does a transposed progression
    numerals_of(transpose_up(state_with_progression("C", "Joyful")).state.current_progression),
    ["I", "V", "vi", "IV"])
assert_equal("<circle" in draw_guitar(), True)
assert_equal("<line" in draw_guitar(), True)
assert_equal(draw_guitar().count("<line"), 11)  # 5 frets and 6 strings
assert_has(make_setup_page(fresh_state(), ""), "<circle")  # the guitar drawing's markup is part of the page

# Capo suggestions in beginner mode
def beginner_state(key: str, mood: str, use_sevenths: bool) -> State:
    """Make a state by generating a progression in beginner mode, to test the capo."""
    return generate(State("C", "Joyful", 4, False, False, 0, [], []), key, mood, 4, use_sevenths, True).state


assert_equal(find_beginner_capo("G", 0, "Joyful", False, 4), 0)  # already open chords, so no capo
assert_equal(find_beginner_capo("C", 0, "Joyful", False, 4), 5)  # G shapes with a capo on fret 5 sound in C
assert_equal(find_beginner_capo("A#", 0, "Joyful", False, 4), 3)  # G shapes with a capo on fret 3 sound in B-flat
assert_equal(find_beginner_capo("Bb", 0, "Joyful", True, 4), 3)
assert_equal(find_beginner_capo("A", 0, "Joyful", False, 4), 2)
assert_equal(find_beginner_capo("Am", 0, "Sorrowful", False, 4), 5)  # minor keys work too
assert_equal(find_beginner_capo("C", 0, "Peaceful", False, 4), -1)  # no capo helps (the F chord is the problem)
assert_equal(find_beginner_capo("F", 0, "Joyful", False, 4), -1)  # it would need a capo above fret 7
assert_equal(find_beginner_capo("C", 1, "Joyful", False, 4), 6)  # steps are counted from the chosen key
assert_equal(sounding_chord_name(make_chord("G", "major"), 3), "Bb")
assert_equal(sounding_chord_name(make_chord("E", "minor"), 3), "Gm")
assert_equal(sounding_chord_name(make_chord("C", "major7"), 2), "Dmaj7")
assert_equal(sounding_chord_name(make_chord("G", "major"), 0), "G")
assert_equal(
    sounding_chords_text(build_progression("G", "Joyful", False, 4), 3), "Bb - F - Gm - Eb")
assert_equal(sounding_chords_text([], 3), "")
assert_equal(capo_suffix(0), "")
assert_equal(capo_suffix(3), " (capo on fret 3)")
assert_equal(describe_capo("Bb", 0), "")
assert_equal(
    describe_capo("Bb", 3),
    "Capo on fret 3: play the shapes below with the capo on and they will sound in Bb. "
    "(Frets are counted from the capo.)")
assert_equal(chord_note_names(make_chord("G", "major"), 3), ["Bb", "D", "F"])
assert_equal(chord_note_names(make_chord("G", "major"), 0), ["G", "B", "D"])
assert_equal(chord_pitch_names(make_chord("G", "major"), 3), ["A#2", "D3", "F3", "A#3", "D4", "A#4"])
assert_equal(chord_notes_text(make_chord("G", "major"), 3), "Bb (root), D (3rd), F (5th)")
assert_equal(beginner_state("A#", "Joyful", False).capo, 3)
assert_equal(chords_text(beginner_state("A#", "Joyful", False).current_progression), "G - D - Em - C")
assert_equal(beginner_state("G", "Joyful", False).capo, 0)  # no capo when it is not needed
assert_equal(  # without beginner mode the barre chords are used and there is no capo
    generate(State("C", "Joyful", 4, False, False, 0, [], []), "A#", "Joyful", 4, False, False).state.capo, 0)
assert_equal(
    chords_text(generate(State("C", "Joyful", 4, False, False, 0, [], []), "A#", "Joyful", 4, False, False)
                .state.current_progression), "Bb - F - Gm - Eb")
assert_has(show_result(beginner_state("A#", "Joyful", False)), "Capo on fret 3")
assert_has(show_result(beginner_state("A#", "Joyful", False)), "they will sound in Bb")
assert_has(show_result(beginner_state("A#", "Joyful", False)), "Sounds like: Bb - F - Gm - Eb")
assert_has(show_result(beginner_state("A#", "Joyful", False)), "sounds as Gm")
assert_has(show_result(beginner_state("A#", "Joyful", False)), "Joyful progression in Bb")
assert_has(  # the chosen key stays the one that is heard
    show_result(beginner_state("C", "Joyful", False)), "Joyful progression in C")


def beginner_after_transposing(changes: list[int]) -> list[str]:
    """Generate a beginner Bb Joyful progression, move it by each change, and return [chords, capo, steps]."""
    state = beginner_state("A#", "Joyful", False)
    for change in changes:
        change_transpose(state, change)
    return [chords_text(state.current_progression), str(state.capo), str(state.transpose_steps)]


assert_equal(beginner_after_transposing([1]), ["G - D - Em - C", "4", "1"])  # B: capo 4
assert_equal(beginner_after_transposing([-2]), ["G - D - Em - C", "1", "-2"])  # A-flat (G#) major: capo 1
assert_equal(beginner_after_transposing([1, -1]), ["G - D - Em - C", "3", "0"])  # back to the original capo
assert_equal(beginner_after_transposing([2, -2]), ["G - D - Em - C", "3", "0"])
assert_has(
    transpose_up(beginner_state("A#", "Joyful", False)), "Capo on fret 4")
assert_has(
    transpose_up(beginner_state("A#", "Joyful", False)), "Sounds like: B - F# - G#m - E")
assert_equal(beginner_state("F", "Sorrowful", False).current_progression, [])  # no progression when nothing works
assert_equal(beginner_state("F", "Sorrowful", False).capo, 0)

# The detail page with a capo: it explains the shape, shows the heard notes, and the CAGED shapes of the heard chord
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "With the capo on fret 3, this shape sounds as")
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "Notes in the chord: Bb (root), D (3rd), F (5th)")
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "Bb2, D3, F3, Bb3, D4, Bb4")
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "high e string: 3 2 0 0 0 3")
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "Five ways to play Bb (the CAGED system)")
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "E shape, starts at fret 6")
assert_has(chord_detail(beginner_state("A#", "Joyful", False), "G"), "without a capo")

# Saving and viewing a progression that uses a capo
def beginner_saved_state() -> State:
    """Make a state with the beginner Bb progression saved as 'Beach'."""
    state = beginner_state("A#", "Joyful", False)
    save_progression(state, "Beach")
    return state


assert_equal(beginner_saved_state().saved_progressions[0].capo, 3)
assert_equal(beginner_saved_state().saved_progressions[0].key, "Bb")
assert_equal(chords_text(beginner_saved_state().saved_progressions[0].chords), "G - D - Em - C")
assert_has(view_saved(beginner_saved_state()), "Beach (Joyful in Bb)")
assert_has(view_saved(beginner_saved_state()), "G - D - Em - C (capo on fret 3)")
assert_has(view_progression(beginner_saved_state(), "Beach"), "Capo on fret 3")
assert_has(view_progression(beginner_saved_state(), "Beach"), "Sounds like: Bb - F - Gm - Eb")
assert_has(make_save_page(beginner_state("A#", "Joyful", False), "", ""), "(G - D - Em - C) (capo on fret 3)")
assert_equal(Progression("Old", "Joyful", "G", []).capo, 0)  # a progression made without a capo has none

# The mood guide mentions the capo in beginner mode
assert_has(
    view_mood_guide(State("C", "Joyful", 4, True, True, 0, [], [])),
    "This one needs barre chords: Bm7. Beginner mode would use a capo on fret 7.")

# Moving chords, finding a capo for chords, and the alternate patterns
assert_equal(chord_display_names(shift_chords(build_progression("C", "Joyful", False, 4), 2)), ["D", "A", "Bm", "G"])
assert_equal(chord_display_names(shift_chords(build_progression("C", "Joyful", False, 4), -2)), ["Bb", "F", "Gm", "Eb"])
assert_equal(numerals_of(shift_chords(build_progression("C", "Joyful", False, 4), 2)), ["I", "V", "vi", "IV"])
assert_equal(shift_chords([], 3), [])
assert_equal(find_capo_for_chords(build_progression("G", "Joyful", False, 4)), 0)
assert_equal(find_capo_for_chords(build_progression("A#", "Joyful", False, 4)), 3)
assert_equal(find_capo_for_chords(build_progression("F", "Sorrowful", False, 4)), -1)
assert_equal(find_capo_for_chords([]), 0)
assert_equal(find_beginner_options("G", "Joyful", False, 4), (0, 0))  # the main pattern, no capo
assert_equal(find_beginner_options("C", "Joyful", False, 4), (0, 5))  # the main pattern is preferred, with a capo
assert_equal(find_beginner_options("C", "Peaceful", False, 4), (1, 0))  # only the alternate pattern works
assert_equal(find_beginner_options("F", "Joyful", False, 4), (1, 3))  # the alternate pattern with a capo on fret 3
assert_equal(find_beginner_options("A#", "Mysterious", False, 4), (1, 3))
assert_equal(find_beginner_options("F", "Sorrowful", False, 4), (-1, -1))  # nothing works
assert_equal(find_beginner_options("F", "Sorrowful", True, 4), (0, 5))  # with 7th chords the main pattern works
assert_equal(find_beginner_options("C", "Bluesy", False, 12), (0, 3))  # A blues shapes with a capo on fret 3
assert_equal(chords_text(build_progression("C", "Peaceful", False, 4, 1)), "C - Am - Dm - G")
assert_equal(numerals_of(build_progression("C", "Peaceful", False, 4, 1)), ["I", "vi", "ii", "V"])
assert_equal(  # the main pattern is the default
    chords_text(build_progression("C", "Peaceful", False, 4)),
    chords_text(build_progression("C", "Peaceful", False, 4, 0)))
assert_equal(chords_text(beginner_state("C", "Peaceful", False).current_progression), "C - Am - Dm - G")
assert_equal(beginner_state("C", "Peaceful", False).pattern, 1)
assert_equal(beginner_state("C", "Peaceful", False).capo, 0)
assert_equal(beginner_state("F", "Joyful", False).capo, 3)
assert_equal(beginner_state("F", "Joyful", False).pattern, 1)
assert_equal(chords_text(beginner_state("F", "Joyful", False).current_progression), "D - G - A - D")
assert_equal(beginner_state("G", "Joyful", False).pattern, 0)  # the main pattern when it works
assert_has(
    show_result(beginner_state("C", "Peaceful", False)),
    "Beginner mode used the pattern I - vi - ii - V, because the main Peaceful pattern needs barre chords here.")
assert_has(show_result(beginner_state("F", "Joyful", False)), "Sounds like: F - Bb - C - F")
assert_has(show_result(beginner_state("F", "Joyful", False)), "Capo on fret 3")
assert_has(
    view_mood_guide(State("C", "Joyful", 4, False, True, 0, [], [])), "Beginner mode would use the pattern")
assert_has(  # a pattern and a capo together (Mysterious in G with 7th chords needs only a capo)
    view_mood_guide(State("C", "Joyful", 4, True, True, 0, [], [])), "Beginner mode would use a capo on fret 7.")


def pattern_after_transposing() -> list[str]:
    """Generate a beginner Peaceful progression in C, move it up 2 half steps, and return [chords, pattern, capo]."""
    state = beginner_state("C", "Peaceful", False)
    change_transpose(state, 2)
    return [chords_text(state.current_progression), str(state.pattern), str(state.capo)]


assert_equal(  # moving it up 2 gives D - Bm - Em - A (Bm is a barre), so the C shapes are played with a capo on fret 2
    pattern_after_transposing(), ["C - Am - Dm - G", "1", "2"])

# Visiting other pages does not change how the current progression is labeled
def stale_check() -> State:
    """Make a Joyful progression in G, then change the setup choices and visit other pages, and return the state."""
    state = generate(State("C", "Joyful", 4, False, False, 0, [], []), "G", "Joyful", 4, False, False).state
    open_mood_guide(state, "Eb", "Bluesy", 8, True, True)  # the setup page's choices are remembered
    open_saved(state, "A", "Peaceful", 4, False, False)
    choose_mood(state, "Mysterious")
    return state


assert_equal(stale_check().mood, "Mysterious")  # the setup page shows the newest choice
assert_equal(stale_check().progression_mood, "Joyful")  # the progression keeps its own mood
assert_equal(stale_check().progression_key, "G")
assert_has(show_result(stale_check()), "Joyful progression in G")
assert_equal(chords_text(stale_check().current_progression), "G - D - Em - C")
assert_has(save_page(stale_check()), "Saving: Joyful progression in G (G - D - Em - C)")
assert_equal(save_progression(stale_check(), "Mine").state.saved_progressions[0].mood, "Joyful")
assert_equal(save_progression(stale_check(), "Mine").state.saved_progressions[0].key, "G")
assert_equal(  # the progression moves, whatever the setup page shows
    chords_text(transpose_up(stale_check()).state.current_progression), "G# - Eb - Fm - C#")
assert_has(transpose_up(stale_check()), "Joyful progression in G#")
assert_equal(  # the setup choices do not change when the progression is moved
    [transpose_up(stale_check()).state.key, transpose_up(stale_check()).state.mood], ["A", "Mysterious"])

# ----------------------------------------------------------------------------------------------
# Start the site
# ----------------------------------------------------------------------------------------------

set_site_information(
    "Michael Catania Jr",
    "Builds guitar chord progressions with fingering diagrams from a key and a mood.",
    "Chord shapes are standard open and barre guitar chords.",
    "See the planning document in this repository.",
    ["https://github.com/mcataniajr/guitar-progression-generator"],
)

start_server(State("C", "Joyful", 4, False, False, 0, [], []))
