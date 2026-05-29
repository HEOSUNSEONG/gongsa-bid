
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

app = FastAPI(title="gongsa-bid", version="my-bids-siping-filter-1.0.0")


DATA_GO_KR_SERVICE_KEY = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip()
G2B_CONSTRUCTION_API_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"
PROFILE_FILE = "company_profile.json"
NATIONWIDE_AMOUNT_LIMIT = 10_000_000_000

SONGWON_KEYWORDS = [
    "포장", "배수", "배수로", "상하수도", "관로",
    "도로", "하천", "소하천", "옹벽", "측구",
    "맨홀", "농로", "재해복구", "정비", "보수",
]


# =========================================================
# 지역 설정
# =========================================================

REGION_BUTTONS = [
    "전체", "전국", "서울", "경기", "인천", "부산", "대구", "광주",
    "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남",
    "경북", "경남", "제주", "수도권", "충청권", "전라권", "경상권",
]

PROFILE_REGION_GROUPS = [
    {
        "title": "기본",
        "items": [
            ("전국", "전국"),
        ],
    },
    {
        "title": "시·도 전체",
        "items": [
            ("서울특별시/전체", "서울특별시"),
            ("경기도/전체", "경기도"),
            ("인천광역시/전체", "인천광역시"),
            ("부산광역시/전체", "부산광역시"),
            ("대구광역시/전체", "대구광역시"),
            ("광주광역시/전체", "광주광역시"),
            ("대전광역시/전체", "대전광역시"),
            ("울산광역시/전체", "울산광역시"),
            ("세종특별자치시/전체", "세종특별자치시"),
            ("강원특별자치도/전체", "강원특별자치도"),
            ("충청북도/전체", "충청북도"),
            ("충청남도/전체", "충청남도"),
            ("전북특별자치도/전체", "전북특별자치도"),
            ("전라남도/전체", "전라남도"),
            ("경상북도/전체", "경상북도"),
            ("경상남도/전체", "경상남도"),
            ("제주특별자치도/전체", "제주특별자치도"),
        ],
    },
    {
        "title": "경상남도",
        "items": [
            ("경상남도/창원시", "창원시"),
            ("경상남도/진주시", "진주시"),
            ("경상남도/통영시", "통영시"),
            ("경상남도/사천시", "사천시"),
            ("경상남도/김해시", "김해시"),
            ("경상남도/밀양시", "밀양시"),
            ("경상남도/거제시", "거제시"),
            ("경상남도/양산시", "양산시"),
            ("경상남도/의령군", "의령군"),
            ("경상남도/함안군", "함안군"),
            ("경상남도/창녕군", "창녕군"),
            ("경상남도/고성군", "고성군"),
            ("경상남도/남해군", "남해군"),
            ("경상남도/하동군", "하동군"),
            ("경상남도/산청군", "산청군"),
            ("경상남도/함양군", "함양군"),
            ("경상남도/거창군", "거창군"),
            ("경상남도/합천군", "합천군"),
        ],
    },
    {
        "title": "경상북도",
        "items": [
            ("경상북도/포항시", "포항시"),
            ("경상북도/경주시", "경주시"),
            ("경상북도/김천시", "김천시"),
            ("경상북도/안동시", "안동시"),
            ("경상북도/구미시", "구미시"),
            ("경상북도/영주시", "영주시"),
            ("경상북도/영천시", "영천시"),
            ("경상북도/상주시", "상주시"),
            ("경상북도/문경시", "문경시"),
            ("경상북도/경산시", "경산시"),
            ("경상북도/의성군", "의성군"),
            ("경상북도/청송군", "청송군"),
            ("경상북도/영양군", "영양군"),
            ("경상북도/영덕군", "영덕군"),
            ("경상북도/청도군", "청도군"),
            ("경상북도/고령군", "고령군"),
            ("경상북도/성주군", "성주군"),
            ("경상북도/칠곡군", "칠곡군"),
            ("경상북도/예천군", "예천군"),
            ("경상북도/봉화군", "봉화군"),
            ("경상북도/울진군", "울진군"),
            ("경상북도/울릉군", "울릉군"),
        ],
    },
    {
        "title": "부산·울산·대구",
        "items": [
            ("부산광역시/기장군", "기장군"),
            ("울산광역시/울주군", "울주군"),
            ("대구광역시/달성군", "달성군"),
            ("대구광역시/군위군", "군위군"),
        ],
    },
    {
        "title": "충청남도",
        "items": [
            ("충청남도/천안시", "천안시"),
            ("충청남도/공주시", "공주시"),
            ("충청남도/보령시", "보령시"),
            ("충청남도/아산시", "아산시"),
            ("충청남도/서산시", "서산시"),
            ("충청남도/논산시", "논산시"),
            ("충청남도/계룡시", "계룡시"),
            ("충청남도/당진시", "당진시"),
            ("충청남도/금산군", "금산군"),
            ("충청남도/부여군", "부여군"),
            ("충청남도/서천군", "서천군"),
            ("충청남도/청양군", "청양군"),
            ("충청남도/홍성군", "홍성군"),
            ("충청남도/예산군", "예산군"),
            ("충청남도/태안군", "태안군"),
        ],
    },
    {
        "title": "충청북도",
        "items": [
            ("충청북도/청주시", "청주시"),
            ("충청북도/충주시", "충주시"),
            ("충청북도/제천시", "제천시"),
            ("충청북도/보은군", "보은군"),
            ("충청북도/옥천군", "옥천군"),
            ("충청북도/영동군", "영동군"),
            ("충청북도/증평군", "증평군"),
            ("충청북도/진천군", "진천군"),
            ("충청북도/괴산군", "괴산군"),
            ("충청북도/음성군", "음성군"),
            ("충청북도/단양군", "단양군"),
        ],
    },
    {
        "title": "전라남도",
        "items": [
            ("전라남도/목포시", "목포시"),
            ("전라남도/여수시", "여수시"),
            ("전라남도/순천시", "순천시"),
            ("전라남도/나주시", "나주시"),
            ("전라남도/광양시", "광양시"),
            ("전라남도/담양군", "담양군"),
            ("전라남도/곡성군", "곡성군"),
            ("전라남도/구례군", "구례군"),
            ("전라남도/고흥군", "고흥군"),
            ("전라남도/보성군", "보성군"),
            ("전라남도/화순군", "화순군"),
            ("전라남도/장흥군", "장흥군"),
            ("전라남도/강진군", "강진군"),
            ("전라남도/해남군", "해남군"),
            ("전라남도/영암군", "영암군"),
            ("전라남도/무안군", "무안군"),
            ("전라남도/함평군", "함평군"),
            ("전라남도/영광군", "영광군"),
            ("전라남도/장성군", "장성군"),
            ("전라남도/완도군", "완도군"),
            ("전라남도/진도군", "진도군"),
            ("전라남도/신안군", "신안군"),
        ],
    },
    {
        "title": "전북특별자치도",
        "items": [
            ("전북특별자치도/전주시", "전주시"),
            ("전북특별자치도/군산시", "군산시"),
            ("전북특별자치도/익산시", "익산시"),
            ("전북특별자치도/정읍시", "정읍시"),
            ("전북특별자치도/남원시", "남원시"),
            ("전북특별자치도/김제시", "김제시"),
            ("전북특별자치도/완주군", "완주군"),
            ("전북특별자치도/진안군", "진안군"),
            ("전북특별자치도/무주군", "무주군"),
            ("전북특별자치도/장수군", "장수군"),
            ("전북특별자치도/임실군", "임실군"),
            ("전북특별자치도/순창군", "순창군"),
            ("전북특별자치도/고창군", "고창군"),
            ("전북특별자치도/부안군", "부안군"),
        ],
    },
    {
        "title": "강원특별자치도",
        "items": [
            ("강원특별자치도/춘천시", "춘천시"),
            ("강원특별자치도/원주시", "원주시"),
            ("강원특별자치도/강릉시", "강릉시"),
            ("강원특별자치도/동해시", "동해시"),
            ("강원특별자치도/태백시", "태백시"),
            ("강원특별자치도/속초시", "속초시"),
            ("강원특별자치도/삼척시", "삼척시"),
            ("강원특별자치도/홍천군", "홍천군"),
            ("강원특별자치도/횡성군", "횡성군"),
            ("강원특별자치도/영월군", "영월군"),
            ("강원특별자치도/평창군", "평창군"),
            ("강원특별자치도/정선군", "정선군"),
            ("강원특별자치도/철원군", "철원군"),
            ("강원특별자치도/화천군", "화천군"),
            ("강원특별자치도/양구군", "양구군"),
            ("강원특별자치도/인제군", "인제군"),
            ("강원특별자치도/고성군", "고성군"),
            ("강원특별자치도/양양군", "양양군"),
        ],
    },
    {
        "title": "경기도",
        "items": [
            ("경기도/수원시", "수원시"),
            ("경기도/성남시", "성남시"),
            ("경기도/의정부시", "의정부시"),
            ("경기도/안양시", "안양시"),
            ("경기도/부천시", "부천시"),
            ("경기도/광명시", "광명시"),
            ("경기도/평택시", "평택시"),
            ("경기도/동두천시", "동두천시"),
            ("경기도/안산시", "안산시"),
            ("경기도/고양시", "고양시"),
            ("경기도/과천시", "과천시"),
            ("경기도/구리시", "구리시"),
            ("경기도/남양주시", "남양주시"),
            ("경기도/오산시", "오산시"),
            ("경기도/시흥시", "시흥시"),
            ("경기도/군포시", "군포시"),
            ("경기도/의왕시", "의왕시"),
            ("경기도/하남시", "하남시"),
            ("경기도/용인시", "용인시"),
            ("경기도/파주시", "파주시"),
            ("경기도/이천시", "이천시"),
            ("경기도/안성시", "안성시"),
            ("경기도/김포시", "김포시"),
            ("경기도/화성시", "화성시"),
            ("경기도/광주시", "광주시"),
            ("경기도/양주시", "양주시"),
            ("경기도/포천시", "포천시"),
            ("경기도/여주시", "여주시"),
            ("경기도/연천군", "연천군"),
            ("경기도/가평군", "가평군"),
            ("경기도/양평군", "양평군"),
        ],
    },
    {
        "title": "제주특별자치도",
        "items": [
            ("제주특별자치도/제주시", "제주시"),
            ("제주특별자치도/서귀포시", "서귀포시"),
        ],
    },
    {
        "title": "권역",
        "items": [
            ("수도권", "수도권"),
            ("충청권", "충청권"),
            ("전라권", "전라권"),
            ("경상권", "경상권"),
        ],
    },
]

