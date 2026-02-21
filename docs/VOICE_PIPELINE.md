# Voice Pipeline Design

**Last Updated:** 2026-02-21  
**Status:** Design Complete  
**Target Platform:** Client Devices (Laptop, Desktop, Phone) + RPi5 Host

---

## 1. Overview & Philosophy

The Voice Pipeline enables the AI companion to **hear and speak**, providing natural voice-based interaction. The system is **privacy-first, local-first, and fully offline-capable** while allowing users to optionally integrate their own cloud models.

### Design Principles

1. **Privacy First:** Voice processing happens locally by default
2. **Offline Capable:** Works without internet connection
3. **Disabled by Default:** User must explicitly enable voice features
4. **Low Latency:** Real-time speech recognition and synthesis
5. **Expressive:** Advanced prosody, emotional modulation, personality-driven
6. **Flexible:** Support wake word, push-to-talk, or both

### Key Features

- **Voice disabled by default:** Explicit opt-in required
- **Hybrid activation:** Wake word ("Hey Companion") OR push-to-talk (user choice)
- **Local models:** Whisper (STT), Piper (TTS), Silero VAD, Porcupine (wake word)
- **Cloud integration:** Optional user-provided API keys for custom models
- **Multiple voices:** 10+ voices, personality-based selection
- **Advanced prosody:** Natural pauses, emphasis, emotional modulation
- **SSML support:** Fine-grained speech control (future feature)

---

## 2. Architecture Overview

### 2.1 System Components

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Voice Pipeline                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  CLIENT DEVICE (Audio I/O)                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Audio Input (Microphone)                          │ │ │
│  │  │  - PortAudio / PulseAudio / ALSA                          │ │ │
│  │  │  - Sample rate: 16 kHz                                    │ │ │
│  │  │  - Channels: Mono                                         │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │ Raw audio stream                         │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Voice Activity Detection (VAD)                    │ │ │
│  │  │  - Silero VAD (8 MB model)                               │ │ │
│  │  │  - Detects speech vs silence                             │ │ │
│  │  │  - Reduces false wake-ups                                │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │ Voice detected                           │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Wake Word Detection (if enabled)                  │ │ │
│  │  │  - Porcupine (3 MB model)                                │ │ │
│  │  │  - Wake words: "Hey Companion", "Companion"              │ │ │
│  │  │  - Low false positive rate                               │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │ Wake word detected OR push-to-talk       │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Speech-to-Text (STT)                              │ │ │
│  │  │                                                            │ │ │
│  │  │  LOCAL (Default):                                         │ │ │
│  │  │  • Whisper-tiny (39 MB)                                   │ │ │
│  │  │  • Whisper-base (74 MB) - Better accuracy                │ │ │
│  │  │  • Latency: ~500ms - 1s                                   │ │ │
│  │  │                                                            │ │ │
│  │  │  CLOUD (Optional, User-Provided):                         │ │ │
│  │  │  • User's OpenAI API key → Whisper API                    │ │ │
│  │  │  • User's Azure Speech key → Azure STT                    │ │ │
│  │  │  • User's Google Cloud key → Google Speech-to-Text       │ │ │
│  │  │  • Latency: ~200-500ms (network dependent)               │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │ Transcribed text                         │ │
│  │                      │                                           │ │
│  └──────────────────────┼───────────────────────────────────────────┘ │
│                         │ Send to host via mTLS                       │
│                         ▼                                             │
│  HOST DEVICE (RPi5)                                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Auditory Agent (Host-Side)                        │ │ │
│  │  │  - Receives transcribed text from client                 │ │ │
│  │  │  - Extracts intent, emotional tone                        │ │ │
│  │  │  - Feeds to Central Agent for processing                 │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                      │                                           │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Central Agent Processing                          │ │ │
│  │  │  - Intent recognition                                     │ │ │
│  │  │  - Generate response text                                 │ │ │
│  │  │  - Determine emotional tone                               │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │ Response text + emotion                  │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Text-to-Speech Generator                          │ │ │
│  │  │                                                            │ │ │
│  │  │  LOCAL (Default):                                         │ │ │
│  │  │  • Piper TTS (20-100 MB per voice)                        │ │ │
│  │  │  • 10+ voices available                                   │ │ │
│  │  │  • ONNX runtime (fast inference)                          │ │ │
│  │  │                                                            │ │ │
│  │  │  CLOUD (Optional):                                        │ │ │
│  │  │  • User's ElevenLabs API                                  │ │ │
│  │  │  • User's Azure Speech                                    │ │ │
│  │  │  • User's Google TTS                                      │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │                                           │ │
│  │                      ▼                                           │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Prosody & Emotion Modulation                      │ │ │
│  │  │  - Adjust pitch, speed, volume based on emotion          │ │ │
│  │  │  - Add pauses, emphasis                                   │ │ │
│  │  │  - Personality-driven voice characteristics               │ │ │
│  │  └───────────────────┬────────────────────────────────────────┘ │ │
│  │                      │ Audio waveform + phoneme data            │ │
│  └──────────────────────┼───────────────────────────────────────────┘ │
│                         │ Send to client via mTLS                     │
│                         ▼                                             │
│  CLIENT DEVICE (Audio Output)                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Audio Playback                                    │ │ │
│  │  │  - Play audio through speakers                            │ │ │
│  │  │  - Send phoneme data to Character Animation              │ │ │
│  │  │  - Synchronized lip-sync                                  │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  KEY DESIGN:                                                         │
│  • STT happens on client (privacy, low latency)                      │
│  • TTS happens on host (personality/emotion control)                 │
│  • Audio never stored unless user explicitly enables recording       │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Speech-to-Text (STT) Pipeline

