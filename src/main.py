import os
import json
import requests
from dotenv import load_dotenv

from .character_manager import CharacterManager
from .llm_service import LLMService
from .volcano_engine_service import VolcanoEngineService
from .audiobook_generator import AudiobookGenerator

# Load environment variables from .env file
load_dotenv()

# Load Volcano Engine voice metadata from JSON file
VOICE_METADATA_FILE = os.path.join(os.path.dirname(__file__), 'voice_metadata.json')
with open(VOICE_METADATA_FILE, 'r', encoding='utf-8') as f:
    VOLCANO_VOICE_METADATA = json.load(f)

# Main application entry point
if __name__ == "__main__":
    import tkinter as tk # Import Tkinter here to avoid issues if not running GUI
    import sys # Import sys for command-line arguments

    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("\n--- Starting Audiobook Generation API ---")
        # Ensure output_audio directory exists for CharacterManager and AudiobookGenerator
        os.makedirs(os.path.join(os.getcwd(), "output_audio"), exist_ok=True)
        from .api import app as api_app # Import Flask app here
        api_app.run(debug=True, port=5000)
    else:
        print("\n--- Starting Audiobook Generation GUI ---")
        root = tk.Tk()
        app = AudiobookApp(root)
        root.mainloop()

    print("\n--- Audiobook Generation Application Finished ---")

