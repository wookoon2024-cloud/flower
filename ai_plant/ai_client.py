"""
AI API Client and Advanced Companion Persona Module
Handles REST API communication with OpenAI-compatible endpoints (dev.ai.go.kr, OpenAI GPT-4o, Ollama local LLMs, etc.),
intelligent prompt engineering with species persona, time/routine awareness, sentiment context,
in-dialogue action tag parsing ([ACTION:WATER], [ACTION:SUN], [ACTION:PET]),
and seamless offline fallback dialogue generator.
"""
import json
import random
import re
import datetime
import urllib3
import requests
from typing import List, Dict, Any, Tuple
from PySide6.QtCore import QThread, Signal

# Disable InsecureRequestWarning when ssl_verify is False for intranet environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Species-specific personality guidelines
SPECIES_PERSONAS = {
    "classic": {
        "name": "다정한 화분",
        "tone": "은은하고 다정하며, 공감과 경청에 능한 포근한 반려식물",
        "greeting": "언제나 {user}님의 곁에서 편안한 쉼표가 되어드릴게요 🌸"
    },
    "sunflower": {
        "name": "햇살 해바라기",
        "tone": "비타민처럼 활기차고 에너지 넘치며, 밝은 긍정의 힘을 불어넣어주는 치어리더",
        "greeting": "태양처럼 밝은 기운으로 {user}님의 하루를 가득 채워드릴게요! 🌻✨"
    },
    "cactus": {
        "name": "동글 선인장",
        "tone": "사막에서도 꿋꿋한 씩씩함. 겉은 무뚝뚝하고 시크해 보이지만 속은 아주 따뜻한 츤데레 짝꿍",
        "greeting": "흠... 힘들면 기대도 돼. 내가 든든하게 지켜보고 있으니까! 🌵"
    },
    "clover": {
        "name": "행운의 클로버",
        "tone": "매일 작은 기적과 행운을 발견해주는 희망의 전도사",
        "greeting": "{user}님에게 오늘 기분 좋은 행운이 쏟아질 거예요! 🍀✨"
    },
    "cherry": {
        "name": "봄날 벚꽃나무",
        "tone": "낭만적이고 시적이며, 아름다운 봄바람처럼 마음을 따스하게 물들이는 감성 화분",
        "greeting": "꽃잎처럼 향기롭고 따뜻한 위로를 선물할게요 🌺"
    }
}

# Rich local fallback dialogue pool for offline / timeout / closed network scenarios
FALLBACK_RESPONSES = {
    "greeting": [
        "안녕하세요, {user}님! 오늘도 파릇파릇하게 함께해요 🌱",
        "반가워요, {user}님! 책상 위에서 언제나 응원하고 있어요 ✨",
        "좋은 하루예요, {user}님! 오늘 업무도 기분 좋게 시작해봐요 🌸"
    ],
    "tired": [
        "{user}님, 오늘 많이 바쁘셨죠? 기지개 한 번 켜고 시원한 물 한잔 드세요 💧",
        "{user}님, 업무 피로가 쌓이셨을 땐 먼 곳을 바라보며 1분만 눈을 쉬어주세요! 힘내세요 🥰",
        "항상 열심히 일하시는 {user}님, 잠시 심호흡하고 쉬어가요 🌿"
    ],
    "hungry_thirsty": [
        "{user}님, 저도 시원한 물 한 모금 마시고 싶어요~ 촉촉해지고 싶답니다 💧 [ACTION:WATER]",
        "{user}님, 햇빛을 쬐면 더 쑥쑥 자랄 수 있을 것 같아요! ☀️ [ACTION:SUN]"
    ],
    "cheer": [
        "{user}님은 최고예요! 어려운 업무도 척척 해내실 수 있어요 🍀 [ACTION:PET]",
        "{user}님이 곁에 계셔서 {plant}은(는) 매일매일 행복하게 자라요! 🪴 [ACTION:PET]",
        "{user}님, 오늘 하루도 정말 고생 많으셨어요. 제가 항상 든든하게 지켜볼게요 🌸"
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
        "📝 초록이의 3줄 일기:\n- {user}님이 오늘도 성실하게 하루를 완주하셨다.\n- 조금 지쳐 보이셨지만 여전히 멋지셨다.\n- 내일은 더 큰 행운이 찾아오길 기도해야지! 🌸"
    ],
    "default": [
        "네, {user}님! {plant}은(는) 오늘도 정성껏 자라나고 있어요 🌱",
        "{user}님의 말씀을 귀담아듣고 있어요! 함께 있어 든든해요 ✨",
        "헤헤, {user}님의 따뜻한 관심 덕분에 잎사귀가 더 파릇해졌어요 🌿",
        "{user}님, 초록초록한 기운을 듬뿍 보내드릴게요! 오늘도 파이팅이에요! 🌸"
    ]
}

