import os
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


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

            <h3>테스트 주소</h3>
            <p><a href="/bids/test-page">가짜 공고 화면 보기</a></p>
            <p><a href="/bids/nara-test?keyword=포장">실제 나라장터 포장 공고 테스트</a></p>
            <p><a href="/bids/nara-test?keyword=배수">실제 나라장터 배수 공고 테스트</a></p>

            <hr>

            <h3>회사 정보</h3>
            <p><b>회사명:</b> 주식회사 송원건설</p>
            <p><b>주소:</b> 경상남도 김해시 삼문로19, 1205호</p>
            <p><b>전화:</b> 055-339-4763</p>
            <p><b>팩스:</b> 055-339-4764</p>
            <p><b>이메일:</b> songwon4763@naver.com</p>
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
        "bids": [
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
    }


@app.get("/bids/test-page", response_class=HTMLResponse)
def bids_test_page():
    bids = bids_test()["bids"]
    cards = ""

    for bid in bids:
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
            {cards}
            <p><a href="/">처음 화면으로 돌아가기</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/bids/nara-test")
def nara_test(keyword: str = "포장"):
    service_key = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip()

    if not service_key:
        return {
            "status": "error",
            "message": "Render 환경변수 DATA_GO_KR_SERVICE_KEY가 없습니다."
        }

    service_key = unquote(service_key)

    today = datetime.now()
    start = today.strftime("%Y%m%d0000")
    end = (today + timedelta(days=30)).strftime("%Y%m%d2359")

    url = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch"

    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "10",
        "inqryDiv": "1",
        "inqryBgnDt": start,
        "inqryEndDt": end,
        "bidNtceNm": keyword,
        "type": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        text = response.text

        try:
            data = response.json()
        except Exception:
            return {
                "status": "error",
                "message": "나라장터 응답을 JSON으로 읽지 못했습니다.",
                "http_status": response.status_code,
                "raw_text_start": text[:500]
            }

        body = data.get("response", {}).get("body", {})
        items = body.get("items", [])

        if isinstance(items, dict):
            items = [items]

        result = []

        for item in items:
            result.append({
                "공고명": item.get("bidNtceNm"),
                "공고번호": item.get("bidNtceNo"),
                "발주기관": item.get("dminsttNm"),
                "공고기관": item.get("ntceInsttNm"),
                "마감일": item.get("bidClseDt"),
                "공고상세URL": item.get("bidNtceDtlUrl")
            })

        return {
            "status": "ok",
            "keyword": keyword,
            "search_start": start,
            "search_end": end,
            "total_count": body.get("totalCount"),
            "count": len(result),
            "bids": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
