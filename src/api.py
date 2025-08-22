from flask import Flask, request, jsonify, send_from_directory
import os
import threading
from dotenv import load_dotenv

from .character_manager import CharacterManager
from .llm_service import LLMService
from .volcano_engine_service import VolcanoEngineService
from .audiobook_generator import AudiobookGenerator

app = Flask(__name__)
load_dotenv() # Load environment variables

# Global dictionary to store generation status and results
# In a real-world scenario, this would be a database or a more robust task queue
GENERATION_STATUS = {}

# Load Volcano Engine voice metadata from JSON file
VOICE_METADATA_FILE = os.path.join(os.path.dirname(__file__), 'voice_metadata.json')
with open(VOICE_METADATA_FILE, 'r', encoding='utf-8') as f:
    VOLCANO_VOICE_METADATA = json.load(f)

def generate_audiobook_task(task_id, text_content, project_id):
    GENERATION_STATUS[task_id] = {"status": "processing", "progress": "Initializing..."}
    try:
        # Initialize services (credentials loaded from .env)
        manager = CharacterManager(base_dir=os.path.join(os.getcwd(), "output_audio"))
        if not manager.get_voice_id("旁白"):
            manager.set_voice_id("旁白", "zh_male_jieshuoxiaoming_moon_bigtts")

        llm_endpoint = os.getenv("LLM_ENDPOINT")
        llm_api_key = os.getenv("LLM_API_KEY")
        if not llm_endpoint or not llm_api_key:
            raise ValueError("LLM_ENDPOINT or LLM_API_KEY not set in .env file or environment.")
        llm_service = LLMService(llm_endpoint, manager)

        tts_app_id = os.getenv("TTS_APP_ID")
        tts_access_key = os.getenv("TTS_ACCESS_KEY")
        tts_resource_id = os.getenv("TTS_RESOURCE_ID")
        if not tts_app_id or not tts_access_key or not tts_resource_id:
            raise ValueError("TTS_APP_ID, TTS_ACCESS_KEY, or TTS_RESOURCE_ID not set in .env file or environment.")
        volcano_service = VolcanoEngineService(tts_app_id, tts_access_key, tts_resource_id)

        generator = AudiobookGenerator(
            llm_service=llm_service,
            volcano_service=volcano_service,
            character_manager=manager,
            output_base_dir=os.path.join(os.getcwd(), "output_audio")
        )

        # Create a temporary file for the text content
        temp_text_file_path = os.path.join(os.getcwd(), "temp_input", f"{task_id}.txt")
        os.makedirs(os.path.dirname(temp_text_file_path), exist_ok=True)
        with open(temp_text_file_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        final_audiobook_path = generator.generate_audiobook(temp_text_file_path, project_id)

        os.remove(temp_text_file_path) # Clean up temporary file
        os.rmdir(os.path.dirname(temp_text_file_path)) # Clean up temporary directory

        if final_audiobook_path:
            GENERATION_STATUS[task_id] = {"status": "completed", "file_path": final_audiobook_path, "download_url": f"/download/{os.path.basename(final_audiobook_path)}"}
        else:
            GENERATION_STATUS[task_id] = {"status": "failed", "message": "Audiobook generation failed."}

    except Exception as e:
        GENERATION_STATUS[task_id] = {"status": "failed", "message": str(e)}
    print(f"Task {task_id} finished with status: {GENERATION_STATUS[task_id]['status']}")

@app.route("/generate_audiobook", methods=["POST"])
def generate_audiobook_api():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    text_content = data.get("text")
    project_id = data.get("project_id", f"api_audiobook_{uuid.uuid4().hex[:8]}")

    if not text_content:
        return jsonify({"error": "'text' field is required"}), 400

    task_id = str(uuid.uuid4())
    GENERATION_STATUS[task_id] = {"status": "queued", "progress": "Waiting to start..."}

    # Run the generation in a separate thread
    thread = threading.Thread(target=generate_audiobook_task, args=(task_id, text_content, project_id))
    thread.start()

    return jsonify({"task_id": task_id, "status_url": f"/status/{task_id}"}), 202

@app.route("/status/<task_id>")
def get_status(task_id):
    status = GENERATION_STATUS.get(task_id)
    if not status:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(status)

@app.route("/download/<filename>")
def download_file(filename):
    output_dir = os.path.join(os.getcwd(), "output_audio")
    return send_from_directory(output_dir, filename, as_attachment=True)

if __name__ == "__main__":
    # Ensure output_audio directory exists for CharacterManager and AudiobookGenerator
    os.makedirs(os.path.join(os.getcwd(), "output_audio"), exist_ok=True)
    app.run(debug=True, port=5000)