### 3.1 Audio Input & Processing

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Audio Input Pipeline                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  STAGE 1: Audio Capture                                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Hardware: Microphone input                                     │ │
│  │  API: PortAudio (cross-platform)                                │ │
│  │                                                                 │ │
│  │  Configuration:                                                 │ │
│  │  • Sample rate: 16 kHz (optimal for Whisper)                   │ │
│  │  • Channels: Mono (stereo mixed to mono)                       │ │
│  │  • Format: 16-bit PCM                                           │ │
│  │  • Buffer size: 512 samples (~32ms at 16kHz)                   │ │
│  │                                                                 │ │
│  │  Noise handling:                                                │ │
│  │  • RNNoise noise suppression (optional)                        │ │
│  │  • Automatic gain control (AGC)                                │ │
│  │  • Echo cancellation (if system supports)                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 2: Voice Activity Detection (VAD)                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Model: Silero VAD v4                                           │ │
│  │  Size: 8 MB (ONNX)                                              │ │
│  │  Latency: <10ms per chunk                                       │ │
│  │                                                                 │ │
│  │  Purpose:                                                       │ │
│  │  • Detect when user is speaking vs silence                     │ │
│  │  • Avoid processing ambient noise                              │ │
│  │  • Reduce false wake-ups                                        │ │
│  │  • Save CPU by not running STT on silence                      │ │
│  │                                                                 │ │
│  │  Algorithm:                                                     │ │
│  │  1. Process audio in 512-sample chunks                         │ │
│  │  2. Run Silero VAD → probability of speech (0-1)              │ │
│  │  3. If probability > 0.5 for 3 consecutive chunks → SPEECH     │ │
│  │  4. If probability < 0.3 for 5 consecutive chunks → SILENCE    │ │
│  │                                                                 │ │
│  │  Output: Speech segments with timestamps                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          │ Speech detected                            │
│                          ▼                                            │
│  STAGE 3: Wake Word Detection (Optional)                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Model: Porcupine (Picovoice)                                   │ │
│  │  Size: 3 MB                                                     │ │
│  │  Latency: <5ms                                                  │ │
│  │                                                                 │ │
│  │  Wake words:                                                    │ │
│  │  • "Hey Companion" (default)                                   │ │
│  │  • "Companion" (short form)                                    │ │
│  │  • Custom (user can train their own)                           │ │
│  │                                                                 │ │
│  │  Behavior:                                                      │ │
│  │  • Runs continuously when voice enabled                        │ │
│  │  • Low power (~1% CPU)                                          │ │
│  │  • False positive rate: <1/hour                                │ │
│  │                                                                 │ │
│  │  On wake word detected:                                         │ │
│  │  1. Play "listening" sound (optional)                          │ │
│  │  2. Show visual indicator (character animation)                │ │
│  │  3. Start recording for STT                                     │ │
│  │  4. Record for max 30 seconds or until silence                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  ALTERNATIVE: Push-to-Talk                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  User presses hotkey (e.g., Ctrl+Space)                         │ │
│  │  → Start recording immediately                                  │ │
│  │  → No wake word needed                                          │ │
│  │  → Hold to talk, or toggle mode                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          │ Audio segment ready for STT                │
│                          ▼                                            │
│  STAGE 4: Speech-to-Text                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  LOCAL MODEL (Default): Whisper                                 │ │
│  │  ┌────────────────────────────────────────────────────────────┐│ │
│  │  │                                                             ││ │
│  │  │ Model Options (user selectable):                            ││ │
│  │  │                                                             ││ │
│  │  │ whisper-tiny:                                               ││ │
│  │  │ • Size: 39 MB                                               ││ │
│  │  │ • Speed: ~500ms for 5-second audio                         ││ │
│  │  │ • Accuracy: Good for clear speech                          ││ │
│  │  │ • Languages: 99 languages                                   ││ │
│  │  │                                                             ││ │
│  │  │ whisper-base:                                               ││ │
│  │  │ • Size: 74 MB                                               ││ │
│  │  │ • Speed: ~1s for 5-second audio                            ││ │
│  │  │ • Accuracy: Better, recommended                             ││ │
│  │  │ • Languages: 99 languages                                   ││ │
│  │  │                                                             ││ │
│  │  │ whisper-small: (Optional download)                          ││ │
│  │  │ • Size: 244 MB                                              ││ │
│  │  │ • Speed: ~2s for 5-second audio                            ││ │
│  │  │ • Accuracy: Excellent                                       ││ │
│  │  │                                                             ││ │
│  │  │ Implementation: faster-whisper (optimized C++ backend)      ││ │
│  │  │ Quantization: INT8 for speed                                ││ │
│  │  └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │  CLOUD MODELS (Optional, User-Provided Keys):                   │ │
│  │  ┌────────────────────────────────────────────────────────────┐│ │
│  │  │                                                             ││ │
│  │  │ OpenAI Whisper API:                                         ││ │
│  │  │ • User provides API key                                     ││ │
│  │  │ • Speed: ~200-300ms (network dependent)                    ││ │
│  │  │ • Accuracy: Excellent                                       ││ │
│  │  │ • Cost: $0.006 per minute                                   ││ │
│  │  │                                                             ││ │
│  │  │ Azure Speech Service:                                       ││ │
│  │  │ • User provides subscription key + region                   ││ │
│  │  │ • Speed: ~200-400ms                                         ││ │
│  │  │ • Features: Real-time streaming, diarization               ││ │
│  │  │                                                             ││ │
│  │  │ Google Cloud Speech-to-Text:                                ││ │
│  │  │ • User provides API key                                     ││ │
│  │  │ • Speed: ~300-500ms                                         ││ │
│  │  │ • Features: Punctuation, profanity filter                  ││ │
│  │  └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │  Output: Transcribed text + confidence score                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 5: Post-Processing                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  • Normalize text (lowercase, trim whitespace)                 │ │
│  │  • Fix common transcription errors                             │ │
│  │  • Add punctuation (if missing)                                │ │
│  │  • Detect language (if multilingual)                           │ │
│  │                                                                 │ │
│  │  Example:                                                       │ │
│  │  Raw:    "hey companion whats on my screen"                    │ │
│  │  Fixed:  "Hey companion, what's on my screen?"                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          │ Send to host                               │
│                          ▼                                            │
│                   Auditory Agent (Host)                               │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 STT Implementation (Client-Side)