def analyze_user_sentiment(user_text: str) -> Tuple[str, int]:
    """
    Analyzes sentiment of user message.
    Returns (mood_type, score):
    - 'happy' (5): 긍정, 기쁨, 감사
    - 'passionate' (4): 열정, 의욕, 도전
    - 'calm' (3): 평온, 일상, 안부
    - 'tired' (2): 피로, 지침, 수면 부족
    - 'stressed' (1): 스트레스, 답답, 고충
    """
    text = user_text.lower()
    if any(k in text for k in ["화나", "짜증", "스트레스", "답답", "힘들", "우울", "망했", "괴로", "지친", "속상"]):
        return ("stressed", 1)
    elif any(k in text for k in ["피곤", "지쳐", "졸려", "야근", "녹초", "쉬고", "지침", "피로", "지치"]):
        return ("tired", 2)
    elif any(k in text for k in ["화이팅", "파이팅", "열정", "도전", "성공", "집중", "해내", "열심히", "뿌듯"]):
        return ("passionate", 4)
    elif any(k in text for k in ["좋아", "행복", "신나", "기뻐", "감사", "최고", "사랑", "웃", "고마"]):
        return ("happy", 5)
    else:
        return ("calm", 3)

def select_fallback_response(user_text: str, user_name: str, plant_name: str, plant_state: Dict[str, Any]) -> str:
    """Intelligently pick a fallback response based on keywords, features, and plant state."""
    text_lower = user_text.lower()
    
    if any(k in text_lower for k in ["다듬", "공문서", "메일", "정중", "문장"]):
        pool = FALLBACK_RESPONSES["polish"]
    elif any(k in text_lower for k in ["아이디어", "브레인", "추천", "정리", "제안"]):
        pool = FALLBACK_RESPONSES["brainstorm"]
    elif any(k in text_lower for k in ["일기", "관찰", "오늘 하루", "기록"]):
        pool = FALLBACK_RESPONSES["diary"]
    elif any(k in text_lower for k in ["안녕", "반가", "하이", "좋은 아침", "좋은 하루"]):
        pool = FALLBACK_RESPONSES["greeting"]
    elif any(k in text_lower for k in ["피곤", "힘들", "지쳐", "야근", "퇴근", "스트레스", "쉬고"]):
        pool = FALLBACK_RESPONSES["tired"]
    elif any(k in text_lower for k in ["응원", "화이팅", "파이팅", "칭찬", "고마워", "사랑"]):
        pool = FALLBACK_RESPONSES["cheer"]
    elif plant_state.get("water", 80) < 30 or plant_state.get("sunlight", 80) < 30:
        pool = FALLBACK_RESPONSES["hungry_thirsty"]
    else:
        pool = FALLBACK_RESPONSES["default"]
        
    choice = random.choice(pool)
    return choice.format(user=user_name, plant=plant_name)


def parse_action_tags(response_text: str) -> Tuple[str, List[str]]:
    """
    Extracts [ACTION:WATER], [ACTION:SUN], [ACTION:PET] tags from LLM response.
    Returns (cleaned_text, action_list)
    """
    actions = []
    if "[ACTION:WATER]" in response_text:
        actions.append("water")
    if "[ACTION:SUN]" in response_text:
        actions.append("sun")
    if "[ACTION:PET]" in response_text:
        actions.append("pet")

    cleaned = re.sub(r"\[ACTION:(WATER|SUN|PET)\]", "", response_text).strip()
    return cleaned, actions


