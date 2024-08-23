import curses
import os
from notes import NOTES  # Assuming NOTES array is defined in notes.py
from mido import Message, MidiFile, MidiTrack

DEFAULT_TEMPO = 120
DEFAULT_INSTRUMENT = "1"  # Piano
DEFAULT_VELOCITY = 80

# Initialize tracks with default values
tracks = []
current_track = 0
sustain = False  # Global variable to toggle sustain feature
loop = False  # Global variable to toggle loop feature

OCTAVE_SIZE = 12  # Define how many notes are in one octave

def init_tracks():
    global tracks
    tracks = [{'instrument': DEFAULT_INSTRUMENT, 'velocity': DEFAULT_VELOCITY, 'notes': ['00'] * 16}]

def create_temporary_midi_file(note_hex, velocity=DEFAULT_VELOCITY):
    """Create a temporary MIDI file with a single note."""
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    note = int(note_hex, 16)
    track.append(Message('program_change', program=0, time=0))  # Default instrument
    track.append(Message('note_on', note=note, velocity=velocity, time=0))
    track.append(Message('note_off', note=note, velocity=velocity, time=480))  # 480 ticks for 500ms

    temp_midi_path = "temp_note.mid"
    midi.save(temp_midi_path)
    return temp_midi_path

def play_single_note_midi(note_hex, velocity=90):
    """Create and play a single note using a temporary MIDI file."""
    temp_midi_path = create_temporary_midi_file(note_hex, velocity)
    os.system(f"timidity {temp_midi_path}")  # Using TiMidity++ to play MIDI
    os.remove(temp_midi_path)

def play_track(track):
    """Play a track using TiMidity++."""
    temp_midi_path = "temp_track.mid"
    save_as_midi(track, temp_midi_path)
    os.system(f"timidity {temp_midi_path}")
    os.remove(temp_midi_path)
    
def save_as_midi(track, filename):
    """Save the given track as a MIDI file with sustain functionality."""
    midi = MidiFile()
    miditrack = MidiTrack()
    midi.tracks.append(miditrack)

    # Convert instrument to integer
    instrument = int(track['instrument'])
    
    # Append program change message with correct instrument
    miditrack.append(Message('program_change', program=instrument, time=0))

    # Handle notes with sustain
    previous_note = None
    sustain_start_time = 0

    for beat, note_hex in enumerate(track['notes']):
        note = int(note_hex, 16)
        
        if note_hex == '00':
            # Handle muted note as a pause
            if previous_note is not None:
                # End the previous note
                miditrack.append(Message('note_off', note=previous_note, velocity=DEFAULT_VELOCITY, time=sustain_start_time or 480))
                previous_note = None
                sustain_start_time = 0
            
            miditrack.append(Message('note_on', note=0, velocity=0, time=0))
            miditrack.append(Message('note_off', note=0, velocity=0, time=480))  # Note length
        else:
            if sustain and previous_note == note:
                # Extend the duration of the previous note
                sustain_start_time += 480
            else:
                if previous_note is not None:
                    # End the previous note
                    miditrack.append(Message('note_off', note=previous_note, velocity=DEFAULT_VELOCITY, time=sustain_start_time or 480))
                
                # Start a new note
                miditrack.append(Message('note_on', note=note, velocity=DEFAULT_VELOCITY, time=0))
                sustain_start_time = 480 if sustain else 0
                previous_note = note
            
    # End the last note
    if previous_note is not None:
        miditrack.append(Message('note_off', note=previous_note, velocity=DEFAULT_VELOCITY, time=sustain_start_time or 480))
    
    midi.save(filename)


