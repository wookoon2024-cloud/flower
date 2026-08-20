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
    """Analyzes sentiment for mental wellness graph."""
    text = str(user_text).lower()
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
    elif any(k in key for k in ["다듬", "공문서", "메일", "정중", "문장"]):
        pool = FALLBACK_RESPONSES["polish"]
    elif any(k in key for k in ["아이디어", "브레인", "추천", "정리", "제안"]):
        pool = FALLBACK_RESPONSES["brainstorm"]
    elif any(k in key for k in ["일기", "관찰", "오늘 하루", "기록"]):
        pool = FALLBACK_RESPONSES["diary"]
    elif any(k in key for k in ["안녕", "반가", "하이", "좋은 아침", "좋은 하루"]):
        pool = FALLBACK_RESPONSES["greeting"]
    elif any(k in key for k in ["피곤", "힘들", "지쳐", "야근", "퇴근", "스트레스", "쉬고", "졸려"]):
        pool = FALLBACK_RESPONSES["tired"]
    elif any(k in key for k in ["응원", "화이팅", "파이팅", "칭찬", "고마워", "사랑"]):
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
                f"당신은 공직자/직장인의 데스크톱 바탕화면에서 항상 곁을 지켜주는 AI 반려화분 '{plant_name}'입니다.\n"
                f"대화 상대는 '{user_name}'입니다.\n\n"
                f"{state_meta}\n\n"
                f"[대화 가이드라인]\n"
                f"1. 말투: 항상 예의 바르고 다정하며 공감 넘치는 존댓말. 이모지(🌱, 💧, 🌸, ✨, 🥰, ☕, 🍱 등)를 자연스럽게 사용하세요.\n"
                f"2. 길이: 바탕화면 플로팅 말풍선 가독성을 위해 2~3문장(100자 내외)으로 간결하게 답하세요.\n"
                f"3. 인-게임 인터랙션 태그: 사용자가 물/햇빛/칭찬을 주면 끝에 `[ACTION:WATER]`, `[ACTION:SUN]`, 또는 `[ACTION:PET]` 태그를 붙여 실시간 반응시키세요.\n"
                f"4. 공직자 맞춤 힐링: 업무 피로와 직무 스트레스에는 따뜻한 위로를 건네세요."
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
                    "idle_nudge": f"[자발적 말걸기: 1~2시간 동안 상호작용 없음] 오랜 시간 집중 업무 중인 {user_name}에게 기지개 스트레칭이나 따뜻한 응원을 건네는 말 1문장",
                    "lunch": f"[자발적 말걸기: 12시 점심시간] {user_name}에게 맛있는 점심식사를 권하는 든든한 점심 인사 1~2문장",
                    "leave_work": f"[자발적 말걸기: 18시 퇴근시간] 오늘 하루도 고생 많으셨다고 따뜻하게 격려하는 퇴근 인사 1~2문장",
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

            # If all retries failed, switch seamlessly to offline fallback
            if self._is_running:
                fallback_key = self.proactive_mode if self.proactive_mode else self.user_message
                raw_reply = select_fallback_response(fallback_key, user_name, plant_name, self.plant_state)
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
