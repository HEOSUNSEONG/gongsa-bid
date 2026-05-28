# -*- coding: utf-8 -*-
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

app = FastAPI(title="gongsa-bid", version="profile-worktype-siping-1.0.0")

DATA_GO_KR_SERVICE_KEY = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip()
G2B_CONSTRUCTION_API_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"
PROFILE_FILE = "company_profile.json"
NATIONWIDE_AMOUNT_LIMIT = 10_000_000_000

SONGWON_KEYWORDS = ["포장", "배수", "배수로", "상하수도", "관로", "도로", "하천", "소하천", "옹벽", "측구", "맨홀", "농로", "재해복구", "정비", "보수"]

REGION_BUTTONS = [
    "전체", "전국", "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "수도권", "충청권", "전라권", "경상권"
]

PROFILE_REGION_OPTIONS = [
    "전국",

    # 시·도 전체
    "서울특별시/전체",
    "경기도/전체",
    "인천광역시/전체",
    "부산광역시/전체",
    "대구광역시/전체",
    "광주광역시/전체",
    "대전광역시/전체",
    "울산광역시/전체",
    "세종특별자치시/전체",
    "강원특별자치도/전체",
    "충청북도/전체",
    "충청남도/전체",
    "전북특별자치도/전체",
    "전라남도/전체",
    "경상북도/전체",
    "경상남도/전체",
    "제주특별자치도/전체",

    # 경기도
    "경기도/수원시", "경기도/성남시", "경기도/의정부시", "경기도/안양시",
    "경기도/부천시", "경기도/광명시", "경기도/평택시", "경기도/동두천시",
    "경기도/안산시", "경기도/고양시", "경기도/과천시", "경기도/구리시",
    "경기도/남양주시", "경기도/오산시", "경기도/시흥시", "경기도/군포시",
    "경기도/의왕시", "경기도/하남시", "경기도/용인시", "경기도/파주시",
    "경기도/이천시", "경기도/안성시", "경기도/김포시", "경기도/화성시",
    "경기도/광주시", "경기도/양주시", "경기도/포천시", "경기도/여주시",
    "경기도/연천군", "경기도/가평군", "경기도/양평군",

    # 인천광역시 군 지역
    "인천광역시/강화군", "인천광역시/옹진군",

    # 부산광역시 군 지역
    "부산광역시/기장군",

    # 대구광역시 군 지역
    "대구광역시/달성군", "대구광역시/군위군",

    # 울산광역시 군 지역
    "울산광역시/울주군",

    # 세종
    "세종특별자치시/세종시",

    # 강원특별자치도
    "강원특별자치도/춘천시", "강원특별자치도/원주시", "강원특별자치도/강릉시",
    "강원특별자치도/동해시", "강원특별자치도/태백시", "강원특별자치도/속초시",
    "강원특별자치도/삼척시", "강원특별자치도/홍천군", "강원특별자치도/횡성군",
    "강원특별자치도/영월군", "강원특별자치도/평창군", "강원특별자치도/정선군",
    "강원특별자치도/철원군", "강원특별자치도/화천군", "강원특별자치도/양구군",
    "강원특별자치도/인제군", "강원특별자치도/고성군", "강원특별자치도/양양군",

    # 충청북도
    "충청북도/청주시", "충청북도/충주시", "충청북도/제천시",
    "충청북도/보은군", "충청북도/옥천군", "충청북도/영동군",
    "충청북도/증평군", "충청북도/진천군", "충청북도/괴산군",
    "충청북도/음성군", "충청북도/단양군",

    # 충청남도
    "충청남도/천안시", "충청남도/공주시", "충청남도/보령시",
    "충청남도/아산시", "충청남도/서산시", "충청남도/논산시",
    "충청남도/계룡시", "충청남도/당진시", "충청남도/금산군",
    "충청남도/부여군", "충청남도/서천군", "충청남도/청양군",
    "충청남도/홍성군", "충청남도/예산군", "충청남도/태안군",

    # 전북특별자치도
    "전북특별자치도/전주시", "전북특별자치도/군산시", "전북특별자치도/익산시",
    "전북특별자치도/정읍시", "전북특별자치도/남원시", "전북특별자치도/김제시",
    "전북특별자치도/완주군", "전북특별자치도/진안군", "전북특별자치도/무주군",
    "전북특별자치도/장수군", "전북특별자치도/임실군", "전북특별자치도/순창군",
    "전북특별자치도/고창군", "전북특별자치도/부안군",

    # 전라남도
    "전라남도/목포시", "전라남도/여수시", "전라남도/순천시",
    "전라남도/나주시", "전라남도/광양시", "전라남도/담양군",
    "전라남도/곡성군", "전라남도/구례군", "전라남도/고흥군",
    "전라남도/보성군", "전라남도/화순군", "전라남도/장흥군",
    "전라남도/강진군", "전라남도/해남군", "전라남도/영암군",
    "전라남도/무안군", "전라남도/함평군", "전라남도/영광군",
    "전라남도/장성군", "전라남도/완도군", "전라남도/진도군",
    "전라남도/신안군",

    # 경상북도
    "경상북도/포항시", "경상북도/경주시", "경상북도/김천시",
    "경상북도/안동시", "경상북도/구미시", "경상북도/영주시",
    "경상북도/영천시", "경상북도/상주시", "경상북도/문경시",
    "경상북도/경산시", "경상북도/의성군", "경상북도/청송군",
    "경상북도/영양군", "경상북도/영덕군", "경상북도/청도군",
    "경상북도/고령군", "경상북도/성주군", "경상북도/칠곡군",
    "경상북도/예천군", "경상북도/봉화군", "경상북도/울진군",
    "경상북도/울릉군",

    # 경상남도
    "경상남도/창원시", "경상남도/진주시", "경상남도/통영시",
    "경상남도/사천시", "경상남도/김해시", "경상남도/밀양시",
    "경상남도/거제시", "경상남도/양산시", "경상남도/의령군",
    "경상남도/함안군", "경상남도/창녕군", "경상남도/고성군",
    "경상남도/남해군", "경상남도/하동군", "경상남도/산청군",
    "경상남도/함양군", "경상남도/거창군", "경상남도/합천군",

    # 제주특별자치도
    "제주특별자치도/제주시", "제주특별자치도/서귀포시",

    # 권역
    "수도권",
    "충청권",
    "전라권",
    "경상권",
]