PROFILE_REGION_OPTIONS = [
    value
    for group in PROFILE_REGION_GROUPS
    for value, label in group["items"]
]

REGION_LABELS = {
    value: label
    for group in PROFILE_REGION_GROUPS
    for value, label in group["items"]
}

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


# =========================================================
# 면허 / 공종 / 자재 설정
# =========================================================

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

GENERAL_CONSTRUCTION_LICENSE_OPTIONS = [
    "토목공사업",
    "건축공사업",
    "토목건축공사업",
    "산업·환경설비공사업",
    "조경공사업",
]

SPECIALTY_CONSTRUCTION_LICENSE_OPTIONS = [
    "지반조성·포장공사업",
    "실내건축공사업",
    "금속·창호·지붕·건축물조립공사업",
    "도장·습식·방수·석공사업",
    "조경식재·시설물공사업",
    "철근·콘크리트공사업",
    "구조물해체·비계공사업",
    "상·하수도설비공사업",
    "철도·궤도공사업",
    "철강구조물공사업",
    "수중·준설공사업",
    "승강기·삭도공사업",
    "기계설비·가스공사업",
    "가스·난방공사업",
    "토공사",
    "포장공사",
    "보링·그라우팅·파일공사",
    "금속구조물공사",
    "창호공사",
    "지붕판금·건축물조립공사",
    "도장공사",
    "습식·방수공사",
    "석공사",
    "조경식재공사",
    "조경시설물설치공사",
    "철근·콘크리트공사",
    "구조물해체공사",
    "비계공사",
    "상수도설비공사",
    "하수도설비공사",
    "철도·궤도공사",
    "철강구조물공사",
    "수중공사",
    "준설공사",
    "승강기설치공사",
    "삭도설치공사",
    "기계설비공사",
    "가스시설공사",
    "난방공사",
]

