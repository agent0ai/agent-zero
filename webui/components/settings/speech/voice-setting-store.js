import { createStore } from "/js/AlpineStore.js";

/**
 * Voice selector store for managing TTS voice selection
 * @typedef {Object} VoiceSettingStore
 * @property {Array<SpeechSynthesisVoice>} voices - All available browser voices
 * @property {Array<{code: string, name: string, count: number}>} languages - Unique languages with voice counts
 * @property {string} selectedLanguage - Currently selected language code (e.g., "en-US")
 * @property {string} selectedVoice - Currently selected voice name
 * @property {Array<SpeechSynthesisVoice>} filteredVoices - Voices filtered by selected language
 * @property {boolean} isLoading - Whether voices are still loading from browser API
 * @property {boolean} hasError - Whether an error occurred during initialization
 * @property {Function} init - Initialize the store, load voices, restore saved preference
 * @property {Function} loadVoices - Load available voices from browser SpeechSynthesis API
 * @property {Function} getLanguageName - Parse language code to human-readable name
 * @property {Function} onSelectLanguage - Handle language selection change
 * @property {Function} filterVoicesByLanguage - Filter voices by currently selected language
 * @property {Function} onSelectVoice - Handle voice selection change, save to localStorage
 * @property {Function} getSelectedVoice - Get the SpeechSynthesisVoice object for selected voice
 */

