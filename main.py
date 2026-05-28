from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

BIDS = [
    {
        "grade": "A",
        "title": "김해시 도로 포장 정비공사",
        "agency": "김해시",
        "reason": "포장, 도로, 정비 키워드가 송원건설 주력공종과 잘 맞습니다."
    },
    {
        "grade": "B",
        "title": "배수로 정비 및 측구 보수공사",
        "agency": "경상남도",
        "reason": "배수로, 측구, 보수 키워드가 포함되어 있습니다."
    },
    {
        "grade": "C",
        "title": "하천 주변 시설물 보수공사",
        "agency": "한국농어촌공사",
        "reason": "하천, 보수 키워드는 맞지만 세부 면허 확인이 필요합니다."
    }
]


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <meta charset="utf-8">
        <title>gongsa-bid</title>
    </head>
    <body style="font-family: Arial; padding: 30px; background: #f4f6f8;">
        <div style="max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 14px;">
            <h1>gongsa-bid</h1>
            <h2>건설회사 전용 나라장터 맞춤공고 추천 웹사이트</h2>

            <p>현재는 송원건설 기준으로 나라장터 맞춤공고 추천 기능을 만들고 있습니다.</p>

            <hr>

            <h3>회사 정보</h3>
            <p><b>회사명:</b> 주식회사 송원건설</p>
            <p><b>주소:</b> 경상남도 김해시 삼문로19, 1205호</p>
            <p><b>전화:</b> 055-339-4763</p>
            <p><b>팩스:</b> 055-339-4764</p>
            <p><b>이메일:</b> songwon4763@naver.com</p>

            <hr>

            <h3>송원건설 주력 키워드</h3>
            <p>포장, 배수, 배수로, 상하수도, 관로, 도로, 하천, 소하천, 옹벽, 측구, 맨홀, 농로, 재해복구, 정비, 보수</p>

            <hr>

            <h3>테스트 주소</h3>
            <p><a href="/bids/test">가짜 공고 JSON 보기</a></p>
            <p><a href="/bids/test-page">가짜 공고 화면 보기</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gongsa-bid"
    }


@app.get("/bids/test")
def bids_test():
    return {
        "status": "ok",
        "message": "가짜 공고 테스트 목록입니다.",
        "company": "주식회사 송원건설",
        "bids": BIDS
    }


@app.get("/bids/test-page", response_class=HTMLResponse)
def bids_test_page():
    cards = ""

    for bid in BIDS:
        cards += f"""
        <div style="background: white; padding: 20px; margin-bottom: 15px; border-radius: 12px; border-left: 8px solid #2563eb;">
            <h2>{bid["grade"]}등급 - {bid["title"]}</h2>
            <p><b>발주기관:</b> {bid["agency"]}</p>
            <p><b>추천이유:</b> {bid["reason"]}</p>
        </div>
        """

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>맞춤공고 테스트</title>
    </head>
    <body style="font-family: Arial; padding: 30px; background: #f4f6f8;">
        <div style="max-width: 1000px; margin: auto;">
            <h1>송원건설 맞춤공고 테스트</h1>
            <p>현재는 실제 나라장터 공고가 아니라 가짜 테스트 공고입니다.</p>
            <p>다음 단계에서 실제 나라장터 공고를 연결합니다.</p>

            <hr>

            {cards}

            <p><a href="/">처음 화면으로 돌아가기</a></p>
        </div>
    </body>
    </html>
    """
