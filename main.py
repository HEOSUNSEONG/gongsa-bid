from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>gongsa-bid</h1><p>송원건설 나라장터 맞춤공고 추천 웹사이트 테스트입니다.</p>"

@app.get("/health")
def health():
    return {"status": "ok", "service": "gongsa-bid"}