LICENSE_KEYWORDS = {
    "토목공사업": ["토목", "도로", "하천", "교량", "상하수도", "농로", "구거"],
    "건축공사업": ["건축", "신축", "증축", "리모델링", "보수공사"],
    "토목건축공사업": ["토목건축", "토건", "토목", "건축"],
    "산업·환경설비공사업": ["산업설비", "환경설비", "폐수", "처리장", "플랜트"],
    "조경공사업": ["조경", "공원", "녹지", "식재"],
    "지반조성·포장공사업": ["지반조성", "포장", "아스콘", "아스팔트", "콘크리트포장", "보도포장", "토공", "보링", "그라우팅", "파일"],
    "실내건축공사업": ["실내건축", "인테리어", "내장", "수장"],
    "금속·창호·지붕·건축물조립공사업": ["금속", "창호", "지붕", "판넬", "건축물조립"],
    "도장·습식·방수·석공사업": ["도장", "습식", "방수", "석공", "석축", "타일", "미장"],
    "조경식재·시설물공사업": ["조경", "식재", "시설물", "공원", "놀이터"],
    "철근·콘크리트공사업": ["철근", "콘크리트", "철콘", "옹벽", "측구", "수로", "구조물"],
    "구조물해체·비계공사업": ["해체", "철거", "비계"],
    "상·하수도설비공사업": ["상하수도", "상수도", "하수도", "관로", "관거", "오수", "우수", "맨홀", "배수"],
    "철도·궤도공사업": ["철도", "궤도"],
    "철강구조물공사업": ["철강", "강구조", "철골"],
    "수중·준설공사업": ["수중", "준설"],
    "승강기·삭도공사업": ["승강기", "엘리베이터", "삭도"],
    "기계설비·가스공사업": ["기계설비", "가스", "배관", "냉난방"],
    "가스·난방공사업": ["가스", "난방"],
    "토공사": ["토공", "터파기", "성토", "절토", "흙막이"],
    "포장공사": ["포장", "아스콘", "아스팔트", "콘크리트포장", "보도포장"],
    "철근·콘크리트공사": ["철근", "콘크리트", "철콘", "옹벽", "측구"],
    "상수도설비공사": ["상수도", "상수관", "급수"],
    "하수도설비공사": ["하수도", "하수관", "오수", "우수", "관거"],
}

WORK_TYPE_OPTIONS = [
    "토공", "흙막이", "비탈면보강", "보링·그라우팅", "파일공",
    "포장공", "아스콘포장", "콘크리트포장", "보도블록포장",
    "도로공", "농로공", "교량공", "터널공", "하천공", "소하천정비",
    "구거정비", "제방공", "호안공", "배수공", "배수로", "측구",
    "수로관", "집수정", "우수관로", "오수관로", "상수도관로",
    "하수도관로", "맨홀", "옹벽", "석축", "블록쌓기",
    "철근콘크리트구조물", "암거", "박스 culvert", "재해복구",
    "유지보수", "준설", "수중공", "철도·궤도", "도로안전시설",
    "가드레일", "휀스", "낙석방지", "방음벽",
    "건축공", "신축", "증축", "대수선", "리모델링", "실내건축",
    "내장공", "목공", "창호공", "유리공", "금속공", "지붕공",
    "판금공", "철골공", "도장공", "방수공", "미장공", "타일공",
    "석공", "조적공", "철거공", "구조물해체", "비계공", "단열공",
    "수장공", "기계설비", "냉난방", "공조", "위생설비", "소방설비",
    "가스시설", "난방공", "펌프설비", "배관공", "조경공",
    "조경식재", "조경시설물", "공원시설", "잔디식재", "수목식재",
    "전기공", "통신공", "CCTV", "정보통신", "태양광", "승강기",
    "삭도", "폐기물처리", "산업·환경설비",
]

WORK_TYPE_KEYWORDS = {
    "토공": ["토공", "터파기", "성토", "절토"],
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
    "하천공": ["하천"],
    "소하천정비": ["소하천"],
    "구거정비": ["구거"],
    "배수공": ["배수"],
    "배수로": ["배수로"],
    "측구": ["측구"],
    "수로관": ["수로관", "플륨관", "벤치플륨"],
    "집수정": ["집수정"],
    "상수도관로": ["상수도", "상수관"],
    "하수도관로": ["하수도", "하수관", "관거"],
    "맨홀": ["맨홀"],
    "옹벽": ["옹벽"],
    "석축": ["석축"],
    "재해복구": ["재해복구", "수해복구", "복구"],
    "유지보수": ["유지보수", "보수", "정비"],
    "준설": ["준설"],
    "철근콘크리트구조물": ["철근", "콘크리트", "철콘", "구조물"],
    "건축공": ["건축"],
    "신축": ["신축"],
    "증축": ["증축"],
    "실내건축": ["실내건축", "인테리어"],
    "창호공": ["창호", "샷시"],
    "도장공": ["도장", "페인트"],
    "방수공": ["방수"],
    "석공": ["석공", "화강석"],
    "철거공": ["철거"],
    "구조물해체": ["구조물해체", "해체"],
    "비계공": ["비계"],
    "기계설비": ["기계설비"],
    "가스시설": ["가스시설", "가스"],
    "조경공": ["조경"],
    "조경식재": ["식재", "수목"],
    "전기공": ["전기"],
    "통신공": ["통신"],
    "CCTV": ["CCTV"],
    "정보통신": ["정보통신"],
    "태양광": ["태양광"],
    "폐기물처리": ["폐기물"],
}

