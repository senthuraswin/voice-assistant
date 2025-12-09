"""
Voice Chatbot using Pipecat with OpenAI Realtime API
This works with your microphone and speaks back!
Says "hello" when you say hello, "not understand" otherwise
"""

import asyncio
import os
import sys
import aiohttp
from dotenv import load_dotenv

from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    TextFrame,
    EndFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.openai import OpenAILLMContext
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.vad.silero import SileroVADAnalyzer

load_dotenv()


class HelloDetectorProcessor(FrameProcessor):
    """Custom processor that detects 'hello' and responds accordingly."""
    
    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)
        
        # Look for user messages
        if isinstance(frame, LLMMessagesFrame):
            messages = frame.messages
            
            # Get the last user message
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_text = msg.get("content", "").lower().strip()
                    
                    print(f"\n🎤 You said: {msg.get('content')}")
                    
                    # Check if user said hello
                    if "hello" in user_text:
                        response = "hello"
                    else:
                        response = "not understand"
                    
                    print(f"🤖 Bot responds: {response}")
                    
                    # Create response message
                    response_messages = [
                        {"role": "assistant", "content": response}
                    ]
                    
                    await self.push_frame(LLMMessagesFrame(response_messages))
                    return
        
        # Pass through other frames
        await self.push_frame(frame, direction)


async def main():
    """Main function to run the voice chatbot."""
    
    # Check for required environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    daily_room_url = os.getenv("DAILY_ROOM_URL", "")
    
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        print("Please add your OpenAI API key to the .env file")
        sys.exit(1)
    
    if not daily_room_url:
        print("❌ Error: DAILY_ROOM_URL not found in .env file")
        print("\n📝 To get a Daily.co room URL:")
        print("   1. Go to https://dashboard.daily.co/")
        print("   2. Sign up for a free account")
        print("   3. Create a room")
        print("   4. Copy the room URL")
        print("   5. Add to .env file as: DAILY_ROOM_URL=https://your-domain.daily.co/your-room")
        print("\n💡 Or use local_voice_bot.py which works without Daily.co!")
        sys.exit(1)
    
    async with aiohttp.ClientSession() as session:
        # Initialize Daily transport
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
        
        # Create hello detector processor
        hello_detector = HelloDetectorProcessor()
        
        # User and assistant aggregators
        user_aggregator = LLMUserResponseAggregator()
        assistant_aggregator = LLMAssistantResponseAggregator()
        
        # Build pipeline
        pipeline = Pipeline([
            transport.input(),
            user_aggregator,
            hello_detector,
            assistant_aggregator,
            transport.output(),
        ])
        
        # Create and run task
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
        runner = PipelineRunner()
        
        print("\n" + "="*60)
        print("🎙️  PIPECAT VOICE CHATBOT")
        print("="*60)
        print("✅ Connected to Daily.co room")
        print("💬 Say 'hello' to get a hello response")
        print("💬 Say anything else to hear 'not understand'")
        print("🛑 Press Ctrl+C to exit")
        print("="*60 + "\n")
        
        await runner.run(task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down voice chatbot...")
