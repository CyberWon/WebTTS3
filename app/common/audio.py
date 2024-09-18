from pathlib import Path

import ffmpeg
import os
from loguru import logger
import av
from av.audio.resampler import AudioResampler
import numpy as np


def reSize(input_file, hz=32000, suffix='wav'):
    output_file = input_file.replace(os.path.splitext(input_file)[1], f'{hz}.{suffix}')
    try:
        (
            ffmpeg.input(input_file)
            .output(output_file, **{"ar": f"{hz}", "f": f"{suffix}"})
            .run(overwrite_output=True, quiet=True)
            # .run(overwrite_output=True)
        )
        return output_file
    except Exception as e:
        logger.debug(input_file)
        logger.error(e)
    return input_file


def load_audio(file: str, sr: int) -> np.ndarray:
    if not Path(file).exists():
        raise FileNotFoundError(f"File not found: {file}")
    file = reSize(file, hz=sr)
    try:
        container = av.open(file)
        resampler = AudioResampler(format="fltp", layout="mono", rate=sr)

        # Estimated maximum total number of samples to pre-allocate the array
        # AV stores length in microseconds by default
        estimated_total_samples = int(container.duration * sr // 1_000_000)
        decoded_audio = np.zeros(estimated_total_samples + 1, dtype=np.float32)

        offset = 0
        for frame in container.decode(audio=0):
            frame.pts = None  # Clear presentation timestamp to avoid resampling issues
            resampled_frames = resampler.resample(frame)
            for resampled_frame in resampled_frames:
                frame_data = resampled_frame.to_ndarray()[0]
                end_index = offset + len(frame_data)

                # Check if decoded_audio has enough space, and resize if necessary
                if end_index > decoded_audio.shape[0]:
                    decoded_audio = np.resize(decoded_audio, end_index + 1)

                decoded_audio[offset:end_index] = frame_data
                offset += len(frame_data)

        # Truncate the array to the actual size
        decoded_audio = decoded_audio[:offset]
    except Exception as e:
        raise RuntimeError(f"Failed to load audio: {e}")

    return decoded_audio