MATERIAL_SUPPLY_OPTIONS = [
    "아스콘", "레미콘", "콘크리트", "시멘트", "모래", "쇄석", "골재",
    "혼합골재", "보조기층재", "순환골재", "흄관", "VR관", "PE관",
    "PVC관", "이중벽관", "파형강관", "스틸그레이팅", "맨홀뚜껑",
    "콘크리트맨홀", "집수정", "측구수로관", "U형측구", "벤치플륨관",
    "플륨관", "경계석", "보차도경계석", "도로경계석", "화강석",
    "보도블록", "투수블록", "점자블록", "식생블록", "옹벽블록",
    "축조블록", "콘크리트블록", "철근", "H빔", "철강재",
    "와이어메쉬", "거푸집", "동바리", "가드레일", "휀스",
    "낙석방지망", "방음벽", "도로표지판", "안전표지판", "차선도색재",
    "방수재", "도막재", "에폭시", "페인트", "조경석", "자연석",
    "식재", "잔디", "토목섬유", "부직포", "배수판", "기타 건설자재",
]

MATERIAL_KEYWORDS = {
    "아스콘": ["아스콘", "아스팔트콘크리트"],
    "레미콘": ["레미콘", "레디믹스트"],
    "콘크리트": ["콘크리트"],
    "시멘트": ["시멘트"],
    "모래": ["모래", "세사", "왕사"],
    "쇄석": ["쇄석"],
    "골재": ["골재"],
    "보조기층재": ["보조기층"],
    "흄관": ["흄관"],
    "PE관": ["PE관", "피이관"],
    "PVC관": ["PVC관", "염화비닐관"],
    "스틸그레이팅": ["스틸그레이팅", "그레이팅"],
    "맨홀뚜껑": ["맨홀뚜껑", "맨홀 뚜껑"],
    "집수정": ["집수정"],
    "측구수로관": ["측구수로관", "수로관"],
    "경계석": ["경계석"],
    "보도블록": ["보도블록", "보도 블록"],
    "철근": ["철근"],
    "H빔": ["H빔", "에이치빔"],
    "가드레일": ["가드레일"],
    "휀스": ["휀스", "펜스"],
    "기타 건설자재": ["자재", "납품", "구매"],
}


# 내 회사 맞춤 공고에서 제외할 수 있는 큰 분류 키워드
# 회사 프로필에 해당 면허/공종이 없으면 아래 키워드가 강하게 잡히는 공고는 제외합니다.
PROFILE_EXCLUDE_RULES = {
    "전기": {
        "profile_terms": ["전기공", "전기", "전기공사업"],
        "bid_terms": ["전기공사", "전기 공사", "전기설비", "전력", "배전", "수전", "분전반", "가로등", "보안등", "조명공사"],
    },
    "건축": {
        "profile_terms": ["건축공사업", "토목건축공사업", "건축공", "신축", "증축", "대수선", "리모델링", "실내건축"],
        "bid_terms": ["건축공사", "건축 공사", "신축", "증축", "대수선", "리모델링", "인테리어", "실내건축", "내장공사"],
    },
    "통신": {
        "profile_terms": ["통신공", "정보통신", "CCTV"],
        "bid_terms": ["통신공사", "정보통신", "CCTV", "방송설비", "네트워크"],
    },
    "소방": {
        "profile_terms": ["소방설비"],
        "bid_terms": ["소방공사", "소방설비", "화재감지", "스프링클러"],
    },
    "기계설비": {
        "profile_terms": ["기계설비·가스공사업", "기계설비공사", "기계설비", "냉난방", "공조", "위생설비", "펌프설비", "배관공"],
        "bid_terms": ["기계설비", "냉난방", "공조", "위생설비", "펌프", "보일러", "배관공사"],
    },
    "조경": {
        "profile_terms": ["조경공사업", "조경식재·시설물공사업", "조경공", "조경식재", "조경시설물", "공원시설", "잔디식재", "수목식재"],
        "bid_terms": ["조경공사", "조경 식재", "수목", "잔디", "공원시설", "식재공사"],
    },
}

