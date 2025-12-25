Legal Document Simplifier

A FastAPI-based backend service that simplifies legal documents using AI and detects potential risks. Transforms complex legal jargon into plain language for better public understanding.



🎯 Features

✅ Document Upload - Support for TXT, PDF, and DOCX formats

✅ Text Simplification - AI-powered legal text simplification using Hugging Face

✅ Risk Detection - Identify potential legal risks and issues

✅ Database Storage - PostgreSQL for persistent document management

✅ REST API - Complete API with Swagger UI documentation

✅ Error Handling - Comprehensive error handling and logging



🛠️ Tech Stack

Backend: FastAPI (Python 3.11)



Database: PostgreSQL + SQLAlchemy ORM



AI/ML: Transformers (Hugging Face BART model)



File Processing: PyPDF2, python-docx



API Docs: Swagger UI (auto-generated)



📁 Project Structure

text

legal-doc-simplifier/

├── src/

│   ├── main.py                      # FastAPI application entry point

│   ├── settings.py                  # Configuration and environment variables

│   ├── database.py                  # SQLAlchemy setup and session management

│   ├── models/

│   │   └── document.py              # Database models (Document, RiskFlag)

│   ├── schemas/

│   │   └── document.py              # Pydantic validation schemas

│   ├── routes/

│   │   ├── documents.py             # Document CRUD endpoints

│   │   ├── simplification.py        # Text simplification endpoints

│   │   └── analysis.py              # Risk analysis endpoints

│   ├── pipelines/

│   │   ├── simplification.py        # Hugging Face simplification pipeline

│   │   └── risk\_detection.py        # Pattern-based risk detection

│   └── utils/

│       └── document\_extractor.py    # TXT/PDF/DOCX text extraction

├── uploads/                         # Uploaded documents directory

├── venv/                            # Python virtual environment

├── test\_api.py                      # Integration test suite

├── requirements.txt                 # Python dependencies

├── .env                             # Environment variables (git ignored)

├── .gitignore                       # Git ignore rules

└── README.md                        # This file

🚀 Installation

Prerequisites

Python 3.11+



PostgreSQL 15+



Git



Step-by-Step Setup

1\. Clone Repository

bash

git clone https://github.com/yourusername/legal-doc-simplifier.git

cd legal-doc-simplifier

2\. Create Virtual Environment

bash

\# Windows

python -m venv venv

venv\\Scripts\\activate



\# Linux/Mac

python3 -m venv venv

source venv/bin/activate

You should see (venv) in your terminal prompt.



3\. Install Dependencies

bash

pip install -r requirements.txt

This installs:



FastAPI, Uvicorn (backend framework)



SQLAlchemy, psycopg2 (database)



Transformers, torch (AI models)



PyPDF2, python-docx (file parsing)



4\. Configure Environment

Create a .env file in the project root:



bash

notepad .env

Add these variables:



text

\# Database

DATABASE\_URL=postgresql://legal\_user:password@localhost:5432/legal\_docs\_dev



\# API

API\_TITLE=Legal Document Simplifier

API\_VERSION=0.1.0

DEBUG=True

Save and close.



5\. Set Up PostgreSQL Database

Open PostgreSQL command line:



bash

psql -U postgres

Run these commands:



sql

CREATE DATABASE legal\_docs\_dev;

CREATE USER legal\_user WITH PASSWORD 'password';

ALTER ROLE legal\_user SET client\_encoding TO 'utf8';

ALTER ROLE legal\_user SET default\_transaction\_isolation TO 'read committed';

ALTER ROLE legal\_user SET default\_transaction\_deferrable TO on;

ALTER ROLE legal\_user SET default\_transaction\_read\_only TO off;

GRANT ALL PRIVILEGES ON DATABASE legal\_docs\_dev TO legal\_user;

\\q

6\. Create Database Tables

The tables are auto-created on first run. You can also manually create them:



bash

python -c "

from src.database import engine, Base

from src.models.document import Document, RiskFlag

Base.metadata.create\_all(bind=engine)

print('✓ Tables created successfully')

"

7\. Start the Server

bash

uvicorn src.main:app --reload

You should see:



text

INFO:     Uvicorn running on http://127.0.0.1:8000

INFO:     Application startup complete

Server is now running! 🎉



📚 API Documentation

Interactive API Docs

Open your browser and go to:



text

http://127.0.0.1:8000/docs

This shows all endpoints, request/response schemas, and lets you test them.



Alternative documentation: http://127.0.0.1:8000/redoc



Endpoints Overview

1\. Health Check

text

GET /health

Returns server and database status.



Response:



json

{

&nbsp; "status": "ok",

&nbsp; "database": "ok",

&nbsp; "timestamp": "2025-12-25T16:00:00"

}

2\. Upload Document

text

POST /documents/upload

