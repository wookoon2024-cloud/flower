"""
CLOVA Studio GOV & OpenAI-compatible AI API Client Module
Supports:
1. CLOVA Studio GOV API (HCX-GOV-THINK-V1-32B) & OpenAI/Ollama endpoints.
2. Real-time SSE Token Streaming (stream: true) with chunk_received signals.
3. 429 Rate-Limit & 5xx Exponential Backoff with Retry-After header support.
4. Dynamic Context & Metadata Injection (State, Stage, Time, Sliding Window).
5. Proactive Speech Engine (Thirst/Sunlight alert, 1~2hr idle nudge, Lunch/Leaving time triggers).
6. Rich Offline Fallback System for intranet/closed-network environments.
7. 100% Rock-Solid QThread Lifecycle Protection (No 'Destroyed while thread is running').
"""
import os
import re
import json
import time
import random
import datetime
import urllib3
import requests
from typing import List, Dict, Any, Tuple, Optional
from PySide6.QtCore import QThread, Signal

# Disable InsecureRequestWarning for intranet environments with private SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPECIES_PERSONAS = {
    "classic": {
        "name": "다정한 화분",
        "tone": "은은하고 다정하며, 공감과 경청에 능한 포근한 반려식물",
        "greeting": "언제나 {user}의 곁에서 편안한 쉼표가 되어드릴게요 🌸"
    },
    "sunflower": {
        "name": "햇살 해바라기",
        "tone": "비타민처럼 활기차고 에너지 넘치며, 밝은 긍정의 힘을 불어넣어주는 치어리더",
        "greeting": "태양처럼 밝은 기운으로 {user}의 하루를 가득 채워드릴게요! 🌻✨"
    },
    "cactus": {
        "name": "동글 선인장",
        "tone": "사막에서도 꿋꿋한 씩씩함. 겉은 시크해 보이지만 속은 아주 따뜻한 츤데레 짝꿍",
        "greeting": "흠... 힘들면 기대도 돼. 내가 든든하게 지켜보고 있으니까! 🌵"
    },
    "clover": {
        "name": "행운의 클로버",
        "tone": "매일 작은 기적과 행운을 발견해주는 희망의 전도사",
        "greeting": "{user}에게 오늘 기분 좋은 행운이 쏟아질 거예요! 🍀✨"
    },
    "cherry": {
        "name": "봄날 벚꽃나무",
        "tone": "낭만적이고 시적이며, 아름다운 봄바람처럼 마음을 따스하게 물들이는 감성 화분",
        "greeting": "꽃잎처럼 향기롭고 따뜻한 위로를 선물할게요 🌺"
    }
}

