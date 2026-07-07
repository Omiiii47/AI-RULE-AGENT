# AI Agent for Business Rule Management

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (get one at https://aistudio.google.com/apikey)
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Try it
Open the frontend (usually http://localhost:3000) and type:

> Increase personal loan minimum salary to 40000

Check `backend/business_rules.json` afterward — the value should be updated.
