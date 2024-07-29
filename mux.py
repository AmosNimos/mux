import subprocess
import curses
import argparse
import re
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from tempfile import NamedTemporaryFile
import os
import time

# Constants for single-track mode
MIDI_INSTRUMENT = 1  # Piano
TEMPO = 500000  # 120 BPM (microseconds per beat)
NOTE_VELOCITY = 127  # Max velocity for louder sound
OCTAVE_COUNT = 4  # Octave range 1 to 4

note_names = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
]

def note_number_to_midi(note_number):
    return note_number if 0 <= note_number <= 127 else 128  # Use 128 to represent a muted note

def parse_notes_file(filename):
    tracks = []
    with open(filename, 'r') as file:
        tempo = int(file.readline().strip())
        for line in file:
            match = re.match(r'inst_id:(\d+);(.*)', line.strip())
            if match:
                instrument = int(match.group(1))
                notes = [(int(note.split(':')[0]), int(note.split(':')[1])) for note in match.group(2).split(',')]
                tracks.append((instrument, notes))
    return tempo, tracks

def convert_midi_to_audio(midi_file, output_file, format):
    wav_tmp = NamedTemporaryFile(delete=False, suffix='.wav')
    
    # Convert MIDI to WAV using timidity
    subprocess.run(['timidity', midi_file, '-Ow', '-o', wav_tmp.name])
    
    if format == 'wav':
        os.rename(wav_tmp.name, output_file)
    else:
        # Convert WAV to the desired format using ffmpeg
        subprocess.run(['ffmpeg', '-i', wav_tmp.name, output_file])
        os.remove(wav_tmp.name)

def export_song(tempo, tracks, output_file, format='midi'):
    midi = MidiFile()
    midi_tracks = []

    for instrument, notes in tracks:
        midi_track = MidiTrack()
        midi_tracks.append(midi_track)
        midi.tracks.append(midi_track)

        # Set instrument
        midi_track.append(Message('program_change', program=instrument))

        for note, length in notes:
            midi_track.append(Message('note_on', note=note, velocity=NOTE_VELOCITY, time=0))
            midi_track.append(Message('note_off', note=note, velocity=NOTE_VELOCITY, time=length))
    
    midi.save(output_file)

    if format != 'midi':
        convert_midi_to_audio(output_file, output_file, format)

# Single-track mode functions
def init_track():
    return [[[] for _ in range(16)] for _ in range(128)]

