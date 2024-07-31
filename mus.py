import curses
import time
import mido
from mido import MidiFile, MidiTrack, Message

# Constants
NOTE_LENGTH = 7  # Adjusted to fit 6 tracks within brackets [123456]
SONG_LENGTH = 16
DEFAULT_BPM = 120
MIN_TRACK_ID = 0
MAX_TRACK_ID = 5
NUM_NOTES = 16  # Number of different notes
VOLUME_LEVELS = [20, 40, 60, 80, 100, 127]  # 6 volume levels
INSTRUMENTS = ['Acoustic Grand Piano', 'Violin', 'Flute', 'Trumpet', 'Electric Guitar', 'Drums']  # 6 instruments

# Default values
active_track_id = 0
tempo = DEFAULT_BPM
tracks = {i: [[False] * SONG_LENGTH for _ in range(NUM_NOTES)] for i in range(MIN_TRACK_ID, MAX_TRACK_ID + 1)}
volumes = {i: 127 for i in range(MIN_TRACK_ID, MAX_TRACK_ID + 1)}
instruments = {i: 0 for i in range(MIN_TRACK_ID, MAX_TRACK_ID + 1)}
muted = {i: False for i in range(MIN_TRACK_ID, MAX_TRACK_ID + 1)}
current_position = 0
current_note = 0

# Initialize screen
stdscr = curses.initscr()
curses.cbreak()
curses.noecho()
stdscr.keypad(True)
curses.curs_set(0)  # Hide default CLI cursor
curses.start_color()
curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Active track color
curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Other tracks color
curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Current hovered note color
curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)  # Unactive track color
curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Info text color

def draw_tracks(stdscr, tracks, active_track_id, current_position, current_note):
    max_y, max_x = stdscr.getmaxyx()
    num_notes_visible = max_x // NOTE_LENGTH
    start_index = (current_position // num_notes_visible) * num_notes_visible
    end_index = start_index + num_notes_visible

    for note_idx in range(NUM_NOTES):
        for i in range(start_index, end_index):
            if i >= SONG_LENGTH:
                break

            note_display = ['_'] * (MAX_TRACK_ID + 1)
            for track_id, track in tracks.items():
                if track[note_idx][i]:
                    note_display[track_id] = str(track_id).zfill(2)[-1]  # Ensure two-character track ID

            note_display_str = "[{}]".format("".join(note_display))
            if i == current_position and note_idx == current_note:
                color_pair = 3  # Highlight current note
            else:
                color_pair = 1  # Active track color

            x_pos = (i - start_index) * NOTE_LENGTH
            y_pos = note_idx + 1
            stdscr.addstr(y_pos, x_pos, note_display_str, curses.color_pair(color_pair))
            # Coloring the active track and other tracks differently
            for idx, char in enumerate(note_display):
                if char != '_':
                    char_color = curses.color_pair(1) if idx == active_track_id else curses.color_pair(4)
                    stdscr.addch(y_pos, x_pos + 1 + idx, char, char_color)

    stdscr.refresh()

def draw_info(stdscr, active_track_id, tempo, volumes, instruments, muted):
    max_y, max_x = stdscr.getmaxyx()
    info_y = NUM_NOTES + 2  # Position below the notes grid

    volume_index = VOLUME_LEVELS.index(volumes[active_track_id])
    instrument_name = INSTRUMENTS[instruments[active_track_id]]
    mute_status = "Muted" if muted[active_track_id] else "Unmuted"

    info_str = f"Track: {active_track_id}, Instrument: {instrument_name}, Volume: {volume_index + 1}, Tempo: {tempo}, Status: {mute_status}"
    stdscr.addstr(info_y, 0, info_str, curses.color_pair(5))
    stdscr.refresh()

def main(stdscr):
    global current_position, current_note, active_track_id, tempo

    while True:
        stdscr.clear()
        draw_tracks(stdscr, tracks, active_track_id, current_position, current_note)
        draw_info(stdscr, active_track_id, tempo, volumes, instruments, muted)
        key = stdscr.getch()

        if key == curses.KEY_RIGHT:
            current_position = (current_position + 1) % SONG_LENGTH
        elif key == curses.KEY_LEFT:
            current_position = (current_position - 1) % SONG_LENGTH
        elif key == curses.KEY_UP:
            current_note = (current_note - 1) % NUM_NOTES
        elif key == curses.KEY_DOWN:
            current_note = (current_note + 1) % NUM_NOTES
        elif key == ord(' '):
            track = tracks[active_track_id]
            track[current_note][current_position] = not track[current_note][current_position]
        elif key == ord('\n'):
            play_song()
        elif key == ord('-'):
            active_track_id = max(MIN_TRACK_ID, active_track_id - 1)
        elif key == ord('='):
            active_track_id = min(MAX_TRACK_ID, active_track_id + 1)
        elif key == ord('V'):
            volume_index = VOLUME_LEVELS.index(volumes[active_track_id])
            if volume_index < len(VOLUME_LEVELS) - 1:
                volumes[active_track_id] = VOLUME_LEVELS[volume_index + 1]
        elif key == ord('v'):
            volume_index = VOLUME_LEVELS.index(volumes[active_track_id])
            if volume_index > 0:
                volumes[active_track_id] = VOLUME_LEVELS[volume_index - 1]
        elif key == ord('I'):
            if instruments[active_track_id] < len(INSTRUMENTS) - 1:
                instruments[active_track_id] += 1
        elif key == ord('i'):
            if instruments[active_track_id] > 0:
                instruments[active_track_id] -= 1
        elif key == ord('T'):
            tempo += 5
        elif key == ord('t'):
            tempo = max(tempo - 5, 1)
        elif key == ord('m'):
            muted[active_track_id] = not muted[active_track_id]
        elif key == ord('q'):
            break

def play_song():
    global tempo
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))

    ticks_per_beat = mid.ticks_per_beat
    ticks_per_note = ticks_per_beat * 4 // SONG_LENGTH

    for track_id in range(MIN_TRACK_ID, MAX_TRACK_ID + 1):
        midi_track = MidiTrack()
        mid.tracks.append(midi_track)
        midi_track.append(Message('program_change', program=instruments[track_id]))
        for i in range(SONG_LENGTH):
            notes_to_play = []
            for note_idx in range(NUM_NOTES):
                if tracks[track_id][note_idx][i] and not muted[track_id]:
                    notes_to_play.append((60 + note_idx, volumes[track_id]))  # Adjust MIDI note numbers as needed

            if notes_to_play:
                for note, volume in notes_to_play:
                    midi_track.append(Message('note_on', note=note, velocity=volume, time=0))
                for note, volume in notes_to_play:
                    midi_track.append(Message('note_off', note=note, velocity=volume, time=ticks_per_note))
            else:
                # Add a silence
                midi_track.append(Message('note_off', note=0, velocity=0, time=ticks_per_note))

    mid.save('temp_song.mid')
    # Play the MIDI file using timidity
    import subprocess
    subprocess.run(['timidity', 'temp_song.mid'])

try:
    curses.wrapper(main)
finally:
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.curs_set(1)  # Restore default CLI cursor
    curses.endwin()