REGION_KEYWORDS = {
    "전국": ["전국", "전지역", "전 지역", "지역제한없음", "지역 제한 없음", "제한없음", "제한 없음"],
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
    "경남": ["경남", "경상남도", "김해", "김해시", "창녕", "창녕군"],
    "제주": ["제주", "제주도", "제주특별자치도"],
    "수도권": ["서울", "서울특별시", "경기", "경기도", "인천", "인천광역시"],
    "충청권": ["충북", "충청북도", "충남", "충청남도", "대전", "대전광역시", "세종", "세종특별자치시"],
    "전라권": ["전북", "전라북도", "전북특별자치도", "전남", "전라남도", "광주", "광주광역시"],
    "경상권": ["경북", "경상북도", "경남", "경상남도", "부산", "부산광역시", "대구", "대구광역시", "울산", "울산광역시"],
}

CATEGORY_KEYWORDS = {
    "포장": ["포장", "아스콘", "아스팔트", "콘크리트포장"],
    "배수/측구": ["배수", "배수로", "측구", "수로", "우수", "집수정"],
    "상하수도/관로": ["상하수도", "상수도", "하수도", "관로", "관거", "오수", "맨홀"],
    "도로/농로": ["도로", "농로", "차도", "보도", "인도"],
    "하천/소하천": ["하천", "소하천", "구거", "제방"],
    "옹벽/구조물": ["옹벽", "석축", "블록", "구조물"],
    "재해복구/정비/보수": ["재해복구", "복구", "정비", "보수", "유지보수"],
    "자재납품": ["납품", "구매", "자재", "관급자재", "물품", "제조", "구입"],
}

GENERAL_CONSTRUCTION_LICENSE_OPTIONS = ["토목공사업", "건축공사업", "토목건축공사업", "산업·환경설비공사업", "조경공사업"]
SPECIALTY_CONSTRUCTION_LICENSE_OPTIONS = [
    "지반조성·포장공사업", "실내건축공사업", "금속·창호·지붕·건축물조립공사업", "도장·습식·방수·석공사업", "조경식재·시설물공사업", "철근·콘크리트공사업", "구조물해체·비계공사업", "상·하수도설비공사업", "철도·궤도공사업", "철강구조물공사업", "수중·준설공사업", "승강기·삭도공사업", "기계설비·가스공사업", "가스·난방공사업",
    "토공사", "포장공사", "보링·그라우팅·파일공사", "목재창호·목재구조물공사", "금속구조물공사", "창호공사", "지붕판금·건축물조립공사", "도장공사", "습식·방수공사", "석공사", "조경식재공사", "조경시설물설치공사", "철근·콘크리트공사", "구조물해체공사", "비계공사", "상수도설비공사", "하수도설비공사", "철도·궤도공사", "철강구조물공사", "수중공사", "준설공사", "승강기설치공사", "삭도설치공사", "기계설비공사", "가스시설공사", "난방공사",
]
LICENSE_OPTIONS = GENERAL_CONSTRUCTION_LICENSE_OPTIONS + SPECIALTY_CONSTRUCTION_LICENSE_OPTIONS

LICENSE_KEYWORDS = {
    "토목공사업": ["토목", "도로", "하천", "교량", "상하수도", "농로", "구거"],
    "건축공사업": ["건축", "신축", "증축", "리모델링", "보수공사"],
    "토목건축공사업": ["토목건축", "토건", "토목", "건축"],
    "산업·환경설비공사업": ["산업설비", "환경설비", "폐수", "처리장", "플랜트"],
    "조경공사업": ["조경", "공원", "녹지", "식재"],
    "지반조성·포장공사업": ["지반조성", "포장", "아스콘", "아스팔트", "콘크리트포장", "보도포장", "토공", "보링", "그라우팅", "파일"],
    "철근·콘크리트공사업": ["철근", "콘크리트", "철콘", "옹벽", "측구", "수로", "구조물"],
    "상·하수도설비공사업": ["상하수도", "상수도", "하수도", "관로", "관거", "오수", "우수", "맨홀", "배수"],
    "구조물해체·비계공사업": ["해체", "철거", "비계"],
    "포장공사": ["포장", "아스콘", "아스팔트", "콘크리트포장", "보도포장"],
    "토공사": ["토공", "터파기", "성토", "절토", "흙막이"],
    "상수도설비공사": ["상수도", "상수관", "급수"],
    "하수도설비공사": ["하수도", "하수관", "오수", "우수", "관거"],
}


