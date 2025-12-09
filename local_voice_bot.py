import speech_recognition as sr
import pyttsx3
import sys

def init_tts():
    """Initialize text-to-speech engine"""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        return engine
    except Exception as e:
        print(f"Warning: Could not initialize TTS: {e}")
        return None

def speak(text, engine):
    """Convert text to speech"""
    if engine:
        engine.say(text)
        engine.runAndWait()
    else:
        print(f"Bot would say: {text}")

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
    print("🎙️  LOCAL VOICE CHATBOT")
    print("="*60)
    print("✅ Using your computer's microphone")
    print("💬 Say 'hello' to get a hello response")
    print("💬 Say anything else to hear 'not understand'")
    print("🛑 Press Ctrl+C to exit")
    print("="*60)
    
    # Initialize TTS
    print("\n🔧 Initializing text-to-speech...")
    tts_engine = init_tts()
    
    if tts_engine:
        print("✅ TTS ready!")
    else:
        print("⚠️  TTS not available, will print responses only")
    
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
                speak(response, tts_engine)
            
            print("\n" + "-"*60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down voice chatbot...")
        sys.exit(0)

if __name__ == "__main__":
    main()