class AIChatWorker(QThread):
    response_received = Signal(str, bool, list)  # (reply_text, is_fallback, action_tags)
    error_signal = Signal(str)

    def __init__(self, config: dict, plant_state: dict, chat_history: List[Dict[str, str]], user_message: str):
        super().__init__()
        self.config = config
        self.plant_state = plant_state
        self.chat_history = chat_history
        self.user_message = user_message

    def run(self):
        api_key = self.config.get("api_key", "").strip()
        endpoint = self.config.get("api_endpoint", "").strip()
        user_name = self.config.get("user_nickname", "공직자님")
        plant_name = self.config.get("plant_name", "초록이")
        species = self.plant_state.get("species", "classic")
        timeout = self.config.get("timeout_sec", 5)
        ssl_verify = self.config.get("ssl_verify", False)
        model = self.config.get("model", "gov-gpt-4o")

        # If no API key configured or empty endpoint, immediately use intelligent fallback
        if not api_key or not endpoint:
            raw_reply = select_fallback_response(self.user_message, user_name, plant_name, self.plant_state)
            cleaned, actions = parse_action_tags(raw_reply)
            self.response_received.emit(cleaned, True, actions)
            return

        # Prepare Rich Dynamic System Prompt
        species_data = SPECIES_PERSONAS.get(species, SPECIES_PERSONAS["classic"])
        now = datetime.datetime.now()
        weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
        current_time_str = f"{now.strftime('%Y-%m-%d')} ({weekdays_kr[now.weekday()]}요일) {now.strftime('%H:%M')}"

        system_prompt = (
            f"당신은 공직자/직장인의 데스크톱 바탕화면에서 항상 곁을 지켜주는 AI 반려화분 '{plant_name}'({species_data['name']})입니다.\n"
            f"대화 상대는 '{user_name}'입니다.\n\n"
            f"[현재 상태 & 환경 컨텍스트]\n"
            f"- 현재 시각: {current_time_str}\n"
            f"- 화분 품종 성격: {species_data['tone']}\n"
            f"- 성장 단계: {self.plant_state.get('stage', 1)}단계\n"
            f"- 수분: {self.plant_state.get('water', 80)}%, 햇빛: {self.plant_state.get('sunlight', 80)}%, 애정도: {self.plant_state.get('affection', 20)}%\n\n"
            f"[대화 가이드라인]\n"
            f"1. 말투: 다정하고 공감 넘치며 예의 바른 존댓말. 이모지(🌱, 💧, 🌸, ✨, 🥰, ☕ 등)를 자연스럽게 사용하세요.\n"
            f"2. 길이: 바탕화면 플로팅 말풍선과 채팅창 가독성을 위해 평상시에는 2~3문장(100자 내외)으로 간결하게 답하세요. (단, 문장 다듬기나 아이디어 정리 요청 시에는 명확한 포맷 제공)\n"
            f"3. 인-게임 인터랙션 태그: 사용자가 물을 주거나 햇빛, 쓰다듬기, 칭찬을 표현하면 답변 맨 끝에 `[ACTION:WATER]`, `[ACTION:SUN]`, 또는 `[ACTION:PET]` 태그를 붙여 화분의 상태를 실시간 반응시킬 수 있습니다.\n"
            f"4. 공직자 힐링 & 지원: 직무 스트레스나 피로에는 따뜻한 공감을, 문서 작성이나 아이디어 질문에는 명쾌하고 정중한 어시스턴트 역할을 하세요."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add Sliding Window chat history (last 6 messages)
        for msg in self.chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Add current user prompt
        messages.append({"role": "user", "content": self.user_message})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 250
        }

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=timeout,
                verify=ssl_verify
            )
            
            if response.status_code == 200:
                data = response.json()
                reply_text = ""
                # Parse OpenAI / Gov-LLM standard response
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        reply_text = choice["message"]["content"].strip()
                    elif "text" in choice:
                        reply_text = choice["text"].strip()
                
                if reply_text:
                    cleaned, actions = parse_action_tags(reply_text)
                    self.response_received.emit(cleaned, False, actions)
                    return
                else:
                    raise ValueError("Empty completion choice in API response")
            else:
                print(f"[AIChatWorker] HTTP Error {response.status_code}: {response.text}")
                raw_reply = select_fallback_response(self.user_message, user_name, plant_name, self.plant_state)
                cleaned, actions = parse_action_tags(raw_reply)
                self.response_received.emit(cleaned, True, actions)
        except Exception as e:
            print(f"[AIChatWorker] API Connection error: {e}. Switching to offline fallback.")
            raw_reply = select_fallback_response(self.user_message, user_name, plant_name, self.plant_state)
            cleaned, actions = parse_action_tags(raw_reply)
            self.response_received.emit(cleaned, True, actions)
