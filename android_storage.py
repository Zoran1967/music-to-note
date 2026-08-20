# -*- coding: utf-8 -*-
from kivy.clock import Clock
from kivy.utils import platform


def _sdk_int():
    from jnius import autoclass

    VERSION = autoclass("android.os.Build$VERSION")
    return VERSION.SDK_INT


def save_to_downloads(local_path, display_name, mime_type, on_done):
    if platform != "android":
        on_done(False, "Cuvanje u Download radi samo na Android uredjaju")
        return

    try:
        sdk = _sdk_int()
    except Exception as e:
        on_done(False, "Greska pri proveri Android verzije: {}".format(e))
        return

    if sdk >= 29:
        _save_mediastore(local_path, display_name, mime_type, on_done)
    else:
        _save_legacy(local_path, display_name, on_done)


def _save_mediastore(local_path, display_name, mime_type, on_done):
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        resolver = context.getContentResolver()

        ContentValues = autoclass("android.content.ContentValues")
        MediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
        Downloads = autoclass("android.provider.MediaStore$Downloads")
        Environment = autoclass("android.os.Environment")

        values = ContentValues()
        values.put(MediaColumns.DISPLAY_NAME, display_name)
        values.put(MediaColumns.MIME_TYPE, mime_type)
        values.put(MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)

        item_uri = resolver.insert(Downloads.EXTERNAL_CONTENT_URI, values)
        if item_uri is None:
            on_done(False, "MediaStore insert nije uspeo")
            return

        output_stream = resolver.openOutputStream(item_uri)
        with open(local_path, "rb") as f_in:
            chunk = f_in.read(65536)
            while chunk:
                output_stream.write(bytearray(chunk))
                chunk = f_in.read(65536)
        output_stream.flush()
        output_stream.close()

        on_done(True, "Download/{}".format(display_name))
    except Exception as e:
        on_done(False, "Greska pri cuvanju u Download: {}".format(e))


def _save_legacy(local_path, display_name, on_done):
    try:
        from android.permissions import (
            request_permissions,
            Permission,
            check_permission,
        )

        def _do_copy():
            try:
                from jnius import autoclass

                Environment = autoclass("android.os.Environment")
                JFile = autoclass("java.io.File")

                downloads_dir = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS
                )
                downloads_dir.mkdirs()
                dest_file = JFile(downloads_dir, display_name)
                dest_path = dest_file.getAbsolutePath()

                with open(local_path, "rb") as f_in, open(dest_path, "wb") as f_out:
                    chunk = f_in.read(65536)
                    while chunk:
                        f_out.write(chunk)
                        chunk = f_in.read(65536)

                on_done(True, "Download/{}".format(display_name))
            except Exception as e:
                on_done(False, "Greska pri cuvanju u Download: {}".format(e))

        if check_permission(Permission.WRITE_EXTERNAL_STORAGE):
            _do_copy()
            return

        def _callback(permissions, results):
            def _apply(dt):
                if bool(results) and all(results):
                    _do_copy()
                else:
                    on_done(False, "Dozvola za skladiste nije odobrena")

            Clock.schedule_once(_apply)

        request_permissions([Permission.WRITE_EXTERNAL_STORAGE], _callback)
    except Exception as e:
        on_done(False, "Greska pri trazenju dozvole: {}".format(e))
