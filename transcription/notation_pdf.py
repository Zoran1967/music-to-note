# -*- coding: utf-8 -*-
"""
transcription/notation_pdf.py

FAZA 4: Export prepoznatih nota kao PDF sa notnim sistemom (violinski
kljuc), koji se moze odstampati ili podeliti.

Sada sa RITMOM: note imaju trajanje (osmine, četvrtine, polovine)
proporcionalno njihovom trajanju u sekundama. Duža nota = duže
trajanje. Sistem radi bez poznatog tempa tako što normalizuje
trajanja na najčešće muzičke vrednosti.
"""

from transcription.simple_pdf import SimplePDFCanvas, PAGE_A4

# mm conversion (reportlab used lib.units.mm = 72/25.4 points per mm;
# defined locally now to drop the reportlab dependency entirely).
mm = 72.0 / 25.4

NOTE_LETTERS = ["C", "D", "E", "F", "G", "A", "B"]

STAFF_LINE_GAP = 4 * mm
STEP_HEIGHT = STAFF_LINE_GAP / 2.0
NOTE_SPACING = 10 * mm
LEFT_MARGIN = 20 * mm
CLEF_COLUMN_WIDTH = 20 * mm
STAFF_LINES = 5
NOTES_PER_ROW = 12
ROW_PITCH = 10 * STAFF_LINE_GAP  # vertical distance between successive staff rows


def _pitch_to_step(note_name):
    """'A4' -> (step, accidental). Step 0 = bottom staff line (E4)."""
    letter = note_name[0]
    rest = note_name[1:]
    accidental = ""
    if rest and rest[0] in "#b":
        accidental = rest[0]
        rest = rest[1:]
    try:
        octave = int(rest)
    except (ValueError, IndexError):
        octave = 4

    letter_index = NOTE_LETTERS.index(letter)
    ref_letter_index = NOTE_LETTERS.index("E")
    ref_octave = 4
    step = (octave - ref_octave) * 7 + (letter_index - ref_letter_index)
    return step, accidental


def _determine_note_duration(duration_sec, min_dur, max_dur):
    """
    Pretvara trajanje u sekundama u muzičku notnu vrednost.
    Vraća (duration_type, is_dotted) gde duration_type je:
    'whole', 'half', 'quarter', 'eighth', 'sixteenth'
    """
    if max_dur <= min_dur or duration_sec <= 0:
        return "quarter", False

    # Normalizuj na opseg [0, 1]
    normalized = (duration_sec - min_dur) / (max_dur - min_dur)

    if normalized < 0.15:
        return "sixteenth", False
    elif normalized < 0.35:
        return "eighth", False
    elif normalized < 0.65:
        return "quarter", False
    elif normalized < 0.85:
        return "half", False
    else:
        return "whole", False


def _draw_staff(c, x_start, y_bottom, width):
    c.setLineWidth(0.6)
    for i in range(STAFF_LINES):
        y = y_bottom + i * STAFF_LINE_GAP
        c.line(x_start, y, x_start + width, y)


