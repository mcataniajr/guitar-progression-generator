"""Guitar Chord Progression Generator: a Drafter web app."""
from dataclasses import dataclass
from drafter import *

# Website settings (these must come before start_server, so they are kept right after the imports)
hide_debug_information()
set_website_title("Guitar Progression Generator")
set_website_style("daub")
set_website_framed(False)

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


@dataclass
class Progression:
    """A named, saved chord progression."""
    name: str
    mood: str
    key: str
    chords: list[Chord]


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
            + "). Choose another key or turn off beginner mode.")


def transpose_error_message(barre_names: list[str]) -> str:
    """Write the error shown when beginner mode is on but transposing would need barre chords."""
    return ("Beginner mode: transposing would include barre chords (" + join_names(barre_names)
            + "). Turn off beginner mode on the setup page to transpose.")


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
    return make_chord(scale[degree], quality)


def build_progression(major_key: str, mood: str, use_sevenths: bool, length: int) -> list[Chord]:
    """Build a chord progression for a major key, a mood, and a length."""
    template = MOOD_TEMPLATES[mood][0]
    if mood == "Bluesy":
        length = len(template)  # the 12-bar blues always has 12 chords
    scale = get_scale(major_key)
    chords = []
    for position in range(length):
        numeral = template[position % len(template)]  # % repeats the pattern if the length is longer
        chords.append(numeral_to_chord(numeral, scale, use_sevenths))
    return chords


def build_current_progression(key_choice: str, steps: int, mood: str, use_sevenths: bool, length: int) -> list[Chord]:
    """Build the progression for a dropdown key choice that has been transposed by some number of half steps."""
    root, is_minor = parse_key(key_choice)
    new_root = transpose_note(root, steps)
    major_key = resolve_key(new_root, is_minor)
    return build_progression(major_key, mood, use_sevenths, length)


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


def make_chord_block(chord: Chord) -> Div:
    """Build the block for one chord: its name with its diagram below (or a note if it has no fingering yet)."""
    name = display_chord_name(chord)
    if len(chord.frets) == 6:
        diagram = SVG(draw_diagram(chord.frets), width=100, height=130, viewBox="0 0 100 130")
        return Div(name, "\n", diagram, style_display="inline-block", style_padding="8px")
    return Div(name, "\n", "(no diagram yet)", style_display="inline-block", style_padding="8px")


# ----------------------------------------------------------------------------------------------
# Chord detail helpers: which notes are in a chord, and which notes the guitar strings play
# ----------------------------------------------------------------------------------------------

def chord_note_names(chord: Chord) -> list[str]:
    """Return the notes that make up the chord (not counting repeats), such as ['C', 'E', 'G'] for C."""
    names = []
    for interval in CHORD_INTERVALS[chord.quality]:
        names.append(to_display_name(transpose_note(chord.root, interval)))
    return names


def chord_notes_text(chord: Chord) -> str:
    """Write the notes of a chord with the job each one does, such as 'C (root), E (3rd), G (5th)'."""
    names = chord_note_names(chord)
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


def chord_pitch_names(chord: Chord) -> list[str]:
    """Return the note played by each sounding string, low to high, such as ['C3', 'E3', 'G3', 'C4', 'E4'] for C.

    A string is sounding if its fret is 0 or more. The note is the open string's pitch plus the fret number.
    """
    names = []
    for string_number in range(len(chord.frets)):
        if chord.frets[string_number] >= 0:
            names.append(pitch_name(OPEN_STRING_PITCHES[string_number] + chord.frets[string_number]))
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
    result = []
    for chord in chords:
        if find_chord_position(result, chord.name) == -1:
            result.append(chord)
    return result


# ----------------------------------------------------------------------------------------------
# Routes (one thin working path: index -> generate -> show_result)
# ----------------------------------------------------------------------------------------------