```python
# stt_engine.py - Speech-to-Text engine

import asyncio
import numpy as np
from typing import Optional, Dict, Any
import pyaudio
from faster_whisper import WhisperModel

class STTEngine:
    """Speech-to-Text engine (client-side)."""
    
    def __init__(self, model_size: str = 'base', use_cloud: bool = False):
        """
        Initialize STT engine.
        
        Args:
            model_size: 'tiny', 'base', 'small' for local Whisper
            use_cloud: Whether to use cloud API (requires user keys)
        """
        self.model_size = model_size
        self.use_cloud = use_cloud
        
        if not use_cloud:
            # Load local Whisper model
            self.model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8"  # Quantized for speed
            )
        else:
            self.cloud_client = self._init_cloud_client()
        
        # Audio config
        self.sample_rate = 16000
        self.chunk_size = 512
        
        # Initialize PortAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # VAD
        self.vad = self._init_vad()
        
        # Wake word detector (if enabled)
        self.wake_word_detector = None
    
    def _init_vad(self):
        """Initialize Voice Activity Detection."""
        import torch
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False
        )
        (get_speech_timestamps, _, _, _, _) = utils
        return {'model': model, 'utils': get_speech_timestamps}
    
    async def start_listening(self, mode: str = 'wake_word'):
        """
        Start listening for voice input.
        
        Args:
            mode: 'wake_word' or 'push_to_talk'
        """
        # Open audio stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        
        if mode == 'wake_word':
            await self._listen_with_wake_word()
        else:
            await self._listen_push_to_talk()
    
    async def _listen_with_wake_word(self):
        """Listen for wake word, then transcribe."""
        print("Listening for wake word...")
        
        while True:
            # Collect audio chunks
            audio_buffer = []
            
            for _ in range(100):  # ~3 seconds of audio
                chunk = await self._read_audio_chunk()
                
                # Check VAD
                if self._is_speech(chunk):
                    audio_buffer.append(chunk)
                    
                    # Check for wake word
                    if len(audio_buffer) > 20:  # At least 1 second
                        audio_data = np.concatenate(audio_buffer[-20:])
                        
                        if await self._detect_wake_word(audio_data):
                            print("Wake word detected!")
                            
                            # Play listening sound
                            await self._play_listening_sound()
                            
                            # Notify character animation
                            await self._notify_listening_state()
                            
                            # Start recording for STT
                            transcript = await self._record_and_transcribe()
                            
                            if transcript:
                                await self._send_to_host(transcript)
                            
                            # Reset buffer
                            audio_buffer.clear()
            
            await asyncio.sleep(0.01)
    
    async def _record_and_transcribe(
        self,
        max_duration: float = 30.0
    ) -> Optional[str]:
        """
        Record audio until silence, then transcribe.
        
        Args:
            max_duration: Maximum recording duration in seconds
        
        Returns:
            Transcribed text or None
        """
        audio_buffer = []
        silence_chunks = 0
        max_silence = 20  # ~1 second of silence ends recording
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            chunk = await self._read_audio_chunk()
            audio_buffer.append(chunk)
            
            # Check if still speaking
            if self._is_speech(chunk):
                silence_chunks = 0
            else:
                silence_chunks += 1
            
            # Stop conditions
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if silence_chunks >= max_silence:
                print("Silence detected, processing...")
                break
            
            if elapsed > max_duration:
                print("Max duration reached")
                break
        
        # Concatenate audio
        audio_data = np.concatenate(audio_buffer)
        
        # Transcribe
        transcript = await self._transcribe(audio_data)
        
        return transcript
    
    async def _transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio waveform (16kHz, mono)
        
        Returns:
            Transcribed text
        """
        if self.use_cloud:
            return await self._transcribe_cloud(audio_data)
        else:
            return await self._transcribe_local(audio_data)
    
    async def _transcribe_local(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe using local Whisper model."""
        # Convert to float32 and normalize
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Run Whisper
        segments, info = self.model.transcribe(
            audio_float,
            beam_size=5,
            language="en",  # Auto-detect if None
            vad_filter=True
        )
        
        # Concatenate segments
        text = " ".join([segment.text for segment in segments])
        
        # Post-process
        text = text.strip()
        
        if not text:
            return None
        
        print(f"Transcribed: {text}")
        return text
    
    async def _transcribe_cloud(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe using cloud API (user-provided)."""
        # Implementation depends on which cloud provider
        # Here's example for OpenAI Whisper API
        
        import openai
        import tempfile
        import soundfile as sf
        
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, audio_data, self.sample_rate)
            tmp_path = tmp.name
        
        # Call OpenAI API
        with open(tmp_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
        
        return transcript['text']
    
    def _is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Check if audio chunk contains speech using VAD."""
        import torch
        
        # Convert to float
        audio_float = audio_chunk.astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_float)
        
        # Run VAD
        speech_prob = self.vad['model'](audio_tensor, self.sample_rate).item()
        
        return speech_prob > 0.5
    
    async def _detect_wake_word(self, audio_data: np.ndarray) -> bool:
        """Detect wake word in audio."""
        # Use Porcupine or similar
        # Simplified for example
        
        if self.wake_word_detector is None:
            import pvporcupine
            self.wake_word_detector = pvporcupine.create(
                keywords=['hey_companion']
            )
        
        # Process audio
        audio_int16 = audio_data.astype(np.int16)
        result = self.wake_word_detector.process(audio_int16)
        
        return result >= 0  # Wake word index
    
    async def _read_audio_chunk(self) -> np.ndarray:
        """Read one audio chunk from stream."""
        # This is simplified; actual implementation would use callback
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        return np.frombuffer(data, dtype=np.int16)
    
    async def _play_listening_sound(self):
        """Play a sound to indicate listening state."""
        # Play short beep or chime
        pass
    
    async def _notify_listening_state(self):
        """Notify character animation to show listening state."""
        # Send message to character controller
        pass
    
    async def _send_to_host(self, transcript: str):
        """Send transcribed text to host."""
        # Send via client communicator
        await self.client_comm.send({
            'type': 'voice_input',
            'transcript': transcript,
            'timestamp': datetime.utcnow().isoformat()
        })
```

