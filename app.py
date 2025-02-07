import streamlit as st
import os
import json
import re
import google.generativeai as genai

# 커스텀 CSS 적용 (배경, 글꼴, 카드 디자인 등)
st.markdown(
    """
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .title {
        font-family: 'Helvetica', sans-serif;
        font-size: 2.8em; 
        color: #3366cc;
        text-align: center;
        margin-bottom: 20px;
    }
    .header {
        font-family: 'Helvetica', sans-serif;
        font-size: 1.75em;
        color: #333;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .subheader {
        font-family: 'Helvetica', sans-serif;
        font-size: 1.25em;
        color: #555;
    }
    .score-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .criterion-item {
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# questions.json에서 문제 데이터 로드
with open('questions.json', encoding='utf-8') as f:
    question_data = json.load(f)

# criteria.json에서 채점 기준 데이터 로드
with open('criteria.json', encoding='utf-8') as f:
    criteria_data = json.load(f)

def build_criteria_text():
    """
    criteria.json에 있는 채점 기준을 동적으로 문자열로 변환하여 반환합니다.
    """
    criteria_text = ""
    for criterion, items in criteria_data.items():
        criteria_text += f"{criterion}:\n"
        for item in items:
            criteria_text += f"   - {item['점수']}점: {item['설명']}\n"
        criteria_text += "\n"
    return criteria_text

def build_expected_json_output():
    """
    criteria.json에 있는 모든 기준을 동적으로 JSON 출력 예시 형태로 생성합니다.
    """
    keys = list(criteria_data.keys())
    expected = "{" + ", ".join([f'"{key}": 0' for key in keys]) + "}"
    return expected

def grade_answer_with_api(answer):
    # 환경 변수에서 GEMINI_API_KEY를 가져옴
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        return None

    # API 키는 환경설정에서 별도로 관리하는 것이 보안상 좋습니다.
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    # Gemini 2.0 Flash Experimental 모델 생성
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
    )

    # 채팅 세션 시작 (이전 대화 기록 없음)
    chat_session = model.start_chat(history=[])

    # criteria.json의 내용으로 동적으로 프롬프트 작성
    criteria_text = build_criteria_text()
    expected_json = build_expected_json_output()

    prompt = f"""
학생의 답안:
{answer}

문제:
{question_data["question"]}

다음 채점 기준을 참고하여 학생의 답안을 평가해 주세요:
{criteria_text}
최종 결과를 아래와 같이 JSON 형식으로 출력해 주세요:
{expected_json}
    """

    # AI 모델에 프롬프트 전송
    response = chat_session.send_message(prompt)

    # 응답 내 순수 JSON 부분만 추출
    try:
        json_match = re.search(r'({.*})', response.text, re.DOTALL)
        if json_match:
            pure_json = json_match.group(1)
            result = json.loads(pure_json)
        else:
            st.error("적절한 JSON 형태를 찾지 못했습니다.")
            result = None
    except Exception as e:
        st.error("응답 파싱 실패: " + str(e))
        result = None

    return result

# 앱 제목 표시
st.markdown('<div class="title">논술형 문제 채점 시스템</div>', unsafe_allow_html=True)

# 좌측 사이드바에 학생 정보 입력 받기
with st.sidebar:
    st.markdown('<div class="header">학생 정보</div>', unsafe_allow_html=True)
    student_id = st.text_input("학번", key="student_id")
    student_name = st.text_input("이름", key="student_name")

# 본문: 문제 및 답안 입력 영역
st.markdown('<div class="header">문제</div>', unsafe_allow_html=True)
st.info(question_data["question"], icon="✍️")

st.markdown('<div class="header">답안 작성</div>', unsafe_allow_html=True)
answer = st.text_area("답안을 아래에 작성해주세요:", height=250)

# 제출 버튼 및 결과 처리
if st.button("제출"):
    if not answer:
        st.error("답안을 작성해 주세요.")
    else:
        with st.spinner("채점 중입니다... 잠시 기다려 주세요!"):
            api_response = grade_answer_with_api(answer)
        if api_response:
            try:
                total_score = sum(api_response.values())
                result_card = f"""
                <div class="score-card">
                    <h2>{student_name} ({student_id})님의 채점 결과</h2>
                    <h3>총점: {total_score}점</h3>
                    <hr>
                """
                # 각 평가 항목별 점수와 설명을 카드 형식으로 나열
                for criterion, score in api_response.items():
                    description = next(
                        (item["설명"] for item in criteria_data[criterion] if item["점수"] == score),
                        "설명이 없습니다."
                    )
                    result_card += f"""<p class="criterion-item"><strong>{criterion}</strong>: {score}점 &mdash; {description}</p>"""
                result_card += "</div>"
                st.markdown(result_card, unsafe_allow_html=True)
            except Exception as e:
                st.error("채점 결과 처리 중 오류 발생: " + str(e))