WORK_TYPE_OPTIONS = [
    # 토목 공종
    "토공",
    "흙막이",
    "비탈면보강",
    "보링·그라우팅",
    "파일공",
    "포장공",
    "아스콘포장",
    "콘크리트포장",
    "보도블록포장",
    "도로공",
    "농로공",
    "교량공",
    "터널공",
    "하천공",
    "소하천정비",
    "구거정비",
    "제방공",
    "호안공",
    "배수공",
    "배수로",
    "측구",
    "수로관",
    "집수정",
    "우수관로",
    "오수관로",
    "상수도관로",
    "하수도관로",
    "맨홀",
    "옹벽",
    "석축",
    "블록쌓기",
    "철근콘크리트구조물",
    "암거",
    "박스 culvert",
    "재해복구",
    "유지보수",
    "준설",
    "수중공",
    "철도·궤도",
    "도로안전시설",
    "가드레일",
    "휀스",
    "낙석방지",
    "방음벽",

    # 건축 공종
    "건축공",
    "신축",
    "증축",
    "대수선",
    "리모델링",
    "실내건축",
    "내장공",
    "목공",
    "창호공",
    "유리공",
    "금속공",
    "지붕공",
    "판금공",
    "철골공",
    "도장공",
    "방수공",
    "미장공",
    "타일공",
    "석공",
    "조적공",
    "철거공",
    "구조물해체",
    "비계공",
    "단열공",
    "수장공",

    # 설비 공종
    "기계설비",
    "냉난방",
    "공조",
    "위생설비",
    "소방설비",
    "가스시설",
    "난방공",
    "펌프설비",
    "배관공",

    # 조경 공종
    "조경공",
    "조경식재",
    "조경시설물",
    "공원시설",
    "잔디식재",
    "수목식재",

    # 전기·통신·기타 공종
    "전기공",
    "통신공",
    "CCTV",
    "정보통신",
    "태양광",
    "승강기",
    "삭도",
    "폐기물처리",
    "산업·환경설비",
]

WORK_TYPE_KEYWORDS = {
    "토공": ["토공", "터파기", "성토", "절토", "흙쌓기", "흙깎기"],
    "흙막이": ["흙막이", "가시설"],
    "비탈면보강": ["비탈면", "사면", "법면", "낙석"],
    "보링·그라우팅": ["보링", "그라우팅"],
    "파일공": ["파일", "말뚝"],
    "포장공": ["포장"],
    "아스콘포장": ["아스콘", "아스팔트"],
    "콘크리트포장": ["콘크리트포장"],
    "보도블록포장": ["보도블록", "보도 블록", "인도포장"],
    "도로공": ["도로", "차도", "보도", "인도"],
    "농로공": ["농로"],
    "교량공": ["교량", "교량보수"],
    "터널공": ["터널"],
    "하천공": ["하천"],
    "소하천정비": ["소하천"],
    "구거정비": ["구거"],
    "제방공": ["제방"],
    "호안공": ["호안"],
    "배수공": ["배수"],
    "배수로": ["배수로"],
    "측구": ["측구"],
    "수로관": ["수로관", "플륨관", "벤치플륨"],
    "집수정": ["집수정"],
    "우수관로": ["우수", "우수관"],
    "오수관로": ["오수", "오수관"],
    "상수도관로": ["상수도", "상수관"],
    "하수도관로": ["하수도", "하수관", "관거"],
    "맨홀": ["맨홀"],
    "옹벽": ["옹벽"],
    "석축": ["석축"],
    "블록쌓기": ["블록쌓기", "축조블록", "옹벽블록"],
    "철근콘크리트구조물": ["철근", "콘크리트", "철콘", "구조물"],
    "암거": ["암거"],
    "박스 culvert": ["박스", "BOX", "culvert", "컬버트"],
    "재해복구": ["재해복구", "수해복구", "복구"],
    "유지보수": ["유지보수", "보수", "정비"],
    "준설": ["준설"],
    "수중공": ["수중"],
    "철도·궤도": ["철도", "궤도"],
    "도로안전시설": ["도로안전", "교통안전시설"],
    "가드레일": ["가드레일"],
    "휀스": ["휀스", "펜스", "울타리"],
    "낙석방지": ["낙석"],
    "방음벽": ["방음벽"],

    "건축공": ["건축"],
    "신축": ["신축"],
    "증축": ["증축"],
    "대수선": ["대수선"],
    "리모델링": ["리모델링"],
    "실내건축": ["실내건축", "인테리어"],
    "내장공": ["내장"],
    "목공": ["목공", "목재"],
    "창호공": ["창호", "샷시"],
    "유리공": ["유리"],
    "금속공": ["금속"],
    "지붕공": ["지붕"],
    "판금공": ["판금"],
    "철골공": ["철골"],
    "도장공": ["도장", "페인트"],
    "방수공": ["방수"],
    "미장공": ["미장"],
    "타일공": ["타일"],
    "석공": ["석공", "화강석"],
    "조적공": ["조적", "벽돌"],
    "철거공": ["철거"],
    "구조물해체": ["구조물해체", "해체"],
    "비계공": ["비계"],
    "단열공": ["단열"],
    "수장공": ["수장"],

    "기계설비": ["기계설비"],
    "냉난방": ["냉난방"],
    "공조": ["공조"],
    "위생설비": ["위생설비"],
    "소방설비": ["소방"],
    "가스시설": ["가스시설", "가스"],
    "난방공": ["난방"],
    "펌프설비": ["펌프"],
    "배관공": ["배관"],

    "조경공": ["조경"],
    "조경식재": ["식재", "수목"],
    "조경시설물": ["조경시설물", "공원시설"],
    "공원시설": ["공원"],
    "잔디식재": ["잔디"],
    "수목식재": ["수목", "나무"],

    "전기공": ["전기"],
    "통신공": ["통신"],
    "CCTV": ["CCTV"],
    "정보통신": ["정보통신"],
    "태양광": ["태양광"],
    "승강기": ["승강기", "엘리베이터"],
    "삭도": ["삭도"],
    "폐기물처리": ["폐기물"],
    "산업·환경설비": ["산업설비", "환경설비", "폐수", "처리장"],
}


