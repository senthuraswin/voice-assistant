#
# Simple Hello Bot using Pipecat
# Says "hello" if user says hello, else says "not understand"
#

import os

from dotenv import load_dotenv
from loguru import logger

print("🚀 Starting Simple Hello Bot...")
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
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)


class HelloProcessor(FrameProcessor):
    """Simple processor: responds 'hello' if user says hello, else 'not understand'."""

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            text = frame.text.lower().strip()
            logger.info(f"🎤 User said: {text}")

            if "hello" in text or "hi" in text:
                response = "Hello!"
            else:
                response = "Not understand."

            logger.info(f"🤖 Bot responds: {response}")
            await self.push_frame(TextFrame(text=response))
        else:
            await self.push_frame(frame)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting bot")

    # Speech-to-Text (Deepgram)
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    # Text-to-Speech (Cartesia)
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
    )

    # Our simple hello logic - NO OpenAI needed!
    hello_processor = HelloProcessor()

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Pipeline: Mic -> STT -> HelloProcessor -> TTS -> Speaker
    pipeline = Pipeline(
        [
            transport.input(),      # Your microphone
            rtvi,                   # RTVI processor
            stt,                    # Deepgram: voice -> text
            hello_processor,        # Our logic: hello -> "Hello!", else -> "Not understand."
            tts,                    # Cartesia: text -> voice
            transport.output(),     # Your speaker
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
        logger.info("✅ Client connected - say 'hello' to test!")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point."""

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
