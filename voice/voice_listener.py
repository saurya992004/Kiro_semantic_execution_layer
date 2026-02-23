"""
Voice Listener for JARVIS
=========================
Records audio from the microphone and transcribes it using
Groq's Whisper large-v3 model (speech-to-text).

Usage:
    listener = VoiceListener()
    text = listener.listen()   # blocks until speech is captured
    if text:
        # feed text into MasterAgent as usual
        agent.process_command(text)
"""

import os
import io
import time
import wave
import logging
import tempfile
from typing import Optional

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VoiceListener:
    """
    Microphone listener that transcribes speech using Groq Whisper large-v3.

    Parameters
    ----------
    sample_rate : int
        Audio sample rate in Hz (default 16 000 — Whisper's native rate).
    channels : int
        Number of audio channels (1 = mono).
    silence_threshold : float
        RMS energy level below which audio is considered silence.
    silence_duration : float
        Seconds of consecutive silence required to stop recording.
    max_duration : float
        Maximum recording length in seconds (safety cap).
    min_speech_duration : float
        Minimum seconds of non-silent audio before sending to Whisper.
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        channels: int = 1,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        max_duration: float = 30.0,
        min_speech_duration: float = 0.3,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration
        self.min_speech_duration = min_speech_duration

        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        logger.info("VoiceListener initialised (Groq Whisper large-v3)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def listen(self, prompt_text: str = "") -> Optional[str]:
        """
        Record from the microphone until silence, then transcribe.

        Returns the transcribed string, or None if nothing was captured.
        """
        print("\n🎤 Listening... (speak now, auto-stops on silence)")
        audio_data = self._record_until_silence()

        if audio_data is None or len(audio_data) == 0:
            print("⚠️  No audio captured.")
            return None

        speech_seconds = len(audio_data) / self.sample_rate
        if speech_seconds < self.min_speech_duration:
            print("⚠️  Too short to transcribe.")
            return None

        print("🔄 Transcribing...")
        text = self._transcribe(audio_data)

        if text:
            print(f"📝 You said: \"{text}\"")
        else:
            print("⚠️  Could not transcribe audio.")

        return text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_until_silence(self) -> Optional[np.ndarray]:
        """
        Stream audio from the mic.
        Stops when `silence_duration` seconds of silence is detected,
        or when `max_duration` is reached.
        """
        chunk_duration = 0.1          # seconds per chunk
        chunk_size = int(self.sample_rate * chunk_duration)

        frames: list[np.ndarray] = []
        silent_chunks = 0
        speaking_chunks = 0
        max_chunks = int(self.max_duration / chunk_duration)
        silence_chunks_needed = int(self.silence_duration / chunk_duration)
        min_speech_chunks = int(self.min_speech_duration / chunk_duration)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
            ) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(chunk_size)
                    rms = float(np.sqrt(np.mean(chunk ** 2)))

                    frames.append(chunk.copy())

                    if rms < self.silence_threshold:
                        silent_chunks += 1
                        # Stop only once we have had some speech first
                        if (
                            speaking_chunks >= min_speech_chunks
                            and silent_chunks >= silence_chunks_needed
                        ):
                            break
                    else:
                        silent_chunks = 0
                        speaking_chunks += 1

        except Exception as exc:
            logger.error(f"Microphone error: {exc}")
            print(f"\n❌ Microphone error: {exc}")
            return None

        if not frames:
            return None

        audio = np.concatenate(frames, axis=0).flatten()
        return audio

    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Send audio to Groq Whisper large-v3 and return transcript."""
        try:
            # Convert float32 → int16 PCM, write to an in-memory WAV buffer
            pcm = (audio * 32767).astype(np.int16)

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)          # 16-bit = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(pcm.tobytes())
            wav_buffer.seek(0)

            # Groq SDK accepts a file-like tuple: (filename, bytes, mimetype)
            transcription = self.client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("audio.wav", wav_buffer.read(), "audio/wav"),
                response_format="text",
            )

            # response_format="text" returns a plain string
            if isinstance(transcription, str):
                return transcription.strip()

            # Fallback for object response
            return getattr(transcription, "text", "").strip() or None

        except Exception as exc:
            logger.error(f"Transcription error: {exc}")
            print(f"\n❌ Transcription error: {exc}")
            return None

    def calibrate_silence_threshold(self, duration: float = 2.0) -> float:
        """
        Sample ambient noise for `duration` seconds and set the silence
        threshold to 1.5× that level.  Call before listen() in a noisy
        environment.
        """
        print(f"🔇 Calibrating silence threshold ({duration}s)…")
        chunk_size = int(self.sample_rate * 0.1)
        rms_values = []

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
            ) as stream:
                steps = int(duration / 0.1)
                for _ in range(steps):
                    chunk, _ = stream.read(chunk_size)
                    rms_values.append(float(np.sqrt(np.mean(chunk ** 2))))
        except Exception as exc:
            logger.warning(f"Calibration failed: {exc}")
            return self.silence_threshold

        if rms_values:
            ambient = float(np.mean(rms_values))
            self.silence_threshold = max(ambient * 1.5, 0.005)
            print(f"✅ Silence threshold set to {self.silence_threshold:.4f}")

        return self.silence_threshold
