# CloudShield AI - Smart and Secure System Prototype

CloudShield AI is a DIT637 Smart and Secure Systems prototype organized around the course's three critical elements: **cloud computing, software security, and artificial intelligence**. The system uses the public CICIDS2017 network-flow dataset to train an intrusion-detection model, exposes the selected model through a secured FastAPI service, and creates analyst-reviewable security alerts. AWS is the proposed cloud platform, while the implementation remains reproducible locally and in Docker.

## Course alignment

### 1. Cloud computing

The cloud layer defines how the prototype maps to AWS services:

- Amazon EC2 or a container service for compute
- Amazon VPC for network isolation
- Amazon S3 for model and dataset storage
- AWS IAM for least-privilege access control
- AWS KMS for key management and encryption
- Amazon CloudWatch for centralized logging and monitoring
- AWS Security Hub for centralized security findings

`src/layers/cloud_computing_layer.py` exposes this mapping and writes `results/cloud_deployment_manifest.json` during training. The code therefore separates the cloud deployment concern from the machine-learning logic.

### 2. Software security

The software-security layer protects the AI service itself rather than assuming that an accurate model is automatically secure. The prototype includes:

- strict feature-schema validation before inference
- optional API-key authentication using `CLOUDSHIELD_API_KEY`
- security-related HTTP response headers
- SHA-256 visibility for the saved model artifact
- controlled FastAPI endpoints
- append-only JSONL alert events for auditability
- explicit analyst review instead of automatic blocking
- Docker packaging for a repeatable runtime

`src/security.py` contains the API-key, model-integrity, and HTTP-header controls. These are prototype controls; production deployment should use managed identity, TLS termination, secrets management, rate limiting, and centralized immutable logs.

### 3. Artificial intelligence

The AI layer uses CICIDS2017 for supervised binary intrusion detection:

- BENIGN = 0
- ATTACK = 1
- Random Forest as the primary model
- Decision Tree as the baseline
- 80/20 stratified train/test split
- model comparison by accuracy, precision, recall, F1-score, false-positive rate, and confusion matrix
- feature-importance output when supported by the selected model

The selected model is persisted and reused by FastAPI so training and inference are separate stages.

## Architecture

```text
                         SMART + SECURE SYSTEM

  CLOUD COMPUTING              SOFTWARE SECURITY                 ARTIFICIAL INTELLIGENCE
  -----------------            -----------------                 -----------------------
  AWS target design            API key / headers                 CICIDS2017 dataset
  VPC / IAM / KMS        +     input validation            +     preprocessing
  S3 / CloudWatch              model integrity                   Random Forest / Tree
  Security Hub                 audit / analyst review            prediction confidence
          |                            |                                  |
          +----------------------------+----------------------------------+
                                       |
                                       v
CICIDS2017 -> Data Layer -> Preprocessing -> ML Model -> FastAPI -> Alert -> Analyst Review
```

## Source-code organization

```text
cloudshield_ai/
  data/
    raw/                     # CICIDS2017 CSV files go here
    alerts/                  # prototype audit/alert events
  models/                    # trained model and feature schema
  results/                   # metrics and cloud deployment manifest
  src/
    obtain_dataset.py
    train_and_evaluate.py
    api.py
    security.py
    layers/
      data_layer.py
      preprocessing_layer.py
      machine_learning_layer.py
      cloud_computing_layer.py
      alert_analyst_layer.py
  tests/
  Dockerfile
  requirements.txt
```

## Obtain the CICIDS2017 dataset

The project does not redistribute CICIDS2017. Obtain it from the Canadian Institute for Cybersecurity at the University of New Brunswick.

Official dataset page:

`https://www.unb.ca/cic/datasets/ids-2017.html`

Run:

```bash
python -m src.obtain_dataset
```

Then:

1. Open the official CICIDS2017 page printed by the script.
2. Download the machine-learning CSV package, commonly distributed as `MachineLearningCSV.zip`.
3. Extract the CSV files under `data/raw/`.
4. Run the dataset-verification script again.
5. Do not commit the dataset to GitHub; `.gitignore` excludes it.

The loader searches recursively, so the original extracted directory structure can remain under `data/raw/`.

## Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Train and evaluate the AI layer

For a lightweight course run:

```bash
python -m src.train_and_evaluate --sample-frac 0.10
```

For a deterministic memory limit:

```bash
python -m src.train_and_evaluate --max-rows-per-file 50000
```

For all available rows:

```bash
python -m src.train_and_evaluate
```

Generated artifacts include:

- `models/cloudshield_model.joblib`
- `models/feature_names.joblib`
- `models/model_metadata.json`
- `results/metrics.csv`
- `results/metrics.json`
- `results/feature_importance.csv`
- `results/cloud_deployment_manifest.json`

## Run the secured FastAPI service

Train a model first, then optionally set an API key:

```bash
export CLOUDSHIELD_API_KEY="replace-with-a-secret-value"
uvicorn src.api:app --reload --port 8000
```

If `CLOUDSHIELD_API_KEY` is configured, protected endpoints require:

```text
X-API-Key: replace-with-a-secret-value
```

Important endpoints:

- `GET /health` - service status and saved-model SHA-256
- `GET /architecture` - shows how the code implements cloud computing, software security, and AI
- `GET /schema/features` - required CICIDS2017 inference schema
- `POST /predict` - BENIGN/ATTACK prediction with probabilities
- `GET /alerts` - analyst alert queue
- `POST /alerts/{alert_id}/review` - analyst decision

Interactive API documentation is available at `/docs`.

## Alert and analyst layer

An ATTACK prediction creates an alert with an ID, UTC timestamp, attack probability, confidence, severity, and status. The analyst can change the status to `ACKNOWLEDGED`, `FALSE_POSITIVE`, `ESCALATED`, or `CLOSED` and add a note.

This human-in-the-loop design is intentional. AI supports security decision-making but does not automatically block traffic because false positives and model uncertainty remain possible.

## Docker

After the model artifacts exist:

```bash
docker build -t cloudshield-ai .
docker run -p 8000:8000 -e CLOUDSHIELD_API_KEY="replace-with-a-secret-value" cloudshield-ai
```

## Tests

```bash
pytest -q
```

## Smart and secure system interpretation

CloudShield AI is not presented as only a machine-learning experiment. Its smart capability comes from data-driven detection and confidence-based classification. Its secure capability comes from protected interfaces, validation, model-integrity awareness, audit events, least-privilege cloud design, encryption planning, and analyst oversight. The cloud layer provides the scalable environment in which the software-security and AI layers can operate together.

## Limitations and future work

CICIDS2017 is an older benchmark, binary classification hides individual attack categories, and the prototype uses offline data instead of live AWS telemetry. Future work should include newer datasets, multiclass classification, VPC Flow Logs, managed authentication, TLS, Secrets Manager, CloudWatch integration, immutable audit storage, model-drift monitoring, explainable AI, adversarial testing, and production-grade deployment controls.