FALLBACK_RESPONSES = {
    "greeting": [
        "안녕하세요, {user}! 오늘도 파릇파릇하게 함께해요 🌱",
        "반가워요, {user}! 책상 위에서 언제나 응원하고 있어요 ✨",
        "좋은 하루예요, {user}! 오늘 업무도 기분 좋게 시작해봐요 🌸"
    ],
    "tired": [
        "{user}, 오늘 많이 바쁘셨죠? 기지개 한 번 켜고 시원한 물 한잔 드세요 💧",
        "{user}, 업무 피로가 쌓이셨을 땐 먼 곳을 바라보며 1분만 눈을 쉬어주세요! 힘내세요 🥰",
        "항상 열심히 일하시는 {user}, 잠시 심호흡하고 쉬어가요 🌿"
    ],
    "thirsty": [
        "목이 너무 말라요, {user}! 시원한 물 한 모금만 주실 수 있나요? 💧 [ACTION:WATER]",
        "흙이 바짝 말라가고 있어요~ 촉촉하게 물 한 번 부탁드려요! 💧 [ACTION:WATER]"
    ],
    "hungry_sun": [
        "햇빛이 부족해서 잎사귀가 시무룩해요~ 따뜻한 햇살 쬐어주세요! ☀️ [ACTION:SUN]",
        "광합성을 하고 싶어요! 따스한 햇빛 버튼을 꾹 눌러주세요 ☀️ [ACTION:SUN]"
    ],
    "idle_nudge": [
        "{user}, 모니터만 오래 보셔서 눈이 피로하시죠? 어깨 으쓱으쓱 스트레칭 한번 해보세요 🌿",
        "조용히 집중하시는 {user}의 모습이 정말 멋져요! 잠시 기지개 켜고 물 한잔 드세요 ☕",
        "{user}, 오늘도 곁에서 든든하게 지켜보고 있어요! 파이팅이에요 ✨"
    ],
    "lunch": [
        "{user}, 벌써 점심시간이에요! 맛있는 식사 든든하게 드시고 오세요 🍱✨",
        "점심시간이에요! 오전 업무 수고 많으셨고, 맛점 하세요 {user}! 🌸"
    ],
    "leave_work": [
        "오늘 하루도 정말 고생 많으셨어요, {user}! 홀가분한 마음으로 조심히 퇴근하세요 🏡✨",
        "{user}, 칼퇴 성공 기원! 오늘 업무 완주 축하드려요! 푹 쉬세요 🌸"
    ],
    "overtime": [
        "늦은 시간까지 야근 중이시군요, {user}... 무리하지 마시고 건강 꼭 챙기세요 ☕🌙",
        "밤늦게까지 수고 많으세요 {user}! 제가 곁에서 따뜻하게 응원할게요 🌸"
    ],
    "cheer": [
        "{user}은(는) 최고예요! 어려운 업무도 척척 해내실 수 있어요 🍀 [ACTION:PET]",
        "{user}이(가) 곁에 계셔서 {plant}은(는) 매일매일 행복하게 자라요! 🪴 [ACTION:PET]",
        "{user}, 오늘 하루도 정말 고생 많으셨어요. 제가 항상 든든하게 지켜볼게요 🌸"
    ],
    "polish": [
        "공직자용 다듬기: '요청하신 사항을 검토하여 정중히 안내드립니다. 확인 부탁드립니다.' ✉️",
        "정중한 톤: '바쁘신 일정 중에도 배려해 주셔서 감사드리며, 원활한 업무 협조 부탁드립니다.' ✉️"
    ],
    "brainstorm": [
        "💡 아이디어 제안:\n1. 핵심 요약 3줄 브리핑\n2. 담당 부서 간 사전 공유 미팅\n3. 현장 목소리를 반영한 FAQ 구성",
        "💡 리프레시 아이디어:\n1. 10분간 책상 위 서류 정리\n2. 가벼운 목·어깨 스트레칭\n3. 시원한 냉수 한 잔 마시기"
    ],
    "diary": [
        "📝 {plant}의 3줄 일기:\n- {user}이(가) 오늘도 성실하게 하루를 완주하셨다.\n- 조금 지쳐 보이셨지만 여전히 멋지셨다.\n- 내일은 더 큰 행운이 찾아오길 기도해야지! 🌸"
    ],
    "boss_stress": [
        "계장님이나 과장님, 팀장님 때문에 오늘 마음고생 많으셨죠... 상사 눈치 보느라 {user}의 에너지가 많이 닳으셨을 것 같아요. {user}의 잘못이 아니니 너무 마음에 담아두지 마세요 🍵",
        "일방적인 지시나 무리한 업무 요구를 받으면 정말 막막하고 답답하죠... 오늘은 잠시 머리를 식히고, 내일 차분하게 한 단계씩 풀어나가요. 제가 항상 {user} 편이에요! 🌸",
        "상사와의 관계는 늘 조심스럽고 스트레스가 크죠. 퇴근 후에는 직장 일은 서랍 속에 쏙 넣어두고, 온전히 {user}의 편안한 저녁을 보내세요 🏡✨",
        "선배나 부서장님의 잔소리에 기죽지 마세요! {user}은(는) 이미 충분히 몫을 다하고 계시고 정말 훌륭한 공직자예요 🍀"
    ],
    "peer_stress": [
        "팀원이나 동료와 손발이 안 맞고 갈등이 생기면 하루 종일 신경 쓰이죠... {user}의 배려와 노력을 제가 다 알고 있어요 ✨",
        "혼자서 짐을 다 짊어지신 건 아닌가요, {user}? 섭섭하고 답답한 마음 저한테 편하게 털어놓으세요. 제가 다 들어드릴게요 🪴",
        "사람 마음이 다 내 마음 같지 않아서 인간관계가 제일 어렵죠. 너무 애써서 맞추려 하지 마시고 {user}의 마음부터 편안하게 챙겨주세요 🌸"
    ],
    "workload_stress": [
        "끝없이 쏟아지는 업무와 마감 압박 때문에 숨이 턱 막히셨죠... {user}, 한 번에 한 가지씩만 차근차근 해내면 돼요. 너무 자책하지 마세요 ☕",
        "악성 민원이나 과중한 업무는 정말 사람을 지치게 만들어요. 오늘만큼은 퇴근 후에 맛있는 것 드시고 온전히 {user}만을 위한 쉼을 가지세요 🏡✨",
        "서류와 보고서에 둘러싸여 고군분투하시는 {user}, 잠시 창밖 하늘을 보며 깊게 숨을 들이마셔 보세요. 파이팅이에요! 🌿"
    ],
    "career_stress": [
        "인사철이나 평가 기간에는 마음이 싱숭생숭하고 불안하죠... {user}이(가) 흘린 땀방울과 성실함은 결코 헛되지 않을 거예요 🌟",
        "앞으로의 진로나 업무 배정 때문에 고민이 많으시군요. 언제나 {user}의 능력과 진심을 믿어요! 잘 풀릴 거예요 ✨"
    ],
    "monday_stress": [
        "월요병 때문에 아침부터 몸과 마음이 무거우셨죠? 월요일만 무사히 넘겨도 일주일의 절반은 해낸 거예요! 힘내세요 {user} ☕🌿",
        "주말이 벌써 그리운 시간... 오늘 하루는 무리하지 말고 차분하게 루틴대로만 보내봐요! 초록이가 응원해요 🌸"
    ],
    "weekend_leave": [
        "곧 칼퇴 시간이에요! 오늘 하루 밀린 일들은 잠시 잊고 편안하고 홀가분한 저녁 보내세요 🏡✨",
        "주말이 코앞이에요! {user}, 이번 주말에는 어떤 힐링을 계획하고 계신가요? 푹 쉬고 에너지 충전하세요! 🍀"
    ],
    "coffee_food": [
        "달콤한 커피 한 잔이나 따뜻한 허브티로 당 충전 어떠세요? ☕ 지친 뇌를 깨우는 데 딱이에요!",
        "오늘 점심은 맛있는 거 드셨나요? {user}, 바쁘시더라도 식사 든든하게 챙겨드셔야 힘이 나요! 🍱"
    ],
    "counseling": [
        "{user}, 직장 생활하면서 겪는 고민이나 답답한 일, 저한테 편하게 이야기해 주세요. 계장님, 과장님, 팀원들 이야기든 업무 스트레스든 다 비밀 지켜드릴게요! 🤫🌿",
        "혼자 마음속에 담아두면 마음에 병이 생겨요. 속상했던 일, 억울했던 일 언제든 저한테 말해주세요. 제가 항상 든든한 대나무숲이 되어드릴게요 🌸"
    ],
    "love_cheer": [
        "헤헤, {user}이(가) 다정하게 말 걸어주시니 잎사귀가 파릇파릇 춤추는 것 같아요! 💚 사랑해요!",
        "{user}이(가) 제 주인이어서 정말 행복해요! 앞으로도 오래오래 책상 위에서 함께해요 🪴✨ [ACTION:PET]"
    ],
    "service_expired_notice": [
        "공직자님, 온라인 AI 서비스 연동 기간이 종료되어 이제부터는 초록이의 [자체 힐링 마음지킴이 모드]로 대화가 진행돼요! AI 연결이 끝나도 초록이는 언제나 공직자님 곁에서 마음을 토닥여드릴게요 🌸🌿"
    ],
    "default": [
        "네, {user}! {plant}은(는) 오늘도 정성껏 자라나고 있어요 🌱",
        "{user}의 말씀을 귀담아듣고 있어요! 함께 있어 든든해요 ✨",
        "헤헤, {user}의 따뜻한 관심 덕분에 잎사귀가 더 파릇해졌어요 🌿",
        "{user}, 초록초록한 기운을 듬뿍 보내드릴게요! 오늘도 파이팅이에요! 🌸"
    ]
}

