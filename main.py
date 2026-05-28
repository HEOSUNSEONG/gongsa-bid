import os
import re
import html
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import List

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="gongsa-bid", version="company-profile-1.0.0")


# =========================================================
# 기본 설정
# =========================================================

DATA_GO_KR_SERVICE_KEY = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip()

G2B_CONSTRUCTION_API_URL = (
    "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"
)

PROFILE_FILE = "company_profile.json"

SONGWON_KEYWORDS = [
    "포장", "배수", "배수로", "상하수도", "관로",
    "도로", "하천", "소하천", "옹벽", "측구",
    "맨홀", "농로", "재해복구", "정비", "보수",
]

NATIONWIDE_AMOUNT_LIMIT = 10_000_000_000  # 100억 원

REGION_BUTTONS = [
    "전체",
    "전국",
    "서울",
    "경기",
    "인천",
    "부산",
    "대구",
    "광주",
    "대전",
    "울산",
    "세종",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주",
    "수도권",
    "충청권",
    "전라권",
    "경상권",
]

REGION_KEYWORDS = {
    "전국": [
        "전국",
        "전지역",
        "전 지역",
        "지역제한없음",
        "지역 제한 없음",
        "제한없음",
        "제한 없음",
    ],
    "서울": ["서울", "서울특별시"],
    "경기": ["경기", "경기도"],
    "인천": ["인천", "인천광역시"],
    "부산": ["부산", "부산광역시"],
    "대구": ["대구", "대구광역시"],
    "광주": ["광주", "광주광역시"],
    "대전": ["대전", "대전광역시"],
    "울산": ["울산", "울산광역시"],
    "세종": ["세종", "세종특별자치시"],
    "강원": ["강원", "강원도", "강원특별자치도"],
    "충북": ["충북", "충청북도"],
    "충남": ["충남", "충청남도"],
    "전북": ["전북", "전라북도", "전북특별자치도"],
    "전남": ["전남", "전라남도"],
    "경북": ["경북", "경상북도"],
    "경남": ["경남", "경상남도", "김해", "김해시"],
    "제주": ["제주", "제주도", "제주특별자치도"],

    "수도권": ["서울", "서울특별시", "경기", "경기도", "인천", "인천광역시"],
    "충청권": [
        "충북", "충청북도",
        "충남", "충청남도",
        "대전", "대전광역시",
        "세종", "세종특별자치시",
    ],
    "전라권": [
        "전북", "전라북도", "전북특별자치도",
        "전남", "전라남도",
        "광주", "광주광역시",
    ],
    "경상권": [
        "경북", "경상북도",
        "경남", "경상남도",
        "부산", "부산광역시",
        "대구", "대구광역시",
        "울산", "울산광역시",
    ],
}

CATEGORY_KEYWORDS = {
    "포장": ["포장", "아스콘", "아스팔트", "콘크리트포장"],
    "배수/측구": ["배수", "배수로", "측구", "수로", "우수", "집수정"],
    "상하수도/관로": ["상하수도", "상수도", "하수도", "관로", "관거", "오수", "맨홀"],
    "도로/농로": ["도로", "농로", "차도", "보도", "인도"],
    "하천/소하천": ["하천", "소하천", "구거", "제방"],
    "옹벽/구조물": ["옹벽", "석축", "블록", "구조물"],
    "재해복구/정비/보수": ["재해복구", "복구", "정비", "보수", "유지보수"],
}

LICENSE_OPTIONS = [
    "토목공사업",
    "토목건축공사업",
    "상하수도설비공사업",
    "지반조성·포장공사업",
    "포장공사업",
    "철근·콘크리트공사업",
    "구조물해체·비계공사업",
    "금속창호·지붕건축물조립공사업",
    "도장·습식·방수·석공사업",
    "조경공사업",
    "조경식재·시설물공사업",
    "시설물유지관리",
    "기타",
]

LICENSE_KEYWORDS = {
    "토목공사업": ["토목", "토목공사업", "토목공사"],
    "토목건축공사업": ["토목건축", "토건", "토목건축공사업"],
    "상하수도설비공사업": ["상하수도", "상수도", "하수도", "관로", "관거", "오수", "우수", "맨홀"],
    "지반조성·포장공사업": ["지반조성", "포장", "아스콘", "아스팔트", "콘크리트포장", "보도포장"],
    "포장공사업": ["포장", "아스콘", "아스팔트", "콘크리트포장", "보도포장"],
    "철근·콘크리트공사업": ["철근", "콘크리트", "철콘", "옹벽", "측구", "수로", "구조물"],
    "구조물해체·비계공사업": ["해체", "철거", "비계"],
    "금속창호·지붕건축물조립공사업": ["금속", "창호", "지붕", "판넬"],
    "도장·습식·방수·석공사업": ["도장", "습식", "방수", "석공", "석축"],
    "조경공사업": ["조경", "식재", "공원"],
    "조경식재·시설물공사업": ["조경", "식재", "시설물", "공원"],
    "시설물유지관리": ["유지관리", "보수", "정비", "보강", "시설물"],
    "기타": [],
}

