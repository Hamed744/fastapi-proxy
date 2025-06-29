from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLOUDFLARE_WORKER_URL = "https://aisada-proxy.asrasahar744.workers.dev"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS", "HEAD"])
async def proxy_gateway(request: Request):
    # >>>>> منطق جدید و صحیح برای UptimeRobot <<<<<
    if request.method == "HEAD":
        # UptimeRobot یک درخواست HEAD برای بررسی سلامت می‌فرستد.
        # ما فقط یک پاسخ موفقیت‌آمیز خالی برمی‌گردانیم تا وضعیت "Up" نشان داده شود.
        logger.info("Responding to HEAD request from UptimeRobot with 200 OK.")
        return Response(status_code=200, content="OK")

    target_url = request.headers.get('x-target-huggingface-url')
    if not target_url and request.method == "GET":
        target_url = request.query_params.get('X-Target-HuggingFace-URL')
    
    if not target_url:
        return Response(content="Error: X-Target-HuggingFace-URL is missing.", status_code=400)

    headers_to_forward = {
        'Content-Type': request.headers.get('Content-Type'),
        'X-Target-HuggingFace-URL': target_url,
        'User-Agent': 'Render-Proxy-Gateway/1.0'
    }
    headers_to_forward = {k: v for k, v in headers_to_forward.items() if v is not None}
    
    body_content = await request.body()
    
    logger.info(f"Streaming {request.method} request for {target_url} to Cloudflare worker.")

    client = httpx.AsyncClient(http2=True)
    
    try:
        worker_req = client.build_request(
            method=request.method,
            url=CLOUDFLARE_WORKER_URL,
            headers=headers_to_forward,
            content=body_content,
            timeout=180.0
        )
        worker_resp = await client.send(worker_req, stream=True)

        response_headers = {
            key: value for key, value in worker_resp.headers.items()
            if key.lower() not in ['content-encoding', 'transfer-encoding', 'connection']
        }

        return StreamingResponse(
            worker_resp.aiter_bytes(),
            status_code=worker_resp.status_code,
            headers=response_headers,
            media_type=worker_resp.headers.get('content-type')
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred during streaming: {e}")
        await client.aclose()
        return Response("Error: An internal error occurred in the proxy gateway.", status_code=500)
