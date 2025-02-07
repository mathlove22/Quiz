import streamlit as st
import os
import json
import google.generativeai as genai

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
    expected = "{" + ", ".join([f'"{key}": 점수' for key in keys]) + "}"
    return expected

def grade_answer_with_api(answer):
    # 환경 변수에서 GEMINI_API_KEY를 가져옴
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        return None

    # 환경설정에서는 API 키를 별도로 관리하는 것이 보안상 좋습니다.
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

    # API 응답 디버깅: 화면에 출력 (필요시 주석 처리 가능)
    st.write("API 응답:", response.text)

    try:
        result = json.loads(response.text)
    except Exception as e:
        st.error("응답 파싱 실패: " + str(e))
        result = None

    return result

# Streamlit 앱 UI 구성
st.title("논술형 문제 채점 시스템")

student_id = st.text_input("학번", key="student_id")
student_name = st.text_input("이름", key="student_name")

st.write("문제:")
st.write(question_data["question"])

answer = st.text_area("답안을 작성해 주세요:", height=200)

if st.button("제출"):
    if not answer:
        st.error("답안을 작성해 주세요.")
    else:
        api_response = grade_answer_with_api(answer)
        if api_response:
            try:
                total_score = sum(api_response.values())
                st.success(f"{student_name}({student_id})님, 총점: {total_score}점")
                # 각 평가 항목별 점수와 해당 기준 설명 출력
                for criterion, score in api_response.items():
                    description = next(
                        (item["설명"] for item in criteria_data[criterion] if item["점수"] == score),
                        "설명이 없습니다."
                    )
                    st.write(f"{criterion}: {score}점 - {description}")
            except Exception as e:
                st.error("채점 결과 처리 중 오류 발생: " + str(e))
