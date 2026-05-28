import os
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote, quote
from html import escape

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


SONGWON_KEYWORDS = [
    "포장", "배수", "배수로", "상하수도", "관로",
    "도로", "하천", "소하천", "옹벽", "측구",
    "맨홀", "농로", "재해복구", "정비", "보수"
]


CATEGORIES = {
    "all": {
        "label": "전체보기",
        "keywords": []
    },
    "pavement": {
        "label": "포장/도로",
        "keywords": ["포장", "도로", "농로"]
    },
    "water": {
        "label": "상하수도/관로",
        "keywords": ["상하수도", "관로"]
    },
    "drain": {
        "label": "배수/측구",
        "keywords": ["배수", "배수로", "측구"]
    },
    "river": {
        "label": "하천/재해복구",
        "keywords": ["하천", "소하천", "재해복구"]
    },
    "structure": {
        "label": "옹벽/맨홀",
        "keywords": ["옹벽", "맨홀"]
    },
    "repair": {
        "label": "정비/보수",
        "keywords": ["정비", "보수"]
    },
    "etc": {
        "label": "기타",
        "keywords": []
    }
}


def is_closed(close_date: str):
    if not close_date:
        return False

    try:
        close_dt = datetime.strptime(close_date, "%Y-%m-%d %H:%M:%S")
        return close_dt < datetime.now()
    except Exception:
        return False


def classify_bid(title: str, search_keyword: str):
    text = f"{title or ''} {search_keyword or ''}"

    for category_key, category_info in CATEGORIES.items():
        if category_key in ["all", "etc"]:
            continue

        for keyword in category_info["keywords"]:
            if keyword in text:
                return category_key

    return "etc"


