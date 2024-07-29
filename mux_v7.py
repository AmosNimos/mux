# mutli-track-editor
import subprocess
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

def export_song(tempo, tracks, instruments, output_file, format='midi'):
    if format == 'midi':
        create_midi(tempo, tracks, output_file)
        print(f"MIDI file '{output_file}' created successfully!")
    else:
        with NamedTemporaryFile(delete=False, suffix='.mid') as midi_tmp:
            create_midi(tempo, tracks, midi_tmp.name)
            convert_midi_to_audio(midi_tmp.name, output_file, format)
            os.remove(midi_tmp.name)
        print(f"Audio file '{output_file}' created successfully in {format} format!")

def create_midi(tempo, tracks, output_file):
    mid = MidiFile()
    for instrument, notes in tracks:
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage('set_tempo', tempo=bpm2tempo(tempo)))
        track.append(Message('program_change', program=instrument))

        previous_note = None
        previous_volume = None
        note_duration = 480  # Default note duration

        for note, volume in notes:
            midi_note = note_number_to_midi(note)
            if 0 <= midi_note <= 127:  # Skip muted notes
                if note == previous_note and volume == previous_volume:
                    note_duration += 480  # Extend duration if same note and volume
                else:
                    if previous_note is not None:
                        track.append(Message('note_off', note=previous_note, velocity=previous_volume, time=note_duration))
                    track.append(Message('note_on', note=midi_note, velocity=volume, time=0))
                    previous_note = midi_note
                    previous_volume = volume
                    note_duration = 480

        if previous_note is not None:
            track.append(Message('note_off', note=previous_note, velocity=previous_volume, time=note_duration))

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

    volume_levels = [0, 32, 64, 96, 127]
    volume_chars = ['   ', '-__', '--_', '---', '+++']
    volume_display_time = 0
    current_note = None  # Variable to save the current note value

    while k != ord('q'):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(0, 0, f"Tempo: {tempo} BPM | Chunk: {current_chunk+1}/{chunks} | Tracks: {len(tracks)}")

        for i in range(len(tracks)):
            instrument_id = instruments[i]
            stdscr.addstr(i * 2 + 1, 0, f"Track {i + 1} (inst:{instrument_id}) [{len(tracks[i])}/{chunks}]")
            for j in range(len(tracks[i][current_chunk])):
                note, volume = tracks[i][current_chunk][j]
                display_note = "---" if note == -1 else f"{note:3}"
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
            if note < -1:
                note = -1
            current_note, current_volume = tracks[cursor_y][current_chunk][cursor_x]
            if current_volume == 0:  # Mute volume level
                new_volume = max(volume_levels)  # Set to max volume
            else:
                new_volume = current_volume
            tracks[cursor_y][current_chunk][cursor_x] = (note, new_volume)
            current_note = note  # Save the note value
            volume_display_time = time.time() + 1  # Display volume bar for 1 second
            curses.setupterm()
        elif k == ord('h') and current_note is not None:
            current_note, current_volume = tracks[cursor_y][current_chunk][cursor_x]
            if current_volume == 0:  # Mute volume level
                new_volume = max(volume_levels)  # Set to max volume
            else:
                new_volume = current_volume
            tracks[cursor_y][current_chunk][cursor_x] = (current_note, new_volume)
        elif k == ord('+'):
            instruments[cursor_y] = (instruments[cursor_y] + 1) % 128
        elif k == ord('-'):
            instruments[cursor_y] = (instruments[cursor_y] - 1) % 128
        elif k == ord('p'):
            curses.endwin()
            with NamedTemporaryFile(delete=False, suffix='.mid') as tmp:
                create_midi(tempo, [(instruments[i], [note for chunk in tracks[i] for note in chunk]) for i in range(len(tracks))], tmp.name)
                play_midi_file(tmp.name)
                os.remove(tmp.name)
            curses.initscr()
            curses.curs_set(0)
            stdscr.nodelay(1)
            stdscr.timeout(100)
        elif k == ord('e'):
            curses.endwin()
            file_name = input("Enter file name: ")
            export_song(tempo, [(instruments[i], [note for chunk in tracks[i] for note in chunk]) for i in range(len(tracks))], instruments, f'{file_name}.mid')
            curses.initscr()
            curses.curs_set(0)
            stdscr.nodelay(1)
            stdscr.timeout(100)
        elif k == ord('i'):
            # move to single track editor module (ste.py)
                

    curses.endwin()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MIDI Sequencer')
    parser.add_argument('-p', '--play', help='Play a MIDI file', action='store_true')
    parser.add_argument('-s', '--stop', help='Stop playing MIDI files', action='store_true')
    parser.add_argument('file', nargs='?', help='Notes file to load')
    args = parser.parse_args()

    if args.play:
        if args.file:
            play_midi_file(args.file)
        else:
            print("Please provide a MIDI file to play.")
    elif args.stop:
        stop_midi()
    elif args.file:
        tempo, tracks = parse_notes_file(args.file)
        export_song(tempo, tracks, [0]*len(tracks), 'output.mid')
    else:
        curses.wrapper(main)
