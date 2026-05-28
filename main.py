from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>gongsa-bid</title>
    </head>
    <body>
        <h1>gongsa-bid 테스트 웹사이트입니다.</h1>
        <p>건설회사 전용 나라장터 맞춤공고 추천 웹사이트를 만들고 있습니다.</p>
        <p>1차 목표: 송원건설 기준 맞춤 공고 추천 화면 만들기</p>
    </body>
    </html>
    """


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "gongsa-bid"
    }
