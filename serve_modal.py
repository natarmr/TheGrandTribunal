import os
import json
import modal
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

app = modal.App("grand-tribunal-inference")
volume = modal.Volume.from_name("grand-tribunal-volume", create_if_missing=True)

# Pre-bake the model weights into the container image to eliminate 20-30s of download time
inference_image = (
    modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.10")
    .apt_install("ffmpeg")
    .pip_install(
        "vllm",
        "fastapi",
        "uvicorn",
        "pydantic",
        "hf_transfer",
        "voxcpm",
        "soundfile",
        "transformers",
        "python-multipart",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_commands("hf download Qwen/Qwen2.5-3B-Instruct")
    .run_commands("hf download openbmb/VoxCPM2")
    .run_commands("hf download openai/whisper-tiny.en")
)

# =====================================================================
# Consolidated Model (Judge + 4 Characters on 1 GPU)
# =====================================================================
@app.cls(
    image=inference_image,
    gpu="a10g",
    volumes={"/vol": volume},
    min_containers=0,
    scaledown_window=900,
)
@modal.concurrent(max_inputs=15)
class TribunalModel:
    @modal.enter()
    def load_model(self):
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.engine.async_llm_engine import AsyncLLMEngine
        from vllm.lora.request import LoRARequest

        print("Loading Tribunal Base Model + 5 LoRA adapters...")
        engine_args = AsyncEngineArgs(
            model="Qwen/Qwen2.5-3B-Instruct",
            enable_lora=True,
            max_loras=5,
            max_lora_rank=16,
            max_cpu_loras=5,
            dtype="bfloat16",
            enforce_eager=True,
            gpu_memory_utilization=0.45,
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        
        self.adapters = {}
        
        # Load Judge Adapter
        judge_path = "/vol/adapters/judge"
        if os.path.exists(judge_path):
            self.adapters["judge"] = LoRARequest("judge", 1, judge_path)
            print("Loaded adapter for judge")
        else:
            print("Warning: Judge adapter not found!")
            
        # Load Character Adapters
        for i, char_name in enumerate(["oscar_wilde", "friedrich_nietzsche", "plato", "schopenhauer"], start=2):
            adapter_path = f"/vol/adapters/{char_name}"
            if os.path.exists(adapter_path):
                self.adapters[char_name] = LoRARequest(char_name, i, adapter_path)
                print(f"Loaded adapter for {char_name}")
            else:
                print(f"Warning: Adapter for {char_name} not found!")

        self.display_names = {
            "oscar_wilde": "Oscar Wilde",
            "friedrich_nietzsche": "Friedrich Nietzsche",
            "plato": "Plato",
            "schopenhauer": "Arthur Schopenhauer",
        }

        print("Loading speech models on the shared A10G...")
        from transformers import pipeline
        from voxcpm import VoxCPM

        self.stt = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-tiny.en",
            device="cuda",
        )
        self.tts = VoxCPM.from_pretrained("openbmb/VoxCPM2", device="cuda")
        print("Tribunal Model loaded successfully.")

    @modal.method()
    async def evaluate_judge(self, topic: str, argument: str):
        from vllm import SamplingParams
        from transformers import AutoTokenizer
        import uuid
        
        if "judge" not in self.adapters:
            raise ValueError("Judge adapter is missing from volume!")

        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
        system_prompt = "You are the Grand Tribunal Judge. Score the argument on the topic across five axes: score (1-10), logic (1-10), relevance (1-10), creativity (1-5), and reasoning (one sentence explaining the score). Reply strictly in JSON."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {topic}\nArgument: {argument}"}
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        sampling_params = SamplingParams(temperature=0.0, max_tokens=250, stop=["<|im_end|>"])
        generator = self.engine.generate(
            prompt,
            sampling_params,
            str(uuid.uuid4()),
            lora_request=self.adapters["judge"]
        )
        
        final_output = None
        async for output in generator:
            final_output = output
        return final_output.outputs[0].text

    @modal.method()
    async def generate_character(self, character: str, situation: str):
        from vllm import SamplingParams
        from transformers import AutoTokenizer
        import uuid

        if character not in self.adapters:
            raise ValueError(f"Unknown or missing adapter for character: {character}")

        display_name = self.display_names.get(character, character.replace("_", " ").title())
        system_prompt = f"You are {display_name}. First, identify the core logical premise or underlying meaning of the opponent's argument. Then, attack that core premise directly in your characteristic style and voice. Do not get distracted by surface-level details. Output a JSON object with 'response' (your verbal reply, 1-3 sentences) and 'expression' ('neutral' or 'objecting')."
        
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Situation: {situation}"}
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        sampling_params = SamplingParams(temperature=0.7, max_tokens=300, stop=["<|im_end|>"])
        generator = self.engine.generate(
            prompt,
            sampling_params,
            str(uuid.uuid4()),
            lora_request=self.adapters[character]
        )
        
        final_output = None
        async for output in generator:
            final_output = output
        return final_output.outputs[0].text

    @modal.method()
    async def transcribe_audio(self, audio_bytes: bytes, suffix: str = ".wav"):
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
            audio_file.write(audio_bytes)
            audio_path = audio_file.name

        try:
            result = self.stt(audio_path)
            if isinstance(result, dict):
                return result.get("text", "")
            return str(result)
        finally:
            try:
                os.remove(audio_path)
            except OSError:
                pass

    @modal.method()
    async def synthesize_speech(self, text: str):
        import io
        import numpy as np
        import soundfile as sf

        audio = self.tts.generate(text=text, cfg_value=2.0)
        sample_rate = 48000

        if isinstance(audio, dict):
            sample_rate = int(audio.get("sample_rate") or audio.get("sampling_rate") or sample_rate)
            audio = audio.get("audio") or audio.get("wav") or audio.get("waveform")
        elif isinstance(audio, tuple):
            audio, sample_rate = audio[0], int(audio[1])

        audio = np.asarray(audio)
        if audio.ndim > 1:
            audio = np.squeeze(audio)

        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV")
        buffer.seek(0)
        return buffer.getvalue()

# =====================================================================
# FastAPI Web Endpoints
# =====================================================================
web_app = FastAPI(title="The Grand Tribunal Inference API")

@app.function(image=inference_image, min_containers=0, scaledown_window=900)
@modal.asgi_app()
def api():
    @web_app.post("/judge")
    async def judge_endpoint(request: Request):
        try:
            data = await request.json()
            topic = data.get("topic")
            argument = data.get("argument")
            
            if not topic or not argument:
                return JSONResponse({"error": "Missing 'topic' or 'argument'"}, status_code=400)
                
            model = TribunalModel()
            result = await model.evaluate_judge.remote.aio(topic, argument)
            
            try:
                parsed = json.loads(result)
                return JSONResponse(parsed)
            except json.JSONDecodeError:
                return JSONResponse({"raw_response": result, "error": "Failed to parse JSON"})
                
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @web_app.post("/character")
    async def character_endpoint(request: Request):
        try:
            data = await request.json()
            character = data.get("character")
            situation = data.get("situation")
            
            if not character or not situation:
                return JSONResponse({"error": "Missing 'character' or 'situation'"}, status_code=400)
                
            model = TribunalModel()
            result = await model.generate_character.remote.aio(character, situation)
            
            try:
                parsed = json.loads(result)
                return JSONResponse(parsed)
            except json.JSONDecodeError:
                return JSONResponse({"raw_response": result, "error": "Failed to parse JSON"})
                
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @web_app.post("/stt")
    async def stt_endpoint(file: UploadFile = File(...)):
        try:
            audio_bytes = await file.read()
            suffix = os.path.splitext(file.filename or "")[1] or ".wav"
            model = TribunalModel()
            text = await model.transcribe_audio.remote.aio(audio_bytes, suffix)
            return JSONResponse({"text": text})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @web_app.post("/tts")
    async def tts_endpoint(request: Request):
        try:
            data = await request.json()
            text = data.get("text")
            if not text:
                return JSONResponse({"error": "Missing 'text'"}, status_code=400)

            model = TribunalModel()
            audio_bytes = await model.synthesize_speech.remote.aio(text)
            return StreamingResponse(
                iter([audio_bytes]),
                media_type="audio/wav",
                headers={"Content-Disposition": "inline; filename=tribunal_reply.wav"},
            )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    return web_app

@app.local_entrypoint()
async def test_end_to_end():
    print("==========================================")
    print(" RIGOROUS SMOKE TEST: THE GRAND TRIBUNAL")
    print("==========================================\n")

    model = TribunalModel()

    print("[1/3] Testing Character Model: Oscar Wilde")
    print("Topic: Video games as high art.")
    wilde_res = await model.generate_character.remote.aio("oscar_wilde", "I believe video games are the highest form of modern art, superior to painting.")
    print(f"\n--- Oscar Wilde Responds ---\n{wilde_res}\n----------------------------\n")

    print("[2/3] Testing Character Model: Friedrich Nietzsche")
    print("Topic: Social Media.")
    nietzsche_res = await model.generate_character.remote.aio("friedrich_nietzsche", "Social media brings us closer together as a global community.")
    print(f"\n--- Nietzsche Responds ---\n{nietzsche_res}\n--------------------------\n")

    print("[3/3] Testing Judge Model")
    print("Topic: The meaning of life is just to be happy.")
    print("Argument: Happiness is merely a fleeting chemical state. True meaning is found in overcoming great struggles and leaving a legacy.")
    judge_res = await model.evaluate_judge.remote.aio("The meaning of life is just to be happy.", "Happiness is merely a fleeting chemical state. True meaning is found in overcoming great struggles and leaving a legacy.")
    print(f"\n--- Judge Score ---\n{judge_res}\n-------------------\n")

    print("[4/4] Testing Speech Models (TTS -> STT Closed Loop)")
    test_text = "The court has reached a verdict."
    print(f"Synthesizing TTS for: '{test_text}'")
    audio_bytes = await model.synthesize_speech.remote.aio(test_text)
    print(f"Generated {len(audio_bytes)} bytes of audio.")
    assert audio_bytes.startswith(b"RIFF"), "TTS failed: Audio bytes do not start with WAV magic header RIFF!"
    print("TTS Success: Valid WAV format detected.")

    print("Transcribing synthesized audio back to text...")
    transcription = await model.transcribe_audio.remote.aio(audio_bytes, ".wav")
    print(f"Transcription: '{transcription}'")
    assert "court" in transcription.lower() or "verdict" in transcription.lower(), f"STT failed: Expected transcription to contain 'court' or 'verdict', got '{transcription}'"
    print("STT Success: Correct transcription returned.")
    
    print("✅ Smoke test complete!")
