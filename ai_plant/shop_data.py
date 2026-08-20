"""
Shop Catalog Data for AI Plant Companion Widget
Defines items for Pot Saucers (화분 받침대) and Pet Companions (반려동물).
"""
from typing import Dict, Any

SAUCER_CATALOG: Dict[str, Dict[str, Any]] = {
    "basic": {
        "id": "basic",
        "name": "포근한 기본 도자기 받침",
        "emoji": "🪴",
        "cost": 0,
        "desc": "화분을 작업표시줄 위에 안정감 있게 안착시켜주는 기본 도자기 받침대입니다.",
        "color": "#D27D46"
    },
    "wood": {
        "id": "wood",
        "name": "따스한 내추럴 원목 받침대",
        "emoji": "🪵",
        "cost": 100,
        "desc": "자연의 나뭇결이 살아 숨쉬는 따스하고 아늑한 원목 트레이입니다.",
        "color": "#B45309"
    },
    "marble": {
        "id": "marble",
        "name": "순백의 로열 대리석 받침대",
        "emoji": "🏛️",
        "cost": 200,
        "desc": "은은한 마블 무늬가 고급스러운 깔끔한 프리미엄 대리석 받침대입니다.",
        "color": "#64748B"
    },
    "gold": {
        "id": "gold",
        "name": "황실의 찬란한 황금 받침대",
        "emoji": "👑",
        "cost": 350,
        "desc": "찬란한 금빛 광채와 보석 장식이 빛나는 럭셔리 골드 받침대입니다.",
        "color": "#EAB308"
    },
    "amethyst": {
        "id": "amethyst",
        "name": "신비로운 자수정 크리스탈",
        "emoji": "🔮",
        "cost": 500,
        "desc": "영롱한 보랏빛 크리스탈 오라와 별가루를 뿜어내는 마법의 받침대입니다.",
        "color": "#9333EA"
    },
    "rainbow": {
        "id": "rainbow",
        "name": "환상의 오로라 레인보우",
        "emoji": "🌈",
        "cost": 750,
        "desc": "일곱 빛깔 신비로운 오로라 빛무리가 화분을 환상적으로 감싸줍니다.",
        "color": "#EC4899"
    }
}

PET_CATALOG: Dict[str, Dict[str, Any]] = {
    "none": {
        "id": "none",
        "name": "반려동물 없음",
        "emoji": "🌱",
        "cost": 0,
        "desc": "화분 혼자서 조용하게 자라나는 상태입니다.",
        "species": "none"
    },
    "cat_calico": {
        "id": "cat_calico",
        "name": "사랑스러운 삼색 아기냥이",
        "emoji": "🐱",
        "cost": 250,
        "desc": "야옹~ 화분 옆에서 꼬리를 살랑이며 기분 좋게 낮잠과 그루밍을 즐겨요.",
        "species": "cat",
        "dialogues": [
            "야옹~ 꼬리를 살랑살랑 흔들며 화분을 쳐다봐요! 🐾",
            "골골송을 부르며 화분 옆에 얌전히 웅크려요. 💤",
            "공직자님 손길에 머리를 폭 비비며 애교를 부려요! 💕"
        ]
    },
    "cat_black": {
        "id": "cat_black",
        "name": "시크한 턱시도 고양이",
        "emoji": "🐈‍⬛",
        "cost": 300,
        "desc": "도도한 매력의 턱시도냥이! 화분 곁을 아장아장 걷다가 쿨쿨 잠들어요.",
        "species": "cat",
        "dialogues": [
            "시크하게 바라보다가 깜짝 윙크를 날려줘요! ✨",
            "화분 밑에서 세상 편안한 자세로 식빵을 구워요. 🍞",
            "사뿐사뿐 걸어와 앞발로 콕 찔러보며 인사해요! 🐾"
        ]
    },
    "dog_shiba": {
        "id": "dog_shiba",
        "name": "똘망똘망 시바견",
        "emoji": "🐶",
        "cost": 350,
        "desc": "멍멍! 쫑긋한 귀와 말린 꼬리를 흔들며 화분 주변을 신나게 돌아요.",
        "species": "dog",
        "dialogues": [
            "멍멍! 꼬리를 헬리콥터처럼 신나게 흔들어요! 🐕",
            "화분 곁에 턱을 괴고 엎드려 똘망똘망 눈을 맞춰요! ✨",
            "헤헤 웃으며 공직자님 손을 핥아 응원해줘요! 💛"
        ]
    },
    "dog_retriever": {
        "id": "dog_retriever",
        "name": "듬직한 골든 리트리버",
        "emoji": "🐕",
        "cost": 450,
        "desc": "온순하고 듬직한 천사견! 따스한 눈빛으로 공직자님과 화분을 지켜줘요.",
        "species": "dog",
        "dialogues": [
            "왕! 듬직한 꼬리로 바닥을 탁탁 치며 반겨줘요! 🌟",
            "화분 옆에 누워서 행복한 미소로 낮잠을 자요. 💤",
            "공직자님, 오늘 하루도 제가 든든하게 지켜드릴게요! 🐾"
        ]
    },
    "bunny_white": {
        "id": "bunny_white",
        "name": "앙증맞은 흰토끼",
        "emoji": "🐰",
        "cost": 300,
        "desc": "코를 킁킁거리며 화분 곁을 깡총깡총 뛰어다니는 귀여운 복토끼입니다.",
        "species": "bunny",
        "dialogues": [
            "깡총! 긴 귀를 쫑긋거리며 화분 잎사귀를 살펴봐요! 🌿",
            "앞발로 세수를 뽀짝뽀짝 하며 행운을 선물해요! 🍀",
            "공직자님 곁에 털썩 앉아 앙증맞게 코를 킁킁거려요! 💕"
        ]
    }
}
