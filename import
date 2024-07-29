import json

def save_notes(track, file_path):
    with open(file_path, 'w') as f:
        for y in range(128):
            line = ''
            for x in range(16):
                line += '+' if track[y][x] else ' '
            f.write(line + '\n')

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
                    track[y][x].append(y)
    return track