MATERIAL_SUPPLY_OPTIONS = ["아스콘", "레미콘", "콘크리트", "시멘트", "모래", "쇄석", "골재", "혼합골재", "보조기층재", "순환골재", "흄관", "VR관", "PE관", "PVC관", "이중벽관", "파형강관", "스틸그레이팅", "맨홀뚜껑", "콘크리트맨홀", "집수정", "측구수로관", "U형측구", "벤치플륨관", "플륨관", "경계석", "보차도경계석", "도로경계석", "화강석", "보도블록", "투수블록", "점자블록", "식생블록", "옹벽블록", "축조블록", "콘크리트블록", "철근", "H빔", "철강재", "와이어메쉬", "거푸집", "동바리", "가드레일", "휀스", "낙석방지망", "방음벽", "도로표지판", "안전표지판", "차선도색재", "방수재", "도막재", "에폭시", "페인트", "조경석", "자연석", "식재", "잔디", "토목섬유", "부직포", "배수판", "기타 건설자재"]
MATERIAL_KEYWORDS = {name: [name] for name in MATERIAL_SUPPLY_OPTIONS}
MATERIAL_KEYWORDS.update({"아스콘": ["아스콘", "아스팔트콘크리트"], "레미콘": ["레미콘", "레디믹스트"], "스틸그레이팅": ["스틸그레이팅", "그레이팅"], "맨홀뚜껑": ["맨홀뚜껑", "맨홀 뚜껑"], "보도블록": ["보도블록", "보도 블록"], "기타 건설자재": ["자재", "납품", "구매"]})

AMOUNT_KEYS = ["presmptPrce", "asignBdgtAmt", "bssamt", "baseAmount", "bdgtAmt", "cntrctAmt", "totPrdprcNum", "추정가격", "추정금액", "기초금액", "예정금액", "배정예산액", "공사예정금액", "총공사금액"]


def h(value) -> str:
    return "" if value is None else html.escape(str(value), quote=True)


def today_yyyymmddhhmm() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


def future_yyyymmddhhmm(days: int = 30) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y%m%d%H%M")


def parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for pattern in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"]:
        try:
            return datetime.strptime(text, pattern)
        except Exception:
            pass
    only_numbers = re.sub(r"[^0-9]", "", text)
    for size, pattern in [(14, "%Y%m%d%H%M%S"), (12, "%Y%m%d%H%M"), (8, "%Y%m%d")]:
        if len(only_numbers) >= size:
            try:
                return datetime.strptime(only_numbers[:size], pattern)
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
    try:
        return int(numbers) if numbers else 0
    except Exception:
        return 0


def format_money(amount: int) -> str:
    if not amount:
        return "-"
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:,.1f}억"
    return f"{amount:,}원"


def get_first(item: dict, keys: list, default: str = "") -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def get_bid_amount(item: dict) -> int:
    amounts = [parse_money_to_number(item.get(key)) for key in AMOUNT_KEYS]
    return max(amounts) if amounts else 0


def get_deadline(item: dict) -> str:
    return get_first(item, ["bidClseDt", "bidClseDate", "bidClseTm", "opengDt", "rbidOpengDt"])


def get_bid_no(item: dict) -> str:
    return get_first(item, ["bidNtceNo", "bidno", "bidNo", "공고번호"])


def get_bid_ord(item: dict) -> str:
    return get_first(item, ["bidNtceOrd", "bidseq", "bidSeq", "공고차수"], "00")


def get_bid_name(item: dict) -> str:
    return get_first(item, ["bidNtceNm", "bidNm", "공고명"], "제목 없음")


def get_agency(item: dict) -> str:
    return get_first(item, ["dminsttNm", "ntceInsttNm", "orderInsttNm", "realDmndInsttNm", "수요기관", "공고기관"], "-")


def get_region_text(item: dict) -> str:
    return get_first(item, ["prtcptPsblRgnNm", "prtcptPsblRgn", "bidPrtcptLmtRgnNm", "rgnLmtNm", "rgnLmt", "cnstrtsiteRgnNm", "공사지역", "참가가능지역", "지역제한"], "")


def make_search_text(item: dict) -> str:
    keys = ["bidNtceNm", "dminsttNm", "ntceInsttNm", "orderInsttNm", "realDmndInsttNm", "prtcptPsblRgnNm", "prtcptPsblRgn", "bidPrtcptLmtRgnNm", "rgnLmtNm", "rgnLmt", "cnstrtsiteRgnNm", "indstrytyNm", "lcnsLmtNm", "bidPrtcptLmtYn"]
    parts = [str(item.get(key)) for key in keys if item.get(key)]
    parts += [str(value) for value in item.values() if value]
    return " ".join(parts)


def get_nationwide_reason(item: dict) -> str:
    text = make_search_text(item)
    if any(keyword in text for keyword in REGION_KEYWORDS["전국"]):
        return "전국/지역제한없음 문구"
    if get_bid_amount(item) >= NATIONWIDE_AMOUNT_LIMIT:
        return "금액 100억 이상"
    return ""


def match_region(item: dict, region: str) -> bool:
    if not region or region == "전체":
        return True
    region = region.strip()
    if region == "전국":
        return bool(get_nationwide_reason(item))
    keywords = REGION_KEYWORDS.get(region) or [region]
    cleaned = [keyword.replace(" 전체", "") for keyword in keywords]
    text = make_search_text(item)
    return any(keyword in text for keyword in cleaned)


def infer_region_label(item: dict) -> str:
    region_text = get_region_text(item)
    if region_text:
        return region_text
    text = make_search_text(item)
    found = []
    for region in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
        if any(keyword in text for keyword in REGION_KEYWORDS.get(region, [])):
            found.append(region)
    if found:
        return ", ".join(dict.fromkeys(found))
    if get_nationwide_reason(item):
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
    return [name for name, keywords in LICENSE_KEYWORDS.items() if any(keyword in text for keyword in keywords)]