const model = {
  voices: [],
  languages: [],
  selectedLanguage: "",
  selectedVoice: "",
  filteredVoices: [],
  isLoading: true,
  hasError: false,

  async init() {
    this.isLoading = true;
    this.hasError = false;
    console.log("[Voice Selector] Initializing...");

    // Load selected voice from localStorage (like microphone does)
    let saved = null;
    try {
      // Try new key first
      saved = localStorage.getItem('voiceSelectedVoice');

      // Migrate from old key if present
      if (!saved) {
        const oldSaved = localStorage.getItem('ttsSelectedVoice');
        if (oldSaved) {
          localStorage.setItem('voiceSelectedVoice', oldSaved);
          localStorage.removeItem('ttsSelectedVoice');
          saved = oldSaved;
          console.log('[Voice Selector] Migrated from old localStorage key (ttsSelectedVoice → voiceSelectedVoice)');
        }
      }
    } catch (error) {
      console.error('[Voice Selector] localStorage unavailable:', error);
      // Continue without saved preference
    }

    // Migration: If no localStorage value, try to migrate from settings
    if (!saved) {
      try {
        const response = await fetchApi("/settings_get", { method: "POST" });
        const data = await response.json();
        const speechSection = data.settings.sections.find(s => s.title === "Speech");
        if (speechSection) {
          const voiceField = speechSection.fields.find(f => f.id === "tts_browser_voice");
          if (voiceField && voiceField.value) {
            saved = voiceField.value;
            try {
              localStorage.setItem('voiceSelectedVoice', saved);
              console.log(`[Voice Selector] Migrated voice from settings to localStorage: "${saved}"`);
            } catch (storageError) {
              console.error('[Voice Selector] Failed to save migrated voice to localStorage:', storageError);
              // Use the value but don't persist it
            }
          }
        }
      } catch (error) {
        console.error("[Voice Selector] Failed to migrate voice from settings:", error);

        // Notify user (non-blocking)
        if (window.toastFetchError) {
          window.toastFetchError('Could not load voice preferences. Using defaults.', error);
        }
      }
    }

    if (saved) {
      this.selectedVoice = saved;
      console.log(`[Voice Selector] Loaded from localStorage: "${this.selectedVoice}"`);
    }

    // Load available voices
    await this.loadVoices();
    console.log(`[Voice Selector] Found ${this.voices.length} voices in ${this.languages.length} languages`);

    // If we have a saved voice, try to select it and its language
    if (this.selectedVoice) {
      const voice = this.voices.find(v => v.name === this.selectedVoice);
      if (voice) {
        this.selectedLanguage = voice.lang;
        this.filterVoicesByLanguage();
        console.log(`[Voice Selector] Restored saved voice: ${this.selectedVoice} (${voice.lang})`);
      } else {
        console.warn(`[Voice Selector] Saved voice "${this.selectedVoice}" not found in available voices`);
      }
    }

    // If no language selected yet, select the first one
    if (!this.selectedLanguage && this.languages.length > 0) {
      this.selectedLanguage = this.languages[0].code;
      this.filterVoicesByLanguage();
      console.log(`[Voice Selector] No saved voice, defaulting to ${this.selectedLanguage}`);
    }

    this.isLoading = false;
    console.log("[Voice Selector] Initialization complete");
  },

  async loadVoices() {
    // Get voices from browser
    let voices = window.speechSynthesis.getVoices();

    // If voices not loaded yet, wait for them
    if (voices.length === 0) {
      await new Promise(resolve => {
        window.speechSynthesis.onvoiceschanged = () => {
          resolve();
        };
        // Fallback timeout
        setTimeout(resolve, 1000);
      });
      voices = window.speechSynthesis.getVoices();
    }

    this.voices = voices;

    // Extract unique languages, sorted by commonality
    const languageMap = new Map();
    voices.forEach(voice => {
      const langCode = voice.lang;
      const langName = this.getLanguageName(langCode);

      if (!languageMap.has(langCode)) {
        languageMap.set(langCode, {
          code: langCode,
          name: langName,
          count: 0
        });
      }
      languageMap.get(langCode).count++;
    });

    // Sort by: 1) common languages first, 2) voice count, 3) name
    const commonLangs = ['en', 'fr', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'zh', 'ko'];
    this.languages = Array.from(languageMap.values()).sort((a, b) => {
      // Check if either is a common language (by prefix)
      const aCommon = commonLangs.findIndex(c => a.code.startsWith(c));
      const bCommon = commonLangs.findIndex(c => b.code.startsWith(c));

      if (aCommon !== -1 && bCommon !== -1) {
        return aCommon - bCommon; // Both common, sort by priority
      }
      if (aCommon !== -1) return -1; // a is common, b is not
      if (bCommon !== -1) return 1;  // b is common, a is not

      // Neither common, sort by voice count then name
      if (b.count !== a.count) return b.count - a.count;
      return a.name.localeCompare(b.name);
    });
  },

  getLanguageName(langCode) {
    // Parse language code (e.g., "en-US" -> "English (United States)")
    const parts = langCode.split('-');
    const langPart = parts[0];
    const regionPart = parts[1];

    const langNames = {
      'en': 'English',
      'fr': 'French',
      'es': 'Spanish',
      'de': 'German',
      'it': 'Italian',
      'pt': 'Portuguese',
      'ru': 'Russian',
      'ja': 'Japanese',
      'zh': 'Chinese',
      'ko': 'Korean',
      'ar': 'Arabic',
      'hi': 'Hindi',
      'nl': 'Dutch',
      'sv': 'Swedish',
      'da': 'Danish',
      'no': 'Norwegian',
      'fi': 'Finnish',
      'pl': 'Polish',
      'tr': 'Turkish',
      'cs': 'Czech',
      'el': 'Greek',
      'he': 'Hebrew',
      'th': 'Thai',
      'vi': 'Vietnamese',
      'id': 'Indonesian',
      'ms': 'Malay',
      'ro': 'Romanian',
      'hu': 'Hungarian',
      'uk': 'Ukrainian',
      'ca': 'Catalan',
      'sk': 'Slovak',
      'hr': 'Croatian',
      'bg': 'Bulgarian',
      'sr': 'Serbian',
    };

    const regionNames = {
      'US': 'United States',
      'GB': 'United Kingdom',
      'CA': 'Canada',
      'AU': 'Australia',
      'FR': 'France',
      'DE': 'Germany',
      'IT': 'Italy',
      'ES': 'Spain',
      'MX': 'Mexico',
      'BR': 'Brazil',
      'PT': 'Portugal',
      'RU': 'Russia',
      'JP': 'Japan',
      'CN': 'China',
      'KR': 'Korea',
      'IN': 'India',
      'AR': 'Argentina',
      'CL': 'Chile',
      'CO': 'Colombia',
    };

    let name = langNames[langPart] || langCode;
    if (regionPart) {
      name += ` (${regionNames[regionPart] || regionPart})`;
    }

    return name;
  },

  onSelectLanguage() {
    this.filterVoicesByLanguage();

    // Auto-select first voice in the new language
    if (this.filteredVoices.length > 0) {
      this.selectedVoice = this.filteredVoices[0].name;
      this.onSelectVoice();
    }
  },

  filterVoicesByLanguage() {
    if (!this.selectedLanguage) {
      this.filteredVoices = [];
      return;
    }

    this.filteredVoices = this.voices.filter(v =>
      v.lang === this.selectedLanguage
    ).sort((a, b) => a.name.localeCompare(b.name));
  },

  async onSelectVoice() {
    // Save to localStorage (like microphone does)
    try {
      localStorage.setItem('voiceSelectedVoice', this.selectedVoice);
      console.log(`[Voice Selector] Saved voice to localStorage: ${this.selectedVoice}`);
    } catch (error) {
      console.error('[Voice Selector] Failed to save voice preference:', error);
      // Optionally notify user
      if (window.toastFetchError) {
        window.toastFetchError('Could not save voice preference (storage unavailable)', error);
      }
    }
  },

  getSelectedVoice() {
    // Guard against uninitialized state
    if (!this.voices || this.voices.length === 0) {
      console.warn('[Voice Selector] Voices not loaded yet, using browser default');
      return null;
    }

    const voice = this.voices.find(v => v.name === this.selectedVoice);

    if (!voice && this.selectedVoice) {
      console.warn(`[Voice Selector] Saved voice "${this.selectedVoice}" not found, using browser default`);
    }

    return voice || null;
  }
};

const store = createStore("voiceSetting", model);

export { store };
