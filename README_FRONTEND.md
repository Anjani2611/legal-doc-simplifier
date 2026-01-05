Legal Document Simplifier – Frontend

Simple, responsive frontend for the Legal Document Simplifier API.



Overview

This frontend is a single-page app (SPA) built with:



HTML – Structure



CSS – Layout and styling



Vanilla JS – API calls and UI logic



It talks directly to the FastAPI backend at:



text

http://localhost:8000/simplify/text

Directory Layout

From project root:



text

legal-doc-simplifier/

├── frontend/

│   ├── index.html      # Main UI

│   ├── styles.css      # Styles

│   └── app.js          # Frontend logic + API calls

├── src/

│   ├── main.py         # FastAPI app (serves /simplify/text and /app)

│   └── ...

└── docs/

&nbsp;   └── API.md          # API documentation

Features

Paste or type legal text



Click Simplify to hit /simplify/text



See:



Document summary



Clause-by-clause breakdown



Risk badges (low / medium / high, color-coded)



Extracted entities (parties, amounts, deadlines)



Clause-level and document-level warnings



Setup

1\. Backend

From project root:



bash

cd legal-doc-simplifier

source venv/Scripts/activate    # Windows Git Bash

\# or: source venv/bin/activate  # Linux/macOS



uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

2\. Frontend

Once backend is running:



text

http://localhost:8000/app

Open in browser.



Usage

Open http://localhost:8000/app



Paste legal text in the textarea (or click Load Example)



Click Simplify



Inspect:



Summary block at top



Clause cards with:



Original text



Simplified text



Risk badge



Entities (e.g., buyer, seller, amounts, deadlines)



Warnings badges



Use Clear to reset the form.



API Integration

Frontend sends:



text

POST /simplify/text

Content-Type: application/json

Body:



json

{

&nbsp; "text": "<legal text>",

&nbsp; "target\_level": "simple",

&nbsp; "language": "en"

}

Response is rendered directly into the UI.



Customization

Change Example Text

Edit in frontend/app.js:



javascript

const EXAMPLE\_TEXT = `...your example here...`;

Change Colors

Edit CSS variables in frontend/styles.css:



css

:root {

&nbsp;   --primary: #2563eb;

&nbsp;   --success: #10b981;

&nbsp;   --warning: #f59e0b;

&nbsp;   --danger: #ef4444;

}

Troubleshooting

Frontend 404:



Check frontend/ exists and app.mount("/app", StaticFiles(...)) is present in src/main.py.



CORS errors in browser console:



Ensure CORSMiddleware is configured in src/main.py.



No output / blank area:



Check browser console for errors (F12 → Console).



Check backend logs for exceptions.



Deployment (Production)

CORS Configuration

Update src/main.py to restrict origins:



python

app.add\_middleware(

&nbsp;   CORSMiddleware,

&nbsp;   allow\_origins=\["https://yourdomain.com"],  # Restrict to your domain

&nbsp;   allow\_credentials=True,

&nbsp;   allow\_methods=\["\*"],

&nbsp;   allow\_headers=\["\*"],

)

Static File Optimization

Minify CSS and JS files



Enable gzip compression via reverse proxy (Nginx, Caddy)



Add cache headers for static assets



Docker Deployment

Add to Dockerfile:



text

COPY frontend/ /app/frontend/

Related Docs

API docs (Markdown): docs/API.md



Swagger UI: http://localhost:8000/docs



ReDoc: http://localhost:8000/redoc



Tech Stack

Frontend: HTML5 + CSS3 + Vanilla JavaScript



Backend: FastAPI (Python 3.11+)



ML: HuggingFace Transformers (google/flan-t5-large)



Validation: Pydantic schemas



License

MIT





