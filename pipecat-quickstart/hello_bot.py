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
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.frames.frames import ErrorFrame
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

    # Text-to-Speech (ElevenLabs) with robust fallback handling.
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    def make_error_pusher(msg: str):
        class ErrorPusher(FrameProcessor):
            async def process_frame(self, frame: Frame, direction):
                await super().process_frame(frame, direction)
                logger.error(msg)
                await self.push_frame(ErrorFrame(error=msg, fatal=False, processor=self))

        return ErrorPusher()

    tts = None

    if ELEVENLABS_API_KEY:
        # Try ElevenLabs with retries and a voice-id fallback
        attempts = 0
        max_attempts = 3
        last_exc = None
        tried_default_voice = False
        while attempts < max_attempts:
            attempts += 1
            try:
                logger.info(f"Attempting ElevenLabs TTS (attempt {attempts}) with voice '{ELEVENLABS_VOICE_ID}'")
                tts = ElevenLabsTTSService(api_key=ELEVENLABS_API_KEY, voice_id=ELEVENLABS_VOICE_ID, model_id="eleven_turbo_v2")
                logger.info("✅ ElevenLabs TTS initialized")
                break
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                logger.warning(f"ElevenLabs TTS init failed (attempt {attempts}): {e}")
                # If voice not found or handshake/wss issue, try default Rachel voice once
                if ("voice does not exist" in msg or "voice does not exist" in str(e) or "handshake" in msg or "websocket" in msg) and not tried_default_voice:
                    tried_default_voice = True
                    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
                    logger.warning(f"Retrying ElevenLabs with default voice id '{ELEVENLABS_VOICE_ID}'")
                    awaitable_delay = 0.5
                    try:
                        import time

                        time.sleep(awaitable_delay)
                    except Exception:
                        pass
                    continue
                # backoff before retry
                try:
                    import time

                    time.sleep(0.5 * attempts)
                except Exception:
                    pass

        if tts is None:
            logger.error(f"ElevenLabs TTS unavailable: {last_exc}")

    if tts is None:
        # Try Cartesia fallback if available
        try:
            from pipecat.services.cartesia.tts import CartesiaTTSService

            cart_api = os.getenv("CARTESIA_API_KEY")
            if cart_api:
                logger.info("Falling back to Cartesia TTS")
                tts = CartesiaTTSService(api_key=cart_api, voice_id=os.getenv("CARTESIA_VOICE_ID", "71a7ad14-091c-4e8e-a314-022ece01c121"))
            else:
                logger.error("Cartesia API key missing; cannot fallback to Cartesia TTS")
                tts = make_error_pusher("No TTS available: ElevenLabs failed and Cartesia API key missing")
        except Exception as e:
            logger.error(f"Cartesia fallback not available: {e}")
            tts = make_error_pusher(f"No TTS available: ElevenLabs failed ({last_exc}) and Cartesia unavailable ({e})")

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
