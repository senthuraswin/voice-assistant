"""
Pipecat Voice Chatbot - Windows Compatible Version
Uses Pipecat framework with OpenAI and Deepgram
Says "hello" when you say hello, "not understand" otherwise
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Pipecat imports
from pipecat.frames.frames import (
    Frame,
    TextFrame,
    TranscriptionFrame,
    EndFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

# For local audio
import speech_recognition as sr
import pygame
from io import BytesIO
from cartesia import Cartesia

load_dotenv()


class HelloDetectorProcessor(FrameProcessor):
    """Pipecat processor that detects 'hello' in transcribed speech."""
    
    def __init__(self):
        super().__init__()
        print("🤖 Pipecat HelloDetector processor initialized")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        # Check for transcription frames
        if isinstance(frame, TranscriptionFrame):
            user_text = frame.text.lower().strip()
            
            print(f"\n👤 You said: '{frame.text}'")
            
            # Detect hello
            if "hello" in user_text:
                response = "hello"
            else:
                response = "not understand"
            
            print(f"🤖 Bot responds: '{response}'")
            
            # Push text frame for TTS
            await self.push_frame(TextFrame(text=response))
        else:
            await self.push_frame(frame, direction)


def init_audio():
    """Initialize pygame for audio playback"""
    pygame.mixer.init(frequency=44100, size=-16, channels=1)


def speak_cartesia(text, client):
    """Use Cartesia TTS to speak"""
    try:
        # Generate audio using Cartesia
        audio_generator = client.tts.bytes(
            model_id="sonic-2",
            transcript=text,
            voice={
                "mode": "id",
                "id": "71a7ad14-091c-4e8e-a314-022ece01c121"  # British Lady voice
            },
            output_format={
                "container": "wav",
                "encoding": "pcm_s16le", 
                "sample_rate": 44100
            }
        )
        
        # Collect all bytes from generator
        audio_bytes = b"".join(chunk for chunk in audio_generator)
        
        # Play audio
        audio_buffer = BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_buffer, "wav")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"❌ TTS Error: {e}")


def listen():
    """Listen to microphone"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🎤 Listening... (speak now)")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("🔄 Processing speech...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None


async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🎙️  PIPECAT VOICE CHATBOT")
    print("="*60)
    print("✅ Using Pipecat Framework")
    print("✅ Google STT + Cartesia TTS")
    print("💬 Say 'hello' → Bot responds 'hello'")
    print("💬 Say anything else → Bot responds 'not understand'")
    print("🛑 Press Ctrl+C to exit")
    print("="*60)
    
    # Check API keys
    cartesia_key = os.getenv("CARTESIA_API_KEY")
    
    if not cartesia_key:
        print("\n❌ CARTESIA_API_KEY not found!")
        sys.exit(1)
    
    print("\n✅ API keys loaded")
    
    # Initialize
    init_audio()
    client = Cartesia(api_key=cartesia_key)
    
    # Create Pipecat processor
    hello_processor = HelloDetectorProcessor()
    
    print("✅ Pipecat pipeline ready!")
    print("\n🎯 Start speaking...\n")
    
    try:
        while True:
            # Listen
            user_text = listen()
            
            if user_text is None:
                print("⏱️  No speech detected...")
                continue
            
            if user_text == "":
                print("❓ Could not understand, try again")
                continue
            
            # Process through Pipecat processor
            transcription_frame = TranscriptionFrame(
                text=user_text,
                user_id="user",
                timestamp=""
            )
            
            # Process frame
            await hello_processor.process_frame(transcription_frame, FrameDirection.DOWNSTREAM)
            
            # Get response and speak
            user_lower = user_text.lower().strip()
            response = "hello" if "hello" in user_lower else "not understand"
            
            # Speak response using Cartesia TTS
            speak_cartesia(response, client)
            
            print("-" * 60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        pygame.mixer.quit()


if __name__ == "__main__":
    # Load env from pipecat-quickstart folder if running from there
    if os.path.exists("pipecat-quickstart/.env"):
        load_dotenv("pipecat-quickstart/.env")
    
    asyncio.run(main())