AMOUNT_KEYS = [
    "presmptPrce", "asignBdgtAmt", "bssamt", "baseAmount", "bdgtAmt",
    "cntrctAmt", "totPrdprcNum", "추정가격", "추정금액", "기초금액",
    "예정금액", "배정예산액", "공사예정금액", "총공사금액",
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


def parse_profile_amount(value) -> int:
    return parse_money_to_number(value)


def format_money(amount: int) -> str:
    """
    금액을 100,000,000원 형식으로 표시합니다.
    억 단위로 줄이지 않고 원 단위 콤마 표시를 사용합니다.
    """
    if not amount:
        return "-"

    try:
        amount = int(amount)
    except Exception:
        return "-"

    return f"{amount:,}원"


def region_display_name(value: str) -> str:
    if not value:
        return ""

    if value in REGION_LABELS:
        return REGION_LABELS[value]

    if "/" in value:
        sido, sigun = value.split("/", 1)
        if sigun == "전체":
            return sido
        return sigun

    return value


def format_region_list(values: list) -> str:
    if not values:
        return ""

    return ", ".join(region_display_name(value) for value in values)


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
    parts = []

    important_keys = [
        "bidNtceNm", "dminsttNm", "ntceInsttNm", "orderInsttNm",
        "realDmndInsttNm", "prtcptPsblRgnNm", "prtcptPsblRgn",
        "bidPrtcptLmtRgnNm", "rgnLmtNm", "rgnLmt", "cnstrtsiteRgnNm",
        "indstrytyNm", "lcnsLmtNm", "bidPrtcptLmtYn",
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


def region_aliases(region_value: str) -> list:
    aliases = {
        "서울특별시": ["서울", "서울특별시"],
        "경기도": ["경기", "경기도"],
        "인천광역시": ["인천", "인천광역시"],
        "부산광역시": ["부산", "부산광역시"],
        "대구광역시": ["대구", "대구광역시"],
        "광주광역시": ["광주", "광주광역시"],
        "대전광역시": ["대전", "대전광역시"],
        "울산광역시": ["울산", "울산광역시"],
        "세종특별자치시": ["세종", "세종특별자치시"],
        "강원특별자치도": ["강원", "강원도", "강원특별자치도"],
        "충청북도": ["충북", "충청북도"],
        "충청남도": ["충남", "충청남도"],
        "전북특별자치도": ["전북", "전라북도", "전북특별자치도"],
        "전라남도": ["전남", "전라남도"],
        "경상북도": ["경북", "경상북도"],
        "경상남도": ["경남", "경상남도"],
        "제주특별자치도": ["제주", "제주도", "제주특별자치도"],
    }
    return aliases.get(region_value, [region_value])


def keywords_for_region(region: str) -> list:
    if not region:
        return []

    region = region.strip()

    if region in REGION_KEYWORDS:
        return REGION_KEYWORDS.get(region, [])

    if "/" in region:
        sido, sigun = region.split("/", 1)

        if sigun == "전체":
            return region_aliases(sido)

        # 김해시, 창녕군처럼 시·군을 선택한 경우에는
        # 도 전체가 아니라 해당 시·군 이름 중심으로 검색합니다.
        return [sigun]

    old_map = {
        "경남 전체": ["경남", "경상남도"],
        "경북 전체": ["경북", "경상북도"],
        "부산 전체": ["부산", "부산광역시"],
        "울산 전체": ["울산", "울산광역시"],
        "김해시": ["김해", "김해시"],
        "창녕군": ["창녕", "창녕군"],
    }

    return old_map.get(region, [region])


def match_region(item: dict, region: str) -> bool:
    if not region or region == "전체":
        return True

    region = region.strip()

    if region == "전국":
        return bool(get_nationwide_reason(item))

    keywords = keywords_for_region(region)
    text = make_search_text(item)

    return any(keyword in text for keyword in keywords if keyword)


def infer_region_label(item: dict) -> str:
    region_text = get_region_text(item)

    if region_text:
        return region_text

    text = make_search_text(item)
    found = []

    for region in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
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
        if any(keyword in text for keyword in keywords):
            found.append(license_name)

    return found


def infer_materials(item: dict) -> list:
    text = make_search_text(item)
    found = []

    for material_name, keywords in MATERIAL_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            found.append(material_name)

    return found


def infer_work_types(item: dict) -> list:
    text = make_search_text(item)
    found = []

    for work_type, keywords in WORK_TYPE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            found.append(work_type)

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


def fetch_nara_bids(keyword: str, page_no: int = 1, num_rows: int = 100, days_forward: int = 30) -> dict:
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
    materials = infer_materials(item)
    work_types = infer_work_types(item)

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
            result = fetch_nara_bids(keyword, page_no, num_rows, days_forward)

            if not result.get("ok"):
                errors.append({
                    "keyword": keyword,
                    "page_no": page_no,
                    "error": result.get("error"),
                    "preview": result.get("preview", ""),
                })
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


def match_profile_regions(item: dict, profile_regions: list) -> bool:
    if not profile_regions:
        return True

    for region in profile_regions:
        if match_region(item, region):
            return True

    return False


def get_profile_matched_regions(item: dict, profile_regions: list) -> list:
    matched = []

    for region in profile_regions or []:
        if match_region(item, region):
            matched.append(region_display_name(region))

    return matched


def profile_selected_terms(profile: dict) -> list:
    terms = []
    terms.extend(profile.get("licenses", []) or [])
    terms.extend(profile.get("work_types", []) or [])
    terms.extend(profile.get("material_supplies", []) or [])
    return terms


def profile_has_any_term(profile: dict, terms: list) -> bool:
    selected_text = " ".join(profile_selected_terms(profile))
    return any(term in selected_text for term in terms)


def bid_has_any_term(item: dict, terms: list) -> bool:
    text = make_search_text(item)
    return any(term in text for term in terms)


def get_profile_exclude_reason(item: dict, profile: dict) -> str:
    for group_name, rule in PROFILE_EXCLUDE_RULES.items():
        if bid_has_any_term(item, rule.get("bid_terms", [])):
            if not profile_has_any_term(profile, rule.get("profile_terms", [])):
                return f"{group_name} 관련 공고 - 회사 프로필에 해당 면허/공종 없음"
    return ""


def match_profile_specialty(item: dict, profile: dict) -> bool:
    selected_licenses = set(profile.get("licenses", []) or [])
    selected_work_types = set(profile.get("work_types", []) or [])
    selected_materials = set(profile.get("material_supplies", []) or [])

    if not selected_licenses and not selected_work_types and not selected_materials:
        return True

    if get_profile_exclude_reason(item, profile):
        return False

    inferred_licenses = set(infer_licenses(item))
    inferred_work_types = set(infer_work_types(item))
    inferred_materials = set(infer_materials(item))

    if selected_licenses and inferred_licenses.intersection(selected_licenses):
        return True

    if selected_work_types and inferred_work_types.intersection(selected_work_types):
        return True

    if selected_materials and inferred_materials.intersection(selected_materials):
        return True

    text = make_search_text(item)
    for keyword in split_keywords(profile.get("keyword_text", "")):
        if keyword and keyword in text:
            return True

    return False


def get_profile_specialty_reason(item: dict, profile: dict) -> str:
    exclude_reason = get_profile_exclude_reason(item, profile)
    if exclude_reason:
        return exclude_reason

    selected_licenses = set(profile.get("licenses", []) or [])
    selected_work_types = set(profile.get("work_types", []) or [])
    selected_materials = set(profile.get("material_supplies", []) or [])

    inferred_licenses = set(infer_licenses(item))
    inferred_work_types = set(infer_work_types(item))
    inferred_materials = set(infer_materials(item))

    matched = []

    license_match = inferred_licenses.intersection(selected_licenses)
    work_match = inferred_work_types.intersection(selected_work_types)
    material_match = inferred_materials.intersection(selected_materials)

    if license_match:
        matched.append("면허: " + ", ".join(sorted(license_match)))

    if work_match:
        matched.append("공종: " + ", ".join(sorted(work_match)))

    if material_match:
        matched.append("자재: " + ", ".join(sorted(material_match)))

    if matched:
        return " / ".join(matched)

    text = make_search_text(item)
    keyword_match = [kw for kw in split_keywords(profile.get("keyword_text", "")) if kw and kw in text]

    if keyword_match:
        return "키워드: " + ", ".join(keyword_match[:5])

    return "-"




def match_profile_siping(item: dict, profile: dict) -> bool:
    """
    시공능력평가액이 입력되어 있으면,
    공고 금액이 시평액보다 큰 공고는 내 회사 맞춤 공고에서 제외합니다.

    단, 나라장터 API에서 금액을 못 읽은 공고는 일단 포함합니다.
    """
    profile_limit = int(profile.get("siping_amount") or 0)

    if profile_limit <= 0:
        return True

    bid_amount = get_bid_amount(item)

    if bid_amount <= 0:
        return True

    return bid_amount <= profile_limit


def get_profile_siping_reason(item: dict, profile: dict) -> str:
    profile_limit = int(profile.get("siping_amount") or 0)
    bid_amount = get_bid_amount(item)

    if profile_limit <= 0:
        return "시평액 미입력"

    if bid_amount <= 0:
        return "공고 금액 정보 없음"

    if bid_amount <= profile_limit:
        return f"시평액 이내: {format_money(bid_amount)} / {format_money(profile_limit)}"

    return f"시평액 초과: {format_money(bid_amount)} / {format_money(profile_limit)}"


def search_bids_for_profile(
    profile: dict,
    exclude_closed: bool = True,
    days_forward: int = 30,
    pages_per_keyword: int = 1,
    num_rows: int = 100,
) -> dict:
    keywords = split_keywords(profile.get("keyword_text", ""))
    profile_regions = profile.get("possible_regions", [])

    all_items = []
    errors = []

    for keyword in keywords:
        for page_no in range(1, pages_per_keyword + 1):
            result = fetch_nara_bids(keyword, page_no, num_rows, days_forward)

            if not result.get("ok"):
                errors.append({
                    "keyword": keyword,
                    "page_no": page_no,
                    "error": result.get("error"),
                    "preview": result.get("preview", ""),
                })
                continue

            for item in result.get("items", []):
                if exclude_closed and is_closed(item):
                    continue

                if not match_profile_regions(item, profile_regions):
                    continue

                if not match_profile_specialty(item, profile):
                    continue

                if not match_profile_siping(item, profile):
                    continue

                bid = simplify_bid(item, keyword=keyword)
                matched_regions = get_profile_matched_regions(item, profile_regions)
                bid["profile_match_region_label"] = ", ".join(matched_regions) if matched_regions else "-"
                specialty_reason = get_profile_specialty_reason(item, profile)
                siping_reason = get_profile_siping_reason(item, profile)
                bid["profile_match_reason"] = f"{specialty_reason} / {siping_reason}" if specialty_reason != "-" else siping_reason
                all_items.append(bid)

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
        "mode": "profile",
        "exclude_closed": exclude_closed,
        "keywords": keywords,
        "profile_regions": profile_regions,
        "profile_regions_label": format_region_list(profile_regions),
        "count": len(deduped),
        "errors": errors,
        "bids": deduped,
    }


# =========================================================
# 회사 프로필
# =========================================================

def default_company_profile() -> dict:
    return {
        "company_name": "주식회사 송원건설",
        "manager_name": "",
        "address": "경상남도 김해시 삼문로19, 1205호",
        "phone": "055-339-4763",
        "fax": "055-339-4764",
        "email": "songwon4763@naver.com",
        "main_region": "경상남도/전체",
        "possible_regions": [
            "전국",
            "경상남도/전체",
            "경상남도/김해시",
            "경상남도/창녕군",
            "부산광역시/전체",
            "울산광역시/전체",
            "경상북도/전체",
        ],
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

    parts = re.split(r"[,，\n/]+", keyword_text)
    keywords = []

    for part in parts:
        text = part.strip()
        if text:
            keywords.append(text)

    return keywords or SONGWON_KEYWORDS


# =========================================================
# HTML 함수
# =========================================================

def render_region_select_options(selected: str) -> str:
    html_parts = []

    for group in PROFILE_REGION_GROUPS:
        html_parts.append(f'<optgroup label="{h(group["title"])}">')

        for value, label in group["items"]:
            selected_text = "selected" if value == selected else ""
            html_parts.append(f'<option value="{h(value)}" {selected_text}>{h(label)}</option>')

        html_parts.append("</optgroup>")

    return "".join(html_parts)


def render_region_checkbox_group(name: str, selected: list) -> str:
    selected = selected or []
    group_html = []

    for group in PROFILE_REGION_GROUPS:
        item_html = []

        for value, label in group["items"]:
            checked = "checked" if value in selected else ""
            item_html.append(f"""
                <label class="check-item">
                    <input type="checkbox" name="{h(name)}" value="{h(value)}" {checked}>
                    {h(label)}
                </label>
            """)

        group_html.append(f"""
            <div class="region-group">
                <h4>{h(group["title"])}</h4>
                <div class="check-grid">{"".join(item_html)}</div>
            </div>
        """)

    return "".join(group_html)


def render_checkbox_group(name: str, options: list, selected: list) -> str:
    html_parts = []
    selected = selected or []

    for option in options:
        checked = "checked" if option in selected else ""
        html_parts.append(f"""
            <label class="check-item">
                <input type="checkbox" name="{h(name)}" value="{h(option)}" {checked}>
                {h(option)}
            </label>
        """)

    return f'<div class="check-grid">{"".join(html_parts)}</div>'


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

        rows.append(f"""
            <tr>
                <td class="num">{idx}</td>
                <td><span class="{dday_class}">{h(dday)}</span></td>
                <td class="title">
                    <div class="bid-name">{h(bid.get("bid_name"))}</div>
                    <div class="small">공고번호: {h(bid.get("bid_no"))} / 키워드: {h(bid.get("keyword"))}</div>
                </td>
                <td>{h(bid.get("category"))}</td>
                <td>{h(bid.get("license_label"))}</td>
                <td>{h(bid.get("work_type_label"))}</td>
                <td>{h(bid.get("material_label"))}</td>
                <td>{h(bid.get("profile_match_reason", "-"))}</td>
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
        """)

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
                    <th>공종 추정</th>
                    <th>자재 추정</th>
                    <th>맞춤 사유</th>
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
                min-width: 1600px;
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
                max-height: 520px;
                overflow-y: auto;
                padding: 4px;
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

            .region-group {{
                margin-bottom: 18px;
                border: 1px solid #eef2f6;
                border-radius: 12px;
                padding: 12px;
                background: #fcfcfd;
            }}

            .region-group h4 {{
                margin: 0 0 10px;
                font-size: 15px;
                color: #123;
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


# =========================================================
# 라우트
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gongsa-bid",
        "version": "my-bids-siping-filter-1.0.0",
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
            "/bids/my-page",
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
            회사 프로필에서 지역, 시공능력평가액, 면허, 공종, 자재납품 품목을 저장할 수 있습니다.
        </p>

        <div class="menu">
            <a class="top-btn" href="/bids/my-page">내 회사 맞춤 공고</a>
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
            <strong>주 활동지역:</strong> {h(region_display_name(profile.get("main_region")))}<br>
            <strong>입찰 가능지역:</strong> {h(format_region_list(profile.get("possible_regions", [])))}<br>
            <strong>시공능력평가액:</strong> {h(format_money(profile.get("siping_amount", 0)))}<br>
            <strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "아직 선택 안 함")}<br>
            <strong>주력 공종:</strong> {h(", ".join(profile.get("work_types", [])) if profile.get("work_types") else "아직 선택 안 함")}<br>
            <strong>자재납품 품목:</strong> {h(", ".join(profile.get("material_supplies", [])) if profile.get("material_supplies") else "아직 선택 안 함")}<br>
            <strong>주력 키워드:</strong> {h(profile.get("keyword_text"))}
        </div>
    </div>
    """

    return page_layout("gongsa-bid", "건설회사 전용 나라장터 공고 웹플랫폼", body)


@app.get("/company/profile", response_class=HTMLResponse)
def company_profile_page():
    profile = load_company_profile()

    body = f"""
    <div class="card">
        <div class="summary">
            <span class="badge">회사 프로필 등록</span>
            <span class="badge">시평액 입력칸 포함</span>
            <span class="badge">깔끔한 지역 선택</span>
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
                    <label>시공능력평가액</label>
                    <input type="text" name="siping_amount_text" value="{h(profile.get("siping_amount_text", ""))}" placeholder="예: 10억 또는 1,000,000,000">
                </div>

                <div class="form-row">
                    <label>주 활동지역</label>
                    <select name="main_region">
                        {render_region_select_options(profile.get("main_region"))}
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
                전국, 경상남도, 김해시, 창녕군처럼 깔끔하게 보이지만 내부 저장은 정확히 구분됩니다.
            </p>
            {render_region_checkbox_group("possible_regions", profile.get("possible_regions", []))}
        </div>

        <div class="card">
            <h3>보유 종합건설 면허</h3>
            <p class="notice">종합공사를 시공할 수 있는 면허를 선택하세요.</p>
            {render_checkbox_group("licenses", GENERAL_CONSTRUCTION_LICENSE_OPTIONS, profile.get("licenses", []))}
        </div>

        <div class="card">
            <h3>보유 전문건설 면허 / 주력분야</h3>
            <p class="notice">전문건설 대업종과 세부 주력분야를 선택하세요.</p>
            {render_checkbox_group("licenses", SPECIALTY_CONSTRUCTION_LICENSE_OPTIONS, profile.get("licenses", []))}
        </div>

        <div class="card">
            <h3>주력 공종</h3>
            <p class="notice">
                실제로 잘하는 공종을 선택하세요.
                나중에 공고명과 키워드를 보고 내 회사 맞춤 공고를 걸러내는 기준으로 사용합니다.
            </p>
            {render_checkbox_group("work_types", WORK_TYPE_OPTIONS, profile.get("work_types", []))}
        </div>

        <div class="card">
            <h3>자재납품 가능 품목</h3>
            <p class="notice">자재납품은 건설업 면허와 따로 저장합니다.</p>
            {render_checkbox_group("material_supplies", MATERIAL_SUPPLY_OPTIONS, profile.get("material_supplies", []))}
        </div>

        <div class="card">
            <h3>주력 검색 키워드</h3>
            <p class="notice">쉼표로 구분해서 입력하세요. 비워두면 기본 송원 키워드를 사용합니다.</p>
            <div class="form-row">
                <label>키워드</label>
                <textarea name="keyword_text">{h(profile.get("keyword_text"))}</textarea>
            </div>

            <button type="submit">회사 프로필 저장</button>
            <a class="top-btn" href="/">취소하고 첫 화면</a>
        </div>
    </form>
    """

    return page_layout("회사 프로필 등록", "회사 정보, 지역, 시공능력평가액, 면허, 공종, 자재납품 품목을 저장하는 화면입니다", body)


@app.get("/company/profile-save", response_class=HTMLResponse)
def company_profile_save(
    company_name: str = Query(""),
    manager_name: str = Query(""),
    address: str = Query(""),
    phone: str = Query(""),
    fax: str = Query(""),
    email: str = Query(""),
    main_region: str = Query("경상남도/전체"),
    possible_regions: List[str] = Query(default=[]),
    siping_amount_text: str = Query(""),
    licenses: List[str] = Query(default=[]),
    work_types: List[str] = Query(default=[]),
    material_supplies: List[str] = Query(default=[]),
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
        "siping_amount_text": siping_amount_text.strip(),
        "siping_amount": parse_profile_amount(siping_amount_text),
        "licenses": licenses,
        "work_types": work_types,
        "material_supplies": material_supplies,
        "keyword_text": keyword_text.strip(),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_company_profile(profile)

    body = f"""
    <div class="card">
        <h2>회사 프로필 저장 완료</h2>
        <p class="notice">
            회사 프로필이 저장되었습니다.<br>
            다음 단계에서 이 프로필의 가능지역, 시평액, 면허, 공종을 기준으로 맞춤 공고를 보여주도록 연결하면 됩니다.
        </p>

        <div class="profile-box">
            <strong>회사명:</strong> {h(profile.get("company_name"))}<br>
            <strong>담당자:</strong> {h(profile.get("manager_name"))}<br>
            <strong>주소:</strong> {h(profile.get("address"))}<br>
            <strong>전화:</strong> {h(profile.get("phone"))}<br>
            <strong>팩스:</strong> {h(profile.get("fax"))}<br>
            <strong>이메일:</strong> {h(profile.get("email"))}<br>
            <strong>주 활동지역:</strong> {h(region_display_name(profile.get("main_region")))}<br>
            <strong>입찰 가능지역:</strong> {h(format_region_list(profile.get("possible_regions", [])))}<br>
            <strong>시공능력평가액:</strong> {h(format_money(profile.get("siping_amount", 0)))}<br>
            <strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "선택 안 함")}<br>
            <strong>주력 공종:</strong> {h(", ".join(profile.get("work_types", [])) if profile.get("work_types") else "선택 안 함")}<br>
            <strong>자재납품 품목:</strong> {h(", ".join(profile.get("material_supplies", [])) if profile.get("material_supplies") else "선택 안 함")}<br>
            <strong>주력 키워드:</strong> {h(profile.get("keyword_text"))}<br>
            <strong>저장시간:</strong> {h(profile.get("updated_at"))}
        </div>

        <div class="menu">
            <a class="top-btn" href="/">첫 화면</a>
            <a class="top-btn" href="/company/profile">다시 수정하기</a>
            <a class="top-btn" href="/company/profile-data" target="_blank">JSON 확인</a>
            <a class="top-btn" href="/bids/my-page">내 회사 맞춤 공고</a>
            <a class="top-btn" href="/bids/songwon-page">공고 보기</a>
        </div>
    </div>
    """

    return page_layout("회사 프로필 저장 완료", "저장된 회사 정보를 확인하세요", body)


@app.get("/company/profile-data")
def company_profile_data():
    return JSONResponse(load_company_profile())


@app.get("/bids/nara")
def nara_json(
    keyword: str = Query("포장", description="검색 키워드"),
    region: str = Query("전체", description="지역 필터"),
    days_forward: int = Query(30, description="오늘부터 며칠 뒤까지 검색할지"),
):
    result = search_bids_by_keywords([keyword], region, True, days_forward, 1, 100)
    return JSONResponse(result)


@app.get("/bids/nara-page", response_class=HTMLResponse)
def nara_page(
    keyword: str = Query("포장"),
    region: str = Query("전체"),
    days_forward: int = Query(30),
):
    result = search_bids_by_keywords([keyword], region, True, days_forward, 1, 100)
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
        <div class="menu">{region_buttons}</div>
    </div>

    {error_html}

    <div class="card">{render_bid_table(result.get("bids", []))}</div>
    """

    return page_layout(f"개별 검색 - {keyword}", f"지역: {region} / 마감 지난 공고 제외 / D-day 표시", body)


