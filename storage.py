# -*- coding: utf-8 -*-
"""
storage.py
Upravljanje čuvanjem notnih zapisa u JSON fajlu.
"""

import json
import os
import uuid
from datetime import datetime


class SheetStorage:
    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "sheet_entries.json")
        self.entries = []
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.entries = json.load(f)
            except Exception as e:
                print(f"Greška pri učitavanju: {e}")
                self.entries = []
        else:
            self.entries = []

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Greška pri čuvanju: {e}")

    def add_entry(self, name, notes):
        entry = {
            "id": str(uuid.uuid4()),
            "name": name,
            "notes": notes,
            "created": datetime.now().isoformat()
        }
        self.entries.append(entry)
        self.save()
        return entry

    def delete_entry(self, entry_id):
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        self.save()

    def rename_entry(self, entry_id, new_name):
        for e in self.entries:
            if e["id"] == entry_id:
                e["name"] = new_name
                self.save()
                return True
        return False

    def get_entry(self, entry_id):
        for e in self.entries:
            if e["id"] == entry_id:
                return e
        return None

    def get_all_entries(self):
        return self.entries


class MidiStorage:
    """
    Trajna biblioteka izvezenih MIDI fajlova.

    Svaki zapis se sastoji od (a) same .mid datoteke, sačuvane u
    internom 'midi_library' podfolderu app-a, i (b) unosa u
    midi_entries.json koji čuva ime i vreme kreiranja. Ovo je odvojeno
    od SheetStorage (koji čuva note kao JSON) jer ovde čuvamo gotov,
    binarni MIDI fajl spreman za ponovni izvoz u Downloads.
    """

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.midi_dir = os.path.join(storage_dir, "midi_library")
        os.makedirs(self.midi_dir, exist_ok=True)
        self.file_path = os.path.join(storage_dir, "midi_entries.json")
        self.entries = []
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.entries = json.load(f)
            except Exception as e:
                print(f"Greška pri učitavanju MIDI liste: {e}")
                self.entries = []
        else:
            self.entries = []

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Greška pri čuvanju MIDI liste: {e}")

    def add_entry(self, name, source_midi_path):
        """Kopira postojeći .mid fajl u internu biblioteku i dodaje ga na listu."""
        entry_id = str(uuid.uuid4())
        stored_filename = "{}.mid".format(entry_id)
        stored_path = os.path.join(self.midi_dir, stored_filename)

        with open(source_midi_path, 'rb') as src, open(stored_path, 'wb') as dst:
            dst.write(src.read())

        entry = {
            "id": entry_id,
            "name": name,
            "filename": stored_filename,
            "created": datetime.now().isoformat(),
        }
        self.entries.append(entry)
        self.save()
        return entry

    def delete_entry(self, entry_id):
        entry = self.get_entry(entry_id)
        if entry:
            stored_path = os.path.join(self.midi_dir, entry["filename"])
            try:
                if os.path.exists(stored_path):
                    os.remove(stored_path)
            except Exception as e:
                print(f"Greška pri brisanju MIDI fajla: {e}")
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        self.save()

    def get_entry(self, entry_id):
        for e in self.entries:
            if e["id"] == entry_id:
                return e
        return None

    def get_entry_path(self, entry_id):
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        return os.path.join(self.midi_dir, entry["filename"])

    def get_all_entries(self):
        return self.entries