AMOUNT_KEYS = [
    "presmptPrce",
    "asignBdgtAmt",
    "bssamt",
    "baseAmount",
    "bdgtAmt",
    "cntrctAmt",
    "totPrdprcNum",
    "추정가격",
    "추정금액",
    "기초금액",
    "예정금액",
    "배정예산액",
    "공사예정금액",
    "총공사금액",
]


# =========================================================
# 공통 함수
# =========================================================

def h(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def today_yyyymmddhhmm() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


def future_yyyymmddhhmm(days: int = 30) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y%m%d%H%M")


def parse_date(value):
    if not value:
        return None

    text = str(value).strip()

    patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
        "%Y%m%d",
    ]

    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern)
        except Exception:
            pass

    only_numbers = re.sub(r"[^0-9]", "", text)

    if len(only_numbers) >= 14:
        try:
            return datetime.strptime(only_numbers[:14], "%Y%m%d%H%M%S")
        except Exception:
            pass

    if len(only_numbers) >= 12:
        try:
            return datetime.strptime(only_numbers[:12], "%Y%m%d%H%M")
        except Exception:
            pass

    if len(only_numbers) >= 8:
        try:
            return datetime.strptime(only_numbers[:8], "%Y%m%d")
        except Exception:
            pass

    return None


def parse_money_to_number(value) -> int:
    if value is None:
        return 0

    text = str(value).strip()

    if not text:
        return 0

    if "억" in text:
        numbers = re.sub(r"[^0-9.]", "", text)
        try:
            return int(float(numbers) * 100_000_000)
        except Exception:
            return 0

    numbers = re.sub(r"[^0-9]", "", text)

    if not numbers:
        return 0

    try:
        return int(numbers)
    except Exception:
        return 0


def format_money(amount: int) -> str:
    if not amount:
        return "-"

    if amount >= 100_000_000:
        eok = amount / 100_000_000
        return f"{eok:,.1f}억"

    return f"{amount:,}원"


def get_first(item: dict, keys: list, default: str = "") -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def get_bid_amount(item: dict) -> int:
    amounts = []

    for key in AMOUNT_KEYS:
        value = item.get(key)
        amount = parse_money_to_number(value)
        if amount > 0:
            amounts.append(amount)

    if not amounts:
        return 0

    return max(amounts)


def get_deadline(item: dict) -> str:
    return get_first(
        item,
        [
            "bidClseDt",
            "bidClseDate",
            "bidClseTm",
            "opengDt",
            "rbidOpengDt",
        ],
    )


def get_bid_no(item: dict) -> str:
    return get_first(item, ["bidNtceNo", "bidno", "bidNo", "공고번호"])


def get_bid_ord(item: dict) -> str:
    return get_first(item, ["bidNtceOrd", "bidseq", "bidSeq", "공고차수"], "00")


def get_bid_name(item: dict) -> str:
    return get_first(item, ["bidNtceNm", "bidNm", "공고명"], "제목 없음")


def get_agency(item: dict) -> str:
    return get_first(
        item,
        [
            "dminsttNm",
            "ntceInsttNm",
            "orderInsttNm",
            "realDmndInsttNm",
            "수요기관",
            "공고기관",
        ],
        "-",
    )


def get_region_text(item: dict) -> str:
    return get_first(
        item,
        [
            "prtcptPsblRgnNm",
            "prtcptPsblRgn",
            "bidPrtcptLmtRgnNm",
            "rgnLmtNm",
            "rgnLmt",
            "cnstrtsiteRgnNm",
            "공사지역",
            "참가가능지역",
            "지역제한",
        ],
        "",
    )


def make_search_text(item: dict) -> str:
    parts = []

    important_keys = [
        "bidNtceNm",
        "dminsttNm",
        "ntceInsttNm",
        "orderInsttNm",
        "realDmndInsttNm",
        "prtcptPsblRgnNm",
        "prtcptPsblRgn",
        "bidPrtcptLmtRgnNm",
        "rgnLmtNm",
        "rgnLmt",
        "cnstrtsiteRgnNm",
        "indstrytyNm",
        "lcnsLmtNm",
        "bidPrtcptLmtYn",
    ]

    for key in important_keys:
        value = item.get(key)
        if value:
            parts.append(str(value))

    for value in item.values():
        if value:
            parts.append(str(value))

    return " ".join(parts)


def get_nationwide_reason(item: dict) -> str:
    text = make_search_text(item)
    amount = get_bid_amount(item)

    nationwide_keywords = REGION_KEYWORDS.get("전국", [])

    if any(keyword in text for keyword in nationwide_keywords):
        return "전국/지역제한없음 문구"

    if amount >= NATIONWIDE_AMOUNT_LIMIT:
        return "금액 100억 이상"

    return ""


