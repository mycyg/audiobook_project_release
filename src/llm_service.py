import os
import json
import requests
from dotenv import load_dotenv

from .character_manager import CharacterManager

# Load environment variables
load_dotenv()

# Load Volcano Engine voice metadata from JSON file
VOICE_METADATA_FILE = os.path.join(os.path.dirname(__file__), 'voice_metadata.json')
with open(VOICE_METADATA_FILE, 'r', encoding='utf-8') as f:
    VOLCANO_VOICE_METADATA = json.load(f)


class LLMService:
    def __init__(self, llm_api_endpoint: str, character_manager: CharacterManager):
        self.llm_api_endpoint = llm_api_endpoint
        self.character_manager = character_manager

    def _call_llm(self, prompt: str) -> str:
        """
        Calls the Volcano LLM API with the given prompt and returns the raw JSON string response.
        """
        LLM_API_KEY = os.getenv("LLM_API_KEY")
        if not LLM_API_KEY:
            raise ValueError("LLM_API_KEY environment variable not set.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "doubao-seed-1-6-250615") # Default to original if not set
        payload = {
            "model": LLM_MODEL_NAME, # Now configurable
            "messages": [
                {
                    "content": [
                        {
                            "text": prompt,
                            "type": "text"
                        }
                    ],
                    "role": "user"
                }
            ]
        }

        try:
            response = requests.post(self.llm_api_endpoint, headers=headers, json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx) 
            
            llm_response = response.json()
            print(f"Raw LLM response: {json.dumps(llm_response, indent=2, ensure_ascii=False)}")

            extracted_text = ""
            if llm_response and llm_response.get("choices") and llm_response["choices"][0].get("message"):
                content = llm_response["choices"][0]["message"].get("content")
                if isinstance(content, list):
                    extracted_text = "".join([c.get("text", "") for c in content if c.get("type") == "text"])
                elif isinstance(content, str):
                    extracted_text = content
            
            if not extracted_text:
                print("LLM response content is empty or malformed.")
                # Return a default JSON structure if LLM response is empty/malformed
                return json.dumps([{"speaker_name": "旁白", "speaker_voice_id": "zh_male_jieshuoxiaoming_moon_bigtts", "text": "LLM返回内容为空或格式不正确。"}], ensure_ascii=False)

            return extracted_text # Return the extracted JSON string

        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM API: {e}")
            return json.dumps([{"speaker_name": "旁白", "speaker_voice_id": "zh_male_jieshuoxiaoming_moon_bigtts", "text": f"LLM API调用失败: {e}"}], ensure_ascii=False)
        except json.JSONDecodeError as e:
            print(f"Error decoding LLM API response JSON: {e}")
            raw_response_content = response.text if 'response' in locals() else "(No raw response available)"
            print(f"Raw LLM response: {raw_response_content[:500]}...")
            return json.dumps([{"speaker_name": "旁白", "speaker_voice_id": "zh_male_jieshuoxiaoming_moon_bigtts", "text": f"LLM返回JSON解析失败: {e}"}], ensure_ascii=False)
        except Exception as e:
            print(f"An unexpected error occurred during LLM API call: {e}")
            return json.dumps([{"speaker_name": "旁白", "speaker_voice_id": "zh_male_jieshuoxiaoming_moon_bigtts", "text": f"LLM处理异常: {e}"}], ensure_ascii=False)

    def process_text_chunk(self, text_chunk: str) -> list:
        """
        Processes a text chunk using the LLM to identify characters, assign voices,
        and annotate the text.
        Returns a list of dictionaries: [{'speaker_name': '...', 'speaker_voice_id': '...', 'text': '...'}]
        """
        # Ensure narrator voice is set up initially
        if not self.character_manager.get_voice_id("旁白"):
            self.character_manager.set_voice_id("旁白", "zh_male_jieshuoxiaoming_moon_bigtts")
            print("Initialized '旁白' voice to 'zh_male_jieshuoxiaoming_moon_bigtts'")

        # Step 1: Construct the prompt for the LLM
        # This prompt needs to be carefully designed to guide the LLM.
        # It should include:
        # - The text chunk to process.
        # - The current global character-alias mapping (for context).
        # - The current global character-voice mapping (for consistency).
        # - The available voice metadata (for new voice assignments).
        # - Clear instructions on the desired output format (JSON).

        current_aliases = self.character_manager.get_all_alias_mappings()
        current_voices = self.character_manager.get_all_voice_mappings()
        available_voices_meta = VOLCANO_VOICE_METADATA

        prompt = f"""
        你是一个专业的有声书制作助手。你的任务是分析小说文本，识别说话者，并为他们分配合适的音色。
        请严格按照以下步骤和输出格式进行：

        1.  **分析文本：** 仔细阅读以下文本块。
        2.  **识别角色和别名：** 识别文本中出现的所有角色及其别名。如果发现新的别名，请将其关联到已知的规范角色名。
        3.  **音色分配：**
            *   对于已知的角色（在“当前角色音色映射”中），请严格使用其已分配的音色ID。
            *   对于新识别的角色（不在“当前角色音色映射”中），请根据角色在文本中的描述（例如，性别、年龄、性格），从“可用音色元数据”中**严格选择一个存在的音色ID**。确保音色选择与角色特征匹配。
            *   旁白请使用已分配的旁白音色。
        4.  **输出格式：** 严格以 JSON 数组的形式输出，每个元素是一个字典，包含 'speaker_name', 'speaker_voice_id', 'text'。
            *   'speaker_name' 必须是规范的角色名（如果存在别名，请转换为规范名）。
            *   'speaker_voice_id' 必须是分配给该角色的音色ID，**且必须是“可用音色元数据”中存在的有效ID**。
            *   'text' 是对应的文本内容。

        --- 文本块 ---
        {text_chunk}

        --- 当前角色别名映射 ---
        {json.dumps(current_aliases, ensure_ascii=False, indent=2)}

        --- 当前角色音色映射 ---
        {json.dumps(current_voices, ensure_ascii=False, indent=2)}

        --- 可用音色元数据 ---
        {json.dumps(available_voices_meta, ensure_ascii=False, indent=2)}

        请直接输出 JSON 数组，不要包含任何其他文字或解释。
        """

        try:
            llm_json_str = self._call_llm(prompt) # _call_llm now returns the JSON string
            
            # Parse the LLM's JSON response
            try:
                annotated_text_data = json.loads(llm_json_str)
            except json.JSONDecodeError:
                print("Warning: LLM response is not valid JSON. Attempting to parse as single segment.")
                annotated_text_data = [{'speaker_name': '旁白', 'speaker_voice_id': 'zh_male_jieshuoxiaoming_moon_bigtts', 'text': llm_json_str}]

            # Validate and sanitize speaker_voice_id
            for segment in annotated_text_data:
                suggested_voice_id = segment.get('speaker_voice_id')
                if suggested_voice_id not in VOLCANO_VOICE_METADATA:
                    print(f"Warning: LLM suggested invalid voice ID '{suggested_voice_id}'. Falling back to narrator voice.")
                    segment['speaker_voice_id'] = 'zh_male_jieshuoxiaoming_moon_bigtts' # Fallback to a known good narrator voice

            # Update character manager based on LLM's implicit decisions (if any, for new characters)
            # In a real implementation, the LLM would explicitly tell us about new aliases/voice assignments.
            # For this placeholder, we rely on the _call_llm dummy logic.
            
            # Validate and return
            if isinstance(annotated_text_data, list) and all(isinstance(item, dict) and 
                                                            'speaker_name' in item and 
                                                            'speaker_voice_id' in item and 
                                                            'text' in item 
                                                            for item in annotated_text_data):
                return annotated_text_data
            else:
                print("Warning: LLM response format invalid after validation.")
                return []
        except Exception as e:
            print(f"An unexpected error occurred during LLM processing: {e}")
            return []