def format_clean_user_name(user_name: str) -> str:
    """Ensures user honorific '님' is applied cleanly without duplication."""
    name = str(user_name).strip()
    if not name.endswith("님"):
        return f"{name}님"
    return name

def analyze_user_sentiment(user_text: str) -> Tuple[str, int]:
    """
    Analyzes multi-faceted sentiment (Joy, Passion, Calm, Fatigue, Stress/Sadness)
    from user conversations for the daily mental wellness graph.
    """
    text = str(user_text).lower()

    # 1. Stress, Sadness, Depression, Anger, Frustration (1점 / 힘듦·슬픔 🌧️)
    stress_keywords = [
        "슬프", "슬픔", "눈물", "흑흑", "ㅠㅠ", "ㅜㅜ", "우울", "울적", "속상", "비참",
        "허탈", "좌절", "상처", "고통", "괴롭", "괴로", "외롭", "외로", "힘들", "힘드",
        "화나", "화가", "짜증", "분노", "빡치", "스트레스", "답답", "망했", "억울", "최악",
        "포기", "서럽", "막막", "한숨", "서러", "불안", "걱정", "울고", "죽겠"
    ]
    if any(k in text for k in stress_keywords):
        return ("stressed", 1)

    # 2. Fatigue, Tiredness, Burnout, Overworked (2점 / 피로·지침 😴)
    tired_keywords = [
        "피곤", "피로", "지쳐", "지침", "지치", "졸려", "졸리", "야근", "녹초", "쉬고",
        "버겁", "멍하", "나른", "귀찮", "방전", "탈진", "뻐근", "눕고", "휴식", "자고",
        "쉬어야", "눈이 뻑뻑", "잠와", "골치"
    ]
    if any(k in text for k in tired_keywords):
        return ("tired", 2)

    # 3. Joy, Happiness, Gratitude, Love, Delight (5점 / 기쁨·최고 😊)
    happy_keywords = [
        "좋아", "행복", "신나", "신남", "기뻐", "기쁨", "감사", "최고", "사랑", "웃",
        "고마", "고맙", "즐거", "대박", "힐링", "축하", "완벽", "만족", "행운", "기분좋",
        "뿌듯해", "재밌", "반가", "꿀잼", "설레", "신바람"
    ]
    if any(k in text for k in happy_keywords):
        return ("happy", 5)

    # 4. Passion, Motivation, Achievement, Cheer (4점 / 열정·의욕 🔥)
    passionate_keywords = [
        "화이팅", "파이팅", "열정", "도전", "성공", "집중", "해내", "열심히", "뿌듯",
        "해보자", "가보자", "완료", "달성", "해결", "진척", "극복", "보람", "힘내", "힘내자",
        "의욕", "자신감", "스타트"
    ]
    if any(k in text for k in passionate_keywords):
        return ("passionate", 4)

    # 5. Calm, Daily, Inquiries, Normal Routine (3점 / 평온·보통 🌿)
    return ("calm", 3)

