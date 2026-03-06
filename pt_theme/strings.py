"""
strings.py — All user-facing strings for Personal Tutor
No string literals should be hard-coded in UI files.
"""


class Strings:
    # ── App ───────────────────────────────────────────────────────────────────
    APP_TITLE         = "Personal Tutor"
    APP_VERSION       = "v1.0.0"

    # ── Sidebar Navigation ────────────────────────────────────────────────────
    NAV_EXTRACTED     = "EXTRACTED"
    NAV_SUMMARIZE     = "SUMMARIZE"
    NAV_AUDIO         = "AUDIO"
    NAV_ASK           = "ASK QUESTIONS"

    # ── Upload Panel ──────────────────────────────────────────────────────────
    UPLOAD_TITLE      = "UPLOAD"
    UPLOAD_BTN        = "+ UPLOAD"
    UPLOAD_SUBMIT     = "SUBMIT"
    UPLOAD_FILES_BTN  = "FILES"

    LINK_PLACEHOLDER  = "Paste link here..."
    ADD_LINK_TIP      = "Add another link"
    ADD_LINK_SYMBOL   = "+"

    # ── Content Area Placeholders ─────────────────────────────────────────────
    CONTENT_EMPTY     = "Upload a file or paste a link to get started."
    EXTRACTED_EMPTY   = "No text extracted yet. Upload a document first."
    SUMMARIZE_EMPTY   = "No summary available. Run Summarize after extracting."
    AUDIO_EMPTY       = "No audio generated yet."
    ASK_EMPTY         = "Ask a question about your uploaded content."
    ASK_PLACEHOLDER   = "Type your question here..."
    ASK_SEND          = "Send"

    # ── Tooltips ──────────────────────────────────────────────────────────────
    TIP_UPLOAD        = "Upload files or paste links"
    TIP_EXTRACTED     = "View extracted text"
    TIP_SUMMARIZE     = "Summarize the content"
    TIP_AUDIO         = "Convert content to audio"
    TIP_ASK           = "Ask questions about content"
    TIP_ADD_LINK      = "Add a new link"
    TIP_REMOVE_LINK   = "Remove this link"
    TIP_BROWSE_FILES  = "Browse for files"

    # ── Dialogs & Messages ────────────────────────────────────────────────────
    MSG_NO_INPUT      = "Please add at least one link or file."
    MSG_SUBMIT_OK     = "Content submitted successfully!"
    MSG_LOADING       = "Processing..."
    MSG_OCR_RUNNING   = "Extracting text with OCR..."
    MSG_OCR_DONE      = "Text extraction complete."
    MSG_OCR_FAIL      = "OCR failed. Please check the file and try again."
    MSG_SUMMARIZING   = "Summarizing content..."
    MSG_AUDIO_GEN     = "Generating audio..."
    MSG_UNSUPPORTED   = "Unsupported file type."

    # ── File Filters ──────────────────────────────────────────────────────────
    FILE_FILTER_ALL   = "Supported Files (*.pdf *.png *.jpg *.jpeg *.bmp *.tiff)"
    FILE_FILTER_PDF   = "PDF Files (*.pdf)"
    FILE_FILTER_IMAGE = "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