Upload a legal document (TXT, PDF, or DOCX).



Request:



bash

curl -X POST http://127.0.0.1:8000/documents/upload \\

&nbsp; -F "file=@contract.pdf" \\

&nbsp; -F "document\_type=contract"

Response:



json

{

&nbsp; "id": 1,

&nbsp; "filename": "contract.pdf",

&nbsp; "file\_size": 12345,

&nbsp; "processing\_status": "pending",

&nbsp; "uploaded\_at": "2025-12-25T16:00:00"

}

3\. List Documents

text

GET /documents/

List all uploaded documents.



Query Parameters:



skip (int): Offset for pagination (default: 0)



limit (int): Results per page (default: 10)



Response:



json

{

&nbsp; "total": 5,

&nbsp; "documents": \[

&nbsp;   {

&nbsp;     "id": 1,

&nbsp;     "filename": "contract.pdf",

&nbsp;     "file\_size": 12345,

&nbsp;     "document\_type": "contract",

&nbsp;     "processing\_status": "completed"

&nbsp;   }

&nbsp; ]

}

4\. Get Document Details

text

GET /documents/{id}

Get details of a specific document.



Example: GET /documents/1



Response:



json

{

&nbsp; "id": 1,

&nbsp; "filename": "contract.pdf",

&nbsp; "original\_text": "...",

&nbsp; "simplified\_text": "...",

&nbsp; "is\_processed": true,

&nbsp; "uploaded\_at": "2025-12-25T16:00:00"

}

5\. Simplify Text

text

POST /simplify/text

Simplify raw legal text without uploading.



Request:



bash

curl -X POST http://127.0.0.1:8000/simplify/text \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{

&nbsp;   "text": "Notwithstanding any provision herein to the contrary, the indemnifying party shall defend and indemnify the indemnified parties from any and all claims..."

&nbsp; }'

Response:



json

{

&nbsp; "original": "Notwithstanding...",

&nbsp; "simplified": "The party must defend and protect...",

&nbsp; "reduction": 35.5,

&nbsp; "status": "completed"

}

6\. Simplify Document

text

POST /simplify/document/{id}

Simplify a stored document.



Example: POST /simplify/document/1



Response:



json

{

&nbsp; "id": 1,

&nbsp; "filename": "contract.pdf",

&nbsp; "original\_length": 5000,

&nbsp; "simplified\_length": 3250,

&nbsp; "status": "completed",

&nbsp; "reduction": 35.0

}

7\. Analyze Document (Risk Detection)

text

POST /analyze/document/{id}

Detect potential risks in a legal document.



Example: POST /analyze/document/1



Response:



json

{

&nbsp; "document\_id": 1,

&nbsp; "filename": "contract.pdf",

&nbsp; "text\_length": 5000,

&nbsp; "word\_count": 850,

&nbsp; "risks\_detected": 3,

&nbsp; "avg\_risk\_score": 65.0,

&nbsp; "risks": \[

&nbsp;   {

&nbsp;     "risk\_level": "HIGH",

&nbsp;     "risk\_score": 75,

&nbsp;     "description": "Unlimited liability clause detected",

&nbsp;     "recommendation": "⚠️ Negotiate modifications with counterparty"

&nbsp;   },

&nbsp;   {

&nbsp;     "risk\_level": "MEDIUM",

&nbsp;     "risk\_score": 50,

&nbsp;     "description": "Termination without cause clause",

&nbsp;     "recommendation": "Consider requesting clarification"

&nbsp;   }

&nbsp; ]

}

8\. Get Document Risks

text

GET /analyze/document/{id}/risks

Retrieve previously detected risks.



Query Parameters:



risk\_level (str): Filter by level (LOW, MEDIUM, HIGH, CRITICAL)



Example: GET /analyze/document/1/risks?risk\_level=HIGH



Response:



json

{

&nbsp; "document\_id": 1,

&nbsp; "total\_risks": 2,

&nbsp; "risks": \[

&nbsp;   {

&nbsp;     "id": 1,

&nbsp;     "risk\_level": "HIGH",

&nbsp;     "risk\_score": 75,

&nbsp;     "description": "Unlimited liability clause"

&nbsp;   }

&nbsp; ]

}

9\. Delete Document

text

DELETE /documents/{id}

Delete a document and its file.



Example: DELETE /documents/1



Response:



json

{

&nbsp; "status": "deleted",

&nbsp; "id": 1

}

💻 Usage Examples

Example 1: Upload and Analyze a Contract

bash

\# 1. Upload

curl -X POST http://127.0.0.1:8000/documents/upload \\

&nbsp; -F "file=@my\_contract.pdf" \\

&nbsp; -F "document\_type=contract"

\# Returns: {"id": 1, ...}



\# 2. Analyze for risks

curl -X POST http://127.0.0.1:8000/analyze/document/1