def infer_materials(item: dict) -> list:
    text = make_search_text(item)
    return [name for name, keywords in MATERIAL_KEYWORDS.items() if any(keyword in text for keyword in keywords)]


def get_d_day(deadline_text: str) -> str:
    deadline = parse_date(deadline_text)
    if not deadline:
        return "-"
    now = datetime.now()
    if deadline < now:
        return "마감"
    diff_days = (deadline.date() - now.date()).days
    return "D-day" if diff_days == 0 else f"D-{diff_days}"


def is_closed(item: dict) -> bool:
    deadline = parse_date(get_deadline(item))
    return bool(deadline and deadline < datetime.now())


def make_g2b_url(item: dict) -> str:
    direct_url = get_first(item, ["bidNtceUrl", "bidNtceDtlUrl", "ntceUrl", "bidUrl"], "")
    if direct_url.startswith("http"):
        return direct_url
    bid_no = get_bid_no(item)
    bid_ord = get_bid_ord(item)
    if not bid_no:
        return "https://www.g2b.go.kr"
    return "https://www.g2b.go.kr:8101/ep/tbid/tbidFwd.do" + f"?bidno={quote(bid_no)}&bidseq={quote(bid_ord)}"


def normalize_api_items(data) -> list:
    try:
        body = data.get("response", {}).get("body", {})
        items = body.get("items", [])
        item = items.get("item", []) if isinstance(items, dict) else items
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
        if v not in (None, ""):
            query_parts.append(f"{quote(str(k))}={quote(str(v))}")
    return G2B_CONSTRUCTION_API_URL + "?" + "&".join(query_parts)


def fetch_nara_bids(keyword: str, page_no: int = 1, num_rows: int = 100, days_forward: int = 30) -> dict:
    if not DATA_GO_KR_SERVICE_KEY:
        return {"ok": False, "error": "Render 환경변수 DATA_GO_KR_SERVICE_KEY가 없습니다.", "items": [], "total_count": 0}
    params = {
        "type": "json",
        "pageNo": page_no,
        "numOfRows": num_rows,
        "inqryDiv": 1,
        "inqryBgnDt": today_yyyymmddhhmm(),
        "inqryEndDt": future_yyyymmddhhmm(days_forward),
        "bidNtceNm": keyword,
    }
    try:
        res = requests.get(build_api_url(params), timeout=20)
        try:
            data = res.json()
        except Exception:
            return {"ok": False, "error": "API 응답이 JSON이 아닙니다.", "status_code": res.status_code, "preview": res.text[:500], "items": [], "total_count": 0}
        items = normalize_api_items(data)
        try:
            total_count = int(data.get("response", {}).get("body", {}).get("totalCount", 0))
        except Exception:
            total_count = len(items)
        return {"ok": True, "keyword": keyword, "page_no": page_no, "num_rows": num_rows, "total_count": total_count, "items": items}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": [], "total_count": 0}


