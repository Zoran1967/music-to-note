# -*- coding: utf-8 -*-
"""
storage.py

Upravljanje čuvanjem notnih zapisa u JSON fajlu (sheet_entries.json).
Ovaj fajl se čuva u privatnom Android direktorijumu.
"""

import json
import os
import uuid
from datetime import datetime


class SheetStorage:
    def __init__(self, storage_dir):
        # storage_dir je putanja do foldera gde se čuvaju podaci
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "sheet_entries.json")
        self.entries = []
        self.load()

    def load(self):
        """Učitava podatke iz JSON fajla ako postoji."""
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
        """Čuva podatke u JSON fajl."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Greška pri čuvanju: {e}")

    def add_entry(self, name, notes):
        """Dodaje novi notni zapis."""
        entry = {
            "id": str(uuid.uuid4()),  # Jedinstveni ID
            "name": name,
            "notes": notes,          # Lista nota
            "created": datetime.now().isoformat()
        }
        self.entries.append(entry)
        self.save()
        return entry

    def delete_entry(self, entry_id):
        """Briše zapis po ID-ju."""
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        self.save()

    def rename_entry(self, entry_id, new_name):
        """Preimenuje zapis po ID-ju."""
        for e in self.entries:
            if e["id"] == entry_id:
                e["name"] = new_name
                self.save()
                return True
        return False

    def get_entry(self, entry_id):
        """Vraća jedan zapis po ID-ju."""
        for e in self.entries:
            if e["id"] == entry_id:
                return e
        return None

    def get_all_entries(self):
        """Vraća sve zapise."""
        return self.entries