def match_region(item: dict, region: str) -> bool:
    if not region or region == "전체":
        return True

    region = region.strip()

    if region == "전국":
        return bool(get_nationwide_reason(item))

    keywords = REGION_KEYWORDS.get(region)

    if not keywords:
        return True

    text = make_search_text(item)

    return any(keyword in text for keyword in keywords)


def infer_region_label(item: dict) -> str:
    region_text = get_region_text(item)

    if region_text:
        return region_text

    text = make_search_text(item)

    found = []

    for region in [
        "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산",
        "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
    ]:
        for keyword in REGION_KEYWORDS.get(region, []):
            if keyword in text:
                found.append(region)
                break

    if found:
        return ", ".join(dict.fromkeys(found))

    nationwide_reason = get_nationwide_reason(item)
    if nationwide_reason:
        return "전국"

    return "지역정보 없음"


def infer_category(item: dict) -> str:
    text = make_search_text(item)

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "기타"


def infer_licenses(item: dict) -> list:
    text = make_search_text(item)
    found = []

    for license_name, keywords in LICENSE_KEYWORDS.items():
        if not keywords:
            continue

        if any(keyword in text for keyword in keywords):
            found.append(license_name)

    return found


def get_d_day(deadline_text: str) -> str:
    deadline = parse_date(deadline_text)

    if not deadline:
        return "-"

    now = datetime.now()
    diff_days = (deadline.date() - now.date()).days

    if deadline < now:
        return "마감"

    if diff_days == 0:
        return "D-day"

    return f"D-{diff_days}"


def is_closed(item: dict) -> bool:
    deadline_text = get_deadline(item)
    deadline = parse_date(deadline_text)

    if not deadline:
        return False

    return deadline < datetime.now()


def make_g2b_url(item: dict) -> str:
    direct_url = get_first(
        item,
        [
            "bidNtceUrl",
            "bidNtceDtlUrl",
            "ntceUrl",
            "bidUrl",
        ],
        "",
    )

    if direct_url.startswith("http"):
        return direct_url

    bid_no = get_bid_no(item)
    bid_ord = get_bid_ord(item)

    if not bid_no:
        return "https://www.g2b.go.kr"

    return (
        "https://www.g2b.go.kr:8101/ep/tbid/tbidFwd.do"
        f"?bidno={quote(bid_no)}&bidseq={quote(bid_ord)}"
    )


def normalize_api_items(data) -> list:
    try:
        response = data.get("response", {})
        body = response.get("body", {})
        items = body.get("items", [])

        if isinstance(items, dict):
            item = items.get("item", [])
        else:
            item = items

        if isinstance(item, dict):
            return [item]

        if isinstance(item, list):
            return [x for x in item if isinstance(x, dict)]

    except Exception:
        pass

    return []


def build_api_url(params: dict) -> str:
    key = DATA_GO_KR_SERVICE_KEY

    if not key:
        return ""

    safe_key = key if "%" in key else quote(key, safe="")

    query_parts = [f"serviceKey={safe_key}"]

    for k, v in params.items():
        if v is None or v == "":
            continue
        query_parts.append(f"{quote(str(k))}={quote(str(v))}")

    return G2B_CONSTRUCTION_API_URL + "?" + "&".join(query_parts)


def fetch_nara_bids(
    keyword: str,
    page_no: int = 1,
    num_rows: int = 100,
    days_forward: int = 30,
) -> dict:
    if not DATA_GO_KR_SERVICE_KEY:
        return {
            "ok": False,
            "error": "Render 환경변수 DATA_GO_KR_SERVICE_KEY가 없습니다.",
            "items": [],
            "total_count": 0,
        }

    params = {
        "type": "json",
        "pageNo": page_no,
        "numOfRows": num_rows,
        "inqryDiv": 1,
        "inqryBgnDt": today_yyyymmddhhmm(),
        "inqryEndDt": future_yyyymmddhhmm(days_forward),
        "bidNtceNm": keyword,
    }

    url = build_api_url(params)

    try:
        res = requests.get(url, timeout=20)
        text = res.text

        try:
            data = res.json()
        except Exception:
            return {
                "ok": False,
                "error": "API 응답이 JSON이 아닙니다.",
                "status_code": res.status_code,
                "preview": text[:500],
                "items": [],
                "total_count": 0,
            }

        items = normalize_api_items(data)

        total_count = 0

        try:
            total_count = int(data.get("response", {}).get("body", {}).get("totalCount", 0))
        except Exception:
            total_count = len(items)

        return {
            "ok": True,
            "keyword": keyword,
            "page_no": page_no,
            "num_rows": num_rows,
            "total_count": total_count,
            "items": items,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "items": [],
            "total_count": 0,
        }