def simplify_bid(item: dict, keyword: str = "") -> dict:
    deadline = get_deadline(item)
    amount = get_bid_amount(item)
    licenses = infer_licenses(item)
    materials = infer_materials(item)
    return {
        "keyword": keyword,
        "category": infer_category(item),
        "region_label": infer_region_label(item),
        "nationwide_reason": get_nationwide_reason(item),
        "amount": amount,
        "amount_label": format_money(amount),
        "license_label": ", ".join(licenses) if licenses else "-",
        "work_type_label": ", ".join(work_types) if work_types else "-",
        "material_label": ", ".join(materials) if materials else "-",
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


def search_bids_by_keywords(keywords: list, region: str = "전체", exclude_closed: bool = True, days_forward: int = 30, pages_per_keyword: int = 1, num_rows: int = 100) -> dict:
    all_items = []
    errors = []
    for keyword in keywords:
        for page_no in range(1, pages_per_keyword + 1):
            result = fetch_nara_bids(keyword, page_no, num_rows, days_forward)
            if not result.get("ok"):
                errors.append({"keyword": keyword, "page_no": page_no, "error": result.get("error"), "preview": result.get("preview", "")})
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
        key = (bid.get("bid_no") or "", bid.get("bid_ord") or "", bid.get("bid_name") or "", bid.get("deadline") or "")
        if key not in seen:
            seen.add(key)
            deduped.append(bid)
    deduped.sort(key=lambda bid: parse_date(bid.get("deadline")) or datetime.max)
    return {"status": "ok", "region": region, "exclude_closed": exclude_closed, "keywords": keywords, "count": len(deduped), "errors": errors, "bids": deduped}


def default_company_profile() -> dict:
    return {
        "company_name": "주식회사 송원건설",
        "manager_name": "",
        "address": "경상남도 김해시 삼문로19, 1205호",
        "phone": "055-339-4763",
        "fax": "055-339-4764",
        "email": "songwon4763@naver.com",
        "main_region": "경상남도/전체",
        "possible_regions": ["전국", "경상남도/전체", "경상남도/김해시", "경상남도/창녕군", "부산광역시/전체", "울산광역시/전체", "경상북도/전체"],
        "siping_amount_text": "",
        "siping_amount": 0,
        "licenses": [],
        "work_types": [],
        "material_supplies": [],
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
    keywords = [part.strip() for part in re.split(r"[,，\n/]+", keyword_text) if part.strip()]
    return keywords or SONGWON_KEYWORDS


def render_select_options(options: list, selected: str) -> str:
    return "".join([f'<option value="{h(option)}" {"selected" if option == selected else ""}>{h(option)}</option>' for option in options])


def render_checkbox_group(name: str, options: list, selected: list) -> str:
    selected = selected or []
    parts = []
    for option in options:
        checked = "checked" if option in selected else ""
        parts.append(f'<label class="check-item"><input type="checkbox" name="{h(name)}" value="{h(option)}" {checked}> {h(option)}</label>')
    return '<div class="check-grid">' + "".join(parts) + '</div>'


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
        return '<div class="empty">조건에 맞는 공고가 없습니다.<br>다른 지역을 눌러보거나, 전체 버튼을 눌러보세요.</div>'
    rows = []
    for idx, bid in enumerate(bids, start=1):
        dday = bid.get("d_day", "-")
        dday_class = "dday today" if dday == "D-day" else ("dday closed" if dday == "마감" else "dday")
        rows.append(f'''
        <tr>
            <td class="num">{idx}</td>
            <td><span class="{dday_class}">{h(dday)}</span></td>
            <td class="title"><div class="bid-name">{h(bid.get("bid_name"))}</div><div class="small">공고번호: {h(bid.get("bid_no"))} / 키워드: {h(bid.get("keyword"))}</div></td>
            <td>{h(bid.get("category"))}</td>
            <td>{h(bid.get("license_label"))}</td>
            <td>{h(bid.get("material_label"))}</td>
            <td>{h(bid.get("region_label"))}</td>
            <td>{h(bid.get("amount_label"))}</td>
            <td>{h(bid.get("nationwide_reason") or "-")}</td>
            <td>{h(bid.get("agency"))}</td>
            <td>{h(bid.get("deadline"))}</td>
            <td><a class="link-btn" href="{h(bid.get("g2b_url"))}" target="_blank" rel="noopener">원문 보기</a></td>
        </tr>
        ''')
    return f'''
    <div class="table-wrap"><table>
        <thead><tr><th>No</th><th>D-day</th><th>공고명</th><th>분류</th><th>면허 추정</th><th>자재 추정</th><th>지역</th><th>금액</th><th>전국 사유</th><th>기관</th><th>마감일</th><th>나라장터</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table></div>
    '''


def page_layout(title: str, subtitle: str, body: str) -> str:
    return f'''
    <!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{h(title)}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", Arial, sans-serif; background: #f5f6f8; color: #202124; }}
        header {{ background: #123; color: white; padding: 26px 22px; }}
        header h1 {{ margin: 0 0 8px; font-size: 26px; }} header p {{ margin: 0; opacity: 0.9; line-height: 1.5; }}
        main {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        .card {{ background: white; border-radius: 14px; padding: 18px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
        .menu, .summary, .search-form {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }}
        .region-btn, .top-btn, .link-btn, button {{ display: inline-block; border: 1px solid #d0d7de; background: #ffffff; color: #123; padding: 9px 12px; border-radius: 999px; text-decoration: none; font-size: 14px; cursor: pointer; }}
        .region-btn.active, button {{ background: #123; color: white; border-color: #123; font-weight: 700; }} .top-btn {{ border-radius: 10px; background: #eef4ff; }}
        input[type="text"], input[type="email"], textarea, select {{ width: 100%; padding: 11px 12px; border: 1px solid #d0d7de; border-radius: 10px; font-size: 15px; font-family: inherit; }}
        textarea {{ min-height: 90px; resize: vertical; }} .badge {{ background: #eef4ff; color: #123; border: 1px solid #d9e7ff; border-radius: 999px; padding: 8px 12px; font-size: 14px; }}
        .table-wrap {{ width: 100%; overflow-x: auto; }} table {{ width: 100%; border-collapse: collapse; min-width: 1500px; }}
        th, td {{ border-bottom: 1px solid #eceff3; padding: 12px 10px; vertical-align: top; text-align: left; font-size: 14px; }} th {{ background: #f8fafc; font-weight: 700; }}
        .num {{ width: 55px; color: #667085; }} .title {{ min-width: 340px; }} .bid-name {{ font-weight: 700; margin-bottom: 5px; line-height: 1.35; }} .small {{ color: #667085; font-size: 12px; line-height: 1.4; }}
        .dday {{ display: inline-block; min-width: 56px; text-align: center; padding: 6px 8px; border-radius: 999px; background: #fff4e5; color: #9a5b00; font-weight: 700; }} .dday.today {{ background: #ffe8e8; color: #b42318; }} .dday.closed {{ background: #e5e7eb; color: #6b7280; }}
        .empty {{ padding: 30px; text-align: center; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; color: #475467; line-height: 1.7; }} .notice {{ line-height: 1.7; color: #475467; font-size: 14px; }} .error {{ background: #fff1f3; border: 1px solid #ffd6de; color: #b42318; padding: 12px; border-radius: 10px; white-space: pre-wrap; }}
        .form-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }} .form-row {{ margin-bottom: 14px; }} .form-row label {{ display: block; font-weight: 700; margin-bottom: 7px; }}
        .check-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; max-height: 520px; overflow-y: auto; padding: 4px; }} .check-item {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px; background: #fafafa; font-size: 14px; }} .check-item input {{ margin-right: 6px; }}
        .profile-box {{ line-height: 1.8; color: #344054; }} .profile-box strong {{ color: #111827; }} @media (max-width: 800px) {{ .form-grid, .check-grid {{ grid-template-columns: 1fr; }} }}
    </style></head><body><header><h1>{h(title)}</h1><p>{h(subtitle)}</p></header><main>{body}</main></body></html>
    '''


@app.get("/health")
def health():
    return {"status": "ok", "service": "gongsa-bid", "version": "profile-worktype-siping-1.0.0", "has_DATA_GO_KR_SERVICE_KEY": bool(DATA_GO_KR_SERVICE_KEY)}


@app.get("/routes")
def routes():
    return {"routes": ["/", "/health", "/routes", "/company/profile", "/company/profile-data", "/bids/nara?keyword=포장", "/bids/nara-page?keyword=포장", "/bids/songwon-test", "/bids/songwon-page", "/bids/songwon-page?region=전국", "/bids/songwon-page?region=경남"]}


@app.get("/", response_class=HTMLResponse)
def home():
    profile = load_company_profile()
    body = f'''
    <div class="card"><h2>공사입찰 공고 검색</h2><p class="notice">송원건설 주력 키워드로 나라장터 공사 공고를 검색합니다.<br>회사 프로필에서 전국 시·군·구 지역을 선택할 수 있습니다.</p>
        <div class="menu"><a class="top-btn" href="/bids/songwon-page">전체 공고 보기</a><a class="top-btn" href="/bids/songwon-page?region=전국">전국 공고 보기</a><a class="top-btn" href="/bids/songwon-page?region=경남">경남 공고 보기</a><a class="top-btn" href="/company/profile">회사 프로필 등록</a><a class="top-btn" href="/company/profile-data" target="_blank">프로필 JSON 확인</a></div>
    </div>
    <div class="card"><h3>현재 저장된 회사 프로필</h3><div class="profile-box">
        <strong>회사명:</strong> {h(profile.get("company_name"))}<br><strong>주소:</strong> {h(profile.get("address"))}<br><strong>전화:</strong> {h(profile.get("phone"))}<br><strong>팩스:</strong> {h(profile.get("fax"))}<br><strong>이메일:</strong> {h(profile.get("email"))}<br><strong>주 활동지역:</strong> {h(profile.get("main_region"))}<br><strong>입찰 가능지역:</strong> {h(", ".join(profile.get("possible_regions", [])))}<br><strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "아직 선택 안 함")}<br><strong>자재납품 품목:</strong> {h(", ".join(profile.get("material_supplies", [])) if profile.get("material_supplies") else "아직 선택 안 함")}<br><strong>주력 키워드:</strong> {h(profile.get("keyword_text"))}
    </div></div>'''
    return page_layout("gongsa-bid", "건설회사 전용 나라장터 공고 웹플랫폼", body)


@app.get("/company/profile", response_class=HTMLResponse)
def company_profile_page():
    profile = load_company_profile()
    body = f'''
    <div class="card"><div class="summary"><span class="badge">회사 프로필 등록</span><span class="badge">시·도/시·군 형식 지역 선택</span><a class="top-btn" href="/">첫 화면</a><a class="top-btn" href="/bids/songwon-page">전체 공고 보기</a></div></div>
    <form action="/company/profile-save" method="get">
        <div class="card"><h3>기본 정보</h3><div class="form-grid">
            <div class="form-row"><label>회사명</label><input type="text" name="company_name" value="{h(profile.get("company_name"))}"></div>
            <div class="form-row"><label>담당자명</label><input type="text" name="manager_name" value="{h(profile.get("manager_name"))}" placeholder="예: 홍길동"></div>
            <div class="form-row"><label>전화번호</label><input type="text" name="phone" value="{h(profile.get("phone"))}"></div>
            <div class="form-row"><label>팩스</label><input type="text" name="fax" value="{h(profile.get("fax"))}"></div>
            <div class="form-row"><label>이메일</label><input type="email" name="email" value="{h(profile.get("email"))}"></div>
            <div class="form-row"><label>주 활동지역</label><select name="main_region">{render_select_options(PROFILE_REGION_OPTIONS, profile.get("main_region"))}</select></div>
        </div><div class="form-row"><label>주소</label><input type="text" name="address" value="{h(profile.get("address"))}"></div></div>
        <div class="card"><h3>입찰 가능지역</h3><p class="notice">경상남도/김해시, 경상남도/창녕군, 경상남도/전체, 전국처럼 여러 개를 선택할 수 있습니다.</p>{render_checkbox_group("possible_regions", PROFILE_REGION_OPTIONS, profile.get("possible_regions", []))}</div>
        <div class="card"><h3>보유 종합건설 면허</h3>{render_checkbox_group("licenses", GENERAL_CONSTRUCTION_LICENSE_OPTIONS, profile.get("licenses", []))}</div>
        <div class="card"><h3>보유 전문건설 면허 / 주력분야</h3>{render_checkbox_group("licenses", SPECIALTY_CONSTRUCTION_LICENSE_OPTIONS, profile.get("licenses", []))}</div>
        <div class="card"><h3>자재납품 가능 품목</h3><p class="notice">자재납품은 건설업 면허와 따로 저장합니다.</p>{render_checkbox_group("material_supplies", MATERIAL_SUPPLY_OPTIONS, profile.get("material_supplies", []))}</div>
        <div class="card"><h3>주력 검색 키워드</h3><textarea name="keyword_text">{h(profile.get("keyword_text"))}</textarea><br><br><button type="submit">회사 프로필 저장</button><a class="top-btn" href="/">취소하고 첫 화면</a></div>
    </form>'''
    return page_layout("회사 프로필 등록", "회사 정보, 지역, 시공능력평가액, 면허, 공종, 자재납품 품목을 저장하는 화면입니다", body)


@app.get("/company/profile-save", response_class=HTMLResponse)
def company_profile_save(company_name: str = Query(""), manager_name: str = Query(""), address: str = Query(""), phone: str = Query(""), fax: str = Query(""), email: str = Query(""), main_region: str = Query("경상남도/전체"), possible_regions: List[str] = Query(default=[]), licenses: List[str] = Query(default=[]), material_supplies: List[str] = Query(default=[]), keyword_text: str = Query("")):
    profile = {"company_name": company_name.strip(), "manager_name": manager_name.strip(), "address": address.strip(), "phone": phone.strip(), "fax": fax.strip(), "email": email.strip(), "main_region": main_region.strip(), "possible_regions": possible_regions, "licenses": licenses, "material_supplies": material_supplies, "keyword_text": keyword_text.strip(), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    save_company_profile(profile)
    body = f'''
    <div class="card"><h2>회사 프로필 저장 완료</h2><p class="notice">회사 프로필이 저장되었습니다.</p><div class="profile-box">
        <strong>회사명:</strong> {h(profile.get("company_name"))}<br><strong>입찰 가능지역:</strong> {h(", ".join(profile.get("possible_regions", [])))}<br><strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "선택 안 함")}<br><strong>자재납품 품목:</strong> {h(", ".join(profile.get("material_supplies", [])) if profile.get("material_supplies") else "선택 안 함")}<br><strong>저장시간:</strong> {h(profile.get("updated_at"))}
    </div><div class="menu"><a class="top-btn" href="/">첫 화면</a><a class="top-btn" href="/company/profile">다시 수정하기</a><a class="top-btn" href="/company/profile-data" target="_blank">JSON 확인</a><a class="top-btn" href="/bids/songwon-page">공고 보기</a></div></div>'''
    return page_layout("회사 프로필 저장 완료", "저장된 회사 정보를 확인하세요", body)


@app.get("/company/profile-data")
def company_profile_data():
    return JSONResponse(load_company_profile())


@app.get("/bids/nara")
def nara_json(keyword: str = Query("포장"), region: str = Query("전체"), days_forward: int = Query(30)):
    return JSONResponse(search_bids_by_keywords([keyword], region, True, days_forward, 1, 100))


@app.get("/bids/nara-page", response_class=HTMLResponse)
def nara_page(keyword: str = Query("포장"), region: str = Query("전체"), days_forward: int = Query(30)):
    result = search_bids_by_keywords([keyword], region, True, days_forward, 1, 100)
    error_html = f'<div class="card"><div class="error">{h(json.dumps(result.get("errors"), ensure_ascii=False, indent=2))}</div></div>' if result.get("errors") else ""
    body = f'''<div class="card"><div class="summary"><span class="badge">검색어: {h(keyword)}</span><span class="badge">선택 지역: {h(region)}</span><span class="badge">공고 수: {h(result.get("count"))}개</span><a class="top-btn" href="/">첫 화면</a><a class="top-btn" href="/bids/songwon-page">송원 전체검색</a></div><form class="search-form" action="/bids/nara-page" method="get"><input type="text" name="keyword" value="{h(keyword)}" placeholder="공고명 검색"><input type="hidden" name="region" value="{h(region)}"><button type="submit">검색</button></form></div><div class="card"><h3>지역별 보기</h3><div class="menu">{render_region_buttons("/bids/nara-page", region, keyword)}</div></div>{error_html}<div class="card">{render_bid_table(result.get("bids", []))}</div>'''
    return page_layout(f"개별 검색 - {keyword}", f"지역: {region} / 마감 지난 공고 제외 / D-day 표시", body)


@app.get("/bids/songwon-test")
def songwon_test(region: str = Query("전체"), days_forward: int = Query(30)):
    profile = load_company_profile()
    keywords = split_keywords(profile.get("keyword_text", ""))
    return JSONResponse(search_bids_by_keywords(keywords, region, True, days_forward, 1, 100))


@app.get("/bids/songwon-page", response_class=HTMLResponse)
def songwon_page(region: str = Query("전체"), keyword: str = Query(""), days_forward: int = Query(30)):
    profile = load_company_profile()
    if keyword.strip():
        keywords = [keyword.strip()]
        keyword_label = keyword.strip()
    else:
        keywords = split_keywords(profile.get("keyword_text", ""))
        keyword_label = "회사 프로필 주력 키워드"
    result = search_bids_by_keywords(keywords, region, True, days_forward, 1, 100)
    error_html = f'<div class="card"><h3>API 오류</h3><div class="error">{h(json.dumps(result.get("errors"), ensure_ascii=False, indent=2))}</div></div>' if result.get("errors") else ""
    body = f'''<div class="card"><div class="summary"><span class="badge">검색 범위: {h(keyword_label)}</span><span class="badge">선택 지역: {h(region)}</span><span class="badge">공고 수: {h(result.get("count"))}개</span><span class="badge">마감 지난 공고 제외</span><a class="top-btn" href="/">첫 화면</a><a class="top-btn" href="/company/profile">회사 프로필</a><a class="top-btn" href="/bids/songwon-test?region={quote(region)}" target="_blank">JSON 보기</a></div><form class="search-form" action="/bids/songwon-page" method="get"><input type="text" name="keyword" value="{h(keyword)}" placeholder="공고명 검색 예: 포장, 배수로, 도로 / 비우면 회사 프로필 키워드"><input type="hidden" name="region" value="{h(region)}"><button type="submit">공고명 검색</button><a class="top-btn" href="/bids/songwon-page?region={quote(region)}">검색 초기화</a></form></div><div class="card"><h3>지역별 보기</h3><p class="notice">전체는 지역 상관없이 모든 공고를 보여줍니다.<br>전국은 지역제한 없음 문구가 있거나 금액이 100억 이상인 공고를 보여줍니다.<br>경상남도/김해시, 충청남도/천안시 같은 지역 선택은 회사 프로필에서 저장할 수 있습니다.</p><div class="menu">{render_region_buttons("/bids/songwon-page", region, keyword)}</div></div>{error_html}<div class="card">{render_bid_table(result.get("bids", []))}</div>'''
    return page_layout("송원건설 전체 공고 검색", "회사 프로필 전국 지역 선택 추가 버전", body)
