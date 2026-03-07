Personal Tutor:
    A local desktop application that turns your study materials — PDFs, images, and web links — into interactive lessons. Extract text, generate AI summaries, quiz yourself, and listen to spoken audio lessons, all running on your machine with your own API keys.

Features:
-Text Extraction

    Upload image files or PDFs and extract text using PaddleOCR (runs fully offline)
    Paste URLs to automatically fetch the video title or webpages and real transcript via youtube-transcript-api, then have an AI rewrite it into a clean structured article
    Paste any webpage URL to scrape and summarise its content
    All extracted text is saved to Data/extracted/ as plain .txt files, organised by source type

-AI Summarisation

    Select one or multiple extracted files and generate a combined summary
    Summaries are saved to Data/summaries/<sourcefilename>_summarized.txt
    Supports multiple files in one summary run — output is named after all source stems combined
    Duplicate runs append _2, _3 etc. rather than overwriting

-Ask Questions (Quiz Mode)

    Generate a set of questions from any extracted files using AI in the form of multiple choice or choose the following
    Question sets are saved as Data/questions/questionN.json and persist across sessions
    Load any saved question set and take it as a quiz
    Results are scored and saved to Data/results/
    Toggle between generating new questions and loading saved ones from the sidebar

-Audio Lessons

    Select extracted files and generate a spoken lesson using a two-stage pipeline:

    Script stage — AI rewrites the material as a natural spoken teaching script (warm intro, analogies, rhetorical questions, recap, conclusion)
    Audio stage — Kokoro TTS converts the script to a WAV audio file in sentence-safe chunks


    Built-in audio player with play/pause, seek bar, time display, and volume control
    Saved lessons appear in the panel and reload automatically on next launch
    10 voice options across American and British accents (see Audio Voices)
    Voice preview: short sample audio for each voice is generated once on first launch so you can audition voices before generating a full lesson

-Multi AI support:
    Supports multiple AI
    Such as Anthropic's Claude Google's Gemini, OpenaAI's ChatGpt

-Settings

    Store API keys for Anthropic, OpenAI, and Google Gemini inside the app — no environment variables needed
    Switch between providers and models at any time from the Settings panel
    Keys are saved locally to Data/keys.json as base64 (never sent anywhere except the chosen API)


Requirements:
    RequirementVersionPython3.10 — 3.12
    PySide66.6+
    PaddleOCR2.x / 3.x
    PaddlePaddle3.3.0 (CPU)
    Kokoro latest
    soundfile latest
    youtube-transcript-api latest


Project Structure:

    Personal-Tutor/
    │
    ├── main.py                      # Entry point
    ├── main_window.py               # Main QMainWindow, worker wiring
    ├── app_config.py                # All path and config constants
    │
    ├── core/                        # Business logic (no UI)
    │   ├── app_state.py             # Shared runtime state
    │   ├── audio_generator.py       # Kokoro TTS — text → WAV
    │   ├── key_store.py             # API key storage (base64, local)
    │   ├── lesson_writer.py         # AI teaching script generation
    │   ├── link_extractor.py        # YouTube + web URL → text
    │   ├── ocr_engine.py            # PaddleOCR wrapper
    │   ├── qa_engine.py             # Question answering
    │   ├── question_generator.py    # AI question set generation
    │   ├── summarizer.py            # AI summarisation
    │   └── workers.py               # QThread workers for all background tasks
    │
    ├── ui/                          # PySide6 panels and widgets
    │   ├── ask_panel.py             # Quiz panel (generate + saved questions)
    │   ├── audio_panel.py           # Audio lesson panel + voice selector
    │   ├── link_row.py              # Individual link row widget
    │   ├── panels.py                # ExtractedPanel, SummarizePanel
    │   ├── settings_panel.py        # API key management UI
    │   ├── sidebar.py               # Left navigation sidebar
    │   └── upload_dialog.py         # File upload + link paste dialog
    │
    ├── pt_theme/                    # Design system
    │   ├── colors.py                # All colour tokens
    │   ├── dimensions.py            # Spacing, radius, layout constants
    │   ├── strings.py               # All UI strings in one place
    │   ├── stylesheet.py            # Global Qt stylesheet
    │   └── typography.py            # Font definitions
    │
    ├── icons/                       # SVG icons
    │   ├── icon_loader.py           # Icon loading helper
    │   └── *.svg                    # ask, audio, extracted, summarize, etc.
    │
    ├── assets/
    │   └── voice_samples/           # Auto-generated WAV previews per voice
    │                                # (created on first launch, ~10 files)
    │
    └── Data/                        # All runtime data (gitignored)
        ├── extracted/
        │   ├── fromfile/            # OCR output from uploaded files
        │   └── fromlink/            # Extracted text from URLs
        ├── summaries/               # AI-generated summaries
        ├── questions/               # Saved question sets (JSON)
        ├── results/                 # Quiz attempt results (JSON)
        ├── lessons/                 # AI-generated lesson scripts (TXT)
        ├── audio/                   # Generated audio lessons (WAV)
        ├── temp/                    # Temporary working files
        └── keys.json                # Stored API keys (base64, local only)

How To Use?

    Extracting content

        Click the + upload button in the bottom-right corner
        Either drag and drop image/PDF files into the file area, or paste one or more URLs into the link box
        Click Submit — OCR or link extraction runs in the background
        Extracted text files appear in the Extracted panel

    Summarising

        Switch to the Summarise panel from the sidebar
        Check one or more extracted files in the left pane
        Click Summarise — the AI summary appears on the right and is saved automatically
        Previously saved summaries are listed at the bottom and can be reloaded at any time

    Quizzing yourself

        Switch to the Ask panel
        Select New Questions, check files, and click Ask to generate a question set
        Switch to Saved Questions to see all saved sets and start a quiz
        Answer each question and submit — your score is shown and saved

    Generating an audio lesson

        Switch to the Audio panel
        Choose a voice from the dropdown — click ▶ next to any voice to hear a preview
        Check the files you want the lesson to cover
        Click Generate Lesson

        Stage 1: AI writes a teaching script (shown in the script viewer when ready)
        Stage 2: Kokoro TTS converts the script to audio (progress shown with a spinner)


        When complete the built-in player loads the lesson automatically
        Previously generated lessons are listed below the player and reload on next launch

AI Providers
    All AI features (summarisation, question generation, lesson script writing, link extraction) use whichever provider you configure in Settings.
    The app makes direct HTTPS calls using only Python's built-in urllib — no third-party AI SDK is required.

    ProviderModels available:
        Anthropicclaude-sonnet-4, claude-opus-4, claude-haiku-4-5
        OpenAIgpt-4o, gpt-4o-mini, gpt-4-turbo
        Google Geminigemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash

Audio Voices:
    Powered by Kokoro TTS.
    All voices run entirely offline after the first model download.
    Heart American Female (warm)
    Bella American Female (soft)
    Nicole American Female (clear)
    Sarah American Female (bright)
    Adam American Male (deep)
    Michael American Male (calm)
    Emma British Female
    Isabella British Female
    George British Male
    Lewis British Male

Data & Privacy:
    Developers Note:
    "The system architecture and UI/UX design of this file-sharing application were solely developed by Asbel Jino, culminating in a uniquely vibe-coded digital environment"
    All data stays on your machine. Nothing is stored remotely.
    The only outbound network calls are to the AI provider API you choose, containing only the text you select for processing.
    API keys are stored in Data/keys.json encoded as base64. This is obfuscation, not encryption — do not share this file.
    Add Data/ to your .gitignore to ensure keys and personal study content are never committed.