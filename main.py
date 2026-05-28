import os
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


SONGWON_KEYWORDS = [
    "포장", "배수", "배수로", "상하수도", "관로",
    "도로", "하천", "소하천", "옹벽", "측구",
    "맨홀", "농로", "재해복구", "정비", "보수"
]


def fetch_nara_bids(keyword: str = "포장"):
    service_key = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip()

    if not service_key:
        return {
            "status": "error",
            "message": "Render 환경변수 DATA_GO_KR_SERVICE_KEY가 없습니다.",
            "bids": []
        }

    service_key = unquote(service_key)

    today = datetime.now()
    start = today.strftime("%Y%m%d0000")
    end = (today + timedelta(days=30)).strftime("%Y%m%d2359")

    url = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch"

    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "30",
        "inqryDiv": "1",
        "inqryBgnDt": start,
        "inqryEndDt": end,
        "bidNtceNm": keyword,
        "type": "json"
    }

    response = requests.get(url, params=params, timeout=20)
    data = response.json()

    body = data.get("response", {}).get("body", {})
    items = body.get("items", [])

    if isinstance(items, dict):
        items = [items]

    bids = []

    for item in items:
        bids.append({
            "공고명": item.get("bidNtceNm"),
            "공고번호": item.get("bidNtceNo"),
            "발주기관": item.get("dminsttNm"),
            "공고기관": item.get("ntceInsttNm"),
            "마감일": item.get("bidClseDt"),
            "나라장터링크": item.get("bidNtceDtlUrl")
        })

    return {
        "status": "ok",
        "keyword": keyword,
        "search_start": start,
        "search_end": end,
        "total_count": body.get("totalCount"),
        "count": len(bids),
        "bids": bids
    }


@app.get("/", response_class=HTMLResponse)
def home():
    keyword_links = ""

    for keyword in SONGWON_KEYWORDS:
        keyword_links += f"""
        <a href="/bids/nara-page?keyword={keyword}"
           style="display:inline-block; padding:8px 12px; margin:4px; background:#2563eb; color:white; text-decoration:none; border-radius:20px;">
           {keyword}
        </a>
        """

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>gongsa-bid</title>
    </head>
    <body style="font-family: Arial; padding: 30px; background: #f4f6f8;">
        <div style="max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 14px;">
            <h1>gongsa-bid</h1>
            <h2>건설회사 전용 나라장터 공고 확인 웹사이트</h2>

            <p>현재는 송원건설 주력 키워드로 나라장터 공고를 검색해서 보여주는 테스트 단계입니다.</p>
            <p>아직 A/B/C 추천등급은 넣지 않았습니다.</p>

            <hr>

            <h3>회사 정보</h3>
            <p><b>회사명:</b> 주식회사 송원건설</p>
            <p><b>주소:</b> 경상남도 김해시 삼문로19, 1205호</p>
            <p><b>전화:</b> 055-339-4763</p>
            <p><b>팩스:</b> 055-339-4764</p>
            <p><b>이메일:</b> songwon4763@naver.com</p>

            <hr>

            <h3>송원건설 주력 키워드</h3>
            <p>아래 키워드를 누르면 실제 나라장터 공고가 검색됩니다.</p>

            <div>
                {keyword_links}
            </div>

            <hr>

            <h3>테스트 주소</h3>
            <p><a href="/bids/nara-test?keyword=포장">포장 공고 JSON 보기</a></p>
            <p><a href="/bids/nara-page?keyword=포장">포장 공고 화면 보기</a></p>
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


@app.get("/bids/nara-test")
def nara_test(keyword: str = "포장"):
    try:
        return fetch_nara_bids(keyword)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "bids": []
        }


@app.get("/bids/nara-page", response_class=HTMLResponse)
def nara_page(keyword: str = "포장"):
    try:
        result = fetch_nara_bids(keyword)
    except Exception as e:
        return f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial; padding: 30px;">
            <h1>오류 발생</h1>
            <p>{str(e)}</p>
            <p><a href="/">처음으로 돌아가기</a></p>
        </body>
        </html>
        """

    bids = result.get("bids", [])

    cards = ""

    if not bids:
        cards = """
        <div style="background:white; padding:20px; border-radius:12px;">
            <p>검색된 공고가 없습니다.</p>
        </div>
        """

    for bid in bids:
        link = bid.get("나라장터링크") or "#"

        cards += f"""
        <div style="background: white; padding: 20px; margin-bottom: 15px; border-radius: 12px; border-left: 8px solid #2563eb;">
            <h2>{bid.get("공고명")}</h2>
            <p><b>공고번호:</b> {bid.get("공고번호")}</p>
            <p><b>발주기관:</b> {bid.get("발주기관")}</p>
            <p><b>공고기관:</b> {bid.get("공고기관")}</p>
            <p><b>마감일:</b> {bid.get("마감일")}</p>
            <p>
                <a href="{link}" target="_blank"
                   style="display:inline-block; padding:10px 14px; background:#111827; color:white; text-decoration:none; border-radius:8px;">
                   나라장터 원문 보기
                </a>
            </p>
        </div>
        """

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{keyword} 공고 목록</title>
    </head>
    <body style="font-family: Arial; padding: 30px; background: #f4f6f8;">
        <div style="max-width: 1000px; margin: auto;">
            <h1>송원건설 나라장터 공고 목록</h1>
            <h2>검색 키워드: {keyword}</h2>

            <p>검색 기간: 오늘부터 30일</p>
            <p>총 검색 수: {result.get("total_count")}</p>
            <p>화면 표시 수: {result.get("count")}</p>

            <hr>

            {cards}

            <p><a href="/">처음 화면으로 돌아가기</a></p>
        </div>
    </body>
    </html>
    """
