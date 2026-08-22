# -*- coding: utf-8 -*-
"""
android_storage.py
Čuvanje fajlova u Android Downloads folder.

Ispravljeno (2. put): pyjnius nije mogao da odluči koju verziju
ContentValues.put() metode da pozove za broj 0/1 (IS_PENDING), jer
Android ima više verzija te metode (za Integer, Float, itd), a običan
Python broj je bio dvosmislen. Sada eksplicitno pravimo pravi Java
Integer objekat, pa više nema zabune.
"""

import os
from kivy.utils import platform

COL_DISPLAY_NAME = "_display_name"
COL_MIME_TYPE = "mime_type"
COL_RELATIVE_PATH = "relative_path"
COL_IS_PENDING = "is_pending"


def save_to_downloads(temp_path, display_name, mime_type, callback=None):
    try:
        if platform == "android":
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity

            Environment = autoclass("android.os.Environment")
            ContentValues = autoclass("android.content.ContentValues")
            MediaStoreDownloads = autoclass("android.provider.MediaStore$Downloads")
            FileInputStream = autoclass("java.io.FileInputStream")
            Integer = autoclass("java.lang.Integer")

            values = ContentValues()
            values.put(COL_DISPLAY_NAME, display_name)
            values.put(COL_MIME_TYPE, mime_type)
            values.put(COL_RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
            # ISPRAVKA: eksplicitan Java Integer, ne "goli" Python broj
            values.put(COL_IS_PENDING, Integer(1))

            uri = context.getContentResolver().insert(
                MediaStoreDownloads.EXTERNAL_CONTENT_URI, values
            )

            if uri is not None:
                input_stream = FileInputStream(temp_path)
                output_stream = context.getContentResolver().openOutputStream(uri)

                buffer = bytearray(8192)
                while True:
                    length = input_stream.read(buffer)
                    if length <= 0:
                        break
                    output_stream.write(buffer, 0, length)

                output_stream.flush()
                output_stream.close()
                input_stream.close()

                update_values = ContentValues()
                # ISPRAVKA: isto ovde, eksplicitan Integer
                update_values.put(COL_IS_PENDING, Integer(0))
                context.getContentResolver().update(uri, update_values, None, None)

                if callback:
                    callback(True, "Fajl sačuvan u Downloads: {}".format(display_name))
            else:
                if callback:
                    callback(False, "Greška: insert() je vratio None (nije napravljen zapis u MediaStore).")

        else:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            dst_path = os.path.join(downloads_dir, display_name)

            with open(temp_path, 'rb') as src, open(dst_path, 'wb') as dst:
                dst.write(src.read())

            if callback:
                callback(True, "Fajl sačuvan na: {}".format(dst_path))

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print("STORAGE ERROR:", error_detail)
        if callback:
            callback(False, "Greška pri čuvanju: {}".format(e))
        else:
            print("Greška pri čuvanju: {}".format(e))
