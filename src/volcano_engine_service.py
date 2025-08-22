import os
import requests
import base64
import uuid
import json
from dotenv import load_dotenv

class VolcanoEngineService:
    def __init__(self, app_id: str, access_key: str, resource_id: str = "volc.service_type.10029", api_endpoint: str = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"):
        self.app_id = app_id
        self.access_key = access_key # Renamed from access_token to access_key as per new doc
        self.resource_id = resource_id
        self.api_endpoint = api_endpoint
        self._initialize_volcano_sdk()

    def _initialize_volcano_sdk(self):
        """
        Volcano Engine SDK initialization is handled by setting up app_id, access_key, resource_id, and endpoint.
        No explicit SDK client object is needed for direct HTTP calls.
        """
        print(f"Initializing Volcano Engine TTS service with AppID: {self.app_id}, ResourceID: {self.resource_id}, Endpoint: {self.api_endpoint}")

    def synthesize_speech(self, text: str, voice_type: str, output_dir: str = "./audio_output") -> str:
        """
        Synthesizes speech from text using the specified voice_type via Volcano Engine HTTP API.
        Handles streaming response.
        Returns the path to the generated audio file.
        """
        os.makedirs(output_dir, exist_ok=True)
        audio_filename = os.path.join(output_dir, f"audio_{uuid.uuid4()}.mp3") # Use UUID for unique filenames

        headers = {
            "X-Api-App-Id": self.app_id,
            "X-Api-Access-Key": self.access_key,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()), # Unique request ID for header
            "Content-Type": "application/json"
        }

        payload = {
            "user": {
                "uid": str(uuid.uuid4()) # Unique user ID
            },
            "req_params": {
                "text": text,
                "speaker": voice_type, # Renamed from voice_type to speaker
                "audio_params": {
                    "format": "mp3", # Request MP3 format
                    "sample_rate": 24000, # Default sample rate
                    "bit_rate": 160 # Default bitrate for MP3
                },
                "namespace": "BidirectionalTTS" # As per new doc example
            }
        }

        try:
            print(f"\n--- Sending Streaming TTS Request ---")
            print(f"URL: {self.api_endpoint}")
            print(f"Headers: {headers}")
            print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            print(f"---------------------------")
            
            # Use stream=True for streaming response
            with requests.post(self.api_endpoint, headers=headers, json=payload, stream=True) as response:
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

                full_audio_data = b""
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        # Attempt to decode chunk as JSON first
                        try:
                            json_data = json.loads(chunk.decode('utf-8'))
                            # If it's a JSON object with 'data' field, it's base64 audio
                            if json_data.get("code") == 0 and json_data.get("data"):
                                full_audio_data += base64.b64decode(json_data["data"])
                            elif json_data.get("code") == 20000000: # End of stream success code
                                print("Received end of stream success code.")
                                break # Exit loop if stream ends successfully
                            else:
                                print(f"Received non-audio JSON chunk: {json_data}")
                        except json.JSONDecodeError:
                            # If not JSON, assume it's raw audio data (though doc implies base64 in JSON)
                            # This part might need refinement based on actual API behavior
                            print("Warning: Received non-JSON chunk. Assuming it's raw audio data.")
                            full_audio_data += chunk
                        except Exception as e:
                            print(f"Error processing chunk: {e}")
                            # Decide whether to continue or break

                if full_audio_data:
                    with open(audio_filename, "wb") as f:
                        f.write(full_audio_data)
                    print(f"Volcano Engine synthesis successful: Text='{text[:30]}...', Voice='{voice_type}', Saved to='{audio_filename}'")
                    return audio_filename
                else:
                    print(f"Volcano Engine synthesis failed: No audio data received for text: {text[:50]}...")
                    return None

        except requests.exceptions.RequestException as e:
            print(f"Network or HTTP error during Volcano Engine synthesis: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"Raw API response on error: {response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding Volcano Engine response JSON: {e}")
            raw_response_content = response.text if 'response' in locals() else "(No raw response available)"
            print(f"Raw response: {raw_response_content[:500]}...")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during Volcano Engine synthesis: {e}")
            return None

# Example Usage (for testing VolcanoEngineService in isolation)
if __name__ == "__main__":
    # You need to replace these with your actual AppID and Access Key
    load_dotenv() # Load .env for testing
    TEST_APP_ID = os.getenv("TTS_APP_ID")
    TEST_ACCESS_KEY = os.getenv("TTS_ACCESS_KEY")
    TEST_RESOURCE_ID = os.getenv("TTS_RESOURCE_ID")

    if not TEST_APP_ID or not TEST_ACCESS_KEY or not TEST_RESOURCE_ID:
        print("Please set TTS_APP_ID, TTS_ACCESS_KEY, and TTS_RESOURCE_ID in your .env file to run this example.")
    else:
        volcano_service = VolcanoEngineService(app_id=TEST_APP_ID, access_key=TEST_ACCESS_KEY, resource_id=TEST_RESOURCE_ID)

        # Using a voice_type from the Volcano Engine list (e.g., from '通用场景' -> '甜美桃子')
        test_voice_type = "zh_female_tianmeitaozi_mars_bigtts"
        test_text = "你好，我是火山引擎的语音合成服务。这是一个美好的旅程。"

        output_file = volcano_service.synthesize_speech(test_text, test_voice_type)
        if output_file:
            print(f"Generated audio at: {output_file}")
        else:
            print("Failed to generate audio.")