def draw_midi_grid(stdscr, track, cursor_x, cursor_y, active_notes, octave):
    height, width = stdscr.getmaxyx()
    start_note = (octave - 1) * 12
    end_note = start_note + 12

    # Draw the note names for the current octave
    for i in range(start_note, end_note):
        note_index = i % 12
        note_name = note_names[note_index] + str((i // 12) + 1)
        if i < height - 2:  # Ensure within window bounds
            if '#' in note_name:
                stdscr.addstr(height - 2 - (i - start_note), 0, note_name, curses.color_pair(1))
                stdscr.addstr(height - 2 - (i - start_note), 4, '|', curses.color_pair(3))
            else:
                stdscr.addstr(height - 2 - (i - start_note), 0, note_name)
                stdscr.addstr(height - 2 - (i - start_note), 4, '|', curses.color_pair(3))

    for y in range(start_note, end_note):
        for x in range(16):
            notes = track[y][x]
            if notes:
                if any(note in active_notes for note in notes):
                    stdscr.addstr(height - 2 - (y - start_note), x * 4 + 5, "[+]", curses.color_pair(2))
                else:
                    stdscr.addstr(height - 2 - (y - start_note), x * 4 + 5, "[+]", curses.color_pair(4))
            else:
                stdscr.addstr(height - 2 - (y - start_note), x * 4 + 5, "[ ]")

    # Ensure cursor is within bounds
    if cursor_y >= start_note and cursor_y < end_note:
        cursor_row = height - 2 - (cursor_y - start_note)
        if cursor_row >= 0 and cursor_row < height - 1:
            cursor_col = cursor_x * 4 + 5
            if cursor_col >= 0 and cursor_col < width - 5:
                stdscr.addstr(cursor_row, cursor_col, "[+]", curses.A_REVERSE)

def play_midi(track, tempo, stdscr):
    midi = MidiFile()
    midi_track = MidiTrack()
    midi.tracks.append(midi_track)

    # Set the instrument to piano
    midi_track.append(Message('program_change', program=MIDI_INSTRUMENT))

    # Convert track notes into MIDI messages
    for x in range(16):
        chord_notes = []
        for y in range(128):
            notes = track[y][x]
            if notes:
                for note in notes:
                    chord_notes.append(Message('note_on', note=note, velocity=NOTE_VELOCITY, time=0))
                    chord_notes.append(Message('note_off', note=note, velocity=NOTE_VELOCITY, time=480))
        if not chord_notes:
            chord_notes.append(Message('note_off', note=0, velocity=0, time=480))  # Silence

        for message in chord_notes:
            midi_track.append(message)

    midi.save('temp.mid')
    
    try:
        subprocess.run(['timidity', 'temp.mid'], check=True)
    except subprocess.CalledProcessError as e:
        stdscr.addstr(0, 0, f"Error: {e}")
        stdscr.refresh()
        time.sleep(2)

def preview_column(track, cursor_x, octave):
    midi = MidiFile()
    midi_track = MidiTrack()
    midi.tracks.append(midi_track)

    # Set the instrument to piano
    midi_track.append(Message('program_change', program=MIDI_INSTRUMENT))

    # Convert notes in the current column into MIDI messages
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
        time.sleep(2)

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

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Color pair for active notes
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Color pair for preview notes
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Color pair for default
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Color pair for placed notes

    stdscr.nodelay(1)
    stdscr.timeout(100)
    height, width = stdscr.getmaxyx()

    track = init_track()
    cursor_x = 0
    cursor_y = (OCTAVE_COUNT - 1) * 12  # Start at the lowest note of the highest octave
    octave = OCTAVE_COUNT  # Starting octave at the top
    multi_track_mode = True

    while True:
        stdscr.clear()

        if multi_track_mode:
            # Multi-track mode
            draw_midi_grid(stdscr, track, cursor_x, cursor_y, set(), octave)
            status_message = f"Use arrow keys to navigate, 'Enter' to toggle note, 'Space' to play, 'p' to preview column, 's' to switch mode, 'q' to quit | Octave: {octave}"
        else:
            # Single-track mode
            draw_midi_grid(stdscr, track, cursor_x, cursor_y, set([cursor_y]), octave)
            status_message = f"Single-track mode | Use arrow keys to navigate, 'Enter' to toggle note, 'Space' to play, 'p' to preview column, 's' to switch mode, 'q' to quit | Octave: {octave}"

        if len(status_message) > width:
            status_message = status_message[:width - 1]  # Ensure message fits within screen width
        
        stdscr.addstr(height - 1, 0, status_message)
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP:
            cursor_y = max((octave - 1) * 12, cursor_y - 1)
        elif key == curses.KEY_DOWN:
            cursor_y = min(octave * 12 - 1, cursor_y + 1)
        elif key == curses.KEY_LEFT:
            cursor_x = max(0, cursor_x - 1)
        elif key == curses.KEY_RIGHT:
            cursor_x = min(15, cursor_x + 1)
        elif key == 10:  # Enter key
            if cursor_y < 128:
                if cursor_y in track[cursor_y][cursor_x]:
                    track[cursor_y][cursor_x].remove(cursor_y)
                else:
                    track[cursor_y][cursor_x].append(cursor_y)
        elif key == ord(' '):
            play_midi(track, TEMPO, stdscr)
        elif key == ord('p'):
            preview_column(track, cursor_x, octave)
        elif key == ord('s'):
            multi_track_mode = not multi_track_mode
        elif key == ord('q'):
            break
        elif key == ord('o'):
            octave = max(1, octave - 1)
        elif key == ord('i'):
            octave = min(OCTAVE_COUNT, octave + 1)

    curses.endwin()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MIDI Grid Composer")
    parser.add_argument("-f", "--file", type=str, help="Load notes from a file")
    args = parser.parse_args()

    if args.file:
        track = load_notes(args.file)
    else:
        track = init_track()

    curses.wrapper(main)
