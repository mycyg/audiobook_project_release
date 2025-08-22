import os
import json
from pydub import AudioSegment
from .llm_service import LLMService
from .volcano_engine_service import VolcanoEngineService
from .character_manager import CharacterManager

class AudiobookGenerator:
    def __init__(self, llm_service: LLMService, volcano_service: VolcanoEngineService, character_manager: CharacterManager, output_base_dir: str = "output_audio"):
        self.llm_service = llm_service
        self.volcano_service = volcano_service
        self.character_manager = character_manager
        self.output_base_dir = output_base_dir
        os.makedirs(self.output_base_dir, exist_ok=True)

    def generate_audiobook(self, text_file_path: str, project_id: str = "default_project") -> str:
        """
        Generates an audiobook from a text file.
        Returns the path to the final merged audiobook file.
        """
        print(f"\n--- Starting audiobook generation for {text_file_path} (Project ID: {project_id}) ---")

        # Ensure narrator voice is set up initially
        if not self.character_manager.get_voice_id("旁白"):
            self.character_manager.set_voice_id("旁白", "narrator_voice_id")
            print("Initialized '旁白' voice to 'narrator_voice_id'")

        # Create a directory for this project's audio chunks
        project_output_dir = os.path.join(self.output_base_dir, f"{project_id}_chunks")
        os.makedirs(project_output_dir, exist_ok=True)

        all_audio_segments = []
        segment_counter = 0

        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            # Simple paragraph splitting. More sophisticated splitting might be needed for complex texts.
            paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]

            for i, paragraph in enumerate(paragraphs):
                print(f"\n--- Processing paragraph {i+1}/{len(paragraphs)} ---")
                # LLM processing
                # The LLM prompt in llm_service.py already includes context (aliases, voices, metadata)
                annotated_segments = self.llm_service.process_text_chunk(paragraph)

                for segment in annotated_segments:
                    speaker_name = segment.get("speaker_name", "旁白")
                    speaker_voice_id = segment.get("speaker_voice_id", "narrator_voice_id")
                    text_to_synthesize = segment.get("text", "")

                    if not text_to_synthesize:
                        print(f"Skipping empty text segment for {speaker_name}.")
                        continue

                    print(f"Synthesizing for {speaker_name} (Voice ID: {speaker_voice_id}): {text_to_synthesize[:50]}...")
                    
                    # Synthesize speech
                    audio_file_path = self.volcano_service.synthesize_speech(
                        text=text_to_synthesize,
                        voice_type=speaker_voice_id,
                        output_dir=project_output_dir # Save individual chunks in project-specific dir
                    )

                    if audio_file_path and os.path.exists(audio_file_path):
                        try:
                            audio_segment = AudioSegment.from_file(audio_file_path)
                            all_audio_segments.append(audio_segment)
                            segment_counter += 1
                        except Exception as e:
                            print(f"Error loading audio segment {audio_file_path}: {e}")
                    else:
                        print(f"Failed to synthesize audio for segment: {text_to_synthesize[:50]}...")

            if not all_audio_segments:
                print("No audio segments were generated. Aborting audiobook creation.")
                return None

            # Merge all audio segments
            print(f"\n--- Merging {segment_counter} audio segments ---")
            merged_audio = AudioSegment.empty()
            for audio_seg in all_audio_segments:
                merged_audio += audio_seg

            final_audiobook_path = os.path.join(self.output_base_dir, f"final_audiobook_{project_id}.mp3")
            merged_audio.export(final_audiobook_path, format="mp3")
            print(f"--- Audiobook generation complete! Saved to: {final_audiobook_path} ---")
            return final_audiobook_path

        except FileNotFoundError:
            print(f"Error: Text file not found at {text_file_path}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during audiobook generation: {e}")
            return None

# Example Usage (for testing AudiobookGenerator in isolation)
if __name__ == "__main__":
    from .llm_service import LLMService
    from .volcano_engine_service import VolcanoEngineService
    from .character_manager import CharacterManager

    # Initialize dependencies
    manager = CharacterManager(base_dir="../output_audio") # Save character data in output_audio
    
    # Set a default voice for narrator if not already set
    if not manager.get_voice_id("旁白"):
        manager.set_voice_id("旁白", "narrator_voice_id")

    # LLM Service (use the actual endpoint from GEMINI.md)
    llm_api_endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    llm_service = LLMService(llm_api_endpoint=llm_api_endpoint, character_manager=manager)

    # Volcano TTS Service (use your actual AppID and Access Token)
    # IMPORTANT: Replace with your actual credentials from GEMINI.md
    TTS_APP_ID = "1438797749" 
    TTS_ACCESS_TOKEN = "JxtO8DlYEbZDUKS4gzvHBei8YqZn_AGx"
    volcano_service = VolcanoEngineService(app_id=TTS_APP_ID, access_token=TTS_ACCESS_TOKEN)

    # Initialize AudiobookGenerator
    generator = AudiobookGenerator(
        llm_service=llm_service,
        volcano_service=volcano_service,
        character_manager=manager,
        output_base_dir="../output_audio"
    )

    # Run the generation
    input_text_file = "../input.txt"
    generated_audiobook_path = generator.generate_audiobook(input_text_file, project_id="my_first_audiobook")

    if generated_audiobook_path:
        print(f"Successfully created audiobook: {generated_audiobook_path}")
    else:
        print("Audiobook generation failed.")
