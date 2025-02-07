import streamlit as st
import requests
import json

# 외부 파일에서 문제와 채점 기준 로드
with open('questions.json') as q_file:
    question_data = json.load(q_file)

with open('criteria.json') as c_file:
    criteria_data = json.load(c_file)

# Google Gemini API 호출 함수
def grade_answer_with_api(answer):
    # TODO: 실제 Google Gemini API의 엔드포인트 URL을 입력하세요.
    api_url = "https://api.google.com/gemini/v2/grade"
    
    # TODO: 실제 API 키 또는 인증 토큰을 입력하세요.
    headers = {
        "Authorization": "AIzaSyBky_Z7l-D3w9gzLUqNLvgoBoYtQb_eYhY",  # API 키 또는 인증 토큰
        "Content-Type": "application/json"
    }
    
    # API 요청에 포함할 데이터
    data = {
        "answer": answer
    }
    
    # API 요청 보내기
    response = requests.post(api_url, headers=headers, json=data)
    
    # API 응답 처리
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API 호출 실패: {response.status_code}")
        return None

# Streamlit 앱 구성
st.title("논술형 문제 채점 시스템")

# 사용자 입력 섹션
st.text_input("학번", key="student_id")
st.text_input("이름", key="student_name")
st.write("문제:")
st.write(question_data["question"])

answer = st.text_area("답안을 작성해 주세요:", height=200)

# 제출 버튼
if st.button("제출"):
    if not answer:
        st.error("답안을 작성해 주세요.")
    else:
        # API 호출하여 채점 결과 받기
        api_response = grade_answer_with_api(answer)
        
        if api_response:
            # API 응답 기반으로 점수 계산 및 출력
            total_score = sum(api_response.values())
            st.success(f"{st.session_state.student_name}({st.session_state.student_id})님, 총점: {total_score}점")
            
            # 각 기준별 점수 및 설명 출력
            for criterion, score in api_response.items():
                description = next(item for item in criteria_data[criterion] if item["점수"] == score)["설명"]
                st.write(f"{criterion}: {score}점 - {description}")

# Streamlit 앱 실행
if __name__ == "__main__":
    st.run()
