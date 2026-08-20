# -*- coding: utf-8 -*-
import wave


def decode_to_wav(input_path, output_wav_path, timeout_us=10000, max_iterations=200000):
    from jnius import autoclass

    MediaExtractor = autoclass("android.media.MediaExtractor")
    MediaCodec = autoclass("android.media.MediaCodec")
    MediaFormat = autoclass("android.media.MediaFormat")

    extractor = MediaExtractor()
    codec = None

    try:
        extractor.setDataSource(input_path)

        track_index = -1
        track_format = None
        mime = None
        for i in range(extractor.getTrackCount()):
            fmt = extractor.getTrackFormat(i)
            m = fmt.getString(MediaFormat.KEY_MIME)
            if m is not None and m.startswith("audio/"):
                track_index = i
                track_format = fmt
                mime = m
                break

        if track_index < 0:
            raise ValueError("Audio zapis nije pronadjen u fajlu")

        extractor.selectTrack(track_index)

        codec = MediaCodec.createDecoderByType(mime)
        codec.configure(track_format, None, None, 0)
        codec.start()

        sample_rate = track_format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        channel_count = track_format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)

        pcm_chunks = []
        buffer_info = MediaCodec.BufferInfo()

        saw_input_eos = False
        saw_output_eos = False
        iterations = 0

        while not saw_output_eos:
            iterations += 1
            if iterations > max_iterations:
                raise RuntimeError("Dekodiranje predugo traje, prekinuto")

            if not saw_input_eos:
                in_index = codec.dequeueInputBuffer(timeout_us)
                if in_index >= 0:
                    in_buffer = codec.getInputBuffer(in_index)
                    sample_size = extractor.readSampleData(in_buffer, 0)
                    if sample_size < 0:
                        codec.queueInputBuffer(
                            in_index, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM
                        )
                        saw_input_eos = True
                    else:
                        pts = extractor.getSampleTime()
                        codec.queueInputBuffer(in_index, 0, sample_size, pts, 0)
                        extractor.advance()

            out_index = codec.dequeueOutputBuffer(buffer_info, timeout_us)
            if out_index >= 0:
                if buffer_info.size > 0:
                    out_buffer = codec.getOutputBuffer(out_index)
                    chunk = bytearray(buffer_info.size)
                    out_buffer.get(chunk)
                    pcm_chunks.append(bytes(chunk))
                codec.releaseOutputBuffer(out_index, False)
                if (buffer_info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0:
                    saw_output_eos = True
            elif out_index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED:
                new_format = codec.getOutputFormat()
                sample_rate = new_format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
                channel_count = new_format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)

        pcm_data = b"".join(pcm_chunks)
        if not pcm_data:
            raise ValueError("Nije moguce dekodovati audio (prazan rezultat)")

        with wave.open(output_wav_path, "wb") as wf:
            wf.setnchannels(channel_count)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
    finally:
        try:
            if codec is not None:
                codec.stop()
                codec.release()
        except Exception:
            pass
        try:
            extractor.release()
        except Exception:
            pass