def fetch_nara_bids(keyword: str = "포장", days: int = 30, rows: int = 30):
    service_key = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip()

    if not service_key:
        return {
            "status": "error",
            "message": "Render 환경변수 DATA_GO_KR_SERVICE_KEY가 없습니다.",
            "keyword": keyword,
            "total_count": 0,
            "count": 0,
            "bids": []
        }

    service_key = unquote(service_key)

    today = datetime.now()
    start = today.strftime("%Y%m%d0000")
    end = (today + timedelta(days=days)).strftime("%Y%m%d2359")

    url = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch"

    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": str(rows),
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
        title = item.get("bidNtceNm")
        close_date = item.get("bidClseDt")

        if is_closed(close_date):
            continue

        bid_no = item.get("bidNtceNo")
        bid_ord = item.get("bidNtceOrd") or item.get("bidPbancOrd") or "000"
        category_key = classify_bid(title, keyword)

        bids.append({
            "검색키워드": keyword,
            "분류키": category_key,
            "분류명": CATEGORIES.get(category_key, {}).get("label", "기타"),
            "공고명": title,
            "공고번호": bid_no,
            "공고차수": bid_ord,
            "발주기관": item.get("dminsttNm"),
            "공고기관": item.get("ntceInsttNm"),
            "마감일": close_date,
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


def fetch_songwon_all_bids():
    all_bids = []
    seen = set()
    keyword_summary = []

    for keyword in SONGWON_KEYWORDS:
        try:
            result = fetch_nara_bids(keyword=keyword, days=30, rows=30)
            bids = result.get("bids", [])

            keyword_summary.append({
                "keyword": keyword,
                "count": len(bids)
            })

            for bid in bids:
                bid_no = bid.get("공고번호") or ""
                bid_ord = bid.get("공고차수") or ""
                title = bid.get("공고명") or ""

                unique_key = f"{bid_no}-{bid_ord}-{title}"

                if unique_key in seen:
                    continue

                seen.add(unique_key)
                all_bids.append(bid)

        except Exception:
            keyword_summary.append({
                "keyword": keyword,
                "count": 0
            })

    all_bids.sort(key=lambda x: x.get("마감일") or "")

    return {
        "status": "ok",
        "company": "주식회사 송원건설",
        "keywords": SONGWON_KEYWORDS,
        "keyword_summary": keyword_summary,
        "count": len(all_bids),
        "bids": all_bids
    }


def filter_bids_by_category(bids, category: str):
    if category == "all":
        return bids

    if category == "etc":
        return [bid for bid in bids if bid.get("분류키") == "etc"]

    return [bid for bid in bids if bid.get("분류키") == category]


def count_by_category(bids):
    counts = {}

    for category_key in CATEGORIES.keys():
        if category_key == "all":
            counts[category_key] = len(bids)
        else:
            counts[category_key] = 0

    for bid in bids:
        category_key = bid.get("분류키") or "etc"

        if category_key not in counts:
            category_key = "etc"

        counts[category_key] += 1

    return counts


def render_category_buttons(selected_category, counts):
    buttons = ""

    for category_key, category_info in CATEGORIES.items():
        label = category_info["label"]
        count = counts.get(category_key, 0)

        if category_key == selected_category:
            background = "#111827"
        else:
            background = "#2563eb"

        buttons += f"""
        <a href="/bids/songwon-page?category={category_key}"
           style="display:inline-block; padding:10px 14px; margin:5px; background:{background}; color:white; text-decoration:none; border-radius:22px;">
           {escape(label)} {count}건
        </a>
        """

    return buttons


def render_keyword_summary(summary):
    summary_html = ""

    for item in summary:
        summary_html += f"""
        <span style="display:inline-block; padding:6px 10px; margin:4px; background:#e5e7eb; border-radius:20px;">
            {escape(str(item.get("keyword")))}: {item.get("count")}건
        </span>
        """

    return summary_html


def render_bid_cards(bids):
    if not bids:
        return """
        <div style="background:white; padding:20px; border-radius:12px;">
            <p>검색된 진행중 공고가 없습니다.</p>
        </div>
        """

    cards = ""

    for bid in bids:
        title = escape(str(bid.get("공고명") or ""))
        bid_no = escape(str(bid.get("공고번호") or ""))
        agency = escape(str(bid.get("발주기관") or ""))
        notice_agency = escape(str(bid.get("공고기관") or ""))
        close_date = escape(str(bid.get("마감일") or ""))
        keyword = escape(str(bid.get("검색키워드") or ""))
        category_name = escape(str(bid.get("분류명") or "기타"))
        link = bid.get("나라장터링크") or "#"

        cards += f"""
        <div style="background:white; padding:20px; margin-bottom:15px; border-radius:12px; border-left:8px solid #2563eb; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="margin-bottom:8px;">
                <span style="font-size:14px; color:white; background:#2563eb; display:inline-block; padding:5px 10px; border-radius:20px;">
                    {category_name}
                </span>
                <span style="font-size:14px; color:white; background:#6b7280; display:inline-block; padding:5px 10px; border-radius:20px;">
                    검색키워드: {keyword}
                </span>
            </div>

            <h2 style="margin-top:8px;">{title}</h2>
            <p><b>공고번호:</b> {bid_no}</p>
            <p><b>발주기관:</b> {agency}</p>
            <p><b>공고기관:</b> {notice_agency}</p>
            <p><b>마감일:</b> {close_date}</p>
            <p>
                <a href="{link}" target="_blank"
                   style="display:inline-block; padding:10px 14px; background:#111827; color:white; text-decoration:none; border-radius:8px;">
                   나라장터 원문 보기
                </a>
            </p>
        </div>
        """

    return cards


@app.get("/", response_class=HTMLResponse)
def home():
    keyword_links = ""

    for keyword in SONGWON_KEYWORDS:
        encoded = quote(keyword)
        keyword_links += f"""
        <a href="/bids/nara-page?keyword={encoded}"
           style="display:inline-block; padding:8px 12px; margin:4px; background:#2563eb; color:white; text-decoration:none; border-radius:20px;">
           {escape(keyword)}
        </a>
        """

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>gongsa-bid</title>
    </head>
    <body style="font-family:Arial; padding:30px; background:#f4f6f8;">
        <div style="max-width:1000px; margin:auto; background:white; padding:30px; border-radius:14px;">
            <h1>gongsa-bid</h1>
            <h2>건설회사 전용 나라장터 공고 확인 웹사이트</h2>

            <p>현재는 송원건설 주력 키워드로 나라장터 공고를 검색해서 보여주는 테스트 단계입니다.</p>
            <p>추천등급 없이, 검색된 진행중 공고를 분류별로 표시합니다.</p>

            <hr>

            <h3>회사 정보</h3>
            <p><b>회사명:</b> 주식회사 송원건설</p>
            <p><b>주소:</b> 경상남도 김해시 삼문로19, 1205호</p>
            <p><b>전화:</b> 055-339-4763</p>
            <p><b>팩스:</b> 055-339-4764</p>
            <p><b>이메일:</b> songwon4763@naver.com</p>

            <hr>

            <h3>송원건설 주력 키워드 개별 검색</h3>
            <p>아래 키워드를 누르면 해당 키워드 공고만 검색됩니다.</p>
            <div>
                {keyword_links}
            </div>

            <hr>

            <h3>분류별 전체 검색</h3>
            <p>송원건설 주력 키워드 15개를 한 번에 검색하고, 면허/공종 분류별로 나눠서 보여줍니다.</p>
            <p>
                <a href="/bids/songwon-page"
                   style="display:inline-block; padding:14px 18px; background:#111827; color:white; text-decoration:none; border-radius:10px;">
                   송원건설 전체 공고 검색하기
                </a>
            </p>
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
        return fetch_nara_bids(keyword=keyword)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "bids": []
        }


@app.get("/bids/nara-page", response_class=HTMLResponse)
def nara_page(keyword: str = "포장"):
    try:
        result = fetch_nara_bids(keyword=keyword)
    except Exception as e:
        return f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family:Arial; padding:30px;">
            <h1>오류 발생</h1>
            <p>{escape(str(e))}</p>
            <p><a href="/">처음으로 돌아가기</a></p>
        </body>
        </html>
        """

    bids = result.get("bids", [])
    cards = render_bid_cards(bids)

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{escape(keyword)} 공고 목록</title>
    </head>
    <body style="font-family:Arial; padding:30px; background:#f4f6f8;">
        <div style="max-width:1000px; margin:auto;">
            <h1>송원건설 나라장터 공고 목록</h1>
            <h2>검색 키워드: {escape(keyword)}</h2>

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


@app.get("/bids/songwon-test")
def songwon_test():
    try:
        return fetch_songwon_all_bids()
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "bids": []
        }


@app.get("/bids/songwon-page", response_class=HTMLResponse)
def songwon_page(category: str = "all"):
    if category not in CATEGORIES:
        category = "all"

    try:
        result = fetch_songwon_all_bids()
    except Exception as e:
        return f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family:Arial; padding:30px;">
            <h1>오류 발생</h1>
            <p>{escape(str(e))}</p>
            <p><a href="/">처음으로 돌아가기</a></p>
        </body>
        </html>
        """

    all_bids = result.get("bids", [])
    summary = result.get("keyword_summary", [])
    counts = count_by_category(all_bids)
    filtered_bids = filter_bids_by_category(all_bids, category)

    selected_label = CATEGORIES.get(category, {}).get("label", "전체보기")

    summary_html = render_keyword_summary(summary)
    category_buttons = render_category_buttons(category, counts)
    cards = render_bid_cards(filtered_bids)

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>송원건설 전체 공고 검색</title>
    </head>
    <body style="font-family:Arial; padding:30px; background:#f4f6f8;">
        <div style="max-width:1100px; margin:auto;">
            <h1>송원건설 전체 공고 검색</h1>
            <p>송원건설 주력 키워드 15개를 검색하고, 중복 공고는 제거했습니다.</p>
            <p>마감일이 지난 공고는 화면에서 제외했습니다.</p>
            <p>추천등급 없이, 면허/공종 분류별로 공고를 나누어 보여줍니다.</p>

            <hr>

            <h3>분류별 보기</h3>
            <div>
                {category_buttons}
            </div>

            <hr>

            <h3>키워드별 검색 결과</h3>
            <div>
                {summary_html}
            </div>

            <hr>

            <h2>{escape(selected_label)}: {len(filtered_bids)}건</h2>
            <p>전체 진행중 공고 수: {result.get("count")}건</p>

            {cards}

            <p><a href="/">처음 화면으로 돌아가기</a></p>
        </div>
    </body>
    </html>
    """
