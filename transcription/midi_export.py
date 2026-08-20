# -*- coding: utf-8 -*-
import re

PPQ = 480
_NOTE_RE = re.compile(r"^([A-G])(#|b)?(-?\d+)$")
_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_name_to_midi(note_name):
    m = _NOTE_RE.match(note_name)
    if not m:
        raise ValueError("Neispravno ime note: {}".format(note_name))
    letter, accidental, octave = m.group(1), m.group(2), int(m.group(3))
    value = _BASE[letter]
    if accidental == "#":
        value += 1
    elif accidental == "b":
        value -= 1
    return (octave + 1) * 12 + value


def _varlen(value):
    buf = [value & 0x7F]
    value >>= 7
    while value:
        buf.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(buf)


def _uint16(v):
    return bytes([(v >> 8) & 0xFF, v & 0xFF])


def _uint32(v):
    return bytes([(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF])


def _uint24(v):
    return bytes([(v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF])


def export_notes_to_midi(notes, out_path, tempo_bpm=120, velocity=100):
    usable = [n for n in notes if n.get("note")]

    ticks_per_sec = PPQ * (tempo_bpm / 60.0)
    events = []
    for n in usable:
        try:
            midi_num = note_name_to_midi(n["note"])
        except Exception:
            continue
        if midi_num < 0 or midi_num > 127:
            continue

        start_tick = int(round(n["start"] * ticks_per_sec))
        end_tick = int(round(n["end"] * ticks_per_sec))
        if end_tick <= start_tick:
            end_tick = start_tick + 1

        events.append((start_tick, 1, midi_num))
        events.append((end_tick, 0, midi_num))

    events.sort(key=lambda e: (e[0], e[1]))

    mpqn = int(round(60000000 / tempo_bpm))

    track_data = bytearray()
    track_data += _varlen(0) + bytes([0xFF, 0x51, 0x03]) + _uint24(mpqn)

    last_tick = 0
    for tick, kind, note_num in events:
        delta = max(0, tick - last_tick)
        last_tick = tick
        track_data += _varlen(delta)
        if kind == 1:
            track_data += bytes([0x90, note_num, velocity])
        else:
            track_data += bytes([0x80, note_num, 0])

    track_data += _varlen(0) + bytes([0xFF, 0x2F, 0x00])

    buf = bytearray()
    buf += b"MThd"
    buf += _uint32(6)
    buf += _uint16(0)
    buf += _uint16(1)
    buf += _uint16(PPQ)
    buf += b"MTrk"
    buf += _uint32(len(track_data))
    buf += bytes(track_data)

    with open(out_path, "wb") as f:
        f.write(bytes(buf))
