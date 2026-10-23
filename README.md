# StudyPilot AI — Free Demo

A small student study companion web app with a minimal cream + forest-green UI. It includes email/password registration, a simple dashboard, PDF uploads and text extraction, study tasks, a practice quiz, notes preview, and a browser-based simulated assistant.

## Important demo disclosure
This is a **demo web app**. Assistant replies use simple rules and extractive snippets; no paid LLM/API is required. `/alexa-demo` is a simulated Alexa-style web experience, **not a real Alexa+ skill or an official Amazon integration**. The included `mcp_server.py` exposes three StudyPilot tools over **MCP Streamable HTTP** at `http://127.0.0.1:8001/mcp`. This is a local self-hosted MCP server; it is not a direct connection to Alexa+ hardware or Amazon's private preview environment.

## Run on Windows (PowerShell)
Open this folder in VS Code, then in the terminal run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`. The Alexa-style simulated page is at `http://127.0.0.1:5000/alexa-demo`.

### Run the MCP Streamable HTTP server (second terminal)
Keep the Flask app running in Terminal 1. Open a second VS Code terminal in this same folder and run:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-mcp.txt
python mcp_server.py
```

The MCP endpoint is `http://127.0.0.1:8001/mcp`. Keep this terminal open while testing. If PowerShell activation is blocked, use `.\.venv\Scripts\python.exe -m pip install -r requirements-mcp.txt` and `.\.venv\Scripts\python.exe mcp_server.py`.

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and then `.\.venv\Scripts\python.exe app.py`.

## Included features
- Register / log in / log out (passwords hashed)
- PDF upload with text extraction for selectable-text PDFs (15 MB limit)
- Basic extractive notes preview
- Add and mark study tasks complete
- Rule-based practice quiz with saved scores
- Text chat and optional browser speech-to-text on the simulated assistant page
- SQLite database created locally on first run

## Known limitations
- Scanned/image-only PDFs need OCR, which is not included.
- The free assistant is rule-based and does not replace an LLM.
- Google sign-in, email reset, and a direct real Alexa+ hardware/skill integration are not implemented. The MCP server is configured for local Streamable HTTP; verify it starts successfully in your environment before claiming it is tested.
- Do not upload confidential documents to a public demo.
- This is a prototype; review and test before public deployment.

## Submission checklist
1. Test registration, login, PDF upload, task creation/completion, quiz and chat locally.
2. Add a demo video showing the actual running app. Clearly say the Alexa-style experience is simulated.
3. Publish the source repository with this README and license.
4. Verify the current hackathon rules and submission deadline before submitting. Never claim real Alexa+ integration unless you implement and test it.
