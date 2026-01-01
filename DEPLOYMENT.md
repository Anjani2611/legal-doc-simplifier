\# Legal Document Simplifier – Deployment Guide



\## 1. Environment Configuration



Set these in your `.env` (do not commit real secrets):



```

DEBUG=False

SECRET\_KEY=change-this-to-a-strong-random-string

DATABASE\_URL=postgresql://user:password@db-host:5432/legal\_simplifier



CELERY\_BROKER\_URL=redis://redis:6379/0

CELERY\_RESULT\_BACKEND=redis://redis:6379/0

```



\- Same `.env` file FastAPI app aur Celery worker dono ke liye use karo.



\## 2. Security, CORS, and Rate Limiting



\- SlowAPI rate limiting enabled rakho (global + per-endpoint limits).

\- `main.py` me CORS ko sirf trusted frontends tak limit karo:



```

allow\_origins=\["https://legal-frontend.example.com"]

```



\- App ko hamesha HTTPS ke peeche chalao:

&nbsp; - Nginx / Traefik reverse proxy, ya

&nbsp; - Cloud load balancer (AWS ALB, GCP LB, etc.) with TLS.



\## 3. Running with Docker



\### 3.1 Build image



Project root (jahan `Dockerfile` hai) se:



```

docker build -t legal-simplifier .

```



\### 3.2 Run application container



```

docker run -d --name legal-simplifier \\

&nbsp; --env-file .env \\

&nbsp; -p 8000:8000 \\

&nbsp; --restart unless-stopped \\

&nbsp; legal-simplifier

```



\- App `http://localhost:8000` (ya host IP) par chalegi.

\- Agar uploads/logs persist karne hain to volume mount use karo.



\## 4. Redis and Celery Workers



\### 4.1 Start Redis



```

docker run -d --name redis \\

&nbsp; -p 6379:6379 \\

&nbsp; --restart unless-stopped \\

&nbsp; redis:7

```



\### 4.2 Start Celery worker



Host se (project root):



```

celery -A src.tasks.celery\_app worker --loglevel=info

```



Ya Docker container ke roop me:



```

docker run -d --name legal-simplifier-worker \\

&nbsp; --env-file .env \\

&nbsp; --link redis \\

&nbsp; legal-simplifier \\

&nbsp; celery -A src.tasks.celery\_app worker --loglevel=info

```



\## 5. Health Checks and Monitoring



\- Load balancer health checks ke liye `GET /health` use karo.

\- Prometheus scrape endpoint ke liye `GET /metrics` use karo.



Example Prometheus config:



```

scrape\_configs:

&nbsp; - job\_name: 'legal-simplifier'

&nbsp;   static\_configs:

&nbsp;     - targets: \['legal-simplifier:8000']

```



\- Logs:

&nbsp; - Structured logs stdout/stderr par jate hain.

&nbsp; - Docker logging driver ya cloud logging service se collect karo.



\## 6. Typical Production Topology



\- Reverse proxy (Nginx/Traefik) → FastAPI container(s) on port 8000.

\- Managed PostgreSQL instance (backups enabled).

\- Redis for Celery + caching.

\- Prometheus + Grafana (ya koi APM) `/metrics` scrape kare.



\## 7. Production Checklist



Before going live:



\- \[ ] `DEBUG=False` in `.env`.

\- \[ ] Strong `SECRET\_KEY` set and stored securely.

\- \[ ] `DATABASE\_URL` production DB par point kar raha hai; backups configured.

\- \[ ] CORS sirf real frontend domains ke liye allowed.

\- \[ ] SlowAPI rate limiting important endpoints pe configured.

\- \[ ] Redis + Celery workers up and healthy.

\- \[ ] `/health` aur `/metrics` monitoring / load balancer me integrated.

\- \[ ] HTTPS enabled via reverse proxy or cloud load balancer.

\- \[ ] Basic integration tests staging environment par pass huye.

\- \[ ] Docker image tag karke registry (ECR/GCR/Docker Hub) me push ki gayi.



\## 8. Local Testing Commands



\- App local run:



```

uvicorn src.main:app --reload

```



\- Important endpoints check karo:



&nbsp; - `GET /health` – DB + app health.

&nbsp; - `GET /documents` – document listing (caching enabled).

&nbsp; - `POST /simplify/text` – text simplification.

&nbsp; - `GET /metrics` – Prometheus metrics.

&nbsp; - `POST /webhooks/register` + simplification call – webhook trigger verify.

