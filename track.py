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

note_names = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
]

def init_track():
    return [[-1 for _ in range(16)] for _ in range(128)]

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
            note = track[y][x]
            if note != -1:
                if y in active_notes:
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
    for y in range(128):
        for x in range(16):
            note = track[y][x]
            if note != -1:
                midi_track.append(Message('note_on', note=note, velocity=NOTE_VELOCITY, time=0))
                midi_track.append(Message('note_off', note=note, velocity=NOTE_VELOCITY, time=480))

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
        note = track[y][cursor_x]
        if note != -1:
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
                    track[y][x] = y
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

    while True:
        stdscr.clear()
        draw_midi_grid(stdscr, track, cursor_x, cursor_y, set(), octave)
        
        status_message = f"Use arrow keys to navigate, 'Enter' to toggle note, 'Space' to play, 'p' to preview column, 'q' to quit | Octave: {octave}"
        if width < len(status_message):
            status_message = status_message[:width - 1]
        stdscr.addstr(height - 1, 0, status_message[:width])

        stdscr.refresh()

        k = stdscr.getch()

        if k == curses.KEY_UP:

            cursor_y += 1
            if cursor_y >= octave * 12:
                octave += 1
                if octave > OCTAVE_COUNT:
                    octave = OCTAVE_COUNT
                cursor_y = (octave - 1) * 12

        elif k == curses.KEY_DOWN:
            cursor_y -= 1
            if cursor_y < (octave - 1) * 12:
                octave -= 1
                if octave < 1:
                    octave = 1
                cursor_y = octave * 12 - 1
        elif k == curses.KEY_LEFT:
            cursor_x = (cursor_x - 1) % 16
        elif k == curses.KEY_RIGHT:
            cursor_x = (cursor_x + 1) % 16
        elif k == ord('\n') or k == 10:
            if track[cursor_y][cursor_x] == -1:
                track[cursor_y][cursor_x] = cursor_y
            else:
                track[cursor_y][cursor_x] = -1
        elif k == ord(' '):
            play_midi(track, TEMPO, stdscr)
        elif k == ord('p'):
            preview_column(track, cursor_x, octave)
        elif k == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)
