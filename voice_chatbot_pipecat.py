import asyncio
import os
import sys
from dotenv import load_dotenv

from pipecat.frames.frames import (
    Frame,
    TextFrame,
    EndFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.vad.silero import SileroVADAnalyzer

# Load environment variables
load_dotenv()


class HelloProcessor(FrameProcessor):
    """Processor that detects 'hello' in user speech and responds accordingly."""
    
    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)
        
        # Check for text frames containing user speech
        if isinstance(frame, TextFrame):
            user_text = frame.text.lower().strip()
            
            print(f"\n🎤 User said: {frame.text}")
            
            # Detect hello and generate response
            if "hello" in user_text:
                response = "hello"
                print(f"🤖 Bot responds: {response}")
            else:
                response = "not understand"
                print(f"🤖 Bot responds: {response}")
            
            # Push response frame
            await self.push_frame(TextFrame(response))
        else:
            # Pass through other frames
            await self.push_frame(frame, direction)


async def main():
    """Main entry point for the voice chatbot."""
    
    # Get API keys from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    daily_room_url = os.getenv("DAILY_ROOM_URL", "")
    
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        print("Please create a .env file with your OpenAI API key")
        print("Copy .env.example to .env and add your key")
        sys.exit(1)
    
    if not daily_room_url:
        print("❌ Error: DAILY_ROOM_URL not found in .env file")
        print("You need a Daily.co room URL for voice communication")
        print("Get one at: https://dashboard.daily.co/")
        sys.exit(1)
    
    try:
        # Initialize transport for voice I/O
        transport = DailyTransport(
            room_url=daily_room_url,
            token=os.getenv("DAILY_TOKEN", ""),
            bot_name="Voice Chatbot",
            params=DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,
            )
        )
        
        # Initialize OpenAI service for TTS
        tts_service = OpenAILLMService(
            api_key=openai_api_key,
            model="gpt-4o-mini"
        )
        
        # Create hello processor
        hello_processor = HelloProcessor()
        
        # Build pipeline
        pipeline = Pipeline([
            transport.input(),      # Get audio input
            hello_processor,        # Process and detect hello
            tts_service,           # Convert response to speech
            transport.output(),    # Output audio
        ])
        
        # Create and run task
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
        runner = PipelineRunner()
        
        print("\n" + "="*60)
        print("🎙️  Voice Chatbot Using Pipecat")
        print("="*60)
        print("✅ Connected to Daily.co room")
        print("💬 Say 'hello' to get a hello response")
        print("💬 Say anything else to hear 'not understand'")
        print("🛑 Press Ctrl+C to exit")
        print("="*60 + "\n")
        
        await runner.run(task)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down voice chatbot...")
