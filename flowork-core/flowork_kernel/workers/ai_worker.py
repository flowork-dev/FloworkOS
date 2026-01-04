########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\workers\ai_worker.py total lines 209 
########################################################################

import sys
import json
import os
import time
import uuid
import traceback

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(write_through=True, encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(write_through=True, encoding='utf-8')

def force_print(msg, is_error=True):
    """Print message to stderr so it shows up in Docker logs immediately."""
    target = sys.stderr if is_error else sys.stdout
    print(f"[{time.strftime('%X')}] {msg}", file=target, flush=True)

def handle_audio_generation(text, model_path, output_dir="temp_audio"):
    try:
        from transformers import pipeline
        import scipy.io.wavfile
        import numpy as np

        force_print(f"[Worker] Starting Audio Gen Process (TTS)...")
        force_print(f"[Worker] Model: {model_path}")

        synthesiser = pipeline("text-to-speech", model=model_path, device=0 if os.getenv("CUDA_VISIBLE_DEVICES") else -1)

        force_print(f"[Worker] Generating Audio for: {text[:30]}...")

        music = synthesiser(text)

        if isinstance(music, list): music = music[0]

        audio_data = music['audio']
        sampling_rate = music['sampling_rate']

        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)

        audio_data = np.squeeze(audio_data)

        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
             audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=1.0, neginf=-1.0)
             audio_data = np.clip(audio_data, -1.0, 1.0)
             audio_data = (audio_data * 32767).astype(np.int16)

        os.makedirs(output_dir, exist_ok=True)
        filename = f"audio_{uuid.uuid4().hex}.wav"
        file_path = os.path.join(output_dir, filename)

        scipy.io.wavfile.write(file_path, rate=sampling_rate, data=audio_data)

        abs_path = os.path.abspath(file_path)
        force_print(f"[Worker] Audio Saved to: {abs_path} (Format: Int16 WAV, Shape: {audio_data.shape})")

        result = {"audio_path": abs_path}
        print(json.dumps(result), file=sys.stdout, flush=True)
        return True

    except Exception as e:
        force_print(f"[Worker ERROR] Audio Gen Failed: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"error": str(e)}), file=sys.stdout, flush=True)
        return False

def handle_image_generation(prompt, model_path, output_dir="temp_gen"):
    try:
        import torch
        from diffusers import StableDiffusionXLPipeline, AutoencoderKL

        force_print(f"[Worker] Starting Image Gen Process...")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        force_print(f"[Worker] Device: {device} | Dtype: {dtype}")

        force_print("[Worker] Loading VAE...")
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=dtype
        )

        force_print(f"[Worker] Loading Pipeline from: {model_path}")
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_path,
            vae=vae,
            torch_dtype=dtype,
            use_safetensors=True,
            variant="fp16" if device == "cuda" else None
        )

        if device == "cuda":
            force_print("[Worker] Enabling Model CPU Offload (Low VRAM Mode)...")
            pipe.enable_model_cpu_offload()

        generator = torch.Generator(device="cpu").manual_seed(int(time.time()))

        force_print(f"[Worker] >>> GENERATING NOW <<< | Prompt: {prompt[:50]}...")

        image = pipe(
            prompt=prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
            generator=generator
        ).images[0]

        force_print("[Worker] Generation Complete. Saving...")

        os.makedirs(output_dir, exist_ok=True)
        filename = f"gen_{uuid.uuid4().hex}.png"
        file_path = os.path.join(output_dir, filename)
        image.save(file_path)

        abs_path = os.path.abspath(file_path)
        force_print(f"[Worker] Saved to: {abs_path}")

        result = {"image_path": abs_path}
        print(json.dumps(result), file=sys.stdout, flush=True)
        return True

    except Exception as e:
        force_print(f"[Worker ERROR] SDXL Failed: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"error": str(e)}), file=sys.stdout, flush=True)
        return False

def main():
    force_print("[Worker] Initializing...")

    if len(sys.argv) < 2:
        force_print("[Worker Error] Missing model_path argument.")
        sys.exit(1)

    model_path = sys.argv[1]

    mode = "text"
    model_path_lower = model_path.lower()

    if any(x in model_path_lower for x in ["stable-diffusion", "sdxl", "flux", "animagine"]):
        mode = "image"
    elif any(x in model_path_lower for x in ["tts", "mms", "audio", "speech"]):
        mode = "audio"

    force_print(f"[Worker] Mode: {mode} | Model: {os.path.basename(model_path)}")

    if mode == "audio":
        force_print("[Worker] Waiting for Text Input (Line Mode)...")
        try:
            prompt = sys.stdin.readline().strip()
        except Exception as e:
            force_print(f"[Worker Error] Failed to read stdin: {e}")
            sys.exit(1)

        if not prompt:
            force_print("[Worker Error] Received empty input.")
            sys.exit(0)

        handle_audio_generation(prompt, model_path)
        sys.exit(0)

    if mode == "image":
        force_print("[Worker] Waiting for Prompt (Line Mode)...")
        try:
            prompt = sys.stdin.readline().strip()
        except Exception as e:
            force_print(f"[Worker Error] Failed to read stdin: {e}")
            sys.exit(1)

        if not prompt:
            force_print("[Worker Error] Received empty prompt or pipe closed.")
            sys.exit(0)

        force_print(f"[Worker] Prompt received: {prompt[:30]}... Processing...")
        handle_image_generation(prompt, model_path)
        sys.exit(0)

    try:
        from llama_cpp import Llama
        prompt = sys.stdin.read()
        if not prompt: sys.exit(0)

        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False
        )
        stream = llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in stream:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta:
                sys.stdout.write(delta['content'])
                sys.stdout.flush()
    except Exception as e:
        force_print(f"[Worker Error] Text Gen Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