def make_setup_page(state: State, error_message: str) -> Page:
    """Build the setup page, with an error message at the top if there is one."""
    content = [Header("Chord Progression Generator")]
    if error_message != "":
        content.append(error_message)
        content.append("\n")
    content.append("Pick a key, a mood, and a length, and get a chord progression.\n")
    content.append("Key: ")
    content.append(SelectBox("key", KEY_OPTIONS, state.key))
    content.append("\n")
    content.append("Mood: ")
    content.append(SelectBox("mood", MOOD_OPTIONS, state.mood))
    content.append("\n")
    content.append("Number of chords: ")
    content.append(SelectBox("length", LENGTH_OPTIONS, str(state.length)))
    content.append("\n")
    content.append(CheckBox("use_sevenths", state.use_sevenths))
    content.append(" Include 7th chords\n")
    content.append(CheckBox("beginner_mode", state.beginner_mode))
    content.append(" Beginner mode (no barre chords)\n")
    content.append(Button("Generate", "generate"))
    content.append(Button("Saved progressions", "open_saved"))
    content.append(Button("Mood guide", "open_mood_guide"))
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
    If beginner mode is on and the progression needs barre chords, show an error on the setup page instead.
    """
    remember_choices(state, key, mood, length, use_sevenths, beginner_mode)
    chords = build_current_progression(key, 0, mood, use_sevenths, length)
    barre_names = barre_chord_names(chords)
    if beginner_mode and len(barre_names) > 0:
        return make_setup_page(state, barre_error_message(barre_names))
    state.transpose_steps = 0
    state.current_progression = chords
    return show_result(state)


def make_result_page(state: State, message: str) -> Page:
    """Build the result page, with a message (an error or a confirmation) near the top if there is one."""
    content = [Header("Your Progression")]
    if message != "":
        content.append(message)
        content.append("\n")
    current_key = transposed_key_name(state.key, state.transpose_steps)
    content.append(state.mood + " progression in " + current_key + "\n")
    if state.transpose_steps != 0:
        content.append(describe_transpose(state.key, state.transpose_steps))
        content.append("\n")
    for chord in state.current_progression:
        content.append(make_chord_block(chord))
    content.append("\n")
    content.append("Look closer at a chord: ")
    for chord in distinct_chords(state.current_progression):
        content.append(Button(display_chord_name(chord), "chord_detail", [Argument("name", chord.name)]))
    content.append("\n")
    content.append(Button("Down a half step", "transpose_down"))
    content.append(Button("Up a half step", "transpose_up"))
    if state.transpose_steps != 0:
        content.append(Button("Back to original key", "reset_transpose"))
    content.append(Button("Save this progression", "save_page"))
    content.append(Button("Saved progressions", "view_saved"))
    content.append(Button("Mood guide", "view_mood_guide"))
    content.append(Button("Back", "index"))
    return Page(state, content)


@route
def show_result(state: State) -> Page:
    """Show the current progression."""
    return make_result_page(state, "")


def change_transpose(state: State, change: int) -> Page:
    """Move the progression by some half steps and show it.

    If beginner mode is on and the new key needs barre chords, nothing changes and an error is shown instead.
    """
    new_steps = state.transpose_steps + change
    chords = build_current_progression(state.key, new_steps, state.mood, state.use_sevenths, state.length)
    barre_names = barre_chord_names(chords)
    if state.beginner_mode and len(barre_names) > 0:
        return make_result_page(state, transpose_error_message(barre_names))
    state.transpose_steps = new_steps
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
    current_key = transposed_key_name(state.key, state.transpose_steps)
    content = [Header("Save Progression")]
    if message != "":
        content.append(message)
        content.append("\n")
    content.append("Saving: " + state.mood + " progression in " + current_key + " (" + chords_text(
        state.current_progression) + ")")
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
    The key is saved as it is shown now, so a transposed progression is saved in its transposed key.
    """
    name = progression_name.strip()
    if name == "":
        return make_save_page(state, "Please type a name for your progression.", "")
    if name_is_taken(state.saved_progressions, name, -1):
        message = 'You already have a progression named "' + name + '". Choose a different name.'
        return make_save_page(state, message, name)
    current_key = transposed_key_name(state.key, state.transpose_steps)
    state.saved_progressions.append(Progression(name, state.mood, current_key, state.current_progression[:]))
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


def make_listen_content(chord: Chord) -> list:
    """Build the sound part of the detail page: a strum of the whole chord and a button for each string's note.

    Drafter plays one note at a time, so the strum plays the notes quickly one after another, low to high.
    """
    pitches = chord_pitch_names(chord)
    strum_notes = []
    for pitch in pitches:
        strum_notes.append((pitch, 1))
    content = ["Strum the chord: ", Melody(strum_notes, tempo=300, waveform="triangle"), "\n"]
    content.append("Or listen to one string at a time:\n")
    for pitch in pitches:
        content.append(Div(display_pitch_name(pitch), "\n", Tone(pitch, duration=1000, waveform="triangle"),
                           style_display="inline-block", style_padding="8px"))
    content.append("\n")
    return content


