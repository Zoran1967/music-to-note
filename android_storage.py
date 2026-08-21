# -*- coding: utf-8 -*-
"""
android_storage.py
Čuvanje fajlova u Android Downloads folder.
Ispravljeno sa IS_PENDING za Android 10+.
"""

import os
from kivy.utils import platform


def save_to_downloads(temp_path, display_name, mime_type, callback=None):
    try:
        if platform == "android":
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity

            Environment = autoclass("android.os.Environment")
            ContentValues = autoclass("android.content.ContentValues")
            MediaStore = autoclass("android.provider.MediaStore$Downloads")
            FileInputStream = autoclass("java.io.FileInputStream")

            values = ContentValues()
            values.put(MediaStore.DISPLAY_NAME, display_name)
            values.put(MediaStore.MIME_TYPE, mime_type)
            values.put(MediaStore.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
            # DODATO: Obavezno za Android 10+ da bi fajl bio vidljiv
            values.put(MediaStore.IS_PENDING, 1)

            uri = context.getContentResolver().insert(MediaStore.EXTERNAL_CONTENT_URI, values)

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

                # DODATO: Finalizuj fajl (postavi IS_PENDING na 0)
                update_values = ContentValues()
                update_values.put(MediaStore.IS_PENDING, 0)
                context.getContentResolver().update(uri, update_values, None, None)

                if callback:
                    callback(True, "Fajl sačuvan u Downloads!")
            else:
                if callback:
                    callback(False, "Greška: Nije moguće napraviti fajl u Downloads.")

        else:
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
