# -*- coding: utf-8 -*-
"""
transcription/media_decode.py

FAZA 2/3: Android MediaCodec-based audio decoding.

Converts MP3/M4A/AAC/OGG/FLAC audio files to 16-bit PCM WAV so that
transcription.pitch_detection.NoteDetector can analyze them.

This implementation uses the older (but widely tested) getInputBuffers()
and getOutputBuffers() methods instead of getInputBuffer()/getOutputBuffer()
which caused issues on some pyjnius versions.

Timeout is set to 300 seconds by default to allow large files to finish.
"""

import os
import wave
import threading
import time

from kivy.clock import Clock


def decode_to_wav(source_path, dest_path, callback=None, progress_callback=None, timeout=300):
    """
    Decode a compressed audio file (MP3/M4A/AAC/OGG/FLAC) to WAV.
    """
    if not os.path.exists(source_path):
        if callback:
            callback(False, "Fajl ne postoji: {}".format(source_path))
        return False

    thread = threading.Thread(
        target=_decode_worker,
        args=(source_path, dest_path, callback, progress_callback, timeout),
        daemon=True,
    )
    thread.start()
    return True


def _get_audio_duration_ms(source_path):
    """Try to get the total duration in milliseconds via MediaMetadataRetriever."""
    try:
        from jnius import autoclass

        MediaMetadataRetriever = autoclass("android.media.MediaMetadataRetriever")
        retriever = MediaMetadataRetriever()
        retriever.setDataSource(source_path)

        METADATA_KEY_DURATION = 9  # MediaMetadataRetriever.METADATA_KEY_DURATION
        duration_str = retriever.extractMetadata(METADATA_KEY_DURATION)
        retriever.release()
        if duration_str:
            return int(duration_str)
    except Exception as e:
        print("MediaMetadataRetriever error: {}".format(e))
    return None


def _decode_worker(source_path, dest_path, callback, progress_callback, timeout):
    """Background worker that does the actual MediaCodec decoding."""
    start_time = time.time()

    try:
        from jnius import autoclass
        from android import mActivity

        MediaExtractor = autoclass("android.media.MediaExtractor")
        MediaFormat = autoclass("android.media.MediaFormat")
        MediaCodec = autoclass("android.media.MediaCodec")

        extractor = MediaExtractor()
        extractor.setDataSource(source_path)

        # Nađi audio track
        num_tracks = extractor.getTrackCount()
        audio_track_index = -1
        mime = None

        for i in range(num_tracks):
            fmt = extractor.getTrackFormat(i)
            mime_type = fmt.getString(MediaFormat.KEY_MIME)
            if mime_type and mime_type.startswith("audio/"):
                audio_track_index = i
                mime = mime_type
                break

        if audio_track_index == -1:
            if callback:
                Clock.schedule_once(
                    lambda dt: callback(False, "Nema audio zapisa u fajlu"), 0
                )
            return

        fmt = extractor.getTrackFormat(audio_track_index)
        sample_rate = fmt.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        channel_count = fmt.getInteger(MediaFormat.KEY_CHANNEL_COUNT)

        extractor.selectTrack(audio_track_index)

        codec = MediaCodec.createDecoderByType(mime)
        codec.configure(fmt, None, None, 0)
        codec.start()

        # Koristimo starije metode zbog kompatibilnosti
        input_buffers = codec.getInputBuffers()
        output_buffers = codec.getOutputBuffers()

        info = autoclass("android.media.MediaCodec$BufferInfo")()

        pcm_data = bytearray()
        input_done = False
        output_done = False

        total_duration_ms = _get_audio_duration_ms(source_path)
        last_progress_pct = -1
        last_presentation_time_us = 0

        while not output_done:
            if time.time() - start_time > timeout:
                codec.stop()
                codec.release()
                extractor.release()
                if callback:
                    Clock.schedule_once(
                        lambda dt: callback(False, "Dekodiranje je predugo trajalo (timeout)"),
                        0,
                    )
                return

            # Ubaci podatke
            if not input_done:
                input_index = codec.dequeueInputBuffer(10000)
                if input_index >= 0:
                    input_buffer = input_buffers[input_index]
                    sample_size = extractor.readSampleData(input_buffer, 0)

                    if sample_size < 0:
                        codec.queueInputBuffer(
                            input_index, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM
                        )
                        input_done = True
                    else:
                        presentation_time = extractor.getSampleTime()
                        codec.queueInputBuffer(
                            input_index, 0, sample_size, presentation_time, 0
                        )
                        extractor.advance()
                elif input_index == MediaCodec.INFO_TRY_AGAIN_LATER:
                    pass
                else:
                    time.sleep(0.005)

            # Izvuci dekodirane podatke
            output_index = codec.dequeueOutputBuffer(info, 10000)
            if output_index >= 0:
                output_buffer = output_buffers[output_index]

                # Kopiraj PCM podatke
                output_buffer.position(info.offset)
                output_buffer.limit(info.offset + info.size)

                temp = bytearray(info.size)
                output_buffer.get(temp, 0, info.size)
                pcm_data.extend(temp)

                last_presentation_time_us = info.presentationTimeUs

                if progress_callback and total_duration_ms:
                    progress = min(1.0, (last_presentation_time_us / 1000.0) / total_duration_ms)
                    pct = int(progress * 100)
                    if pct > last_progress_pct:
                        last_progress_pct = pct
                        Clock.schedule_once(lambda dt, p=progress: progress_callback(p), 0)

                codec.releaseOutputBuffer(output_index, False)

                if info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM:
                    output_done = True
            elif output_index == MediaCodec.INFO_OUTPUT_BUFFERS_CHANGED:
                output_buffers = codec.getOutputBuffers()
            elif output_index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED:
                pass
            elif output_index == MediaCodec.INFO_TRY_AGAIN_LATER:
                pass
            else:
                time.sleep(0.005)

        codec.stop()
        codec.release()
        extractor.release()

        _write_wav(dest_path, pcm_data, sample_rate, channel_count)

        if callback:
            Clock.schedule_once(
                lambda dt: callback(True, "Dekodiranje završeno"),
                0,
            )

    except Exception as e:
        if callback:
            Clock.schedule_once(
                lambda dt: callback(False, "Greska pri dekodiranju: {}".format(e)),
                0,
            )


def _write_wav(path, pcm_data, sample_rate, channel_count):
    """Piše raw PCM podatke u WAV fajl."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channel_count)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(pcm_data))