def make_detail_page(chord: Chord, state: State) -> Page:
    """Build the detail page for one chord."""
    name = display_chord_name(chord)
    content = [Header(name)]
    content.append(name + " is a " + QUALITY_LABEL[chord.quality] + ".\n")
    if len(chord.frets) != 6:
        content.append("This chord does not have a fingering in the program yet.\n")
        content.append("Notes in the chord: " + chord_notes_text(chord) + "\n")
    else:
        if chord.is_barre:
            content.append("It is a barre chord: one finger holds down several strings across the neck.\n")
        else:
            content.append("It is an open chord, so no barre is needed.\n")
        content.append(SVG(draw_diagram(chord.frets), width=200, height=260, viewBox="0 0 100 130"))
        content.append("\n")
        content.append("Frets, low E string to high e string: " + fret_text(chord.frets))
        content.append(" (x means do not play that string, 0 means an open string)\n")
        content.append("Notes in the chord: " + chord_notes_text(chord) + "\n")
        content.append("Notes the strings play, low to high: " + pitch_labels_text(chord_pitch_names(chord)) + "\n")
        content.extend(make_listen_content(chord))
    content.append(Button("Back to my progression", "show_result"))
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
# Mood guide page: what each mood is, its Roman numeral pattern, and an example in the user's key
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
    """Build the mood guide page: every mood with its description, pattern, and an example in the chosen key."""
    content = [Header("Mood Guide")]
    if message != "":
        content.append(message)
        content.append("\n")
    content.append("Each mood is a pattern of Roman numerals. The numeral says which note of the key's scale the chord "
                   "starts on (I is the first note, V is the fifth). A capital letter means a major chord, a small "
                   "letter means a minor chord, and a 7 means a seventh chord.\n")
    content.append("The examples use your current key (" + state.key + ") and your 7th chord choice.\n")
    for mood in MOOD_OPTIONS:
        content.append("\n")
        content.append(mood + "\n")
        content.append(MOOD_DESCRIPTIONS[mood] + "\n")
        content.append("Pattern: " + pattern_text(MOOD_TEMPLATES[mood][0]) + "\n")
        example = build_current_progression(state.key, 0, mood, state.use_sevenths, 4)
        content.append("In " + state.key + ": " + chords_text(example) + "\n")
        barre_names = barre_chord_names(example)
        if len(barre_names) > 0:
            note = "This one needs barre chords: " + join_names(barre_names) + "."
            if state.beginner_mode:
                note = note + " Beginner mode would not allow it."
            content.append(note + "\n")
        content.append(Button("Use " + mood, "choose_mood", [Argument("mood", mood)]))
        content.append("\n")
    content.append("\n")
    if len(state.current_progression) > 0:
        content.append(Button("Back to my progression", "show_result"))
    content.append(Button("Back to setup", "index"))
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
    content = [Header("Saved Progressions")]
    if message != "":
        content.append(message)
        content.append("\n")
    if len(state.saved_progressions) == 0:
        content.append("Nothing saved yet. Make a progression and press 'Save this progression'.")
        content.append("\n")
    for progression in state.saved_progressions:
        content.append(progression.name + " (" + progression.mood + " in " + progression.key + ")")
        content.append("\n")
        content.append(chords_text(progression.chords))
        content.append("\n")
        content.append(Button("View", "view_progression", [Argument("name", progression.name)]))
        content.append(Button("Rename", "rename_page", [Argument("name", progression.name)]))
        content.append(Button("Delete", "delete_progression", [Argument("name", progression.name)]))
        content.append("\n")
    if len(state.current_progression) > 0:
        content.append(Button("Back to my progression", "show_result"))
    content.append(Button("Back to setup", "index"))
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
    content = [Header(progression.name)]
    content.append(progression.mood + " progression in " + progression.key)
    content.append("\n")
    for chord in progression.chords:
        content.append(make_chord_block(chord))
    content.append("\n")
    content.append(Button("Rename", "rename_page", [Argument("name", progression.name)]))
    content.append(Button("Delete", "delete_progression", [Argument("name", progression.name)]))
    content.append(Button("Back to saved progressions", "view_saved"))
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
    content = [Header("Rename Progression")]
    if message != "":
        content.append(message)
        content.append("\n")
    content.append("Current name: " + name)
    content.append("\n")
    content.append("New name: ")
    content.append(TextBox("new_name", typed_name))
    content.append("\n")
    content.append(Button("Rename", "rename_progression", [Argument("name", name)]))
    content.append(Button("Cancel", "cancel_rename", [Argument("name", name)]))
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
assert_equal(barre_error_message(["F", "Bm"]), "Beginner mode: this progression would include barre chords (F, Bm). "
             "Choose another key or turn off beginner mode.")

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
assert_state(
    generate(State("C", "Peaceful", 8, True, False, 3, [], []), "C", "Joyful", 4, False, False),
    State("C", "Joyful", 4, False, False, 0, [
        Chord("C", "C", "major", [-1, 3, 2, 0, 1, 0], False),
        Chord("G", "G", "major", [3, 2, 0, 0, 0, 3], False),
        Chord("Am", "A", "minor", [-1, 0, 2, 2, 1, 0], False),
        Chord("F", "F", "major", [1, 3, 3, 2, 1, 1], True),
    ], []))
