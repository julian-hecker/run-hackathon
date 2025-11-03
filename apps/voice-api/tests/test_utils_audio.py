import math

import audioop
import numpy as np

from voice_api.utils.audio import (
    adk_pcm24k_to_twilio_ulaw8k,
    twilio_ulaw8k_to_adk_pcm16k,
)


def _tone_int16(sample_rate_hz: int, seconds: float, freq_hz: float = 440.0) -> bytes:
    num_samples = int(sample_rate_hz * seconds)
    t = np.arange(num_samples, dtype=np.float32) / float(sample_rate_hz)
    x = 0.5 * np.sin(2.0 * math.pi * freq_hz * t)  # [-0.5, 0.5]
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).astype(np.int16)
    return pcm.tobytes()


def test_twilio_ulaw8k_to_adk_pcm16k_output_length():
    # 1 second @ 8kHz μ-law should become 1 second @ 16kHz 16-bit PCM
    pcm8k = _tone_int16(8000, 1.0)
    ulaw = audioop.lin2ulaw(pcm8k, 2)

    out = twilio_ulaw8k_to_adk_pcm16k(ulaw)

    assert isinstance(out, (bytes, bytearray))
    assert len(out) == 16000 * 2  # 1 sec * 16k samples/sec * 2 bytes/sample


def test_adk_pcm24k_to_twilio_ulaw8k_output_length():
    # 1 second @ 24kHz 16-bit PCM should become 1 second @ 8kHz μ-law (1 byte/sample)
    pcm24k = _tone_int16(24000, 1.0)

    out = adk_pcm24k_to_twilio_ulaw8k(pcm24k)

    assert isinstance(out, (bytes, bytearray))
    assert len(out) == 8000  # 1 sec * 8k samples/sec * 1 byte/sample
