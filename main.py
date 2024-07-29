import curses
import argparse
from grid_interface import draw_midi_grid, handle_user_input
from midi_operations import init_track, load_notes
from config import setup_curses

def draw_midi_grid(stdscr, track, cursor_x, cursor_y, octave, multi_track_mode):
    stdscr.clear()
    height, width = stdscr.getmaxyx()  # Get the current size of the window

    # Ensure we don't go out of bounds
    max_y = min(128, height)
    max_x = min(16, width)

    for y in range(max_y):
        for x in range(max_x):
            char_to_draw = ord(' ')
            if track[y][x]:
                char_to_draw = ord('+')
            if cursor_x == x and cursor_y == y:
                stdscr.addch(y, x, char_to_draw, curses.A_REVERSE)
            else:
                stdscr.addch(y, x, char_to_draw)
    
    stdscr.refresh()


def main(stdscr, track, multi_track_mode, octave):
    setup_curses(stdscr)
    cursor_x = 0
    cursor_y = (octave - 1) * 12

    while True:
        stdscr.clear()
        draw_midi_grid(stdscr, track, cursor_x, cursor_y, octave, multi_track_mode)
        stdscr.refresh()
        key = stdscr.getch()
        cursor_x, cursor_y, multi_track_mode = handle_user_input(
            key, cursor_x, cursor_y, track, octave, multi_track_mode, stdscr
        )
        if key == ord('q'):
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MIDI Grid Composer")
    parser.add_argument("-f", "--file", type=str, help="Load notes from a file")
    args = parser.parse_args()
    
    multi_track_mode = True
    octave = 4

    if args.file:
        track = load_notes(args.file)
    else:
        track = init_track()

    curses.wrapper(main, track, multi_track_mode, octave)
