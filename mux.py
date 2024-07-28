import curses
import argparse
import re
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from tempfile import NamedTemporaryFile
import os
import time

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

def create_midi(tempo, tracks, output_file):
    mid = MidiFile()
    for instrument, notes in tracks:
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage('set_tempo', tempo=bpm2tempo(tempo)))
        track.append(Message('program_change', program=instrument))
        for note, volume in notes:
            midi_note = note_number_to_midi(note)
            if 0 <= midi_note <= 127:  # Skip muted notes
                track.append(Message('note_on', note=midi_note, velocity=volume, time=0))
                track.append(Message('note_off', note=midi_note, velocity=volume, time=480))
    mid.save(output_file)
    print(f"MIDI file '{output_file}' created successfully with tempo {tempo}!")

def play_midi_file(midi_file):
    os.system(f"timidity {midi_file}")

def stop_midi():
    os.system('pkill timidity')

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    k = 0
    cursor_x = 0
    cursor_y = 0
    chunks = 1

    # Initialize grid with tracks and tempo
    tempo = 120
    tracks = [[[(-1, 0) for _ in range(16)] for _ in range(chunks)] for _ in range(4)]  # 4 tracks, 1 chunk, 16 notes each, (note, volume)
    instruments = [0] * 4  # Instrument for each track
    current_chunk = 0

    volume_levels = [0, 16, 48, 64]
    volume_chars = ['___', '-__', '--_', '---']

    volume_display_time = 0

    while k != ord('q'):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(0, 0, f"Tempo: {tempo} BPM | Chunk: {current_chunk+1}/{chunks} | Tracks: {len(tracks)}")

        for i in range(len(tracks)):
            instrument_id = instruments[i]
            stdscr.addstr(i * 2 + 1, 0, f"Track {i + 1} (inst:{instrument_id}) [{len(tracks[i])}/{chunks}]")
            for j in range(len(tracks[i][current_chunk])):
                note, volume = tracks[i][current_chunk][j]
                display_note = "---" if note == 0 else f"{note:3}"
                display_volume = volume_chars[volume_levels.index(volume)] if i == cursor_y and time.time() < volume_display_time else '   '
                stdscr.addstr(i * 2 + 1, j * 3 + 20, display_note)
                stdscr.addstr(i * 2 + 2, j * 3 + 20, display_volume)

        stdscr.addstr(cursor_y * 2 + 1, cursor_x * 3 + 20, f"{tracks[cursor_y][current_chunk][cursor_x][0]:3}", curses.A_REVERSE)
        stdscr.addstr(cursor_y * 2 + 2, cursor_x * 3 + 20, volume_chars[volume_levels.index(tracks[cursor_y][current_chunk][cursor_x][1])], curses.A_REVERSE)

        k = stdscr.getch()

        if k == curses.KEY_DOWN:
            cursor_y = (cursor_y + 1) % len(tracks)
        elif k == curses.KEY_UP:
            cursor_y = (cursor_y - 1) % len(tracks)
        elif k == curses.KEY_RIGHT:
            if cursor_x == 15:
                if current_chunk < chunks - 1:
                    current_chunk += 1
                    cursor_x = 0
            else:
                cursor_x = (cursor_x + 1) % 16
        elif k == curses.KEY_LEFT:
            if cursor_x == 0:
                if current_chunk > 0:
                    current_chunk -= 1
                    cursor_x = 15
            else:
                cursor_x = (cursor_x - 1) % 16
        elif k == ord('v'):
            volume_index = volume_levels.index(tracks[cursor_y][current_chunk][cursor_x][1])
            new_volume_index = (volume_index + 1) % len(volume_levels)
            tracks[cursor_y][current_chunk][cursor_x] = (tracks[cursor_y][current_chunk][cursor_x][0], volume_levels[new_volume_index])
            volume_display_time = time.time() + 2  # Display volume bar for 1 second
        elif k == ord('n'):
            curses.endwin()
            note = int(input("Enter note (0-127 or -1 to mute): "))
            if note > 127:
                note = 127
            if note < 0:
                note = 0
            tracks[cursor_y][current_chunk][cursor_x] = (note, tracks[cursor_y][current_chunk][cursor_x][1])
            volume_index = volume_levels.index(tracks[cursor_y][current_chunk][cursor_x][1])
            new_volume_index = len(volume_levels)
            tracks[cursor_y][current_chunk][cursor_x] = (tracks[cursor_y][current_chunk][cursor_x][0], volume_levels[new_volume_index])
            volume_display_time = time.time() + 1  # Display volume bar for 1 second
            curses.setupterm()
        elif k == ord('+'):
            instruments[cursor_y] = (instruments[cursor_y] + 1) % 128
        elif k == ord('-'):
            instruments[cursor_y] = (instruments[cursor_y] - 1) % 128
        elif k == ord('\n'):
            curses.endwin()
            with NamedTemporaryFile(delete=False, suffix='.mid') as tmp:
                create_midi(tempo, [(instruments[cursor_y], tracks[cursor_y][current_chunk])], tmp.name)
                play_midi_file(tmp.name)
                os.remove(tmp.name)
            curses.initscr()
            curses.curs_set(0)
            stdscr.nodelay(1)
            stdscr.timeout(100)
        elif k == ord('e'):
            curses.endwin()
            file_name = input("Enter file name: ")
            create_midi(tempo, [(instruments[i], [note for chunk in tracks[i] for note in chunk]) for i in range(len(tracks))], f'{file_name}.mid')
            curses.initscr()
            curses.curs_set(0)
            stdscr.nodelay(1)
            stdscr.timeout(100)
        elif k == ord('c'):
            chunks += 1
            for track in tracks:
                track.append([(0, 0) for _ in range(16)])
        elif k == ord('t'):
            tracks.append([[(0, 0) for _ in range(16)] for _ in range(chunks)])
            instruments.append(0)
        elif k == ord('x'):
            curses.endwin()
            confirm = input(f"Delete track {cursor_y + 1}? (y/n): ")
            if confirm.lower() == 'y':
                del tracks[cursor_y]
                del instruments[cursor_y]
                cursor_y = max(0, cursor_y - 1)
            curses.initscr()
            curses.curs_set(0)
            stdscr.nodelay(1)
            stdscr.timeout(100)

        stdscr.refresh()

    stop_midi()

    with open('notes.txt', 'w') as f:
        f.write(f"{tempo}\n")
        for i, track in enumerate(tracks):
            for chunk in track:
                f.write(f"inst_id:{instruments[i]};{','.join(map(lambda x: str(x[0]), chunk))}\n")

    curses.endwin()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Curses-based note editor')
    args = parser.parse_args()
    curses.wrapper(main)
