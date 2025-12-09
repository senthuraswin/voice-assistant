"""
Voice Chatbot with OpenAI Speech
Listens to microphone, responds with high-quality OpenAI voice
Says "hello" when you say hello, "not understand" otherwise
"""

import speech_recognition as sr
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from io import BytesIO
import pygame

load_dotenv()


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
        print(f"Speech error: {e}")


def listen():
    """Listen to microphone and convert speech to text"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🎤 Listening... (say something)")
        
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("🔄 Processing...")
            
            # Use Google's free speech recognition
            text = recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None


def process_input(user_text):
    """Process user input and return response"""
    if not user_text:
        return None
    
    user_lower = user_text.lower().strip()
    
    print(f"👤 You said: '{user_text}'")
    
    # Check for hello
    if "hello" in user_lower:
        response = "hello"
    else:
        response = "not understand"
    
    return response


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🎙️  VOICE CHATBOT WITH OPENAI SPEECH")
    print("="*60)
    print("✅ Using your microphone + OpenAI high-quality voice")
    print("💬 Say 'hello' to get a hello response")
    print("💬 Say anything else to hear 'not understand'")
    print("🛑 Press Ctrl+C to exit")
    print("="*60)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Initialize audio
    print("\n🔧 Initializing audio system...")
    init_audio()
    print("✅ Audio ready!")
    
    print("\n🎯 Ready! Start speaking...\n")
    
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
            
            # Process and respond
            response = process_input(user_text)
            
            if response:
                print(f"🤖 Bot says: '{response}'")
                speak_openai(response, client)
            
            print("\n" + "-"*60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down voice chatbot...")
        pygame.mixer.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
