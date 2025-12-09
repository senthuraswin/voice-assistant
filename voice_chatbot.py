"""
Simple voice chatbot using Pipecat that responds to "hello" and says "not understand" otherwise.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import LLMAssistantResponseAggregator, LLMUserResponseAggregator
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import (
    Frame,
    TextFrame,
    TranscriptionFrame,
    EndFrame,
    TTSTextFrame,
)
from pipecat.services.openai import OpenAILLMService, OpenAITTSService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.vad.silero import SileroVADAnalyzer

# Load environment variables
load_dotenv()


class HelloDetectorProcessor(FrameProcessor):
    """Custom processor that detects 'hello' and responds accordingly."""
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        # Process transcription frames (user speech converted to text)
        if isinstance(frame, TranscriptionFrame):
            user_text = frame.text.lower().strip()
            
            print(f"User said: {frame.text}")
            
            # Check if user said hello
            if "hello" in user_text:
                response = "hello"
                print(f"Bot responds: {response}")
            else:
                response = "not understand"
                print(f"Bot responds: {response}")
            
            # Send response as TTS frame
            await self.push_frame(TTSTextFrame(response))
        else:
            # Pass through other frames
            await self.push_frame(frame, direction)


async def main():
    """Main function to run the voice chatbot."""
    
    # Check for required API keys
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    daily_api_key = os.getenv("DAILY_API_KEY", "")
    
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please copy .env.example to .env and add your OpenAI API key")
        sys.exit(1)
    
    # For local testing without Daily.co, we can use stdin/stdout transport
    # This example uses Daily for real-time voice communication
    
    async with aiohttp.ClientSession() as session:
        # Initialize Daily transport for voice I/O
        transport = DailyTransport(
            room_url=os.getenv("DAILY_ROOM_URL", ""),  # You can create a room via Daily API
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
        
        # Initialize OpenAI TTS service
        tts = OpenAITTSService(
            api_key=openai_api_key,
            voice="alloy"
        )
        
        # Create custom hello detector
        hello_detector = HelloDetectorProcessor()
        
        # Create pipeline
        pipeline = Pipeline([
            transport.input(),           # Receive audio input
            hello_detector,              # Detect hello and generate response
            tts,                         # Convert text response to speech
            transport.output(),          # Send audio output
        ])
        
        # Create task
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
        
        # Run the pipeline
        runner = PipelineRunner()
        
        print("Voice chatbot is running...")
        print("Say 'hello' to get a hello response")
        print("Say anything else to get 'not understand'")
        print("Press Ctrl+C to exit")
        
        await runner.run(task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down voice chatbot...")
