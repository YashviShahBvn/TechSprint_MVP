# MVP Invoice Parsing

Lightweight Flask MVP that uses Google's Gemini (via `google-genai`) to extract structured invoice data from uploaded images or PDFs.

**Features:**
- Upload invoice image or PDF and receive structured JSON following a fixed invoice schema.
- Supports `png`, `jpg`, `jpeg`, `webp`, and `pdf` uploads (max 10MB).
- Simple web UI at the root route and a JSON API endpoint for programmatic use.

**Requirements:**
- Python 3.10+
- See `requirements.txt` for exact package versions.

Setup
-----

- Copy environment example and set your Gemini API key:

	```bash
	copy .env.example .env
	# then edit .env and set GEMINI_API_KEY
	```

- Install dependencies (recommended inside a virtualenv):

	```bash
	python -m venv .venv
	.venv\Scripts\activate   # Windows
	pip install -r requirements.txt
	```

Running (development)
---------------------

- Start the app locally:

	```bash
	python app.py
	```

	The server runs on `http://0.0.0.0:8080` by default. The root (`/`) serves the simple UI and the API is at `/api/parse-invoice`.

Example curl
------------

```bash
curl -X POST http://localhost:8080/api/parse-invoice \
	-F "file=@/path/to/invoice.jpg"
```

Notes
-----
- Uploaded files are temporarily saved to the `uploads/` folder and removed after processing.
- Allowed file types: `png`, `jpg`, `jpeg`, `webp`, `pdf`. Max file size is 10MB (enforced by Flask config).
- Ensure `GEMINI_API_KEY` is set in your `.env` (see `.env.example`).

Troubleshooting
---------------
- If the app exits with "GEMINI_API_KEY not found", confirm `.env` exists and contains a valid key.
- If you receive JSON parse errors, check the Gemini response and ensure the model returns strict JSON (the app attempts to strip common markdown fences).