---

## 4. Text-to-Speech (TTS) Pipeline

### 4.1 TTS Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Text-to-Speech Pipeline                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  INPUT: Response text from Central Agent                             │
│  "You have 5 unread emails. The most recent is from John."           │
│                                                                       │
│  STAGE 1: Text Analysis                                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  • Sentence segmentation                                        │ │
│  │  • Keyword extraction (for emphasis)                           │ │
│  │  • Detect questions, exclamations, statements                  │ │
│  │  • Emotional context (from Emotion Regulator)                  │ │
│  │                                                                 │ │
│  │  Example:                                                       │ │
│  │  Sentences: ["You have 5 unread emails.",                      │ │
│  │             "The most recent is from John."]                    │ │
│  │  Keywords: ["5", "unread", "John"] (emphasis)                  │ │
│  │  Type: Statement (neutral tone)                                │ │
│  │  Emotion: neutral                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 2: Prosody Planning                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Generate prosody markers:                                      │ │
│  │                                                                 │ │
│  │  • Pauses: After commas, periods                               │ │
│  │  • Emphasis: On keywords                                        │ │
│  │  • Pitch: Higher for questions, lower for statements           │ │
│  │  • Speed: Faster for excitement, slower for seriousness        │ │
│  │  • Volume: Louder for emphasis                                 │ │
│  │                                                                 │ │
│  │  Personality influence (Big Five):                              │ │
│  │  • High Extraversion → More energetic, faster speech           │ │
│  │  • High Openness → More varied intonation                      │ │
│  │  • High Conscientiousness → More precise, clear                │ │
│  │  • High Neuroticism → More uncertain, questioning tone         │ │
│  │                                                                 │ │
│  │  Output: SSML-like markup (internal format)                    │ │
│  │  <speak>                                                        │ │
│  │    You have <emphasis>5</emphasis> unread emails.               │ │
│  │    <break time="300ms"/>                                        │ │
│  │    The most recent is from <emphasis>John</emphasis>.           │ │
│  │  </speak>                                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 3: Voice Selection                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  LOCAL VOICES (Piper TTS):                                      │ │
│  │                                                                 │ │
│  │  Default voices (built-in):                                     │ │
│  │  • en_US-lessac-medium (neutral, clear)                        │ │
│  │  • en_US-amy-medium (female, friendly)                         │ │
│  │  • en_US-ryan-medium (male, professional)                      │ │
│  │  • en_US-arctic-medium (male, warm)                            │ │
│  │  • en_GB-southern_english-medium (British accent)              │ │
│  │                                                                 │ │
│  │  Additional voices (downloadable):                              │ │
│  │  • en_US-libritts-high (high quality, 100MB)                   │ │
│  │  • Multiple languages: es, fr, de, ja, zh, etc.                │ │
│  │                                                                 │ │
│  │  Voice characteristics:                                         │ │
│  │  • Sample rate: 22050 Hz                                        │ │
│  │  • Quality: Natural, expressive                                │ │
│  │  • Speed: ~150ms for 5-word sentence                           │ │
│  │                                                                 │ │
│  │  Personality-based selection:                                   │ │
│  │  ┌────────────────────────────────────────────────────────┐   │ │
│  │  │ IF extraversion > 0.7:                                  │   │ │
│  │  │   → Select energetic voice (amy, ryan)                  │   │ │
│  │  │ ELIF extraversion < 0.3:                                │   │ │
│  │  │   → Select calmer voice (arctic, lessac)                │   │ │
│  │  │                                                          │   │ │
│  │  │ IF openness > 0.7:                                       │   │ │
│  │  │   → More varied pitch range                             │   │ │
│  │  │                                                          │   │ │
│  │  │ IF conscientiousness > 0.7:                             │   │ │
│  │  │   → Clearer pronunciation, slower pace                  │   │ │
│  │  └────────────────────────────────────────────────────────┘   │ │
│  │                                                                 │ │
│  │  CLOUD VOICES (Optional, User-Provided):                        │ │
│  │  • ElevenLabs (very natural, expensive)                        │ │
│  │  • Azure Neural TTS (high quality)                             │ │
│  │  • Google Cloud TTS (many languages)                           │ │
│  │  • Amazon Polly (neural voices)                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 4: Speech Synthesis                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  LOCAL SYNTHESIS (Piper):                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐│ │
│  │  │ 1. Load selected voice model (ONNX)                        ││ │
│  │  │ 2. Process text through phonemizer                         ││ │
│  │  │    Text → Phonemes: "hello" → /həˈloʊ/                    ││ │
│  │  │ 3. Generate mel spectrogram from phonemes                  ││ │
│  │  │ 4. Vocoder: Mel spectrogram → Audio waveform              ││ │
│  │  │ 5. Apply prosody modifications (pitch, speed, pauses)     ││ │
│  │  │                                                             ││ │
│  │  │ Output: Audio waveform (16-bit PCM, 22050 Hz)             ││ │
│  │  │ Latency: ~150-300ms for short sentence                     ││ │
│  │  └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │  CLOUD SYNTHESIS:                                               │ │
│  │  ┌────────────────────────────────────────────────────────────┐│ │
│  │  │ Send text + SSML markup to API                             ││ │
│  │  │ Receive audio waveform                                      ││ │
│  │  │ Latency: ~200-500ms (network dependent)                    ││ │
│  │  └────────────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 5: Emotion Modulation                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Modify audio based on emotional state:                        │ │
│  │                                                                 │ │
│  │  JOY/HAPPY:                                                     │ │
│  │  • Pitch: +10-20% (higher)                                     │ │
│  │  • Speed: +15% (faster)                                         │ │
│  │  • Energy: +20% (more dynamic)                                 │ │
│  │                                                                 │ │
│  │  SAD:                                                           │ │
│  │  • Pitch: -10% (lower)                                         │ │
│  │  • Speed: -20% (slower)                                         │ │
│  │  • Energy: -30% (flatter)                                      │ │
│  │                                                                 │ │
│  │  EXCITED:                                                       │ │
│  │  • Pitch: +15% with more variation                            │ │
│  │  • Speed: +25% (much faster)                                   │ │
│  │  • Energy: +40% (very dynamic)                                 │ │
│  │                                                                 │ │
│  │  WORRIED/ANXIOUS:                                               │ │
│  │  • Pitch: Variable (unstable)                                  │ │
│  │  • Speed: Slightly faster                                      │ │
│  │  • Add slight tremolo effect                                   │ │
│  │                                                                 │ │
│  │  Implementation: Audio signal processing                        │ │
│  │  • Pitch shifting: librosa                                     │ │
│  │  • Time stretching: soundstretch                               │ │
│  │  • Filtering: scipy signal processing                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STAGE 6: Phoneme Extraction (for Lip-Sync)                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Extract phoneme timing from synthesis:                        │ │
│  │                                                                 │ │
│  │  Method 1: From TTS model (if supported)                       │ │
│  │  • Piper provides phoneme durations                            │ │
│  │  • Align with generated audio                                  │ │
│  │                                                                 │ │
│  │  Method 2: Forced alignment (fallback)                         │ │
│  │  • Use Montreal Forced Aligner                                 │ │
│  │  • Align text to audio to get phoneme timestamps              │ │
│  │                                                                 │ │
│  │  Output: List of (phoneme, start_time, duration)               │ │
│  │  [                                                              │ │
│  │    ('Y', 0.0, 0.08),                                           │ │
│  │    ('UW', 0.08, 0.12),                                         │ │
│  │    ('HH', 0.20, 0.08),                                         │ │
│  │    ('AE', 0.28, 0.10),                                         │ │
│  │    ('V', 0.38, 0.08),                                          │ │
│  │    ...                                                          │ │
│  │  ]                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  OUTPUT: Audio waveform + phoneme data                                │
│  • Audio: WAV file or raw PCM                                        │
│  • Phonemes: JSON list for lip-sync                                  │
│  • Send to client for playback                                        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 4.2 TTS Implementation (Host-Side)

