# -*- coding: utf-8 -*-
"""
android_storage.py

Čuvanje fajlova u Android Downloads folder.
Koristi MediaStore za Android 10+ (API 29+) i legacy pristup za starije verzije.
"""

import os
from kivy.utils import platform


def save_to_downloads(temp_path, display_name, mime_type, callback=None):
    """
    Čuva fajl iz temp_path u Android Downloads folder.
    callback (success: bool, message: str)
    """
    try:
        if platform == "android":
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity

            # Import Android klase
            Environment = autoclass("android.os.Environment")
            ContentValues = autoclass("android.content.ContentValues")
            MediaStore = autoclass("android.provider.MediaStore$Downloads")
            File = autoclass("java.io.File")
            FileInputStream = autoclass("java.io.FileInputStream")

            # Pripremi ContentValues
            values = ContentValues()
            values.put(MediaStore.Downloads.DISPLAY_NAME, display_name)
            values.put(MediaStore.Downloads.MIME_TYPE, mime_type)
            values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)

            # Upiši u MediaStore
            uri = context.getContentResolver().insert(MediaStore.EXTERNAL_CONTENT_URI, values)

            if uri is not None:
                # Otvori InputStream iz temp fajla
                input_stream = FileInputStream(temp_path)
                # Otvori OutputStream ka MediaStore
                output_stream = context.getContentResolver().openOutputStream(uri)

                # Kopiraj podatke
                buffer = bytearray(8192)
                while True:
                    length = input_stream.read(buffer)
                    if length <= 0:
                        break
                    output_stream.write(buffer, 0, length)

                output_stream.flush()
                output_stream.close()
                input_stream.close()

                if callback:
                    callback(True, "Fajl sačuvan u Downloads!")
            else:
                if callback:
                    callback(False, "Greška: Nije moguće napraviti fajl u Downloads.")

        else:
            # Desktop režim (za testiranje)
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            dst_path = os.path.join(downloads_dir, display_name)
            
            with open(temp_path, 'rb') as src, open(dst_path, 'wb') as dst:
                dst.write(src.read())

            if callback:
                callback(True, f"Fajl sačuvan na: {dst_path}")

    except Exception as e:
        if callback:
            callback(False, f"Greška pri čuvanju: {e}")
        else:
            print(f"Greška pri čuvanju: {e}")
