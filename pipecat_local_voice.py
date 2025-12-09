"""
Voice Chatbot using Pipecat Framework - Local Microphone Version
Listens to your microphone and speaks back using OpenAI
Says "hello" when you say hello, "not understand" otherwise
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import speech_recognition as sr
from openai import OpenAI
from io import BytesIO
import pygame

# Pipecat imports
from pipecat.frames.frames import Frame, TextFrame, TTSTextFrame
from pipecat.processors.frame_processor import FrameProcessor

load_dotenv()


class HelloDetectorProcessor(FrameProcessor):
    """Pipecat processor that detects 'hello' and responds."""
    
    def __init__(self):
        super().__init__()
        print("🤖 Pipecat Hello Detector initialized")
    
    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)
        
        # Process text frames (from speech recognition)
        if isinstance(frame, TextFrame):
            user_text = frame.text.lower().strip()
            
            print(f"\n👤 You said: '{frame.text}'")
            
            # Check for hello
            if "hello" in user_text:
                response = "hello"
            else:
                response = "not understand"
            
            print(f"🤖 Bot responds: '{response}'")
            
            # Create TTS frame
            tts_frame = TTSTextFrame(response)
            await self.push_frame(tts_frame)
        else:
            await self.push_frame(frame, direction)


def init_audio():
    """Initialize pygame for audio playback"""
    pygame.mixer.init()


def speak_openai(text, client):
    """Convert text to speech using OpenAI TTS"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Play the audio
        audio_data = BytesIO(response.content)
        pygame.mixer.music.load(audio_data)
        pygame.mixer.music.play()
        
        # Wait for audio to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"❌ Speech error: {e}")


def listen():
    """Listen to microphone and convert speech to text"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🎤 Listening... (say something)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("🔄 Processing...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"❌ Error: {e}")
            return None


async def main():
    """Main function"""
    print("\n" + "="*60)
    print("🎙️  PIPECAT VOICE CHATBOT (Local Microphone)")
    print("="*60)
    print("✅ Using Pipecat framework")
    print("✅ Using your microphone + OpenAI speech")
    print("💬 Say 'hello' to get a hello response")
    print("💬 Say anything else to hear 'not understand'")
    print("🛑 Press Ctrl+C to exit")
    print("="*60)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    # Initialize components
    print("\n🔧 Initializing...")
    client = OpenAI(api_key=api_key)
    init_audio()
    
    # Create Pipecat processor
    hello_processor = HelloDetectorProcessor()
    
    print("✅ Ready!")
    print("\n🎯 Start speaking...\n")
    
    try:
        while True:
            # Listen for input
            user_text = listen()
            
            if user_text is None:
                print("⏱️  No speech detected, listening again...")
                continue
            
            if user_text == "":
                print("❓ Could not understand, please try again")
                continue
            
            # Process through Pipecat processor
            text_frame = TextFrame(user_text)
            
            # Simulate async processing
            await hello_processor.process_frame(text_frame, None)
            
            # Get the response (simplified - normally would come from pipeline)
            user_lower = user_text.lower().strip()
            if "hello" in user_lower:
                response = "hello"
            else:
                response = "not understand"
            
            # Speak the response
            speak_openai(response, client)
            
            print("\n" + "-"*60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Pipecat voice chatbot...")
        pygame.mixer.quit()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
