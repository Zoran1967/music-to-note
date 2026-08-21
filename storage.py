# -*- coding: utf-8 -*-
"""
storage.py

Jednostavno JSON skladište za sačuvane notne zapise (analize).
Svaki zapis ima redni broj, naziv i listu nota.
Podaci se čuvaju u privatnom direktorijumu aplikacije.
"""

import os
import json


class SheetStorage:
    def __init__(self, data_dir=None):
        if data_dir is None:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            data_dir = context.getFilesDir().getAbsolutePath()
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, "sheet_entries.json")
        self.entries = self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Osiguraj da su svi potrebni ključevi prisutni
            for entry in data:
                if "id" not in entry:
                    entry["id"] = len(data) + 1
                if "name" not in entry:
                    entry["name"] = "Zapis {}".format(entry["id"])
                if "notes" not in entry:
                    entry["notes"] = []
            return data
        except Exception:
            return []

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_entry(self, notes, name=None):
        # Generiši redni broj (najveći postojeći + 1)
        next_id = max([e.get("id", 0) for e in self.entries], default=0) + 1
        if name is None:
            name = "Zapis {}".format(next_id)
        entry = {"id": next_id, "name": name, "notes": notes}
        self.entries.append(entry)
        self._save()
        return entry

    def delete_entry(self, entry_id):
        self.entries = [e for e in self.entries if e.get("id") != entry_id]
        self._save()

    def rename_entry(self, entry_id, new_name):
        for e in self.entries:
            if e.get("id") == entry_id:
                e["name"] = new_name
                break
        self._save()

    def get_entry(self, entry_id):
        for e in self.entries:
            if e.get("id") == entry_id:
                return e
        return None

    def get_all_entries(self):
        # Vrati sortirano po id (rednom broju)
        return sorted(self.entries, key=lambda e: e.get("id", 0))
