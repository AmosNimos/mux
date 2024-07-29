# single-track module
import curses
import mido
from mido import MidiFile, MidiTrack, Message
import time
import subprocess

# Constants
MIDI_INSTRUMENT = 1  # Piano
TEMPO = 500000  # 120 BPM (microseconds per beat)
NOTE_VELOCITY = 127  # Max velocity for louder sound
OCTAVE_COUNT = 4  # Octave range 1 to 4

midi_instruments = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavichord", "Celesta", "Glockenspiel",
    "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion",
    "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)",
    "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar",
    "Guitar Harmonics", "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin", "Viola",
    "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Strings 1", "Orchestral Strings 2",
    "Timpani", "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2", "Choir Aahs",
    "Voice Oohs", "Synth Voice", "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet",
    "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2", "Soprano Sax", "Alto Sax",
    "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet", "Piccolo", "Flute",
    "Recorder", "Pan Flute", "Irish Tin Whistle", "Bamboo Flute", "Shamisen", "Koto",
    "Kalimba", "Bag Pipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise", "Breath Noise",
    "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
]

note_names = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
]

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
        if i < height - 6:  # Ensure within window bounds
            if '#' in note_name:
                stdscr.addstr(height - 6 - (i - start_note), 0, note_name, curses.color_pair(1))
                stdscr.addstr(height - 6 - (i - start_note), 4, '|', curses.color_pair(3))
            else:
                stdscr.addstr(height - 6 - (i - start_note), 0, note_name)
                stdscr.addstr(height - 6 - (i - start_note), 4, '|', curses.color_pair(3))

    for y in range(start_note, end_note):
        for x in range(16):
            notes = track[y][x]
            if notes:
                if any(note in active_notes for note in notes):
                    stdscr.addstr(height - 6 - (y - start_note), x * 4 + 5, "[+]", curses.color_pair(2))
                else:
                    stdscr.addstr(height - 6 - (y - start_note), x * 4 + 5, "[+]", curses.color_pair(4))
            else:
                stdscr.addstr(height - 6 - (y - start_note), x * 4 + 5, "[ ]")

    # Ensure cursor is within bounds
    if cursor_y >= start_note and cursor_y < end_note:
        cursor_row = height - 6 - (cursor_y - start_note)
        if cursor_row >= 0 and cursor_row < height - 5:
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

def display_info(stdscr, tempo, volume, instrument, chunk_num, total_chunks, track_id):
    height, width = stdscr.getmaxyx()
    info = (
        f"Tempo: {tempo // 1000} BPM | Volume: {volume} | Instrument: {instrument} | Track: {track_id} | "
        f"Chunk {chunk_num + 1} of {total_chunks}"
    )
    stdscr.addstr(0, 0, info[:width - 1])

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

    volume = NOTE_VELOCITY
    chunk_num = 0
    total_chunks = 16  # Example value, adjust as needed
    track_id=0
    instrument_id=0
    instrument = midi_instruments[instrument_id]

    while True:
        stdscr.clear()
        draw_midi_grid(stdscr, track, cursor_x, cursor_y, set(), octave)
        
        display_info(stdscr, TEMPO, volume, instrument, chunk_num, total_chunks, track_id)
        
        status_message = f"Use arrow keys to navigate, 'Enter' to toggle note, 'Space' to play, 'p' to preview column, 'q' to quit | Octave: {octave}"
        if width < len(status_message):
            status_message = status_message[:width - 1]
        stdscr.addstr(height - 2, 0, status_message[:width])

        stdscr.refresh()

        k = stdscr.getch()

        if k == curses.KEY_DOWN:
            cursor_y -= 1
            if cursor_y < 0:
                octave = 1
                cursor_y = 0
            if cursor_y < (octave - 1) * 12:
                octave -= 1
                if octave < 1:
                    octave = 1
                cursor_y = (octave - 1) * 12

        elif k == curses.KEY_UP:
            cursor_y += 1
            if cursor_y >= octave * 12:
                octave += 1
                if octave > OCTAVE_COUNT:
                    octave = OCTAVE_COUNT
                cursor_y = (octave - 1) * 12

        elif k == curses.KEY_LEFT:
            cursor_x = (cursor_x - 1) % 16

        elif k == curses.KEY_RIGHT:
            cursor_x = (cursor_x + 1) % 16

        elif k == ord('\n') or k == 10:
            if cursor_y not in track[cursor_y][cursor_x]:
                track[cursor_y][cursor_x].append(cursor_y)
            else:
                track[cursor_y][cursor_x].remove(cursor_y)
                if not track[cursor_y][cursor_x]:  # Ensure it's a list and not empty
                    track[cursor_y][cursor_x] = []

        elif k == ord(' '):
            play_midi(track, TEMPO, stdscr)

        elif k == ord('p'):
            preview_column(track, cursor_x, octave)
        elif k == ord('i'):
            instrument_id+=1
        elif k == ord('t'):
            track_id+=1

        elif k == ord('q'):
            break

curses.wrapper(main)