```python
# tts_engine.py - Text-to-Speech engine (host-side)

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import piper

@dataclass
class SpeechSegment:
    """Represents a segment of synthesized speech."""
    audio: np.ndarray  # Audio waveform
    sample_rate: int
    phonemes: List[Dict[str, Any]]  # Phoneme timing for lip-sync
    duration: float  # Seconds


class TTSEngine:
    """Text-to-Speech engine (host-side)."""
    
    def __init__(
        self,
        personality_mgr: 'PersonalityManager',
        emotion_regulator: 'EmotionRegulator'
    ):
        self.personality = personality_mgr
        self.emotion_regulator = emotion_regulator
        
        # Load default voice model
        self.current_voice = self._select_voice_for_personality()
        self.tts_model = self._load_piper_voice(self.current_voice)
        
        # Audio settings
        self.sample_rate = 22050
    
    def _select_voice_for_personality(self) -> str:
        """Select voice based on personality traits."""
        traits = self.personality.get_all_traits()
        
        # Map personality to voice
        if traits['extraversion'] > 0.7:
            # Outgoing, energetic
            if traits['agreeableness'] > 0.7:
                return 'en_US-amy-medium'  # Friendly female
            else:
                return 'en_US-ryan-medium'  # Professional male
        elif traits['extraversion'] < 0.3:
            # Introverted, calm
            return 'en_US-arctic-medium'  # Warm, calm male
        else:
            # Balanced
            return 'en_US-lessac-medium'  # Neutral, clear
    
    def _load_piper_voice(self, voice_name: str):
        """Load Piper TTS voice model."""
        from piper import PiperVoice
        
        model_path = f"/models/piper/{voice_name}.onnx"
        config_path = f"/models/piper/{voice_name}.json"
        
        voice = PiperVoice.load(model_path, config_path)
        return voice
    
    async def synthesize(
        self,
        text: str,
        emotion: Optional[str] = None,
        emotion_intensity: float = 0.5
    ) -> SpeechSegment:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to speak
            emotion: Emotion name (happy, sad, excited, etc.)
            emotion_intensity: 0.0-1.0
        
        Returns:
            SpeechSegment with audio and phoneme data
        """
        # Stage 1: Text analysis
        text = await self._preprocess_text(text)
        
        # Stage 2: Prosody planning
        ssml = await self._generate_prosody(text, emotion, emotion_intensity)
        
        # Stage 3: Synthesize
        audio, phonemes = await self._synthesize_with_piper(ssml)
        
        # Stage 4: Emotion modulation
        if emotion:
            audio = await self._apply_emotion_modulation(
                audio,
                emotion,
                emotion_intensity
            )
        
        # Create segment
        segment = SpeechSegment(
            audio=audio,
            sample_rate=self.sample_rate,
            phonemes=phonemes,
            duration=len(audio) / self.sample_rate
        )
        
        return segment
    
    async def _preprocess_text(self, text: str) -> str:
        """Preprocess text for TTS."""
        # Normalize
        text = text.strip()
        
        # Fix common issues
        text = text.replace('...', '. ')  # Replace ellipsis
        text = text.replace('  ', ' ')  # Remove double spaces
        
        # Expand abbreviations
        abbreviations = {
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'et cetera',
        }
        for abbr, expansion in abbreviations.items():
            text = text.replace(abbr, expansion)
        
        return text
    
    async def _generate_prosody(
        self,
        text: str,
        emotion: Optional[str],
        intensity: float
    ) -> str:
        """
        Generate prosody markup for text.
        
        Returns SSML-like markup (internal format).
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Identify keywords for emphasis
        keywords = await self._extract_keywords(text)
        
        # Build SSML
        ssml_parts = ['<speak>']
        
        for i, sentence in enumerate(sentences):
            # Add pauses between sentences
            if i > 0:
                ssml_parts.append('<break time="300ms"/>')
            
            # Add emphasis to keywords
            sentence_with_emphasis = sentence
            for keyword in keywords:
                if keyword.lower() in sentence.lower():
                    sentence_with_emphasis = sentence_with_emphasis.replace(
                        keyword,
                        f'<emphasis>{keyword}</emphasis>'
                    )
            
            ssml_parts.append(sentence_with_emphasis)
        
        ssml_parts.append('</speak>')
        
        return ' '.join(ssml_parts)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords for emphasis."""
        # Simplified: identify numbers, names, important words
        import re
        
        keywords = []
        
        # Numbers
        numbers = re.findall(r'\b\d+\b', text)
        keywords.extend(numbers)
        
        # Capitalized words (likely names)
        names = re.findall(r'\b[A-Z][a-z]+\b', text)
        keywords.extend(names)
        
        # TODO: Use NLP for better keyword extraction
        
        return keywords
    
    async def _synthesize_with_piper(
        self,
        text: str
    ) -> tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Synthesize speech using Piper TTS.
        
        Returns:
            (audio_waveform, phoneme_list)
        """
        # Synthesize
        audio_chunks = []
        phonemes = []
        
        for audio_chunk in self.tts_model.synthesize_stream_raw(text):
            audio_chunks.append(audio_chunk)
        
        # Concatenate audio
        audio = np.concatenate(audio_chunks)
        
        # Get phonemes from model
        # (Piper provides this via phonemizer)
        phonemes = await self._extract_phonemes_from_text(text)
        
        return audio, phonemes
    
    async def _extract_phonemes_from_text(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract phoneme timing for lip-sync.
        
        This is simplified; actual implementation would get this from
        Piper's internal phonemizer or use forced alignment.
        """
        # Use espeak-ng for phonemization
        from phonemizer import phonemize
        
        phonemes_str = phonemize(
            text,
            language='en-us',
            backend='espeak',
            strip=True,
            with_stress=True
        )
        
        # Estimate timing (simplified)
        phoneme_list = phonemes_str.split()
        phonemes = []
        
        current_time = 0.0
        for phon in phoneme_list:
            duration = 0.08  # ~80ms per phoneme (rough estimate)
            
            phonemes.append({
                'phoneme': phon,
                'start_time': current_time,
                'duration': duration,
                'mouth_shape': self._phoneme_to_mouth_shape(phon)
            })
            
            current_time += duration
        
        return phonemes
    
    def _phoneme_to_mouth_shape(self, phoneme: str) -> str:
        """Map phoneme to mouth shape for character animation."""
        # Same mapping as in character animation system
        phoneme_map = {
            'M': 'closed',
            'B': 'closed',
            'P': 'closed',
            'AA': 'open',
            'AH': 'open',
            'IH': 'small_open',
            'EH': 'small_open',
            'UW': 'rounded',
            'OW': 'rounded',
            'IY': 'wide',
            'EY': 'wide',
            'F': 'narrow',
            'V': 'narrow',
            'W': 'lip_round',
        }
        
        return phoneme_map.get(phoneme, 'neutral')
    
    async def _apply_emotion_modulation(
        self,
        audio: np.ndarray,
        emotion: str,
        intensity: float
    ) -> np.ndarray:
        """
        Apply emotion-based audio modulation.
        
        Args:
            audio: Audio waveform
            emotion: Emotion name
            intensity: 0.0-1.0
        
        Returns:
            Modulated audio
        """
        import librosa
        import soundfile as sf
        
        # Define emotion parameters
        emotion_params = {
            'joy': {'pitch_shift': 2 * intensity, 'speed': 1.15 * intensity},
            'sadness': {'pitch_shift': -1 * intensity, 'speed': 0.85 * intensity},
            'excitement': {'pitch_shift': 3 * intensity, 'speed': 1.25 * intensity},
            'worry': {'pitch_shift': 0, 'speed': 1.1 * intensity},
            'anger': {'pitch_shift': -2 * intensity, 'speed': 1.2 * intensity},
        }
        
        params = emotion_params.get(emotion, {'pitch_shift': 0, 'speed': 1.0})
        
        # Apply pitch shift
        if params['pitch_shift'] != 0:
            audio = librosa.effects.pitch_shift(
                audio,
                sr=self.sample_rate,
                n_steps=params['pitch_shift']
            )
        
        # Apply time stretch (speed change)
        if params['speed'] != 1.0:
            audio = librosa.effects.time_stretch(
                audio,
                rate=params['speed']
            )
        
        return audio
    
    async def speak(
        self,
        text: str,
        send_to_client_callback
    ):
        """
        High-level API: Synthesize and send to client for playback.
        
        Args:
            text: Text to speak
            send_to_client_callback: Async function to send audio to client
        """
        # Get current emotion
        emotion = self.emotion_regulator.get_current_emotion()
        emotion_intensity = self.emotion_regulator.get_emotion_intensity()
        
        # Synthesize
        segment = await self.synthesize(text, emotion, emotion_intensity)
        
        # Send to client
        await send_to_client_callback({
            'type': 'play_speech',
            'audio': segment.audio.tobytes(),
            'sample_rate': segment.sample_rate,
            'phonemes': segment.phonemes,
            'duration': segment.duration
        })
```

