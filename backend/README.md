# Banking AI-Agent — Microservice Architecture (Lab 4)

## Mô tả kiến trúc

Hệ thống Banking AI-Agent được thiết kế theo mô hình **microservice**, gồm 3 Docker containers và 1 Ollama server bên ngoài:

```
┌──────────────────── Docker Compose ────────────────────┐
│                                                        │
│  ┌──────────────┐    REST     ┌──────────────────┐    │
│  │   Frontend   │ ──────────▶ │   API Gateway    │    │
│  │ Streamlit    │ ◀────────── │   FastAPI :8000   │    │
│  │ :8501        │  Response   │                  │    │
│  └──────────────┘             │  ┌────────────┐  │    │
│                               │  │Intent Node │  │    │
│                               │  │Priority    │  │    │     ┌────────────────┐
│                               │  │Policy      │  │    │     │ Ollama Server  │
│                               │  │Draft Node ─│──│────│────▶│ (Colab/Local)  │
│                               │  │Validation  │  │    │     │ :11434         │
│                               │  │Router      │  │    │     └────────────────┘
│                               │  └─────┬──────┘  │    │            ▲
│                               └────────│─────────┘    │            │
│                                   gRPC │              │            │
│                               ┌────────▼─────────┐    │            │
│                               │  Intent Service  │────│────────────┘
│                               │  gRPC :50051     │    │     HTTP
│                               └──────────────────┘    │
└───────────────────────────────────────────────────────┘
```

### Vai trò từng container

| Container | Port | Vai trò |
|---|---|---|
| **backend** (API Gateway) | 8000 | Entry point, điều phối toàn bộ agentic workflow. Nhận HTTP requests, gọi Intent Service qua gRPC, chạy các workflow nodes, gọi Ollama sinh response. |
| **intent-service** | 50051 | Microservice gRPC độc lập. Nhận message, gọi Ollama để phân loại intent BANKING77, trả về intent/confidence/reason. |
| **frontend** | 8501 | Giao diện Streamlit cho người dùng. Gửi message tới API Gateway, hiển thị kết quả và workflow trace. |
| **Ollama** (external) | 11434 | Server LLM chạy trên Colab (hoặc local). Phục vụ model `gpt-oss:20b` cho cả intent prediction và response generation. |

### Giao tiếp giữa các service

| Từ | Đến | Protocol | Mô tả |
|---|---|---|---|
| Frontend | Backend | HTTP (REST) | `POST /run-agent` |
| Backend | Intent Service | gRPC | `IntentRecognizer` RPC |
| Backend | Ollama | HTTP | `/api/chat` (response generation) |
| Intent Service | Ollama | HTTP | `/api/chat` (intent classification) |

---

## Hướng dẫn sử dụng

### 1. Chuẩn bị Ollama

**Trên Google Colab** (khuyến nghị — cần GPU):

1. Mở notebook `[NOTEBOOK] Ollama.ipynb` trên Colab
2. Chạy các cell để cài Ollama và pull model `gpt-oss:20b`
3. Tạo tunnel Pinggy:
   ```bash
   ssh -p 443 -R0:localhost:11434 qr@a.pinggy.io
   ```
4. Copy URL public (vd: `http://xxxxx.a.free.pinggy.link`)

**Hoặc chạy local** (nếu có GPU đủ mạnh):

```bash
curl -fsSL https://ollama.com/install.sh | sudo sh
ollama serve &
ollama pull gpt-oss:20b
```

### 2. Generate gRPC code từ `.proto`

gRPC code được generate tự động khi build Docker image. Nếu muốn generate thủ công:

```bash
cd intent_service
pip install grpcio-tools
make
```

File được tạo:
- `intent_service_pb2.py` — Python message classes
- `intent_service_pb2_grpc.py` — gRPC client/server stubs

### 3. Build Docker images

```bash
# Build tất cả
docker compose build

# Hoặc build từng service
docker compose build backend
docker compose build intent-service
docker compose build frontend
```

### 4. Chạy hệ thống bằng Docker Compose

```bash
# Với Ollama trên Colab (thay URL Pinggy)
OLLAMA_BASE_URL=http://xxxxx.a.free.pinggy.link docker compose up

# Với Ollama trên local
docker compose up

# Chạy ở background
docker compose up -d

# Xem logs
docker compose logs -f

# Dừng hệ thống
docker compose down
```

### 5. Test API

```bash
# Health check
curl http://localhost:8000/health

# Xem config
curl http://localhost:8000/config

# Gọi agent
curl -X POST http://localhost:8000/run-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "I lost my card and need a replacement"}'
```

### 6. Sử dụng Frontend

Mở trình duyệt tại: **http://localhost:8501**

---

## Biến môi trường

| Service | Biến | Mô tả | Default |
|---|---|---|---|
| backend | `INTENT_SERVICE_HOST` | Hostname Intent Service | `intent-service` |
| backend | `INTENT_SERVICE_PORT` | Port Intent Service | `50051` |
| backend | `OLLAMA_BASE_URL` | URL Ollama server | `http://host.docker.internal:11434` |
| backend | `OLLAMA_MODEL` | Model Ollama | `gpt-oss:20b` |
| intent-service | `OLLAMA_BASE_URL` | URL Ollama server | `http://host.docker.internal:11434` |
| intent-service | `INTENT_MODEL_NAME` | Model cho intent | `gpt-oss:20b` |
| intent-service | `GRPC_PORT` | Port gRPC server | `50051` |
| frontend | `API_BASE_URL` | URL API Gateway | `http://backend:8000` |

---

## Liên kết với Lab trước

| Lab | Nội dung tái sử dụng |
|---|---|
| Lab 2 | Fine-tuned intent model (Llama-3.2-3B + LoRA, BANKING77) — tùy chọn |
| Lab 3 | Agentic workflow, orchestrator, các nodes, Ollama integration |

---

## Thông tin

- **Môn:** Applications of Natural Language Processing in Industry
- **Lab:** Project 4 — REST, gRPC and Deployment with Docker
- **Giảng viên:** Dr. Nguyen Hong Buu Long
