import tkinter as tk
from tkinter import filedialog, messagebox
import os
from dotenv import load_dotenv

from .character_manager import CharacterManager
from .llm_service import LLMService
from .volcano_engine_service import VolcanoEngineService
from .audiobook_generator import AudiobookGenerator

class AudiobookApp:
    def __init__(self, master):
        self.master = master
        master.title("Audiobook Generator")

        # Load environment variables from .env file
        load_dotenv()

        # --- API Credentials --- 
        self.credentials_frame = tk.LabelFrame(master, text="API Credentials")
        self.credentials_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(self.credentials_frame, text="LLM Endpoint:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.llm_endpoint_entry = tk.Entry(self.credentials_frame, width=50)
        self.llm_endpoint_entry.grid(row=0, column=1, padx=5, pady=2)
        self.llm_endpoint_entry.insert(0, os.getenv("LLM_ENDPOINT", "https://ark.cn-beijing.volces.com/api/v3/chat/completions"))

        tk.Label(self.credentials_frame, text="LLM API Key:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.llm_api_key_entry = tk.Entry(self.credentials_frame, width=50, show="*")
        self.llm_api_key_entry.grid(row=1, column=1, padx=5, pady=2)
        self.llm_api_key_entry.insert(0, os.getenv("LLM_API_KEY", ""))

        tk.Label(self.credentials_frame, text="TTS App ID:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.tts_app_id_entry = tk.Entry(self.credentials_frame, width=50)
        self.tts_app_id_entry.grid(row=2, column=1, padx=5, pady=2)
        self.tts_app_id_entry.insert(0, os.getenv("TTS_APP_ID", "1438797749"))

        tk.Label(self.credentials_frame, text="TTS Access Key:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.tts_access_key_entry = tk.Entry(self.credentials_frame, width=50, show="*")
        self.tts_access_key_entry.grid(row=3, column=1, padx=5, pady=2)
        self.tts_access_key_entry.insert(0, os.getenv("TTS_ACCESS_KEY", ""))

        tk.Label(self.credentials_frame, text="TTS Resource ID:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.tts_resource_id_entry = tk.Entry(self.credentials_frame, width=50)
        self.tts_resource_id_entry.grid(row=4, column=1, padx=5, pady=2)
        self.tts_resource_id_entry.insert(0, os.getenv("TTS_RESOURCE_ID", "volc.service_type.10029"))

        # --- Input File Selection --- 
        self.input_frame = tk.LabelFrame(master, text="Input Text File")
        self.input_frame.pack(padx=10, pady=10, fill="x")

        self.input_file_path = tk.StringVar()
        tk.Entry(self.input_frame, textvariable=self.input_file_path, width=40, state="readonly").grid(row=0, column=0, padx=5, pady=2)
        tk.Button(self.input_frame, text="Browse", command=self.browse_file).grid(row=0, column=1, padx=5, pady=2)

        # --- Project ID --- 
        self.project_id_frame = tk.LabelFrame(master, text="Project ID")
        self.project_id_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(self.project_id_frame, text="Project ID:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.project_id_entry = tk.Entry(self.project_id_frame, width=40)
        self.project_id_entry.grid(row=0, column=1, padx=5, pady=2)
        self.project_id_entry.insert(0, "my_audiobook_project")

        # --- Generate Button --- 
        self.generate_button = tk.Button(master, text="Generate Audiobook", command=self.generate_audiobook)
        self.generate_button.pack(pady=10)

        # --- Status and Output --- 
        self.status_frame = tk.LabelFrame(master, text="Status and Output")
        self.status_frame.pack(padx=10, pady=10, fill="x")

        self.status_label = tk.Label(self.status_frame, text="Ready.", fg="blue")
        self.status_label.pack(padx=5, pady=5)

        self.output_link_label = tk.Label(self.status_frame, text="", fg="green", cursor="hand2")
        self.output_link_label.pack(padx=5, pady=5)
        self.output_link_label.bind("<Button-1>", self.open_output_folder)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Text File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.input_file_path.set(file_path)

    def generate_audiobook(self):
        llm_endpoint = self.llm_endpoint_entry.get()
        llm_api_key = self.llm_api_key_entry.get()
        tts_app_id = self.tts_app_id_entry.get()
        tts_access_key = self.tts_access_key_entry.get()
        tts_resource_id = self.tts_resource_id_entry.get()
        input_file = self.input_file_path.get()
        project_id = self.project_id_entry.get()

        if not all([llm_endpoint, llm_api_key, tts_app_id, tts_access_key, tts_resource_id, input_file, project_id]):
            messagebox.showerror("Error", "All fields must be filled.")
            return

        self.status_label.config(text="Generating audiobook... Please wait.", fg="orange")
        self.output_link_label.config(text="")
        self.master.update_idletasks()

        try:
            # Initialize services
            character_manager = CharacterManager(base_dir=os.path.join(os.getcwd(), "output_audio"))
            
            # Set a default voice for narrator if not already set
            if not character_manager.get_voice_id("旁白"):
                character_manager.set_voice_id("旁白", "zh_male_jieshuoxiaoming_moon_bigtts")

            llm_service = LLMService(llm_endpoint, character_manager)
            volcano_service = VolcanoEngineService(tts_app_id, tts_access_key, tts_resource_id)

            generator = AudiobookGenerator(
                llm_service=llm_service,
                volcano_service=volcano_service,
                character_manager=character_manager,
                output_base_dir=os.path.join(os.getcwd(), "output_audio")
            )

            final_audiobook_path = generator.generate_audiobook(input_file, project_id)

            if final_audiobook_path:
                self.status_label.config(text="Audiobook generated successfully!", fg="green")
                self.output_link_label.config(text=f"Open Output Folder: {os.path.dirname(final_audiobook_path)}")
                self.generated_folder = os.path.dirname(final_audiobook_path)
            else:
                self.status_label.config(text="Audiobook generation failed. Check console for details.", fg="red")
                self.generated_folder = None

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_label.config(text="Error during generation.", fg="red")
            self.generated_folder = None

    def open_output_folder(self, event):
        if self.generated_folder and os.path.exists(self.generated_folder):
            os.startfile(self.generated_folder)
        else:
            messagebox.showinfo("Info", "No output folder to open or folder does not exist.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudiobookApp(root)
    root.mainloop()