---

## 5. Audio Synchronization & Playback

### 5.1 Client-Side Audio Playback

```python
# audio_playback.py - Client-side audio playback

import asyncio
import numpy as np
import pyaudio
from typing import Dict, Any, List

class AudioPlayer:
    """Handles audio playback and lip-sync coordination."""
    
    def __init__(self, character_controller: 'CharacterController'):
        self.character = character_controller
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    async def play_speech(
        self,
        audio_data: bytes,
        sample_rate: int,
        phonemes: List[Dict[str, Any]]
    ):
        """
        Play speech audio with synchronized lip-sync.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
            phonemes: Phoneme timing for lip-sync
        """
        # Convert bytes to numpy array
        audio = np.frombuffer(audio_data, dtype=np.int16)
        
        # Open audio stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True
        )
        
        # Start lip-sync in parallel
        lip_sync_task = asyncio.create_task(
            self._animate_lip_sync(phonemes)
        )
        
        # Play audio
        await self._play_audio_async(audio)
        
        # Wait for lip-sync to finish
        await lip_sync_task
        
        # Close stream
        self.stream.stop_stream()
        self.stream.close()
    
    async def _play_audio_async(self, audio: np.ndarray):
        """Play audio asynchronously."""
        chunk_size = 1024
        
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            self.stream.write(chunk.tobytes())
            
            # Allow other async tasks to run
            await asyncio.sleep(0.001)
    
    async def _animate_lip_sync(self, phonemes: List[Dict[str, Any]]):
        """Animate character mouth based on phoneme timing."""
        start_time = asyncio.get_event_loop().time()
        
        for phoneme in phonemes:
            # Wait until phoneme should start
            target_time = start_time + phoneme['start_time']
            current_time = asyncio.get_event_loop().time()
            
            if current_time < target_time:
                await asyncio.sleep(target_time - current_time)
            
            # Set mouth shape
            await self.character.set_mouth_shape(phoneme['mouth_shape'])
            
            # Wait for phoneme duration
            await asyncio.sleep(phoneme['duration'])
        
        # Return to neutral
        await self.character.set_mouth_shape('neutral')
```