assert_state(  # a minor key builds from its relative major, so A minor Sorrowful starts on Am
    generate(State("C", "Joyful", 4, False, False, 0, [], []), "Am", "Sorrowful", 4, False, False),
    State("Am", "Sorrowful", 4, False, False, 0, [
        Chord("Am", "A", "minor", [-1, 0, 2, 2, 1, 0], False),
        Chord("F", "F", "major", [1, 3, 3, 2, 1, 1], True),
        Chord("C", "C", "major", [-1, 3, 2, 0, 1, 0], False),
        Chord("G", "G", "major", [3, 2, 0, 0, 0, 3], False),
    ], []))
assert_has(
    show_result(State("Am", "Sorrowful", 4, False, False, 0, [make_chord("A", "minor")], [])),
    "Sorrowful progression in Am")
assert_state(  # beginner mode with only open chords works normally
    generate(State("C", "Joyful", 4, False, False, 0, [], []), "G", "Joyful", 4, False, True),
    State("G", "Joyful", 4, False, True, 0, [
        Chord("G", "G", "major", [3, 2, 0, 0, 0, 3], False),
        Chord("D", "D", "major", [-1, -1, 0, 2, 3, 2], False),
        Chord("Em", "E", "minor", [0, 2, 2, 0, 0, 0], False),
        Chord("C", "C", "major", [-1, 3, 2, 0, 1, 0], False),
    ], []))
assert_state(  # beginner mode with a barre chord (F) keeps the choices but makes no progression
    generate(State("G", "Joyful", 4, False, False, 0, [], []), "C", "Joyful", 4, False, True),
    State("C", "Joyful", 4, False, True, 0, [], []))
assert_has(
    generate(State("G", "Joyful", 4, False, False, 0, [], []), "C", "Joyful", 4, False, True),
    "Beginner mode: this progression would include barre chords (F). Choose another key or turn off beginner mode.")

# Transpose routes (the key chosen on the setup page stays as the original key; transpose_steps tracks the shift)
assert_state(  # up one half step: G major becomes G-sharp (A-flat) major
    transpose_up(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), [])),
    State("G", "Joyful", 4, False, False, 1, [
        make_chord("G#", "major"), make_chord("D#", "major"), make_chord("F", "minor"), make_chord("C#", "major"),
    ], []))
assert_state(  # down one half step: G major becomes F-sharp major
    transpose_down(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), [])),
    State("G", "Joyful", 4, False, False, -1, [
        make_chord("F#", "major"), make_chord("C#", "major"), make_chord("D#", "minor"), make_chord("B", "major"),
    ], []))
assert_state(  # reset goes back to the original key
    reset_transpose(State("G", "Joyful", 4, False, False, 3, [], [])),
    State("G", "Joyful", 4, False, False, 0, [
        make_chord("G", "major"), make_chord("D", "major"), make_chord("E", "minor"), make_chord("C", "major"),
    ], []))
assert_has(
    show_result(State("Am", "Sorrowful", 4, False, False, 3, [make_chord("C", "minor")], [])),
    "Sorrowful progression in Cm")
assert_has(
    show_result(State("Am", "Sorrowful", 4, False, False, 3, [make_chord("C", "minor")], [])),
    "Original key: Am (transposed up 3 half steps)")
assert_state(  # beginner mode: transposing G up needs barre chords, so nothing changes
    transpose_up(State("G", "Joyful", 4, False, True, 0, build_progression("G", "Joyful", False, 4), [])),
    State("G", "Joyful", 4, False, True, 0, build_progression("G", "Joyful", False, 4), []))
