from fastapi import APIRouter, UploadFile, HTTPException, Request
import tempfile
import subprocess
import os
from pathlib import Path
import jwt
from datetime import datetime

from app.agent.auth import SECRET_KEY

router = APIRouter()

def verify_auth(request: Request):
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        raise HTTPException(401, "缺少认证凭证")
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "无效的认证凭证")
    return True

ALLOWED_EXTENSIONS = {'.txt', '.md', '.docx', '.xlsx', '.xls', '.pdf', '.pptx'}

UPLOAD_DIR = Path(".uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def save_upload(filename: str, content: bytes, parsed_text: str) -> dict:
    date_str = datetime.now().strftime("%Y%m%d")
    time_str = datetime.now().strftime("%H%M%S")

    upload_path = UPLOAD_DIR / date_str
    upload_path.mkdir(exist_ok=True)

    base_name = Path(filename).stem
    safe_name = f"{base_name}_{time_str}"

    original_file = upload_path / f"{safe_name}{Path(filename).suffix}"
    parsed_file = upload_path / f"{safe_name}.txt"

    original_file.write_bytes(content)
    parsed_file.write_text(parsed_text, encoding="utf-8")

    return {
        "original_path": str(original_file),
        "parsed_path": str(parsed_file)
    }

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile):
    verify_auth(request)
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件格式: {ext}")

    content = await file.read()

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = subprocess.run(
            ["markitdown", tmp_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise HTTPException(500, f"文件解析失败: {result.stderr}")

        text = result.stdout.strip()

        if not text:
            raise HTTPException(400, "文件内容为空")

        paths = save_upload(filename, content, text)

        return {"text": text, "filename": filename, "saved_to": paths}

    except subprocess.TimeoutExpired:
        raise HTTPException(500, "文件解析超时")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)