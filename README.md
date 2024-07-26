# Mux - Python MIDI Music Editor

Mux is a simple command-line tool for creating MIDI files. With Mux, you can specify instrument settings, tempo, and a sequence of notes to generate a MIDI file. This tool is ideal for quick MIDI file generation and experimentation.

## Features

- **Instrument Selection**: Choose from a range of instruments.
- **Tempo Control**: Set the tempo in BPM (Beats Per Minute).
- **Note Sequencing**: Input sequences of notes to create music.
- **Customizable Output**: Specify the name of the output MIDI file.

## Installation

To use Mux, you need to have Python 3 and the `mido` library installed. You can install `mido` using pip:

```bash
pip install mido
```

## Usage

To create a MIDI file using Mux, use the following command:

```bash
python create_midi.py -i <instrument> -t <tempo> -f <notes_file> [-o <output_file>]
```

### Arguments

- `-i, --instrument`: **Required**. The instrument number (0-127). This corresponds to the MIDI instrument you want to use.
- `-t, --tempo`: **Required**. The tempo in BPM (0-200). Controls the speed of the music.
- `-f, --file`: **Required**. The path to the file containing the sequence of notes separated by commas.
- `-o, --output`: **Optional**. The name of the output MIDI file. Defaults to `output.mid`.

### Notes File Format

The notes file should contain a sequence of MIDI note numbers separated by commas. For example:

```
60,62,64,65,67,69,71,72
```

This represents a sequence of MIDI notes in ascending order.

## Example

To create a MIDI file with instrument 5, tempo 120 BPM, and notes from `notes.txt`, and save it as `my_song.mid`, use:

```bash
python create_midi.py -i 5 -t 120 -f notes.txt -o my_song.mid
```

## License

This project is licensed under the AGPL License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you find a bug or have a feature request.