assert_has(
    transpose_up(State("G", "Joyful", 4, False, True, 0, build_progression("G", "Joyful", False, 4), [])),
    "Beginner mode: transposing would include barre chords (G#, Eb, Fm, C#). "
    "Turn off beginner mode on the setup page to transpose.")


def check_beginner_blues_transpose() -> list[str]:
    """Move an A blues down two half steps in beginner mode and return the new chord names and steps."""
    state = State("A", "Bluesy", 4, False, True, 0, build_progression("A", "Bluesy", False, 4), [])
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
    save_page(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), [])),
    "Saving: Joyful progression in G (G - D - Em - C)")
assert_state(  # the progression is saved under the typed name, with the chords as they are now
    save_progression(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []),
                     "Campfire"),
    State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), [
        Progression("Campfire", "Joyful", "G", [
            make_chord("G", "major"), make_chord("D", "major"), make_chord("E", "minor"), make_chord("C", "major"),
        ]),
    ]))
assert_state(  # spaces around the name are removed
    save_progression(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []),
                     "  Campfire  "),
    State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), [
        Progression("Campfire", "Joyful", "G", build_progression("G", "Joyful", False, 4)),
    ]))
assert_state(  # a transposed progression is saved in the key it is shown in (G up 2 half steps is A)
    save_progression(State("G", "Joyful", 4, False, False, 2, build_progression("A", "Joyful", False, 4), []),
                     "Beach"),
    State("G", "Joyful", 4, False, False, 2, build_progression("A", "Joyful", False, 4), [
        Progression("Beach", "Joyful", "A", build_progression("A", "Joyful", False, 4)),
    ]))
assert_has(
    save_progression(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []),
                     "Campfire"),
    'Saved "Campfire".')
assert_state(  # a name that is only spaces is not saved
    save_progression(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []), "   "),
    State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []))
assert_has(
    save_progression(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []), "   "),
    "Please type a name for your progression.")
assert_state(  # a name that is already saved is not saved again (capital letters do not matter)
    save_progression(
        State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4),
              [Progression("Campfire", "Joyful", "G", [])]),
        "campfire"),
    State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4),
          [Progression("Campfire", "Joyful", "G", [])]))
assert_has(
    save_progression(
        State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4),
              [Progression("Campfire", "Joyful", "G", [])]),
        "campfire"),
    'You already have a progression named "campfire". Choose a different name.')
assert_has(
    cancel_save(State("G", "Joyful", 4, False, False, 0, build_progression("G", "Joyful", False, 4), []), "abc"),
    "Joyful progression in G")


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
assert_has(show_result(state_with_progression("C", "Joyful")), "Look closer at a chord: ")
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
assert_has(chord_detail(state_with_progression("C", "Joyful"), "C"), "Back to my progression")
assert_state(  # looking at a chord does not change anything in the state
    chord_detail(state_with_progression("C", "Joyful"), "C"), state_with_progression("C", "Joyful"))
assert_has(  # a chord with no fingering still gets a page, without a diagram or sound
    make_detail_page(Chord("C", "C", "major", [], False), state_with_progression("C", "Joyful")),
    "This chord does not have a fingering in the program yet.")

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
assert_has(view_mood_guide(fresh_state()), "The examples use your current key (C)")
assert_has(view_mood_guide(fresh_state()), "In C: C - G - Am - F")  # Joyful in C
assert_has(view_mood_guide(State("G", "Joyful", 4, False, False, 0, [], [])), "In G: G - D - Em - C")
assert_has(  # a minor key uses its relative major's chords
    view_mood_guide(State("Am", "Joyful", 4, False, False, 0, [], [])), "In Am: C - G - Am - F")
assert_has(view_mood_guide(State("G", "Joyful", 4, True, False, 0, [], [])), "In G: Gmaj7 - D7 - Em7 - Cmaj7")
assert_has(view_mood_guide(fresh_state()), "This one needs barre chords: F.")  # Joyful in C needs the F barre chord
assert_has(
    view_mood_guide(State("C", "Joyful", 4, False, True, 0, [], [])),
    "This one needs barre chords: F. Beginner mode would not allow it.")
assert_has(open_mood_guide(fresh_state(), "G", "Peaceful", 8, True, False), "The examples use your current key (G)")
assert_state(
    open_mood_guide(fresh_state(), "G", "Peaceful", 8, True, False), State("G", "Peaceful", 8, True, False, 0, [], []))
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