def simplify_bid(item: dict, keyword: str = "") -> dict:
    deadline = get_deadline(item)
    amount = get_bid_amount(item)
    licenses = infer_licenses(item)

    return {
        "keyword": keyword,
        "category": infer_category(item),
        "region_label": infer_region_label(item),
        "nationwide_reason": get_nationwide_reason(item),
        "amount": amount,
        "amount_label": format_money(amount),
        "license_label": ", ".join(licenses) if licenses else "-",
        "bid_no": get_bid_no(item),
        "bid_ord": get_bid_ord(item),
        "bid_name": get_bid_name(item),
        "agency": get_agency(item),
        "notice_date": get_first(item, ["bidNtceDt", "공고일시"], "-"),
        "deadline": deadline or "-",
        "d_day": get_d_day(deadline),
        "g2b_url": make_g2b_url(item),
        "raw": item,
    }


def search_bids_by_keywords(
    keywords: list,
    region: str = "전체",
    exclude_closed: bool = True,
    days_forward: int = 30,
    pages_per_keyword: int = 1,
    num_rows: int = 100,
) -> dict:
    all_items = []
    errors = []

    for keyword in keywords:
        for page_no in range(1, pages_per_keyword + 1):
            result = fetch_nara_bids(
                keyword=keyword,
                page_no=page_no,
                num_rows=num_rows,
                days_forward=days_forward,
            )

            if not result.get("ok"):
                errors.append(
                    {
                        "keyword": keyword,
                        "page_no": page_no,
                        "error": result.get("error"),
                        "preview": result.get("preview", ""),
                    }
                )
                continue

            for item in result.get("items", []):
                if exclude_closed and is_closed(item):
                    continue

                if not match_region(item, region):
                    continue

                all_items.append(simplify_bid(item, keyword=keyword))

    deduped = []
    seen = set()

    for bid in all_items:
        key = (
            bid.get("bid_no") or "",
            bid.get("bid_ord") or "",
            bid.get("bid_name") or "",
            bid.get("deadline") or "",
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(bid)

    def sort_key(bid):
        dt = parse_date(bid.get("deadline"))
        if not dt:
            return datetime.max
        return dt

    deduped.sort(key=sort_key)

    return {
        "status": "ok",
        "region": region,
        "exclude_closed": exclude_closed,
        "keywords": keywords,
        "count": len(deduped),
        "errors": errors,
        "bids": deduped,
    }


# =========================================================
# 회사 프로필 저장 / 불러오기
# =========================================================

def default_company_profile() -> dict:
    return {
        "company_name": "주식회사 송원건설",
        "manager_name": "",
        "address": "경상남도 김해시 삼문로19, 1205호",
        "phone": "055-339-4763",
        "fax": "055-339-4764",
        "email": "songwon4763@naver.com",
        "main_region": "경남",
        "possible_regions": ["경남", "부산", "울산", "경북", "전국"],
        "licenses": [],
        "keyword_text": "포장, 배수, 배수로, 상하수도, 관로, 도로, 하천, 소하천, 옹벽, 측구, 맨홀, 농로, 재해복구, 정비, 보수",
        "updated_at": "",
    }


def load_company_profile() -> dict:
    if not os.path.exists(PROFILE_FILE):
        return default_company_profile()

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        base = default_company_profile()
        base.update(data)
        return base

    except Exception:
        return default_company_profile()


def save_company_profile(profile: dict) -> None:
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def split_keywords(keyword_text: str) -> list:
    if not keyword_text:
        return SONGWON_KEYWORDS

    parts = re.split(r"[,，\n/]+", keyword_text)
    keywords = []

    for part in parts:
        text = part.strip()
        if text:
            keywords.append(text)

    return keywords or SONGWON_KEYWORDS


# =========================================================
# HTML 화면 함수
# =========================================================

def render_region_buttons(base_path: str, current_region: str, keyword: str = "") -> str:
    buttons = []

    for region in REGION_BUTTONS:
        active = "active" if region == current_region else ""

        href = f"{base_path}?region={quote(region)}"

        if keyword:
            href += f"&keyword={quote(keyword)}"

        buttons.append(f'<a class="region-btn {active}" href="{href}">{h(region)}</a>')

    return "\n".join(buttons)


def render_bid_table(bids: list) -> str:
    if not bids:
        return """
        <div class="empty">
            조건에 맞는 공고가 없습니다.<br>
            다른 지역을 눌러보거나, 전체 버튼을 눌러보세요.
        </div>
        """

    rows = []

    for idx, bid in enumerate(bids, start=1):
        dday = bid.get("d_day", "-")
        dday_class = "dday"

        if dday == "D-day":
            dday_class += " today"
        elif dday == "마감":
            dday_class += " closed"

        nationwide_reason = bid.get("nationwide_reason") or "-"

        rows.append(
            f"""
            <tr>
                <td class="num">{idx}</td>
                <td><span class="{dday_class}">{h(dday)}</span></td>
                <td class="title">
                    <div class="bid-name">{h(bid.get("bid_name"))}</div>
                    <div class="small">공고번호: {h(bid.get("bid_no"))} / 키워드: {h(bid.get("keyword"))}</div>
                </td>
                <td>{h(bid.get("category"))}</td>
                <td>{h(bid.get("license_label"))}</td>
                <td>{h(bid.get("region_label"))}</td>
                <td>{h(bid.get("amount_label"))}</td>
                <td>{h(nationwide_reason)}</td>
                <td>{h(bid.get("agency"))}</td>
                <td>{h(bid.get("deadline"))}</td>
                <td>
                    <a class="link-btn" href="{h(bid.get("g2b_url"))}" target="_blank" rel="noopener">
                        원문 보기
                    </a>
                </td>
            </tr>
            """
        )

    return f"""
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>No</th>
                    <th>D-day</th>
                    <th>공고명</th>
                    <th>분류</th>
                    <th>면허 추정</th>
                    <th>지역</th>
                    <th>금액</th>
                    <th>전국 사유</th>
                    <th>기관</th>
                    <th>마감일</th>
                    <th>나라장터</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """


def page_layout(title: str, subtitle: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{h(title)}</title>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", Arial, sans-serif;
                background: #f5f6f8;
                color: #202124;
            }}

            header {{
                background: #123;
                color: white;
                padding: 26px 22px;
            }}

            header h1 {{
                margin: 0 0 8px;
                font-size: 26px;
            }}

            header p {{
                margin: 0;
                opacity: 0.9;
                line-height: 1.5;
            }}

            main {{
                max-width: 1600px;
                margin: 0 auto;
                padding: 20px;
            }}

            .card {{
                background: white;
                border-radius: 14px;
                padding: 18px;
                margin-bottom: 16px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            }}

            .menu {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 12px;
            }}

            .region-btn,
            .top-btn,
            .link-btn,
            button {{
                display: inline-block;
                border: 1px solid #d0d7de;
                background: #ffffff;
                color: #123;
                padding: 9px 12px;
                border-radius: 999px;
                text-decoration: none;
                font-size: 14px;
                cursor: pointer;
            }}

            .region-btn.active {{
                background: #123;
                color: white;
                border-color: #123;
                font-weight: 700;
            }}

            .top-btn {{
                border-radius: 10px;
                background: #eef4ff;
            }}

            .search-form {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-top: 12px;
            }}

            input[type="text"],
            input[type="email"],
            textarea,
            select {{
                width: 100%;
                padding: 11px 12px;
                border: 1px solid #d0d7de;
                border-radius: 10px;
                font-size: 15px;
                font-family: inherit;
            }}

            textarea {{
                min-height: 90px;
                resize: vertical;
            }}

            button {{
                background: #123;
                color: white;
                border-color: #123;
                border-radius: 10px;
                padding: 11px 16px;
            }}

            .summary {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                align-items: center;
            }}

            .badge {{
                background: #eef4ff;
                color: #123;
                border: 1px solid #d9e7ff;
                border-radius: 999px;
                padding: 8px 12px;
                font-size: 14px;
            }}

            .table-wrap {{
                width: 100%;
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 1450px;
            }}

            th,
            td {{
                border-bottom: 1px solid #eceff3;
                padding: 12px 10px;
                vertical-align: top;
                text-align: left;
                font-size: 14px;
            }}

            th {{
                background: #f8fafc;
                font-weight: 700;
                position: sticky;
                top: 0;
            }}

            .num {{
                width: 55px;
                color: #667085;
            }}

            .title {{
                min-width: 340px;
            }}

            .bid-name {{
                font-weight: 700;
                margin-bottom: 5px;
                line-height: 1.35;
            }}

            .small {{
                color: #667085;
                font-size: 12px;
                line-height: 1.4;
            }}

            .dday {{
                display: inline-block;
                min-width: 56px;
                text-align: center;
                padding: 6px 8px;
                border-radius: 999px;
                background: #fff4e5;
                color: #9a5b00;
                font-weight: 700;
            }}

            .dday.today {{
                background: #ffe8e8;
                color: #b42318;
            }}

            .dday.closed {{
                background: #e5e7eb;
                color: #6b7280;
            }}

            .link-btn {{
                white-space: nowrap;
                border-radius: 8px;
                background: #f6f8fa;
            }}

            .empty {{
                padding: 30px;
                text-align: center;
                background: #f8fafc;
                border: 1px dashed #cbd5e1;
                border-radius: 12px;
                color: #475467;
                line-height: 1.7;
            }}

            .notice {{
                line-height: 1.7;
                color: #475467;
                font-size: 14px;
            }}

            .error {{
                background: #fff1f3;
                border: 1px solid #ffd6de;
                color: #b42318;
                padding: 12px;
                border-radius: 10px;
                white-space: pre-wrap;
            }}

            .form-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
            }}

            .form-row {{
                margin-bottom: 14px;
            }}

            .form-row label {{
                display: block;
                font-weight: 700;
                margin-bottom: 7px;
            }}

            .check-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
            }}

            .check-item {{
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 10px;
                background: #fafafa;
                font-size: 14px;
            }}

            .check-item input {{
                margin-right: 6px;
            }}

            .profile-box {{
                line-height: 1.8;
                color: #344054;
            }}

            .profile-box strong {{
                color: #111827;
            }}

            @media (max-width: 800px) {{
                .form-grid {{
                    grid-template-columns: 1fr;
                }}

                .check-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>{h(title)}</h1>
            <p>{h(subtitle)}</p>
        </header>

        <main>
            {body}
        </main>
    </body>
    </html>
    """


def render_checkbox_group(name: str, options: list, selected: list) -> str:
    html_parts = []

    for option in options:
        checked = "checked" if option in selected else ""
        html_parts.append(
            f"""
            <label class="check-item">
                <input type="checkbox" name="{h(name)}" value="{h(option)}" {checked}>
                {h(option)}
            </label>
            """
        )

    return f'<div class="check-grid">{"".join(html_parts)}</div>'


# =========================================================
# 라우트
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gongsa-bid",
        "version": "company-profile-1.0.0",
        "has_DATA_GO_KR_SERVICE_KEY": bool(DATA_GO_KR_SERVICE_KEY),
    }


@app.get("/routes")
def routes():
    return {
        "routes": [
            "/",
            "/health",
            "/routes",
            "/company/profile",
            "/company/profile-data",
            "/bids/nara?keyword=포장",
            "/bids/nara-page?keyword=포장",
            "/bids/songwon-test",
            "/bids/songwon-page",
            "/bids/songwon-page?region=전국",
            "/bids/songwon-page?region=경남",
        ]
    }


@app.get("/", response_class=HTMLResponse)
def home():
    profile = load_company_profile()

    body = f"""
    <div class="card">
        <h2>공사입찰 공고 검색</h2>
        <p class="notice">
            송원건설 주력 키워드로 나라장터 공사 공고를 검색합니다.<br>
            이번 버전은 회사 프로필 등록 화면을 추가했습니다.
        </p>

        <div class="menu">
            <a class="top-btn" href="/bids/songwon-page">전체 공고 보기</a>
            <a class="top-btn" href="/bids/songwon-page?region=전국">전국 공고 보기</a>
            <a class="top-btn" href="/bids/songwon-page?region=경남">경남 공고 보기</a>
            <a class="top-btn" href="/company/profile">회사 프로필 등록</a>
            <a class="top-btn" href="/company/profile-data" target="_blank">프로필 JSON 확인</a>
        </div>
    </div>

    <div class="card">
        <h3>현재 저장된 회사 프로필</h3>
        <div class="profile-box">
            <strong>회사명:</strong> {h(profile.get("company_name"))}<br>
            <strong>주소:</strong> {h(profile.get("address"))}<br>
            <strong>전화:</strong> {h(profile.get("phone"))}<br>
            <strong>팩스:</strong> {h(profile.get("fax"))}<br>
            <strong>이메일:</strong> {h(profile.get("email"))}<br>
            <strong>주 활동지역:</strong> {h(profile.get("main_region"))}<br>
            <strong>가능지역:</strong> {h(", ".join(profile.get("possible_regions", [])))}<br>
            <strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "아직 선택 안 함")}<br>
            <strong>주력 키워드:</strong> {h(profile.get("keyword_text"))}
        </div>
    </div>
    """

    return page_layout(
        "gongsa-bid",
        "건설회사 전용 나라장터 공고 웹플랫폼",
        body,
    )


@app.get("/company/profile", response_class=HTMLResponse)
def company_profile_page():
    profile = load_company_profile()

    possible_region_options = [
        "전국", "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종",
        "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
        "수도권", "충청권", "전라권", "경상권",
    ]

    body = f"""
    <div class="card">
        <div class="summary">
            <span class="badge">회사 프로필 등록</span>
            <span class="badge">로그인 기능 전 임시 저장 방식</span>
            <a class="top-btn" href="/">첫 화면</a>
            <a class="top-btn" href="/bids/songwon-page">전체 공고 보기</a>
        </div>
    </div>

    <form action="/company/profile-save" method="get">
        <div class="card">
            <h3>기본 정보</h3>

            <div class="form-grid">
                <div class="form-row">
                    <label>회사명</label>
                    <input type="text" name="company_name" value="{h(profile.get("company_name"))}">
                </div>

                <div class="form-row">
                    <label>담당자명</label>
                    <input type="text" name="manager_name" value="{h(profile.get("manager_name"))}" placeholder="예: 홍길동">
                </div>

                <div class="form-row">
                    <label>전화번호</label>
                    <input type="text" name="phone" value="{h(profile.get("phone"))}">
                </div>

                <div class="form-row">
                    <label>팩스</label>
                    <input type="text" name="fax" value="{h(profile.get("fax"))}">
                </div>

                <div class="form-row">
                    <label>이메일</label>
                    <input type="email" name="email" value="{h(profile.get("email"))}">
                </div>

                <div class="form-row">
                    <label>주 활동지역</label>
                    <select name="main_region">
                        {''.join([f'<option value="{h(region)}" {"selected" if region == profile.get("main_region") else ""}>{h(region)}</option>' for region in possible_region_options])}
                    </select>
                </div>
            </div>

            <div class="form-row">
                <label>주소</label>
                <input type="text" name="address" value="{h(profile.get("address"))}">
            </div>
        </div>

        <div class="card">
            <h3>입찰 가능지역</h3>
            <p class="notice">
                회사가 실제로 입찰 검토할 지역을 체크하세요.<br>
                예: 경남 업체라도 부산, 울산, 경북, 전국 공고까지 같이 볼 수 있습니다.
            </p>
            {render_checkbox_group("possible_regions", possible_region_options, profile.get("possible_regions", []))}
        </div>

        <div class="card">
            <h3>보유 건설업 면허</h3>
            <p class="notice">
                나중에 이 면허를 기준으로 “내 회사 맞춤 공고”만 자동으로 보여주게 만들 예정입니다.
            </p>
            {render_checkbox_group("licenses", LICENSE_OPTIONS, profile.get("licenses", []))}
        </div>

        <div class="card">
            <h3>주력 검색 키워드</h3>
            <p class="notice">
                쉼표로 구분해서 입력하세요. 비워두면 기본 송원 키워드를 사용합니다.
            </p>

            <div class="form-row">
                <label>키워드</label>
                <textarea name="keyword_text">{h(profile.get("keyword_text"))}</textarea>
            </div>

            <button type="submit">회사 프로필 저장</button>
            <a class="top-btn" href="/">취소하고 첫 화면</a>
        </div>
    </form>
    """

    return page_layout(
        "회사 프로필 등록",
        "회사 정보와 보유 면허를 저장하는 화면입니다",
        body,
    )


@app.get("/company/profile-save", response_class=HTMLResponse)
def company_profile_save(
    company_name: str = Query(""),
    manager_name: str = Query(""),
    address: str = Query(""),
    phone: str = Query(""),
    fax: str = Query(""),
    email: str = Query(""),
    main_region: str = Query("경남"),
    possible_regions: List[str] = Query(default=[]),
    licenses: List[str] = Query(default=[]),
    keyword_text: str = Query(""),
):
    profile = {
        "company_name": company_name.strip(),
        "manager_name": manager_name.strip(),
        "address": address.strip(),
        "phone": phone.strip(),
        "fax": fax.strip(),
        "email": email.strip(),
        "main_region": main_region.strip(),
        "possible_regions": possible_regions,
        "licenses": licenses,
        "keyword_text": keyword_text.strip(),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_company_profile(profile)

    body = f"""
    <div class="card">
        <h2>회사 프로필 저장 완료</h2>
        <p class="notice">
            회사 프로필이 저장되었습니다.<br>
            다음 단계에서 이 프로필의 보유 면허와 가능지역을 기준으로 맞춤 공고를 보여주도록 연결하면 됩니다.
        </p>

        <div class="profile-box">
            <strong>회사명:</strong> {h(profile.get("company_name"))}<br>
            <strong>담당자:</strong> {h(profile.get("manager_name"))}<br>
            <strong>주소:</strong> {h(profile.get("address"))}<br>
            <strong>전화:</strong> {h(profile.get("phone"))}<br>
            <strong>팩스:</strong> {h(profile.get("fax"))}<br>
            <strong>이메일:</strong> {h(profile.get("email"))}<br>
            <strong>주 활동지역:</strong> {h(profile.get("main_region"))}<br>
            <strong>가능지역:</strong> {h(", ".join(profile.get("possible_regions", [])))}<br>
            <strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "선택 안 함")}<br>
            <strong>주력 키워드:</strong> {h(profile.get("keyword_text"))}<br>
            <strong>저장시간:</strong> {h(profile.get("updated_at"))}
        </div>

        <div class="menu">
            <a class="top-btn" href="/">첫 화면</a>
            <a class="top-btn" href="/company/profile">다시 수정하기</a>
            <a class="top-btn" href="/company/profile-data" target="_blank">JSON 확인</a>
            <a class="top-btn" href="/bids/songwon-page">공고 보기</a>
        </div>
    </div>
    """

    return page_layout(
        "회사 프로필 저장 완료",
        "저장된 회사 정보를 확인하세요",
        body,
    )


@app.get("/company/profile-data")
def company_profile_data():
    return JSONResponse(load_company_profile())


@app.get("/bids/nara")
def nara_json(
    keyword: str = Query("포장", description="검색 키워드"),
    region: str = Query("전체", description="지역 필터"),
    days_forward: int = Query(30, description="오늘부터 며칠 뒤까지 검색할지"),
):
    result = search_bids_by_keywords(
        keywords=[keyword],
        region=region,
        exclude_closed=True,
        days_forward=days_forward,
        pages_per_keyword=1,
        num_rows=100,
    )

    return JSONResponse(result)


@app.get("/bids/nara-page", response_class=HTMLResponse)
def nara_page(
    keyword: str = Query("포장"),
    region: str = Query("전체"),
    days_forward: int = Query(30),
):
    result = search_bids_by_keywords(
        keywords=[keyword],
        region=region,
        exclude_closed=True,
        days_forward=days_forward,
        pages_per_keyword=1,
        num_rows=100,
    )

    region_buttons = render_region_buttons("/bids/nara-page", region, keyword=keyword)

    error_html = ""

    if result.get("errors"):
        error_html = f"""
        <div class="card">
            <div class="error">{h(json.dumps(result.get("errors"), ensure_ascii=False, indent=2))}</div>
        </div>
        """

    body = f"""
    <div class="card">
        <div class="summary">
            <span class="badge">검색어: {h(keyword)}</span>
            <span class="badge">선택 지역: {h(region)}</span>
            <span class="badge">공고 수: {h(result.get("count"))}개</span>
            <a class="top-btn" href="/">첫 화면</a>
            <a class="top-btn" href="/bids/songwon-page">송원 전체검색</a>
        </div>

        <form class="search-form" action="/bids/nara-page" method="get">
            <input type="text" name="keyword" value="{h(keyword)}" placeholder="공고명 검색 예: 포장, 배수로, 도로">
            <input type="hidden" name="region" value="{h(region)}">
            <button type="submit">검색</button>
        </form>
    </div>

    <div class="card">
        <h3>지역별 보기</h3>
        <div class="menu">
            {region_buttons}
        </div>
    </div>

    {error_html}

    <div class="card">
        {render_bid_table(result.get("bids", []))}
    </div>
    """

    return page_layout(
        f"개별 검색 - {keyword}",
        f"지역: {region} / 마감 지난 공고 제외 / D-day 표시",
        body,
    )


@app.get("/bids/songwon-test")
def songwon_test(
    region: str = Query("전체"),
    days_forward: int = Query(30),
):
    profile = load_company_profile()
    keyword_text = profile.get("keyword_text", "")
    keywords = split_keywords(keyword_text)

    return JSONResponse(
        search_bids_by_keywords(
            keywords=keywords,
            region=region,
            exclude_closed=True,
            days_forward=days_forward,
            pages_per_keyword=1,
            num_rows=100,
        )
    )


@app.get("/bids/songwon-page", response_class=HTMLResponse)
def songwon_page(
    region: str = Query("전체"),
    keyword: str = Query("", description="비워두면 회사 프로필 키워드 전체 검색"),
    days_forward: int = Query(30),
):
    profile = load_company_profile()

    if keyword.strip():
        keywords = [keyword.strip()]
        keyword_label = keyword.strip()
    else:
        keywords = split_keywords(profile.get("keyword_text", ""))
        keyword_label = "회사 프로필 주력 키워드"

    result = search_bids_by_keywords(
        keywords=keywords,
        region=region,
        exclude_closed=True,
        days_forward=days_forward,
        pages_per_keyword=1,
        num_rows=100,
    )

    region_buttons = render_region_buttons("/bids/songwon-page", region, keyword=keyword)

    error_html = ""

    if result.get("errors"):
        error_html = f"""
        <div class="card">
            <h3>API 오류</h3>
            <div class="error">{h(json.dumps(result.get("errors"), ensure_ascii=False, indent=2))}</div>
        </div>
        """

    body = f"""
    <div class="card">
        <div class="summary">
            <span class="badge">검색 범위: {h(keyword_label)}</span>
            <span class="badge">선택 지역: {h(region)}</span>
            <span class="badge">공고 수: {h(result.get("count"))}개</span>
            <span class="badge">마감 지난 공고 제외</span>
            <a class="top-btn" href="/">첫 화면</a>
            <a class="top-btn" href="/company/profile">회사 프로필</a>
            <a class="top-btn" href="/bids/songwon-test?region={quote(region)}" target="_blank">JSON 보기</a>
        </div>

        <form class="search-form" action="/bids/songwon-page" method="get">
            <input type="text" name="keyword" value="{h(keyword)}" placeholder="공고명 검색 예: 포장, 배수로, 도로 / 비우면 회사 프로필 키워드">
            <input type="hidden" name="region" value="{h(region)}">
            <button type="submit">공고명 검색</button>
            <a class="top-btn" href="/bids/songwon-page?region={quote(region)}">검색 초기화</a>
        </form>
    </div>

    <div class="card">
        <h3>지역별 보기</h3>
        <p class="notice">
            전체는 지역 상관없이 모든 공고를 보여줍니다.<br>
            전국은 지역제한 없음 문구가 있거나 금액이 100억 이상인 공고를 보여줍니다.<br>
            회사 프로필 화면에서 주력 키워드와 면허를 등록할 수 있습니다.
        </p>

        <div class="menu">
            {region_buttons}
        </div>
    </div>

    {error_html}

    <div class="card">
        {render_bid_table(result.get("bids", []))}
    </div>
    """

    return page_layout(
        "송원건설 전체 공고 검색",
        "회사 프로필 등록 화면 추가 버전",
        body,
    )
