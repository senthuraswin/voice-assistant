#
# Gemini Bot using Pipecat
# Listens, sends user transcription to a Gemini-compatible API, and speaks the reply
#

import os
import asyncio
from dotenv import load_dotenv
from loguru import logger
from google import genai

print("🚀 Starting Gemini Bot...")
print("⏳ Loading models and imports...\n")

logger.info("Loading Local Smart Turn Analyzer V3...")
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

logger.info("✅ Local Smart Turn Analyzer V3 loaded")
logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import TextFrame, Frame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)


class GeminiProcessor(FrameProcessor):
    """Sends transcribed text to a Gemini-compatible API and returns the model reply."""

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            user_text = frame.text.strip()
            logger.info(f"🎤 User said: {user_text}")

            try:
                reply = await asyncio.to_thread(self._call_gemini, user_text)
            except Exception as e:
                logger.error(f"Exception in _call_gemini: {e}", exc_info=True)
                reply = None

            if reply is None:
                reply = "Sorry, I couldn't get a reply from the model."
            else:
                # Clean up the response for TTS
                import re
                reply = reply.strip()
                
                # Remove markdown formatting that might cause TTS issues
                reply = re.sub(r'\*\*(.*?)\*\*', r'\1', reply)  # Remove **bold** formatting
                reply = re.sub(r'\*(.*?)\*', r'\1', reply)      # Remove *italic* formatting
                reply = re.sub(r'`(.*?)`', r'\1', reply)        # Remove `code` formatting
                
                # Replace newlines and bullet points with natural speech pauses
                reply = re.sub(r'\n\s*\*\s+', '. ', reply)      # Convert bullet points to sentences
                reply = re.sub(r'\n+', '. ', reply)             # Replace newlines with period+space
                reply = re.sub(r'\.\.+', '.', reply)            # Fix multiple periods
                reply = re.sub(r'\s+', ' ', reply)              # Normalize whitespace
                reply = reply.strip()
                
                # Keep response reasonable but not too short (2-3 sentences)
                sentences = re.split(r'(?<=[.!?])\s+', reply)
                if len(sentences) > 3:
                    reply = ' '.join(sentences[:3])
                    if not reply.endswith(('.', '!', '?')):
                        reply += '.'

            logger.info(f"🤖 Gemini replied: {reply}")
            logger.debug(f"Sending to TTS: '{reply}' (length: {len(reply)})")
            await self.push_frame(TextFrame(text=reply))
        else:
            await self.push_frame(frame)

    def _call_gemini(self, text: str) -> str | None:
        """Synchronous helper that calls the Google Gemini API using the official SDK.

        Environment variables used:
        - GEMINI_API_KEY: Google AI Studio API key
        - GEMINI_MODEL: Model name (default: gemini-2.5-flash)

        Uses the official google-genai Python SDK.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        if not api_key:
            logger.error("GEMINI_API_KEY not set in environment")
            return None

        try:
            logger.debug(f"Calling Gemini model: {model}")
            logger.debug(f"User input: {text}")
            
            # Create client with API key
            client = genai.Client(api_key=api_key)
            
            # Generate content
            response = client.models.generate_content(
                model=model,
                contents=text,
            )
            
            # Check if response has text
            if hasattr(response, 'text') and response.text:
                logger.debug(f"Response: {response.text[:200]}")
                return response.text
            else:
                # Handle cases where response doesn't have text (blocked, error, etc.)
                logger.error(f"No text in response. Response object: {response}")
                if hasattr(response, 'prompt_feedback'):
                    logger.error(f"Prompt feedback: {response.prompt_feedback}")
                if hasattr(response, 'candidates') and response.candidates:
                    logger.error(f"Candidates: {response.candidates[0]}")
                return "I'm sorry, I couldn't generate a response."

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            return None


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting Gemini bot")

    # Speech-to-Text (Deepgram)
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    # Text-to-Speech (ElevenLabs) - configured to speak complete responses
    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID", "Xtbu4DbP3EiktnAlnmbX"),  # Rachel - default free voice
        model_id=os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2"),
    )

    # Gemini processor
    gemini_processor = GeminiProcessor()

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Pipeline: Mic -> STT -> GeminiProcessor -> TTS -> Speaker
    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            gemini_processor,
            tts,
            transport.output(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("✅ Client connected - speak to send text to Gemini")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