\# 3. View results in Swagger UI

\# Go to http://127.0.0.1:8000/docs

Example 2: Simplify Raw Text

bash

curl -X POST http://127.0.0.1:8000/simplify/text \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{

&nbsp;   "text": "The Party of the first part (hereinafter \\"Provider\\") agrees to indemnify and hold harmless the Party of the second part (hereinafter \\"Client\\") from any and all claims, damages, and liabilities arising out of the performance of services."

&nbsp; }'

Output:



json

{

&nbsp; "original": "The Party of the first part...",

&nbsp; "simplified": "The Provider must protect the Client from any claims or damages related to the services.",

&nbsp; "reduction": 42.5

}

Example 3: Full Document Processing Pipeline

bash

\# 1. Check API health

curl http://127.0.0.1:8000/health



\# 2. Upload document

RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/documents/upload \\

&nbsp; -F "file=@legal\_doc.docx")

DOC\_ID=$(echo $RESPONSE | jq '.id')



\# 3. Simplify the document

curl -X POST http://127.0.0.1:8000/simplify/document/$DOC\_ID



\# 4. Analyze for risks

curl -X POST http://127.0.0.1:8000/analyze/document/$DOC\_ID



\# 5. Get full document details

curl http://127.0.0.1:8000/documents/$DOC\_ID

🧪 Testing

Run Integration Tests

bash

python test\_api.py

Expected Output:



text

============================================================

Legal Document Simplifier - API Test Suite

============================================================



🏥 Testing /health...

✓ Health check passed



📄 Testing GET /documents...

✓ Found 1 documents



📤 Testing POST /documents/upload...

✓ Uploaded document ID: 2



✨ Testing POST /simplify/text...

✓ Original: 245 chars

✓ Simplified: 156 chars

✓ Reduction: 36.3%



⚠️  Testing POST /analyze/document/2...

✓ Risks detected: 1

✓ Average risk score: 50.0



📝 Testing POST /simplify/document/2...

✓ Status: completed

✓ Original: 245 chars

✓ Simplified: 156 chars



============================================================

✅ All tests passed!

============================================================

Test Individual Endpoints

bash

\# Health check

curl http://127.0.0.1:8000/health



\# List documents

curl http://127.0.0.1:8000/documents/



\# Get specific document

curl http://127.0.0.1:8000/documents/1

📊 Database Schema

Documents Table

sql

CREATE TABLE documents (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   filename VARCHAR(255) NOT NULL,

&nbsp;   file\_path VARCHAR(512) NOT NULL,

&nbsp;   file\_size INTEGER NOT NULL,

&nbsp;   original\_text TEXT NOT NULL,

&nbsp;   simplified\_text TEXT,

&nbsp;   document\_type VARCHAR(50),

&nbsp;   language VARCHAR(10) DEFAULT 'en',

&nbsp;   is\_processed BOOLEAN DEFAULT FALSE,

&nbsp;   processing\_status VARCHAR(50) DEFAULT 'pending',

&nbsp;   uploaded\_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

&nbsp;   processed\_at TIMESTAMP WITH TIME ZONE,

&nbsp;   created\_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

&nbsp;   updated\_at TIMESTAMP WITH TIME ZONE

);

Risk Flags Table

sql

CREATE TABLE risk\_flags (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   document\_id INTEGER NOT NULL REFERENCES documents(id),

&nbsp;   risk\_level VARCHAR(20) NOT NULL,

&nbsp;   risk\_score INTEGER NOT NULL CHECK (risk\_score >= 0 AND risk\_score <= 100),

&nbsp;   clause\_text TEXT NOT NULL,

&nbsp;   description TEXT NOT NULL,

&nbsp;   recommendation TEXT,

&nbsp;   created\_at TIMESTAMP WITH TIME ZONE DEFAULT now()

);

⚙️ Configuration

Environment Variables

Create a .env file:



text

\# Server

DEBUG=True

API\_TITLE=Legal Document Simplifier

API\_VERSION=0.1.0



\# Database

DATABASE\_URL=postgresql://legal\_user:password@localhost:5432/legal\_docs\_dev



\# File Upload

UPLOAD\_DIR=uploads

MAX\_FILE\_SIZE=10485760

ALLOWED\_EXTENSIONS=txt,pdf,docx



\# AI Model

MODEL\_NAME=pszemraj/long-t5-tglobal-base-sci-simplify

MODEL\_DEVICE=cpu

Settings

Edit src/settings.py to modify defaults:



python

class Settings(BaseSettings):

&nbsp;   app\_name: str = "Legal Document Simplifier"

&nbsp;   app\_version: str = "0.1.0"

&nbsp;   database\_url: str

&nbsp;   

&nbsp;   # File settings

&nbsp;   UPLOAD\_DIR: str = "uploads"

