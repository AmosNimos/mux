import argparse
import re
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

def note_number_to_midi(note_number):
    # Note number to MIDI number conversion (assuming note_number is an integer from 0 to 127)
    return note_number

def parse_notes_file(filename):
    with open(filename, 'r') as file:
        line = file.readline().strip()
        # Split the line by commas and convert each note to an integer
        return [int(note) for note in line.split(',')]

def create_midi(instrument, tempo, notes_file, output_file):
    notes = parse_notes_file(notes_file)
    
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Set the tempo
    track.append(MetaMessage('set_tempo', tempo=bpm2tempo(tempo)))
    # Set the instrument
    track.append(Message('program_change', program=instrument))
    
    # Add notes to the track
    for note in notes:
        midi_note = note_number_to_midi(note)
        track.append(Message('note_on', note=midi_note, velocity=64, time=0))
        track.append(Message('note_off', note=midi_note, velocity=64, time=480))
    
    mid.save(output_file)
    print(f"MIDI file '{output_file}' created successfully with instrument {instrument}, tempo {tempo}!")

def main():
    parser = argparse.ArgumentParser(description='Create a MIDI file from notes, instrument, and tempo.')
    parser.add_argument('-i', '--instrument', type=int, required=True, help='Instrument number (0-127)')
    parser.add_argument('-t', '--tempo', type=int, required=True, help='Tempo in BPM (0-200)')
    parser.add_argument('-f', '--file', type=str, required=True, help='File containing sequence of notes separated by commas')
    parser.add_argument('-o', '--output', type=str, default='output.mid', help='Output MIDI file name')

    args = parser.parse_args()
    
    # Validate arguments
    if not (0 <= args.instrument <= 127):
        print("Error: Instrument must be between 0 and 127.")
        return
    
    if not (0 <= args.tempo <= 200):
        print("Error: Tempo must be between 0 and 200.")
        return
    
    create_midi(args.instrument, args.tempo, args.file, args.output)

if __name__ == '__main__':
    main()