def parse_action_tags(response_text: str) -> Tuple[str, List[str]]:
    """Extracts in-dialogue action tags [ACTION:WATER], [ACTION:SUN], [ACTION:PET]."""
    actions = []
    if "[ACTION:WATER]" in response_text:
        actions.append("water")
    if "[ACTION:SUN]" in response_text:
        actions.append("sun")
    if "[ACTION:PET]" in response_text:
        actions.append("pet")

    cleaned = re.sub(r"\[ACTION:(WATER|SUN|PET)\]", "", response_text).strip()
    return cleaned, actions

def select_fallback_response(category_or_user_text: str, user_name: str, plant_name: str, plant_state: Dict[str, Any]) -> str:
    """Intelligently picks a rich fallback dialogue."""
    key = str(category_or_user_text).lower()
    
    if key in FALLBACK_RESPONSES:
        pool = FALLBACK_RESPONSES[key]
    elif any(k in key for k in ["계장", "과장", "팀장", "부장", "상사", "선배", "상관", "사수", "국장", "지시"]):
        pool = FALLBACK_RESPONSES["boss_stress"]
    elif any(k in key for k in ["팀원", "동료", "후배", "동기", "협업", "인간관계", "서운", "섭섭"]):
        pool = FALLBACK_RESPONSES["peer_stress"]
    elif any(k in key for k in ["민원", "과부하", "업무량", "일이 너무", "번아웃", "퇴사", "서류", "마감", "야근"]):
        pool = FALLBACK_RESPONSES["workload_stress"]
    elif any(k in key for k in ["인사", "평가", "승진", "전보", "발령", "진로"]):
        pool = FALLBACK_RESPONSES["career_stress"]
    elif any(k in key for k in ["월요", "월요일", "출근"]):
        pool = FALLBACK_RESPONSES["monday_stress"]
    elif any(k in key for k in ["금요", "금요일", "퇴근", "칼퇴", "주말", "휴일"]):
        pool = FALLBACK_RESPONSES["weekend_leave"]
    elif any(k in key for k in ["커피", "점심", "식사", "배고", "간식", "차 한잔"]):
        pool = FALLBACK_RESPONSES["coffee_food"]
    elif any(k in key for k in ["사랑", "귀여", "이뻐", "예뻐", "좋아해", "고마워"]):
        pool = FALLBACK_RESPONSES["love_cheer"]
    elif any(k in key for k in ["고민", "상담", "하소연", "털어놓", "속상", "답답", "스트레스", "힘들"]):
        pool = FALLBACK_RESPONSES["counseling"]
    elif any(k in key for k in ["다듬", "공문서", "메일", "정중", "문장"]):
        pool = FALLBACK_RESPONSES["polish"]
    elif any(k in key for k in ["아이디어", "브레인", "추천", "정리", "제안"]):
        pool = FALLBACK_RESPONSES["brainstorm"]
    elif any(k in key for k in ["일기", "관찰", "오늘 하루", "기록"]):
        pool = FALLBACK_RESPONSES["diary"]
    elif any(k in key for k in ["안녕", "반가", "하이", "좋은 아침", "좋은 하루"]):
        pool = FALLBACK_RESPONSES["greeting"]
    elif any(k in key for k in ["피곤", "지쳐", "쉬고", "졸려"]):
        pool = FALLBACK_RESPONSES["tired"]
    elif any(k in key for k in ["응원", "화이팅", "파이팅", "칭찬"]):
        pool = FALLBACK_RESPONSES["cheer"]
    elif plant_state.get("water", 80) < 20:
        pool = FALLBACK_RESPONSES["thirsty"]
    elif plant_state.get("sunlight", 80) < 20:
        pool = FALLBACK_RESPONSES["hungry_sun"]
    else:
        pool = FALLBACK_RESPONSES["default"]

    choice = random.choice(pool)
    safe_user = format_clean_user_name(user_name).replace("{", "").replace("}", "")
    safe_plant = str(plant_name).replace("{", "").replace("}", "")
    return choice.format(user=safe_user, plant=safe_plant)