@app.get("/bids/songwon-test")
def songwon_test(
    region: str = Query("전체"),
    days_forward: int = Query(30),
):
    profile = load_company_profile()
    keywords = split_keywords(profile.get("keyword_text", ""))

    return JSONResponse(search_bids_by_keywords(keywords, region, True, days_forward, 1, 100))



@app.get("/bids/my-page", response_class=HTMLResponse)
def my_bids_page(
    days_forward: int = Query(30),
):
    profile = load_company_profile()
    result = search_bids_for_profile(
        profile=profile,
        exclude_closed=True,
        days_forward=days_forward,
        pages_per_keyword=1,
        num_rows=100,
    )

    error_html = ""
    if result.get("errors"):
        error_html = f"""
        <div class="card">
            <h3>API 오류</h3>
            <div class="error">{h(json.dumps(result.get("errors"), ensure_ascii=False, indent=2))}</div>
        </div>
        """

    selected_regions = result.get("profile_regions_label") or "선택 안 함"

    body = f"""
    <div class="card">
        <div class="summary">
            <span class="badge">내 회사 맞춤 공고</span>
            <span class="badge">입찰 가능지역: {h(selected_regions)}</span>
            <span class="badge">공고 수: {h(result.get("count"))}개</span>
            <span class="badge">마감 지난 공고 제외</span>
            <a class="top-btn" href="/">첫 화면</a>
            <a class="top-btn" href="/company/profile">회사 프로필 수정</a>
            <a class="top-btn" href="/bids/songwon-page">전체 공고 보기</a>
        </div>
    </div>

    <div class="card">
        <h3>맞춤 공고 기준</h3>
        <p class="notice">
            회사 프로필의 <strong>입찰 가능지역 + 보유 면허 + 주력 공종 + 자재납품 품목 + 시공능력평가액</strong>을 기준으로 공고를 걸러봅니다.<br>
            전기공사, 건축공사처럼 회사 프로필에 없는 면허/공종은 내 회사 맞춤 공고에서 제외합니다.<br>
            시공능력평가액이 입력되어 있으면 공고 금액이 시평액보다 큰 공고는 제외합니다.
        </p>

        <div class="profile-box">
            <strong>회사명:</strong> {h(profile.get("company_name"))}<br>
            <strong>입찰 가능지역:</strong> {h(format_region_list(profile.get("possible_regions", [])))}<br>
            <strong>시공능력평가액:</strong> {h(format_money(profile.get("siping_amount", 0)))}<br>
            <strong>보유 면허:</strong> {h(", ".join(profile.get("licenses", [])) if profile.get("licenses") else "선택 안 함")}<br>
            <strong>주력 공종:</strong> {h(", ".join(profile.get("work_types", [])) if profile.get("work_types") else "선택 안 함")}<br>
            <strong>주력 키워드:</strong> {h(profile.get("keyword_text"))}
        </div>
    </div>

    {error_html}

    <div class="card">
        {render_bid_table(result.get("bids", []))}
    </div>
    """

    return page_layout(
        "내 회사 맞춤 공고",
        "회사 프로필의 입찰 가능지역, 보유 면허, 주력 공종, 시공능력평가액을 기준으로 공고를 보여줍니다",
        body,
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

    result = search_bids_by_keywords(keywords, region, True, days_forward, 1, 100)
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
            <a class="top-btn" href="/bids/my-page">내 회사 맞춤 공고</a>
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
            김해시, 창녕군 같은 지역 선택은 회사 프로필에서 깔끔하게 저장할 수 있습니다.
        </p>

        <div class="menu">{region_buttons}</div>
    </div>

    {error_html}

    <div class="card">{render_bid_table(result.get("bids", []))}</div>
    """

    return page_layout("송원건설 전체 공고 검색", "회사 프로필 시평액 입력 수정 버전", body)
