import curses
from midi_operations import play_midi, preview_column

def draw_midi_grid(stdscr, track, cursor_x, cursor_y, octave, multi_track_mode):
    stdscr.clear()
    for y in range(128):
        for x in range(16):
            if cursor_x == x and cursor_y == y:
                stdscr.addch(y, x, ord('+') if track[y][x] else ord(' '), curses.A_REVERSE)
            else:
                stdscr.addch(y, x, ord('+') if track[y][x] else ord(' '))
    stdscr.refresh()

def handle_user_input(key, cursor_x, cursor_y, track, octave, multi_track_mode, stdscr):
    if key == curses.KEY_UP:
        cursor_y = (cursor_y - 1) % 128
    elif key == curses.KEY_DOWN:
        cursor_y = (cursor_y + 1) % 128
    elif key == curses.KEY_LEFT:
        cursor_x = (cursor_x - 1) % 16
    elif key == curses.KEY_RIGHT:
        cursor_x = (cursor_x + 1) % 16
    elif key == ord('x'):
        if multi_track_mode:
            track[cursor_y][cursor_x] = []
        else:
            if cursor_y in track[cursor_y][cursor_x]:
                track[cursor_y][cursor_x].remove(cursor_y)
            else:
                track[cursor_y][cursor_x].append(cursor_y)
    elif key == ord(' '):
        play_midi(track, stdscr)
    elif key == ord('p'):
        preview_column(track, cursor_x, octave, stdscr)
    elif key == ord('s'):
        multi_track_mode = not multi_track_mode
    elif key == ord('o'):
        octave = max(1, octave - 1)
    elif key == ord('i'):
        octave = min(OCTAVE_COUNT, octave + 1)

    return cursor_x, cursor_y, multi_track_mode