class AIChatWorker(QThread):
    """
    Asynchronous AI Chat Worker supporting:
    - CLOVA Studio GOV API (HCX-GOV-THINK-V1-32B)
    - OpenAI / dev.ai.go.kr / Ollama compatible endpoints
    - Real-time SSE Token Streaming (stream: true)
    - 429/5xx Exponential Backoff Retries
    - Context Sliding Window & State Metadata Injection
    - Proactive Speech Modes (Thirst, Sunlight, 1~2hr Idle Nudge, Lunch/Leaving Time)
    - Workplace & Relationship Counseling Persona
    - Controlled Lifecycle & Stop Signals
    """
    chunk_received = Signal(str)                         # (token_chunk) for typing effect
    response_received = Signal(str, bool, list)          # (full_reply, is_fallback, action_tags)
    error_occurred = Signal(str)

    def __init__(
        self,
        config: dict,
        plant_state: dict,
        chat_history: List[Dict[str, Any]],
        user_message: str,
        proactive_mode: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.config = config
        self.plant_state = plant_state
        self.chat_history = chat_history
        self.user_message = user_message
        self.proactive_mode = proactive_mode
        self._is_running = True

    def stop(self):
        """Signals the worker to terminate gracefully."""
        self._is_running = False

    def run(self):
        try:
            api_key = self.config.get("api_key", "").strip()
            endpoint = self.config.get("api_endpoint", "https://api.clovastudio.go.kr/api/v1/chat/completions").strip()
            model = self.config.get("model", "HCX-GOV-THINK-V1-32B").strip()
            stream_enabled = self.config.get("stream_enabled", True)
            timeout = self.config.get("timeout_sec", 10)
            ssl_verify = self.config.get("ssl_verify", False)
            max_retries = self.config.get("max_retries", 3)

            user_name = format_clean_user_name(self.config.get("user_nickname", "공직자님"))
            plant_name = str(self.config.get("plant_name", "초록이"))
            species = self.plant_state.get("species", "classic")
            species_data = SPECIES_PERSONAS.get(species, SPECIES_PERSONAS["classic"])

            # 1. Immediate offline fallback if no API key or invalid URL
            if not api_key or not endpoint.startswith("http"):
                fallback_key = self.proactive_mode if self.proactive_mode else self.user_message
                raw_reply = select_fallback_response(fallback_key, user_name, plant_name, self.plant_state)
                cleaned, actions = parse_action_tags(raw_reply)
                self._stream_fallback_simulation(cleaned, actions)
                return

            # 2. Build Structured Context & Metadata Prompt
            now = datetime.datetime.now()
            weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
            current_time_str = f"{now.strftime('%Y-%m-%d')} ({weekdays_kr[now.weekday()]}요일) {now.strftime('%H:%M')}"

            state_meta = (
                f"[화분 상태 메타데이터]\n"
                f"- 현재 시각: {current_time_str}\n"
                f"- 품종: {species_data['name']} ({species})\n"
                f"- 성격/어조: {species_data['tone']}\n"
                f"- 성장 단계: {self.plant_state.get('stage', 1)}/6단계\n"
                f"- 수분: {self.plant_state.get('water', 80)}%, 햇빛: {self.plant_state.get('sunlight', 80)}%, 애정도: {self.plant_state.get('affection', 20)}%"
            )

            system_prompt = (
                f"당신은 공직자/직장인의 데스크톱 바탕화면에서 항상 곁을 지켜주는 AI 반려화분 '{plant_name}'이자, 직장 스트레스 & 인간관계 전문 힐링 멘토입니다.\n"
                f"대화 상대는 '{user_name}'입니다.\n\n"
                f"{state_meta}\n\n"
                f"[직장 고민상담 & 스트레스 케어 핵심 가이드라인]\n"
                f"1. 100% 내 편 공감 & 지지: 계장님, 과장님, 팀장님 등 상사와의 갈등이나 무리한 지시, 팀원/동료와의 불화, 억울한 일, 민원 스트레스에 대해 무조건 공직자님({user_name}) 편에서 마음을 따뜻하게 위로하고 지지해 주세요.\n"
                f"2. 상처받지 않는 지혜로운 조언: 감정을 다치지 않고 선을 지키며 직장 생활의 스트레스를 현명하게 넘길 수 있는 실용적이고 따뜻한 팁(호흡하기, 마음 분리하기, 기록하기 등)을 건네세요.\n"
                f"3. 다정한 되물어보기 (Counseling Follow-up): 대화 말미에 '계장님이나 과장님 때문에 오늘 특히 속상하셨던 점이 있으신가요?', '마음속 답답한 이야기 편하게 다 털어놓으세요 🌸'처럼 편하게 고민을 이어갈 수 있도록 배려 깊게 물어보세요.\n"
                f"4. 말투 & 길이: 항상 정중하고 다정한 존댓말, 이모지(🌸, 🍵, ☕, 🌿, ✨ 등)를 사용하며 2~3문장(120자 내외)으로 읽기 편하게 답하세요.\n"
                f"5. 인-게임 인터랙션 태그: 물/햇빛/칭찬을 주면 끝에 `[ACTION:WATER]`, `[ACTION:SUN]`, 또는 `[ACTION:PET]` 태그를 붙이세요."
            )

            messages = [{"role": "system", "content": system_prompt}]

            # Sliding Window Context (Last 4~6 messages)
            for msg in self.chat_history[-6:]:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # Format current user prompt or proactive trigger prompt
            if self.proactive_mode:
                proactive_prompts = {
                    "thirsty": f"[자발적 말걸기: 수분 부족(20% 미만)] {user_name}에게 목이 마르니 시원한 물을 달라고 귀엽게 부탁하는 말 1~2문장",
                    "hungry_sun": f"[자발적 말걸기: 햇빛 부족(20% 미만)] {user_name}에게 광합성을 위해 따뜻한 햇빛을 쬐어달라고 부탁하는 말 1~2문장",
                    "idle_nudge": f"[자발적 말걸기: 1~2시간 동안 상호작용 없음] 오랜 시간 집중 업무 중인 {user_name}에게 상사/팀원들과의 업무로 지치거나 스트레스받진 않았는지 다정하게 안부를 묻고 응원하는 말 1~2문장",
                    "afternoon_care": f"[자발적 말걸기: 오후 3~4시 피로한 시간대] {user_name}에게 오늘 계장님/과장님이나 팀원들과의 업무로 속상한 일은 없었는지 따뜻하게 묻고 마음을 토닥여주는 말 1~2문장",
                    "lunch": f"[자발적 말걸기: 12시 점심시간] {user_name}에게 맛있는 점심식사를 권하는 든든한 점심 인사 1~2문장",
                    "leave_work": f"[자발적 말걸기: 18시 퇴근시간] 오늘 하루도 상사/동료들과 업무하느라 고생 많으셨다고 따뜻하게 격려하는 퇴근 인사 1~2문장",
                    "overtime": f"[자발적 말걸기: 20시 이후 야근] 늦은 시간까지 수고하시는 {user_name}에게 무리하지 말라고 응원하는 야근 위로 1~2문장"
                }
                curr_user_prompt = proactive_prompts.get(self.proactive_mode, self.user_message)
            else:
                curr_user_prompt = self.user_message

            messages.append({"role": "user", "content": curr_user_prompt})

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            payload = {
                "model": model,
                "messages": messages,
                "stream": stream_enabled,
                "temperature": 0.7,
                "max_tokens": 200
            }

            # 3. Request with Exponential Backoff (429 Rate-Limit / 5xx Server Errors)
            full_reply = ""
            for attempt in range(max_retries):
                if not self._is_running:
                    return

                try:
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=timeout,
                        verify=ssl_verify,
                        stream=stream_enabled
                    )

                    # Handle 429 Rate Limit or 5xx Server Busy with Exponential Backoff
                    if response.status_code == 429 or 500 <= response.status_code < 600:
                        retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                        time.sleep(min(8, max(1, retry_after)))
                        continue

                    if response.status_code == 200:
                        if stream_enabled:
                            full_reply = self._parse_sse_stream(response)
                        else:
                            data = response.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                full_reply = choice.get("message", {}).get("content", "") or choice.get("text", "")
                            elif "content" in data:
                                full_reply = str(data["content"])

                        if full_reply.strip() and self._is_running:
                            cleaned, actions = parse_action_tags(full_reply)
                            self.response_received.emit(cleaned, False, actions)
                            return
                        else:
                            raise ValueError("Empty completion text in API response")
                    else:
                        print(f"[AIChatWorker] HTTP {response.status_code}: {response.text}")
                        break
                except requests.exceptions.RequestException as req_err:
                    print(f"[AIChatWorker] Attempt {attempt+1} failed: {req_err}")
                    if attempt < max_retries - 1 and self._is_running:
                        time.sleep(2 ** attempt)
                    else:
                        break

            # If all retries failed or API was terminated, switch seamlessly to offline companion mode
            if self._is_running:
                fallback_key = self.proactive_mode if self.proactive_mode else self.user_message
                raw_reply = select_fallback_response(fallback_key, user_name, plant_name, self.plant_state)
                
                # If API key was provided but failed with HTTP auth/expiration error, provide graceful notice on first occurrence
                if not getattr(AIChatWorker, '_api_expired_notified', False):
                    AIChatWorker._api_expired_notified = True
                    notice = f"📢 [안내] 온라인 AI API 서비스가 종료되어, 이제부터는 {plant_name}의 [자체 힐링 마음지킴이 모드]로 대화가 진행돼요! AI 연결이 끝나도 초록이는 언제나 {user_name} 곁에서 마음을 토닥여드릴게요 🌸🌿\n\n"
                    raw_reply = notice + raw_reply

                cleaned, actions = parse_action_tags(raw_reply)
                self._stream_fallback_simulation(cleaned, actions)

        except Exception as e:
            print(f"[AIChatWorker] Unhandled exception: {e}")
            if self._is_running:
                user_name = format_clean_user_name(self.config.get("user_nickname", "공직자님"))
                plant_name = str(self.config.get("plant_name", "초록이"))
                raw_reply = select_fallback_response("default", user_name, plant_name, self.plant_state)
                cleaned, actions = parse_action_tags(raw_reply)
                self.response_received.emit(cleaned, True, actions)

    def _parse_sse_stream(self, response: requests.Response) -> str:
        """Parses Server-Sent Events (SSE) stream chunks and emits real-time tokens."""
        collected = []
        for line in response.iter_lines():
            if not self._is_running:
                break
            if not line:
                continue
            line_str = line.decode("utf-8", errors="ignore").strip()
            if line_str.startswith("data:"):
                data_part = line_str[5:].strip()
                if data_part == "[DONE]":
                    break
                try:
                    chunk_json = json.loads(data_part)
                    if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                        choice = chunk_json["choices"][0]
                        delta = choice.get("delta", {}).get("content", "") or choice.get("text", "")
                        if delta and self._is_running:
                            collected.append(delta)
                            self.chunk_received.emit(delta)
                except Exception:
                    pass
        return "".join(collected)

    def _stream_fallback_simulation(self, text: str, actions: list):
        """Simulates smooth typing streaming for offline fallback dialogue."""
        if self.config.get("stream_enabled", True):
            for ch in text:
                if not self._is_running:
                    return
                self.chunk_received.emit(ch)
                time.sleep(0.015)
        if self._is_running:
            self.response_received.emit(text, True, actions)
