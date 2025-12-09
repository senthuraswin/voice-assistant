"""
Simple Voice Chatbot using Pipecat Framework
Uses microphone input and speaker output to respond to "hello"
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if we have the necessary imports
try:
    from pipecat.frames.frames import Frame, TextFrame, AudioRawFrame, TTSTextFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.frame_processor import FrameProcessor
    from pipecat.services.openai.tts import OpenAITTSService
    
except ImportError as e:
    print(f"Error importing Pipecat components: {e}")
    print("Make sure you've installed: pip install pipecat-ai[openai]")
    sys.exit(1)


class HelloDetector(FrameProcessor):
    """Detects 'hello' in user speech and responds."""
    
    def __init__(self):
        super().__init__()
        print("🤖 Hello Detector initialized")
    
    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)
        
        # Process transcription frames (from STT)
        if isinstance(frame, TextFrame):
            user_text = frame.text.lower().strip()
            
            print(f"\n🎤 You said: '{frame.text}'")
            
            # Check for hello
            if "hello" in user_text:
                response = "hello"
            else:
                response = "not understand"
            
            print(f"🤖 Bot says: '{response}'")
            
            # Send to TTS
            await self.push_frame(TTSTextFrame(response))
        else:
            # Pass other frames through
            await self.push_frame(frame, direction)


async def main():
    """Main function to run voice chatbot."""
    
    print("\n" + "="*60)
    print("🎙️  Pipecat Voice Chatbot")
    print("="*60)
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("\n❌ Missing OPENAI_API_KEY in .env file")
        print("Please create .env file and add:")
        print("OPENAI_API_KEY=your_key_here")
        print("\nGet your key from: https://platform.openai.com/api-keys")
        return
    
    print("✅ OpenAI API key found")
    print("\nNote: This version needs additional setup for full voice support.")
    print("For now, it demonstrates the Pipecat framework structure.")
    print("\nTo use full voice features, you need:")
    print("  1. A Daily.co account and room URL")
    print("  2. Or local audio setup with PyAudio")
    print("\nPress Ctrl+C to exit\n")
    
    # Initialize components
    try:
        # Text-to-Speech service
        tts = OpenAITTSService(
            api_key=openai_key,
            voice="alloy"
        )
        
        # Hello detector processor
        detector = HelloDetector()
        
        print("="*60)
        print("\n✅ Pipecat components initialized successfully!")
        print("🎯 The framework is ready. To make it fully functional:")
        print("   - Add Daily.co room URL to .env as DAILY_ROOM_URL")
        print("   - Or use local audio transport")
        print("\n   See voice_chatbot_pipecat.py for the full example")
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error initializing components: {e}")
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
