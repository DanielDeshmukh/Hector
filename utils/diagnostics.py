import os
import requests
import base64
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class HectorDiagnostic:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.nv_api_key = os.getenv("NVIDIA_API_KEY")

        if not self.groq_api_key or not self.nv_api_key:
            raise ValueError(
                "Missing API Keys in .env file. Ensure GROQ_API_KEY and NVIDIA_API_KEY are set."
            )

        self.groq_client = Groq(api_key=self.groq_api_key)
        self.session = requests.Session()
        self.nv_headers = {
            "Authorization": f"Bearer {self.nv_api_key}",
            "Accept": "application/json",
        }

    def test_groq_reasoning(self):
        print("\n[1/3] Testing Groq Reasoning (Llama 3.3 70B)...")
        try:
            chat = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": "Confirm H.E.C.T.O.R. system integrity.",
                    }
                ],
            )
            response = chat.choices[0].message.content.strip()
            print(f"  > [SUCCESS] Groq Response: {response[:60]}...")
            return True
        except Exception as e:
            print(f"  > [FAILED] Groq Error: {e}")
            return False

    def test_nvidia_ocr(self, image_path="paddleocr1.png"):
        print(f"\n[2/3] Testing NVIDIA Nemotron OCR (Target: {image_path})...")
        invoke_url = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1"

        if not os.path.exists(image_path):
            print(
                f"  > [SKIPPED] Local image '{image_path}' not found. Place an image in the directory to test OCR."
            )
            return True  # Skipping doesn't mean failure of the API logic

        try:
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode()

            if len(image_b64) >= 180_000:
                print("  > [FAILED] Image too large for standard API (>180kb).")
                return False

            payload = {
                "input": [
                    {"type": "image_url", "url": f"data:image/png;base64,{image_b64}"}
                ]
            }

            response = self.session.post(
                invoke_url, headers=self.nv_headers, json=payload
            )
            if response.status_code == 200:
                print(
                    f"  > [SUCCESS] OCR Data Received: {str(response.json())[:100]}..."
                )
                return True
            else:
                print(f"  > [FAILED] OCR Error {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"  > [FAILED] OCR Exception: {e}")
            return False

    def test_nvidia_reranker(self):
        print("\n[3/3] Testing NVIDIA Nemotron Reranker...")
        invoke_url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking"

        payload = {
            "model": "nvidia/llama-nemotron-rerank-1b-v2",
            "query": {"text": "What is the punishment for theft in BNS?"},
            "passages": [
                {"text": "Section 303 of BNS covers theft and imprisonment."},
                {
                    "text": "A100 provides up to 2 terabytes per second of memory bandwidth."
                },
                {"text": "The weather in Mumbai is humid today."},
            ],
        }

        try:
            response = self.session.post(
                invoke_url, headers=self.nv_headers, json=payload
            )
            response.raise_for_status()

            data = response.json().get("rankings", [])
            if data:
                top_match = data[0]
                print(
                    f"  > [SUCCESS] Reranker Top Index: {top_match['index']} (Logit: {top_match['logit']})"
                )
                return True
            else:
                print("  > [FAILED] Reranker returned empty results.")
                return False
        except Exception as e:
            print(f"  > [FAILED] Reranker Exception: {e}")
            return False


def run_diagnostics():
    print("=" * 60)
    print("H.E.C.T.O.R. SYSTEM DIAGNOSTICS: FRONTIER STACK")
    print("=" * 60)

    try:
        hector = HectorDiagnostic()

        results = [
            hector.test_groq_reasoning(),
            hector.test_nvidia_ocr(),
            hector.test_nvidia_reranker(),
        ]

        print("\n" + "=" * 60)
        if all(results):
            print("FINAL STATUS: ALL FRONTIER SYSTEMS OPERATIONAL")
        else:
            print("FINAL STATUS: PARTIAL SYSTEM CRITICALITY - CHECK LOGS")
        print("=" * 60)
    except Exception as e:
        print(f"INITIALIZATION FAILED: {e}")


if __name__ == "__main__":
    run_diagnostics()
