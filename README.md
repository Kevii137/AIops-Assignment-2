# AIOps Module 3 Assignment

Full write-up (2 pages): [`writeup/writeup.pdf`](writeup/writeup.pdf). Screenshots backing every
claim in the write-up are under `evidence/<qN>/`.

## Layout

- `spam_api/` — the TF-IDF + Naive Bayes spam-detection FastAPI service shared by all four
  questions (`POST /predict`, `GET /healthz`).
  - `train/generate_dataset.py`, `train/train_model.py` — build `data/spam_dataset.csv` and
    `data/model.joblib`.
  - `Dockerfile.naive` / `Dockerfile.multistage` — **Q1**.
  - `app/main.py` — also implements the Redis cache logic used in **Q2** (a no-op when
    `REDIS_HOST` is unset, i.e. for Q1/Q4).
- `q2_compose/` — **Q2**: `docker-compose.yml` (api + redis:7-alpine).
- `q3_indexed_job/` — **Q3**: `shards/generate_shards.py` (8 seeded CSV shards),
  `shards/validate_shard.py` (per-shard worker), `Dockerfile.job`, `indexed-job.yaml`,
  `collect_results.py` (Kubernetes API log collector, needs `requirements.txt`).
- `q4_deployment/` — **Q4**: `deployment.yaml` (2 replicas + probes), `service.yaml`.
- `evidence/q1/` … `evidence/q4/` — screenshots corresponding to evidences asked for in the assignment
- `writeup.pdf` .

## Reproducing

```bash
# Q1
cd spam_api
docker build -t spam-api:naive -f Dockerfile.naive .
docker build -t spam-api:multistage -f Dockerfile.multistage .
docker images spam-api

# Q2
cd ../q2_compose
docker compose up -d --build
curl -i -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"text": "..."}'  # 1st call: x-cache MISS
curl -i -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"text": "..."}'  # 2nd call, same text: x-cache HIT
docker compose down

# Q3 / Q4 
minikube start -p aiops-assignment2 --nodes 2 --cpus 2 --memory 3072 --driver=docker

cd ../q3_indexed_job
python3 shards/generate_shards.py
minikube -p aiops-assignment2 image build -t shard-validator:latest -f Dockerfile.job --all .
kubectl --context aiops-assignment2 apply -f indexed-job.yaml
kubectl --context aiops-assignment2 get pods -o wide -l job-name=shard-validate-job
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python3 collect_results.py --context aiops-assignment2

# Q4 -- spam_api/app/main.py currently defaults APP_VERSION to "v2", the end state of the
# rolling update below. To reproduce the full before/after demo from scratch:
cd ../spam_api
# 1) temporarily edit app/main.py: APP_VERSION default "v2" -> "v1"
minikube -p aiops-assignment2 image build -t spam-api:multistage -f Dockerfile.multistage --all .
cd ../q4_deployment
# 2) ensure deployment.yaml's image is spam-api:multistage, then:
kubectl --context aiops-assignment2 apply -f deployment.yaml -f service.yaml
kubectl --context aiops-assignment2 get pods -o wide -l app=spam-api   # 2 replicas, version v1
kubectl --context aiops-assignment2 delete pod <a-pod-name-from-above>  # self-healing
kubectl --context aiops-assignment2 get pods -o wide -l app=spam-api   # replacement pod appears

# 3) restore app/main.py's default back to "v2" (matching the committed file)
cd ../spam_api
minikube -p aiops-assignment2 image build -t spam-api:v2 -f Dockerfile.multistage --all .
cd ../q4_deployment
# 4) update deployment.yaml's image to spam-api:v2, then:
kubectl --context aiops-assignment2 apply -f deployment.yaml
kubectl --context aiops-assignment2 rollout status deployment/spam-api
kubectl --context aiops-assignment2 rollout history deployment/spam-api
```

## AI-DISCLOSURE

1) Tools used: Claude code
2) How it was used: Writing up code for the API contract, debuging dockerfiles, and building this readme.