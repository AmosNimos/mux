import curses
import mido
from mido import MidiFile, MidiTrack, Message
import time

# MIDI Instrument and Tempo
MIDI_INSTRUMENT = 1
TEMPO = 500000  # 120 BPM (microseconds per beat)
NOTE_VELOCITY = 64  # Increase if sound is too low

note_names = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
]

def init_track():
    return [[-1 for _ in range(16)] for _ in range(128)]

def draw_midi_grid(stdscr, track, cursor_x, cursor_y, active_notes):
    height, width = stdscr.getmaxyx()

    for i in range(128):
        note_name = note_names[i % 12] + str(i // 12)
        if i < height - 2:  # Ensure within window bounds
            if '#' in note_name:
                stdscr.addstr(height - 2 - i, 0, note_name, curses.A_REVERSE)
                stdscr.addstr(height - 2 - i, 4, '|', curses.A_REVERSE)
            else:
                stdscr.addstr(height - 2 - i, 0, note_name)
                stdscr.addstr(height - 2 - i, 4, '|')

    for y in range(min(128, height - 2)):
        for x in range(16):
            note = track[127 - y][x]
            if note != -1:
                if (127 - y) in active_notes:
                    stdscr.addstr(height - 2 - y, x * 4 + 5, "[+]", curses.color_pair(1))
                else:
                    stdscr.addstr(height - 2 - y, x * 4 + 5, "[+]", curses.color_pair(2))
            else:
                stdscr.addstr(height - 2 - y, x * 4 + 5, "[ ]")

    stdscr.addstr(height - 2 - cursor_y, cursor_x * 4 + 5, "[+]", curses.A_REVERSE)

def play_midi(track, tempo, stdscr, cursor_x, cursor_y):
    active_notes = set()
    midi = MidiFile()
    midi_track = MidiTrack()
    midi.tracks.append(midi_track)
    
    for y in range(128):
        for x in range(16):
            note = track[127 - y][x]
            if note != -1:
                midi_track.append(Message('note_on', note=note, velocity=NOTE_VELOCITY, time=0))
                midi_track.append(Message('note_off', note=note, velocity=NOTE_VELOCITY, time=480))
    
    midi.save('temp.mid')
    
    with mido.open_output() as port:
        midi_file = MidiFile('temp.mid')
        for msg in midi_file.play():
            if msg.type == 'note_on':
                active_notes.add(msg.note)
            elif msg.type == 'note_off':
                active_notes.discard(msg.note)
            stdscr.clear()
            draw_midi_grid(stdscr, track, cursor_x, cursor_y, active_notes)
            stdscr.refresh()
            port.send(msg)
            time.sleep(tempo / 1000000.0)  # Convert microseconds to seconds

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
                    track[127 - y][x] = 127 - y
    return track

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Color pair for note cells
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Color pair for active notes
    stdscr.nodelay(1)
    stdscr.timeout(100)
    height, width = stdscr.getmaxyx()

    track = init_track()
    cursor_x = 0
    cursor_y = 0

    while True:
        stdscr.clear()
        draw_midi_grid(stdscr, track, cursor_x, cursor_y, set())
        
        # Adjust the status message to fit within the terminal width
        status_message = "Use arrow keys to navigate, 'Enter' to toggle note, 'Space' to play, 'q' to quit"
        if width < len(status_message):
            status_message = status_message[:width - 1]  # Trim if too wide
        stdscr.addstr(height - 1, 0, status_message[:width])

        stdscr.refresh()

        k = stdscr.getch()

        if k == curses.KEY_UP:
            cursor_y = (cursor_y + 1) % min(128, height - 2)
        elif k == curses.KEY_DOWN:
            cursor_y = (cursor_y - 1) % min(128, height - 2)
        elif k == curses.KEY_LEFT:
            cursor_x = (cursor_x - 1) % 16
        elif k == curses.KEY_RIGHT:
            cursor_x = (cursor_x + 1) % 16
        elif k == ord('\n') or k == 10:
            if track[127 - cursor_y][cursor_x] == -1:
                track[127 - cursor_y][cursor_x] = 127 - cursor_y
            else:
                track[127 - cursor_y][cursor_x] = -1
        elif k == ord(' '):
            play_midi(track, TEMPO, stdscr, cursor_x, cursor_y)
        elif k == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)
