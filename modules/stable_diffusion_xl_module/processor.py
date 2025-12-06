########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\stable_diffusion_xl_module\processor.py total lines 120 
########################################################################

import os
import time
import shutil
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
from flowork_kernel.utils.payload_helper import get_nested_value
from flowork_kernel.utils.file_helper import sanitize_filename

class StableDiffusionXLModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "pro"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.output_dir = os.path.join(self.kernel.data_path, "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)
        self.ai_manager = self.kernel.get_service("ai_provider_manager_service")

    def _create_error_payload(self, payload, error_message):
        self.logger(error_message, "ERROR")
        if "data" not in payload or not isinstance(payload["data"], dict):
            payload["data"] = {}
        payload["data"]["error"] = error_message
        return {"payload": payload, "output_name": "error"}

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        model_folder_name = config.get("model_folder", "stable-diffusion-xl-base-1.0")

        prompt = (
            get_nested_value(payload, config.get("prompt_source_variable"))
            or get_nested_value(payload, "data.prompt")
            or config.get("prompt")
        )

        filename_prefix = config.get("output_filename_prefix", "sdxl")
        user_output_folder = config.get("output_folder", "").strip()

        save_dir = user_output_folder if (user_output_folder and os.path.exists(user_output_folder)) else self.output_dir

        if mode == "SIMULATE":
            status_updater("Simulating image generation (GPU skipped)...", "INFO")
            mock_path = os.path.join(save_dir, f"simulated_{filename_prefix}.png")
            if "data" not in payload: payload["data"] = {}
            payload["data"]["image_path"] = mock_path

            time.sleep(1)
            status_updater("Simulation complete.", "SUCCESS")
            return {"payload": payload, "output_name": "success"}

        if not prompt:
            return self._create_error_payload(payload, "Prompt is missing. Please check your configuration.")

        if not self.ai_manager:
            return self._create_error_payload(payload, "AIProviderManagerService is not available (Kernel Error).")

        endpoint_id = f"(Local Model) {model_folder_name}"

        generation_params = {
            "negative_prompt": config.get("negative_prompt", "blurry, low quality, distortion"),
            "width": int(config.get("width", 1024)),
            "height": int(config.get("height", 1024)),
            "guidance_scale": float(config.get("guidance_scale", 7.0)), # Slightly lower guidance for faster convergence
            "num_inference_steps": int(config.get("num_inference_steps", 20)),
        }

        try:
            status_updater(f"Generating image with {model_folder_name} (Optimized)...", "INFO")

            response = self.ai_manager.query_ai_by_task(
                "image", prompt, endpoint_id=endpoint_id, **generation_params
            )

            if "error" in response:
                return self._create_error_payload(payload, f"AI Error: {response['error']}")

            temp_image_path = response.get("data")

            if not temp_image_path or not os.path.exists(temp_image_path):
                if isinstance(temp_image_path, dict) and "image_path" in temp_image_path:
                    temp_image_path = temp_image_path["image_path"]
                else:
                    return self._create_error_payload(payload, "AI Service did not return a valid file path.")

            sanitized_prefix = sanitize_filename(filename_prefix)
            if not sanitized_prefix: sanitized_prefix = "sdxl_image"

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            final_filename = f"{sanitized_prefix}_{timestamp}.png"
            final_output_path = os.path.join(save_dir, final_filename)

            shutil.move(temp_image_path, final_output_path)

            self.logger(f"Image saved to: {final_output_path}", "INFO")
            status_updater("Image generated successfully!", "SUCCESS")

            if "data" not in payload: payload["data"] = {}
            payload["data"]["image_path"] = final_output_path

            return {"payload": payload, "output_name": "success"}

        except Exception as e:
            return self._create_error_payload(payload, f"Generation failed: {str(e)}")

    def get_data_preview(self, config: dict):
        steps = config.get("num_inference_steps", 20)
        res = f"{config.get('width', 1024)}x{config.get('height', 1024)}"
        model = config.get("model_folder", "Base XL")

        return [
            {
                "status": "ready",
                "message": f"Config: {model} | {res} | {steps} steps (Turbo Mode)",
                "details": {"resolution": res, "steps": steps}
            }
        ]
