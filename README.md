# Guitar Chord Progression Generator

A Drafter web app that builds guitar chord progressions with fingering diagrams. Pick a key, a mood, a length, and
whether to use 7th chords, and the app shows the chords with a diagram for each one.

**Live site:** https://mcataniajr.github.io/guitar-progression-generator/

**Video walkthrough:** VIDEO LINK HERE (replace this with the public video link; the video is 5 minutes or less and
shows the address of the deployed site)

Made by Michael Catania Jr for a Computer Science final project at the University of Delaware.

## What it does
- **Generate a progression** from a key (major or minor), a mood (Joyful, Peaceful, Sorrowful, Mysterious, or
  Bluesy), a length (4 or 8 chords), and an option for 7th chords.
- **Fingering diagrams** for every chord, with the Roman numeral under each one.
- **Transpose** the progression up or down by half steps, or go back to the original key.
- **Beginner mode** avoids barre chords. If a progression needs one, the app finds a capo fret that makes every
  chord an open shape, or uses another pattern for the same mood. It shows the chord names that sound with the capo.
- **Chord detail page** with the notes in the chord, buttons that play each note and a strum, and five ways to play the
  chord on the neck (the CAGED shapes).
- **Mood Guide** that explains each mood with examples in the key of G, and can start a progression from a mood.
- **Save, view, rename, and delete** progressions. Two saved progressions cannot have the same name, and deleting asks
  for confirmation first.

## Project requirements
| Built with Drafter | `main.py` |
| 7+ routes and 5+ pages | 21 routes and 9 pages in `main.py` |
| `State` dataclass with 4+ fields | `State` in `main.py` (12 fields) |
| List of instances and a second dataclass | `Chord` and `Progression`, held in `current_progression` and `saved_progressions` |
| Inputs | Three SelectBoxes, two CheckBoxes, and two TextBoxes |
| Unit tests, type hints, docstrings | Bottom of `main.py`; every function has types and a docstring |
| Planning documents | `planning/` folder |
| Site information | `set_site_information(...)` at the bottom of `main.py` |
| AI conversation | `claude-conversation.md` |

## Repository contents
- `main.py`: the whole Drafter app, with its unit tests
- `planning/`: the requirements plan and the brainstorming and design worksheets
- `claude-conversation.md`: the conversation with Claude (Anthropic) used while building the project
- `.github/workflows/`: the GitHub Pages deployment and type check

## Use of AI
I used Claude (Anthropic) to help plan, write, and test this project. The conversation is saved as
`claude-conversation.md`.