def _draw_treble_clef(c, x, y_bottom):
    c.saveState()
    c.setLineWidth(1.4)
    cx = x + 4 * mm
    c.circle(cx, y_bottom + 1.0 * STAFF_LINE_GAP, 3.2 * mm, stroke=1, fill=0)
    c.circle(cx, y_bottom + 3.0 * STAFF_LINE_GAP, 2.6 * mm, stroke=1, fill=0)
    c.line(cx, y_bottom - 3 * mm, cx, y_bottom + 4.6 * STAFF_LINE_GAP)
    p = c.beginPath()
    p.moveTo(cx, y_bottom - 3 * mm)
    p.curveTo(cx - 3 * mm, y_bottom - 5 * mm, cx + 2 * mm, y_bottom - 6 * mm,
              cx + 1 * mm, y_bottom - 2 * mm)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def _draw_note(c, x, y_bottom, step, accidental, duration_type="quarter"):
    """Crta notu sa odgovarajućim trajanjem."""
    y = y_bottom + step * STEP_HEIGHT

    # Pomoćne linije za note van sistema
    if step < 0:
        s = -2
        while s >= step:
            if s % 2 == 0:
                ly = y_bottom + s * STEP_HEIGHT
                c.line(x - 3 * mm, ly, x + 3 * mm, ly)
            s -= 1
    elif step > 8:
        s = 10
        while s <= step:
            if s % 2 == 0:
                ly = y_bottom + s * STEP_HEIGHT
                c.line(x - 3 * mm, ly, x + 3 * mm, ly)
            s += 2

    # Crtanje note zavisi od trajanja
    rx, ry = 2.2 * mm, 1.6 * mm
    c.setFillColorRGB(0, 0, 0)

    # Note head (elipsa)
    c.ellipse(x - rx, y - ry, x + rx, y + ry, fill=1, stroke=0)

    # Vrat note
    if duration_type in ("whole",):
        # Cela nota nema vrat
        pass
    else:
        if step >= 4:
            c.line(x - rx, y, x - rx, y - 8 * mm)
        else:
            c.line(x + rx, y, x + rx, y + 8 * mm)

    # Dodatne oznake za trajanje
    if duration_type in ("half",):
        # Polovina: šuplja nota (samo obris)
        c.setFillColorRGB(1, 1, 1)
        c.ellipse(x - rx, y - ry, x + rx, y + ry, fill=1, stroke=1)
    elif duration_type in ("eighth", "sixteenth"):
        # Osmina/šesnaestina: barjak na vratu
        flag_x = x + rx if step < 4 else x - rx
        flag_y = y + 8 * mm if step < 4 else y - 8 * mm
        c.line(flag_x, flag_y, flag_x + 3 * mm, flag_y - 2 * mm)

    # Akcidental
    if accidental == "#":
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x - 7 * mm, y - 2 * mm, "#")
    elif accidental == "b":
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x - 7 * mm, y - 2 * mm, "b")


def export_notes_to_pdf(notes, out_path, title="Prepoznate note"):
    """notes: list of dicts with 'note', 'start', 'end' keys.
    Writes a PDF to out_path with ritam (trajanje nota)."""
    usable_notes = [n for n in notes if n.get("note")]

    page_w, page_h = PAGE_A4
    c = SimplePDFCanvas(out_path, pagesize=PAGE_A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(LEFT_MARGIN, page_h - 20 * mm, title)

    if not usable_notes:
        c.setFont("Helvetica", 11)
        c.drawString(LEFT_MARGIN, page_h - 35 * mm, "Nije prepoznata nijedna nota.")
        c.save()
        return

    # Izračunaj trajanja za ritam
    durations = [max(0.08, n["end"] - n["start"]) for n in usable_notes]
    min_dur = min(durations)
    max_dur = max(durations)

    usable_width = page_w - 2 * LEFT_MARGIN
    row_width = min(usable_width, NOTES_PER_ROW * NOTE_SPACING + CLEF_COLUMN_WIDTH)

    row = 0
    col = 0
    y_top_row = page_h - 40 * mm

    for n in usable_notes:
        if col >= NOTES_PER_ROW:
            col = 0
            row += 1

        y_bottom = y_top_row - row * ROW_PITCH
        if y_bottom < 30 * mm:
            c.showPage()
            c.setFont("Helvetica-Bold", 14)
            c.drawString(LEFT_MARGIN, page_h - 20 * mm, title + " (nastavak)")
            row = 0
            col = 0
            y_top_row = page_h - 40 * mm
            y_bottom = y_top_row

        if col == 0:
            _draw_staff(c, LEFT_MARGIN, y_bottom, row_width)
            _draw_treble_clef(c, LEFT_MARGIN + 2 * mm, y_bottom)

        x = LEFT_MARGIN + CLEF_COLUMN_WIDTH + col * NOTE_SPACING
        step, accidental = _pitch_to_step(n["note"])
        duration_sec = n["end"] - n["start"]
        duration_type = _determine_note_duration(duration_sec, min_dur, max_dur)
        _draw_note(c, x, y_bottom, step, accidental, duration_type)

        col += 1

    c.save()
