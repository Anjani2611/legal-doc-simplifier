Legal Document Simplifier API

Overview

The Legal Document Simplifier API transforms complex legal text into plain English with clause-level analysis, entity extraction, and risk assessment.



Clause extraction and classification



Entity extraction (parties, amounts, deadlines)



Risk assessment per clause (low/medium/high)



Input/output validation and guardrails



Base URL

text

http://localhost:8000

Authentication

No authentication required (development mode).



Endpoints

1\. Simplify Text

URL



text

POST /simplify/text

Description



Simplifies legal text with clause extraction, entity recognition, and risk scoring.



Request Body



json

{

&nbsp; "text": "Payment clause: The buyer shall pay the seller $1000 USD within 30 days of delivery.",

&nbsp; "target\_level": "simple",

&nbsp; "language": "en"

}

Fields



Field	Type	Required	Description

text	string	Yes	Legal text to simplify (1–50,000 characters)

target\_level	string	No	Simplification level (default: simple)

language	string	No	Language code (default: en)

Successful Response (200)



json

{

&nbsp; "summary": "The buyer must pay the seller $1000 USD no later than 30 days of delivery.",

&nbsp; "clauses": \[

&nbsp;   {

&nbsp;     "id": "clause\_1",

&nbsp;     "type": "payment\_obligation",

&nbsp;     "original\_text": "Payment clause: The buyer shall pay the seller $1000 USD within 30 days of delivery.",

&nbsp;     "simplified\_text": "The buyer must pay the seller $1000 USD no later than 30 days of delivery.",

&nbsp;     "risk\_level": "high",

&nbsp;     "key\_entities": {

&nbsp;       "party\_1": "buyer",

&nbsp;       "party\_2": "seller",

&nbsp;       "amount": "$1000",

&nbsp;       "deadline": "30 days",

&nbsp;       "conditions": false,

&nbsp;       "numerics": \["1000", "30"]

&nbsp;     },

&nbsp;     "warnings": \["numerics\_present", "time\_sensitive"]

&nbsp;   }

&nbsp; ],

&nbsp; "warnings": \[]

}

Response Fields



Field	Type	Description

summary	string	Overall plain-English summary

clauses	array	List of analyzed clauses

clauses\[].id	string	Clause identifier (e.g. clause\_1)

clauses\[].type	string	Clause type (payment\_obligation, liability, …)

clauses\[].original\_text	string	Original clause text

clauses\[].simplified\_text	string	Simplified plain-English clause text

clauses\[].risk\_level	string	low, medium, or high

clauses\[].key\_entities	object	Extracted entities (parties, amounts, deadlines)

clauses\[].warnings	array	Clause-specific warnings

warnings	array	Document-level warnings

Error Responses



400 Bad Request – Invalid input (e.g. empty text)



500 Internal Server Error – Pipeline/ML failure



Example Error



json

{

&nbsp; "detail": "Input text must be a non-empty string"

}

2\. Health Check

URL



text

GET /health

Description



Check API health and basic metadata.



Response



json

{

&nbsp; "status": "healthy",

&nbsp; "service": "legal-doc-simplifier",

&nbsp; "version": "1.0.0"

}

Clause Types

Type	Description

payment\_obligation	Payment terms and obligations

liability	Liability and indemnification clauses

termination	Termination and cancellation terms

confidentiality	Confidentiality / NDA clauses

warranty	Warranties and representations

condition	Conditional clauses (if, unless, …)

definition	Definitions and terminology

general\_obligation	Generic obligations (shall, must)

general	Fallback when no specific type detected

Risk Levels

Risk assessment is heuristic-based (keyword + type + entities).



Level	Description

low	Informational / definitions / administrative

medium	Obligations, time-sensitive, or conditional clauses

high	Liability, penalties, termination, indemnification

Example Requests

Example 1 – Payment Clause

bash

curl -X POST http://localhost:8000/simplify/text \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{

&nbsp;   "text": "Payment clause: The buyer shall pay the seller $1000 USD within 30 days of delivery.",

&nbsp;   "target\_level": "simple",

&nbsp;   "language": "en"

&nbsp; }'

Example 2 – Liability Clause

bash

curl -X POST http://localhost:8000/simplify/text \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{

&nbsp;   "text": "The contractor shall indemnify and hold harmless the client from any liability or damages arising from breach of this agreement.",

&nbsp;   "target\_level": "simple",

&nbsp;   "language": "en"

&nbsp; }'

Interactive Documentation

Swagger UI: http://localhost:8000/docs



ReDoc: http://localhost:8000/redoc



Frontend UI: http://localhost:8000/app