&nbsp;   MAX\_FILE\_SIZE: int = 10 \* 1024 \* 1024  # 10 MB

&nbsp;   ALLOWED\_EXTENSIONS: set = {"txt", "pdf", "docx"}

🔒 Security Recommendations

For Development ✓ (Current)

All CORS origins allowed (\*)



Debug mode enabled



No authentication required



Files stored locally



For Production ⚠️ (Recommended)

Enable HTTPS



bash

\# Use SSL certificate

uvicorn src.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem

Add Authentication



python

from fastapi.security import HTTPBearer

security = HTTPBearer()



@app.get("/protected")

async def protected(credentials: HTTPAuthCredentialDetails = Depends(security)):

&nbsp;   return {"message": "authenticated"}

Restrict CORS



python

from fastapi.middleware.cors import CORSMiddleware



app.add\_middleware(

&nbsp;   CORSMiddleware,

&nbsp;   allow\_origins=\["https://yourdomain.com"],

&nbsp;   allow\_methods=\["GET", "POST"],

&nbsp;   allow\_headers=\["\*"],

)

Add Rate Limiting



bash

pip install slowapi

Store Files in Cloud



bash

\# Use AWS S3, Google Cloud Storage, or Azure Blob Storage

pip install boto3  # for AWS S3

Enable Logging



python

import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(\_\_name\_\_)

🚨 Troubleshooting

Database Connection Error

bash

\# Verify PostgreSQL is running

psql -U postgres -d legal\_docs\_dev



\# Reset user password

ALTER USER legal\_user WITH PASSWORD 'new\_password';



\# Check connection string in .env

\# Format: postgresql://username:password@localhost:5432/dbname

Model Download Timeout

bash

\# Pre-download model before running server

python -c "

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model\_name = 'pszemraj/long-t5-tglobal-base-sci-simplify'

AutoTokenizer.from\_pretrained(model\_name)

AutoModelForSeq2SeqLM.from\_pretrained(model\_name)

print('✓ Model downloaded successfully')

"

Port 8000 Already in Use

bash

\# Use different port

uvicorn src.main:app --port 8001



\# Or kill process using port 8000 (Windows)

netstat -ano | findstr :8000

taskkill /PID <PID> /F



\# Linux/Mac

lsof -i :8000

kill -9 <PID>

File Upload Fails

bash

\# Check uploads directory exists

mkdir -p uploads



\# Check file permissions

chmod 755 uploads



\# Check file size (max 10 MB by default)

\# Update MAX\_FILE\_SIZE in .env if needed

Virtual Environment Issues

bash

\# Recreate virtual environment

rm -rf venv

python -m venv venv

source venv/Scripts/activate  # or venv\\Scripts\\activate on Windows

pip install -r requirements.txt

📈 Performance Tips

Use GPU for Simplification - Install CUDA/PyTorch GPU version



Enable Database Indexing - Add indexes on frequently queried columns



Cache Models - Load simplification model once at startup



Async Processing - Use Celery for background simplification tasks



CDN for Static Files - Use S3/CloudFront for file delivery



🤝 Contributing

Fork the repository



Create a feature branch: git checkout -b feature/your-feature



Make changes and commit: git commit -am "Add feature"



Push to branch: git push origin feature/your-feature



Submit a pull request



📝 Testing Checklist

Before deploying to production, verify:



&nbsp;Database connection works



&nbsp;File upload accepts TXT/PDF/DOCX



&nbsp;Text extraction works for all formats



&nbsp;Simplification produces shorter text



&nbsp;Risk detection finds at least one risk



&nbsp;API returns valid JSON responses



&nbsp;Error handling works for invalid inputs



&nbsp;Documents persist after server restart



&nbsp;All tests in test\_api.py pass



&nbsp;API documentation loads in Swagger UI



📚 Learning Resources

FastAPI Documentation



SQLAlchemy ORM Guide



PostgreSQL Documentation



Hugging Face Transformers



Pydantic Validation



🎓 Project Timeline

Day	Task	Status

1-2	Setup \& Git	✅ Done

3-4	FastAPI Basics	✅ Done

5-6	PostgreSQL + ORM	✅ Done

7	Text Simplification	✅ Done

8	Document Upload	✅ Done

9	Risk Detection	✅ Done

10	Documentation	✅ Done

📄 License

MIT License - See LICENSE file for details



👤 Author

Anjani - Backend Development



📞 Support

📧 Email: anjanikty980@gmail.com



🐙 GitHub: https://github.com/anjani2611/legal-doc-simplifier



📋 Issues: https://github.com/anjani2611/legal-doc-simplifier/issues



Status: ✅ Production Ready (Days 1-10 Complete)



Total Development Time: ~20 hours

Lines of Code: ~2,500

API Endpoints: 15

Database Tables: 2

Test Coverage: 6 test cases

