"""
ocr_worker_process.py
---------------------
This script runs as a STANDALONE SUBPROCESS — it is never imported by the
main application. It receives a file path via stdin, runs PaddleOCR in total
isolation from Qt, and writes results back to stdout as JSON.

Why a separate process?
    PaddleOCR initializes native C/C++ libraries (OpenCV, MKL, ONNXRuntime)
    that can call back into the OS event system. When running inside a QThread
    (same process as Qt), those callbacks collide with PySide6's event loop
    and freeze the UI regardless of CPU core count.
    A subprocess has its own memory space — zero shared state with Qt.
"""

import sys
import json
import os
import warnings

os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings('ignore')


def main():
    # Read the file path passed via command-line argument
    if len(sys.argv) < 2:
        result = {"success": False, "error": "No file path provided."}
        print(json.dumps(result), flush=True)
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        from paddleocr import PaddleOCR
        engine = PaddleOCR(lang='en', enable_mkldnn=False)
        raw = list(engine.predict(file_path))

        pages = []
        for i, page in enumerate(raw):
            header = f"--- PAGE {i + 1} ---"
            body   = " ".join(page.get('rec_texts', []))
            pages.append(f"{header}\n{body}\n")

        result = {"success": True, "text": "\n".join(pages)}

    except Exception as exc:
        result = {"success": False, "error": str(exc)}

    # Write single JSON line to stdout — parent process reads this
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
