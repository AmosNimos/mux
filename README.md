# Mux - Python MIDI Music Editor

Mux is a command-line tool for creating and editing MIDI files. It allows you to specify instrument settings, tempo, and sequences of notes and volumes to generate MIDI files. Mux is ideal for quick MIDI file generation, music composition, and experimentation.

## Features

- **Instrument Selection**: Choose from a range of instruments.
- **Tempo Control**: Set the tempo in BPM (Beats Per Minute).
- **Note Sequencing**: Input sequences of notes and control their volume.
- **Multi-Track Support**: Create multiple tracks with different instruments and sequences.
- **Chunk Navigation**: Divide your music into manageable chunks for easier editing.
- **Customizable Output**: Specify the name of the output MIDI file.
- **Playback**: Play the generated MIDI file directly from the editor.

## Installation

To use Mux, you need to have Python 3 and the `mido` library installed. You can install `mido` using pip:

```bash
pip install mido
```

You will also need `timidity` for MIDI playback:

```bash
sudo apt-get install timidity
```

## Usage

To start the Mux MIDI editor, use the following command:

```bash
python mux.py
```

### Controls

- **Arrow Keys**: Navigate through the notes and tracks.
- **Space**: Change the volume of the selected note.
- **n**: Input a note (0-127). Default volume is set to max if the note is newly assigned.
- **+/-**: Change the instrument of the selected track.
- **Enter**: Play the current track.
- **e**: Export the current sequence to a MIDI file.
- **c**: Add a new chunk.
- **t**: Add a new track.
- **x**: Delete the current track.
- **q**: Quit the editor.

### Example Workflow

1. **Start the editor**:
   ```bash
   python mux.py
   ```
2. **Navigate to the desired position using the arrow keys**.
3. **Input a note** by pressing `n` and entering the note value.
4. **Adjust the volume** by pressing `space`.
5. **Change the instrument** of the track using `+` or `-`.
6. **Play the current track** by pressing `Enter`.
7. **Export the sequence** to a MIDI file by pressing `e` and entering the file name.

## Notes and Volumes Format

The editor uses a grid where each cell represents a note and its volume. The note input and volume control are intuitive and designed for ease of use.

## License

This project is licensed under the AGPL License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you find a bug or have a feature request.