---

## 6. User Configuration

### 6.1 Voice Settings

```yaml
# voice_config.yaml - User voice settings

voice:
  # Global enable/disable
  enabled: false  # Default: disabled
  
  # Input settings
  input:
    # Activation mode: 'wake_word', 'push_to_talk', 'both'
    mode: both
    
    # Wake word settings (if mode includes wake_word)
    wake_word:
      keyword: "Hey Companion"  # Options: "Hey Companion", "Companion", custom
      sensitivity: 0.5  # 0.0-1.0, higher = more sensitive (more false positives)
    
    # Push-to-talk settings (if mode includes push_to_talk)
    push_to_talk:
      hotkey: "Ctrl+Space"  # User can customize
      mode: "hold"  # Options: "hold" (hold to talk), "toggle" (press to start/stop)
    
    # Microphone settings
    microphone:
      device: "default"  # Or specific device ID
      noise_suppression: true  # RNNoise
      auto_gain_control: true
      echo_cancellation: false  # Enable if using speakers
  
  # STT settings
  stt:
    # Model: 'whisper-tiny', 'whisper-base', 'whisper-small', 'cloud'
    model: whisper-base
    
    # Cloud settings (if model == 'cloud')
    cloud:
      provider: null  # Options: 'openai', 'azure', 'google'
      api_key: null  # User provides
      endpoint: null  # Optional custom endpoint
    
    # Language
    language: "en"  # Auto-detect if null
    
    # Maximum recording duration (seconds)
    max_duration: 30
  
  # TTS settings
  tts:
    # Voice selection
    voice: "auto"  # Options: "auto" (personality-based), or specific voice name
    
    # Available voices (local)
    available_voices:
      - en_US-lessac-medium
      - en_US-amy-medium
      - en_US-ryan-medium
      - en_US-arctic-medium
      - en_GB-southern_english-medium
    
    # Cloud TTS (optional)
    cloud:
      enabled: false
      provider: null  # 'elevenlabs', 'azure', 'google', 'aws'
      api_key: null
      voice_id: null  # Provider-specific voice ID
    
    # Prosody settings
    prosody:
      # Enable advanced prosody
      advanced: true
      
      # Emotion modulation
      emotion_modulation: true
      emotion_intensity: 0.7  # 0.0-1.0
      
      # Personality influence
      personality_driven: true
    
    # Speaking rate (1.0 = normal, 0.5-2.0)
    speed: 1.0
    
    # Pitch adjustment (-1.0 to 1.0, 0 = no change)
    pitch: 0.0
    
    # Volume (0.0-1.0)
    volume: 0.8
  
  # Audio output
  output:
    device: "default"  # Or specific device ID
    
    # Play sound effects
    sounds:
      listening_chime: true  # Play sound when starting to listen
      error_beep: true  # Play sound on errors
  
  # Privacy settings
  privacy:
    # Store voice recordings
    store_recordings: false  # If true, save to disk for review
    
    # Recording retention (days, if storing)
    retention_days: 7
    
    # Share anonymized data for improvement
    share_anonymous_data: false
```

