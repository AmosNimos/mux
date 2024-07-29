import subprocess
from mido import MidiFile, MidiTrack, Message
from tempfile import NamedTemporaryFile
import os

MIDI_INSTRUMENT = 1  # Piano
TEMPO = 500000  # 120 BPM (microseconds per beat)
NOTE_VELOCITY = 127  # Max velocity for louder sound
OCTAVE_COUNT = 4  # Octave range 1 to 4

def init_track():
    return [[[] for _ in range(16)] for _ in range(128)]

def load_notes(file_path):
    track = init_track()
    with open(file_path, 'r') as f:
        for y, line in enumerate(f):
            if y >= 128:
                break
            for x, char in enumerate(line.strip()):
                if x >= 16:
                    break
                if char == '+':
                    track[y][x].append(y)
    return track

def play_midi(track, stdscr):
    midi = MidiFile()
    midi_track = MidiTrack()
    midi.tracks.append(midi_track)

    midi_track.append(Message('program_change', program=MIDI_INSTRUMENT))

    for x in range(16):
        chord_notes = []
        for y in range(128):
            notes = track[y][x]
            if notes:
                for note in notes:
                    chord_notes.append(Message('note_on', note=note, velocity=NOTE_VELOCITY, time=0))
                    chord_notes.append(Message('note_off', note=note, velocity=NOTE_VELOCITY, time=480))
        if not chord_notes:
            chord_notes.append(Message('note_off', note=0, velocity=0, time=480))

        for message in chord_notes:
            midi_track.append(message)

    midi.save('temp.mid')
    try:
        subprocess.run(['timidity', 'temp.mid'], check=True)
    except subprocess.CalledProcessError as e:
        stdscr.addstr(0, 0, f"Error: {e}")
        stdscr.refresh()

def preview_column(track, cursor_x, octave, stdscr):
    midi = MidiFile()
    midi_track = MidiTrack()
    midi.tracks.append(midi_track)

    midi_track.append(Message('program_change', program=MIDI_INSTRUMENT))

    for y in range((octave - 1) * 12, octave * 12):
        notes = track[y][cursor_x]
        if notes:
            for note in notes:
                midi_track.append(Message('note_on', note=note, velocity=NOTE_VELOCITY, time=0))
                midi_track.append(Message('note_off', note=note, velocity=NOTE_VELOCITY, time=480))

    midi.save('temp_preview.mid')
    try:
        subprocess.run(['timidity', 'temp_preview.mid'], check=True)
    except subprocess.CalledProcessError as e:
        stdscr.addstr(0, 0, f"Error: {e}")
        stdscr.refresh()

