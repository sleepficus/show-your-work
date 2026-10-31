"""Playlist exporter: reads a playlist, writes it out."""


def export(rows, out):
    for row in rows:
        out.write(",".join(row) + "\n")
    return len(rows)
