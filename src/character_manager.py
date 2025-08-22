import json
import os

class CharacterManager:
    def __init__(self, base_dir="."):
        self.aliases_file = os.path.join(base_dir, "character_aliases.json")
        self.voices_file = os.path.join(base_dir, "character_voices.json")
        self.character_aliases = {}  # { "canonical_name": ["alias1", "alias2"] }
        self.character_voices = {}   # { "canonical_name": "voice_id" }
        self._load_mappings()

    def _load_mappings(self):
        if os.path.exists(self.aliases_file):
            with open(self.aliases_file, 'r', encoding='utf-8') as f:
                self.character_aliases = json.load(f)
        if os.path.exists(self.voices_file):
            with open(self.voices_file, 'r', encoding='utf-8') as f:
                self.character_voices = json.load(f)

    def _save_mappings(self):
        with open(self.aliases_file, 'w', encoding='utf-8') as f:
            json.dump(self.character_aliases, f, ensure_ascii=False, indent=4)
        with open(self.voices_file, 'w', encoding='utf-8') as f:
            json.dump(self.character_voices, f, ensure_ascii=False, indent=4)

    def get_canonical_name(self, name):
        """Given a name (could be alias), return its canonical name."""
        for canonical, aliases in self.character_aliases.items():
            if name == canonical or name in aliases:
                return canonical
        return None

    def add_alias(self, canonical_name, alias):
        """Add an alias to a canonical character name."""
        if canonical_name not in self.character_aliases:
            self.character_aliases[canonical_name] = []
        if alias not in self.character_aliases[canonical_name]:
            self.character_aliases[canonical_name].append(alias)
        self._save_mappings()

    def get_voice_id(self, canonical_name):
        """Get the voice ID for a canonical character name."""
        return self.character_voices.get(canonical_name)

    def set_voice_id(self, canonical_name, voice_id):
        """Set the voice ID for a canonical character name."""
        self.character_voices[canonical_name] = voice_id
        self._save_mappings()

    def get_all_characters(self):
        """Get a list of all canonical character names."""
        return list(self.character_aliases.keys())

    def get_all_voice_mappings(self):
        """Get the full character-to-voice mapping."""
        return self.character_voices.copy()

    def get_all_alias_mappings(self):
        """Get the full character-to-alias mapping."""
        return self.character_aliases.copy()

if __name__ == "__main__":
    # Example Usage:
    manager = CharacterManager()

    print("Initial aliases:", manager.get_all_alias_mappings())
    print("Initial voices:", manager.get_all_voice_mappings())

    manager.add_alias("哈利波特", "救世主")
    manager.add_alias("哈利波特", "大难不死的男孩")
    manager.set_voice_id("哈利波特", "male_young_voice_001")

    manager.add_alias("赫敏", "万事通小姐")
    manager.set_voice_id("赫敏", "female_young_voice_002")

    print("\nAfter adding characters:")
    print("Aliases:", manager.get_all_alias_mappings())
    print("Voices:", manager.get_all_voice_mappings())

    print("\nGetting canonical name for '救世主':", manager.get_canonical_name("救世主"))
    print("Getting voice ID for '哈利波特':", manager.get_voice_id("哈利波特"))

    # Simulate loading in another session
    print("\nSimulating new session load:")
    new_manager = CharacterManager()
    print("New session aliases:", new_manager.get_all_alias_mappings())
    print("New session voices:", new_manager.get_all_voice_mappings())