---

## 7. Resource Estimates

### Client Device

**STT (When Active):**
- Whisper-tiny: 39 MB model + 100 MB RAM
- Whisper-base: 74 MB model + 150 MB RAM
- Whisper-small: 244 MB model + 250 MB RAM
- VAD (Silero): 8 MB model + 20 MB RAM
- Wake word (Porcupine): 3 MB model + 10 MB RAM
- **Total (base): ~200-250 MB**

**CPU:**
- VAD: ~1-2% (continuous)
- Wake word: ~1% (continuous)
- STT: 20-40% for 1-2 seconds (during transcription)

**Audio Buffer:**
- ~5 MB for 30 seconds of audio

### Host Device (RPi5)

**TTS:**
- Piper voice model: 20-100 MB per voice
- TTS engine: 50 MB
- Emotion modulation: 30 MB (librosa)
- **Total: ~100-180 MB**

**CPU:**
- TTS synthesis: 30-50% for 1-2 seconds
- Idle: <1%

**Storage:**
- Voice models (5 voices): ~200 MB
- TTS engine: 50 MB
- **Total: ~250 MB**

---

## 8. Summary & Next Steps

### Design Complete ✅

**Voice Pipeline includes:**
1. ✅ Disabled by default, explicit opt-in
2. ✅ Hybrid activation (wake word OR push-to-talk)
3. ✅ Local models (Whisper, Piper, Silero VAD, Porcupine)
4. ✅ Cloud integration (optional, user-provided keys)
5. ✅ Multiple voices (10+), personality-based selection
6. ✅ Advanced prosody (pauses, emphasis, emotional modulation)
7. ✅ SSML support (future feature, marked as low priority)
8. ✅ Lip-sync integration with character animation

### Key Features

- **Privacy First:** Local processing, no cloud by default
- **Offline Capable:** Works without internet
- **Expressive:** Emotion modulation, personality-driven voice
- **Low Latency:** ~500ms-1s for STT, ~150-300ms for TTS
- **Flexible:** User can bring their own cloud models

### Integration Points

**With Character Animation:**
- Phoneme data synchronized with mouth animations
- Listening state triggers character animation

**With Central Agent:**
- Voice input processed as text input
- Response text sent to TTS

**With Emotion Regulator:**
- Current emotion modulates voice characteristics

**With Personality System:**
- Big Five traits influence voice selection and prosody

---

**Design Status:** ✅ COMPLETE  
**Ready for:** Implementation Phase 1  
**Estimated Implementation Time:** 3-4 weeks

**Note:** SSML support marked as low priority, can be added later as enhancement.
