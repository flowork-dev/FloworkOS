########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_architect_service\council_orchestrator.py total lines 179 
########################################################################

import json
import logging
import concurrent.futures
import time
import uuid
from typing import List, Dict, Any

from flowork_kernel.services.dataset_manager_service.dataset_manager_service import DatasetManagerService
from flowork_kernel.services.ai_provider_manager_service.ai_provider_manager_service import AIProviderManagerService

logger = logging.getLogger(__name__)

class CouncilOrchestrator:
    def __init__(self, kernel):
        self.kernel = kernel

        self.provider_manager = self.kernel.get_service("ai_provider_manager_service")
        if not self.provider_manager:
            self.provider_manager = AIProviderManagerService(self.kernel, "ai_provider_manager_service")

    def _query_member(self, member_id: str, topic: str) -> Dict:
        """
        Menanyakan pendapat ke satu member dewan.
        """
        try:
            system_prompt = (
                "You are a member of the Neural Council. "
                "You are participating in a debate/analysis session. "
                "Provide a concise, technical, and factual perspective on the user's topic. "
                "Do not be polite or use filler words. Get straight to the point. "
                "Focus on risks, opportunities, and technical implementation."
            )

            response_text = self.provider_manager.generate_text_sync(
                model_id=member_id,
                prompt=topic,
                system_prompt=system_prompt,
                temperature=0.7
            )

            if not response_text:
                return {
                    "member_id": member_id,
                    "status": "error",
                    "response": "[No response generated]"
                }

            return {
                "member_id": member_id,
                "status": "success",
                "response": response_text
            }
        except Exception as e:
            logger.error(f"Council Member {member_id} failed: {e}")
            return {
                "member_id": member_id,
                "status": "error",
                "response": f"[Error: {str(e)}]"
            }

    def stream_deliberation(self, judge_id: str, members: List[str], topic: str):
        """
        Generator utama yang menjalankan sidang dewan.
        Yields: JSON String (chunks) untuk dikirim ke Frontend.
        """

        yield json.dumps({"type": "status", "message": "CONVENING COUNCIL..."}) + "\n"

        evidence_texts = []

        yield json.dumps({"type": "status", "message": f"Consulting {len(members)} members..."}) + "\n"

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_member = {executor.submit(self._query_member, m_id, topic): m_id for m_id in members}

            for future in concurrent.futures.as_completed(future_to_member):
                member_id = future_to_member[future]
                try:
                    data = future.result()

                    log_entry = {
                        "type": "council_log",
                        "speaker": data['member_id'],
                        "message": "Submitted testimony."
                    }
                    yield json.dumps(log_entry) + "\n"

                    evidence_texts.append(f"--- TESTIMONY FROM {member_id} ---\n{data['response']}\n")

                except Exception as exc:
                    logger.error(f"Member {member_id} generated an exception: {exc}")
                    yield json.dumps({"type": "error", "message": f"Member {member_id} crash: {exc}"}) + "\n"

        yield json.dumps({"type": "status", "message": "JUDGE DELIBERATING..."}) + "\n"

        council_dossier = "\n".join(evidence_texts)

        judge_system_prompt = (
            "You are the Presiding Judge of the Neural Council. "
            "A topic has been discussed by the council members. "
            "Your task is to synthesis their views, identify conflicts, and render a Final Verdict.\n\n"
            "Format your response as:\n"
            "1. **Summary of Arguments**: What did the members say?\n"
            "2. **Analysis**: Who is correct? What are the trade-offs?\n"
            "3. **Final Verdict**: The conclusive answer or solution.\n"
        )

        final_prompt = f"TOPIC: {topic}\n\nEVIDENCE FROM COUNCIL:\n{council_dossier}\n\nRender your verdict, Judge."

        full_verdict = "" # Penampung jawaban utuh

        try:
            stream = self.provider_manager.stream_text(
                model_id=judge_id,
                prompt=final_prompt,
                system_prompt=judge_system_prompt,
                temperature=0.5
            )

            for chunk in stream:
                full_verdict += chunk # Kumpulin kata per kata
                yield json.dumps({"type": "content", "chunk": chunk}) + "\n"


            yield json.dumps({"type": "status", "message": "Archiving Verdict to Training Data..."}) + "\n"

            self._auto_save_to_dataset(topic, full_verdict, council_dossier)

            yield json.dumps({"type": "status", "message": "✅ Knowledge Auto-Saved!"}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": f"Judge execution failed: {str(e)}"}) + "\n"

    def _auto_save_to_dataset(self, topic, verdict, evidence):
        """
        Internal helper untuk menyimpan hasil debat ke Dataset Manager secara otomatis.
        """
        try:
            dataset_service = self.kernel.get_service("dataset_manager_service")
            if not dataset_service:
                dataset_service = DatasetManagerService(self.kernel, "dataset_manager_service")

            target_dataset = "Council-Auto-Memory"

            dataset_service.create_dataset(target_dataset)


            training_data = {
                "id": str(uuid.uuid4()),
                "prompt": f"Analisis mendalam mengenai: {topic}",
                "response": verdict,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analisis mendalam mengenai: {topic}\n\nBerikan kesimpulan komprehensif berdasarkan pandangan ahli."
                    },
                    {
                        "role": "assistant",
                        "content": verdict
                    }
                ],
                "meta": {
                    "source": "Neural Council Auto-Save",
                    "timestamp": time.time(),
                    "evidence_summary": evidence[:500] + "..." # Simpan sedikit konteks di meta
                }
            }

            dataset_service.add_data_to_dataset(target_dataset, [training_data])
            logger.info(f"[Council] Verdict saved to dataset '{target_dataset}'")

        except Exception as e:
            logger.error(f"[Council] Auto-save failed: {e}")