def draw_grid(stdscr, x, y, current_octave):
    stdscr.clear()
    sustain_status = "Enabled" if sustain else "Disabled"
    loop_status = "Looping" if loop else "Not Looping"
    stdscr.addstr(0, 0, f"Sustain: {sustain_status} | Loop: {loop_status} | Use arrow keys to move, space to place a note, 'q' to export, 'Enter' to play, '-'/'=' to change track, 'p' to play track, 'l' to toggle loop.")

    max_y, max_x = stdscr.getmaxyx()  # Get terminal size
    offset_x = 6

    # Calculate the range of notes to display for the current octave
    start_note = current_octave * OCTAVE_SIZE
    end_note = start_note + OCTAVE_SIZE
    visible_notes = NOTES[start_note:end_note]

    # Display the note names
    for i, note in enumerate(visible_notes):
        if i == y:
            stdscr.addstr(8, 2, note)

    # Display beats row
    for i in range(16):
        stdscr.addstr(6, offset_x + i * 3, f'{i:02X}')

    # Display placed notes
    for beat in range(16):
        note_hex = tracks[current_track]['notes'][beat]
        note_index = start_note + y  # Calculate the note index for the current row
        cell_x = offset_x + beat * 3
        cell_y = 8  # + y

        if note_hex == '00':
            stdscr.addstr(cell_y, cell_x, '..')
        else:
            stdscr.addstr(cell_y, cell_x, note_hex)

    # Highlight cursor position with inverted color
    cursor_note_index = start_note + y
    if 0 <= y < len(visible_notes) and 0 <= x < 16:
        cursor_note_hex = tracks[current_track]['notes'][x]
        cell_x = offset_x + x * 3
        cell_y = 8  # + y

        # Display the note hex at the cursor position with inverted color
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(cell_y, cell_x, cursor_note_hex if cursor_note_hex != '00' else '..')
        stdscr.attroff(curses.A_REVERSE)
        
    # Display current track id at the top
    stdscr.addstr(1, max_x - 20, f"Track: {current_track}")

    stdscr.refresh()


def main(stdscr):
    global current_track, sustain, loop
    
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.timeout(100)
    
    x, y = 0, 0  # Cursor position
    current_octave = 0  # Track the current octave

    init_tracks()

    while True:
        max_y, max_x = stdscr.getmaxyx()  # Get the current terminal size
        
        draw_grid(stdscr, x, y, current_octave)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            y -= 1
            if y < 0:
                current_octave -= 1
                if current_octave < 0:
                    current_octave = (len(NOTES) // OCTAVE_SIZE) - 1
                y = OCTAVE_SIZE - 1
        elif key == curses.KEY_DOWN:
            y += 1
            if y >= OCTAVE_SIZE:
                current_octave += 1
                if current_octave >= (len(NOTES) // OCTAVE_SIZE):
                    current_octave = 0
                y = 0
        elif key == curses.KEY_LEFT and x > 0:
            x -= 1
        elif key == curses.KEY_RIGHT and x < 15:
            x += 1
        elif key == ord(' '):
            note_index = current_octave * OCTAVE_SIZE + y
            if 0 <= note_index < len(NOTES):
                note = NOTES[note_index]
                print(f"Placing note {note} at grid column {x}, row {y} (octave {current_octave})")
                tracks[current_track]['notes'][x] = note
            else:
                print(f"Note index {note_index} out of range!")

        elif key == ord('-'):
            if current_track > 0:
                current_track -= 1
        elif key == ord('='):
            if current_track < len(tracks) - 1:
                current_track += 1
            else:
                tracks.append({'instrument': DEFAULT_INSTRUMENT, 'velocity': DEFAULT_VELOCITY, 'notes': ['00'] * 16})
                current_track += 1
        elif key == ord('\n'):
            note_index = current_octave * OCTAVE_SIZE + y
            if 0 <= note_index < len(NOTES):
                note = NOTES[note_index]
                play_single_note_midi(note)
        elif key == ord('p'):
            play_track(tracks[current_track])
        elif key == ord('P'):
            for track in tracks:
                play_track(track)
        elif key == ord('q'):
            with open("song.txt", "w") as f:
                f.write(f"# TEMPO:\n{DEFAULT_TEMPO}\n\n# TRACKS:\n")
                for track in tracks:
                    if any(note != '00' for note in track['notes']):
                        f.write(f"{track['instrument']},{track['velocity']},{track['notes']}\n")
            break
        elif key == ord('c'):
            sustain = not sustain  # Toggle sustain feature
            print(f"Sustain {'enabled' if sustain else 'disabled'}")
        elif key == ord('l'):
            loop = not loop  # Toggle loop feature
            print(f"Sustain {'enabled' if sustain else 'disabled'}")


if __name__ == "__main__":
    curses.wrapper(main)
