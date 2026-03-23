import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import datetime

def init_db():
    if not firebase_admin._apps:
        try:
            # ────────────────────────────────────────────────
            # 방식 1: firebase_json 키 (JSON 1줄 문자열) — 가장 안정적
            # ────────────────────────────────────────────────
            if "firebase_json" in st.secrets:
                import json
                cert_dict = json.loads(st.secrets["firebase_json"])
                # JSON 파싱 결과는 이미 올바른 형식이므로 추가 처리 불필요
                cred = credentials.Certificate(cert_dict)
                firebase_admin.initialize_app(cred)

            # ────────────────────────────────────────────────
            # 방식 2: [firebase] 섹션 (TOML 개별 키 방식)
            #   → private_key 줄바꿈이 깨질 수 있어 교정 로직 적용
            # ────────────────────────────────────────────────
            elif "firebase" in st.secrets:
                cert_dict = dict(st.secrets["firebase"])
                if "private_key" in cert_dict:
                    pk = cert_dict["private_key"]
                    # \r 제거, 리터럴 \\n → 실제 \n 변환, 앞뒤 따옴표/공백 제거
                    pk = pk.replace("\r", "").replace("\\n", "\n").strip().strip('"').strip("'")
                    # PEM 본문(Base64) 재구성: 숨겨진 잘못된 문자 제거
                    header = "-----BEGIN PRIVATE KEY-----"
                    footer = "-----END PRIVATE KEY-----"
                    if header in pk and footer in pk:
                        body = pk.split(header)[1].split(footer)[0]
                        clean_body = "".join(body.split())  # 모든 공백/개행 제거 후 순수 Base64만 추출
                        pk = f"{header}\n{clean_body}\n{footer}"
                    cert_dict["private_key"] = pk
                cred = credentials.Certificate(cert_dict)
                firebase_admin.initialize_app(cred)

            # ────────────────────────────────────────────────
            # 방식 3: 로컬 firebase-key.json 파일 (로컬 개발용)
            # ────────────────────────────────────────────────
            else:
                import os
                key_path = os.path.join(os.path.dirname(__file__), "firebase-key.json")
                if os.path.exists(key_path):
                    cred = credentials.Certificate(key_path)
                    firebase_admin.initialize_app(cred)
                else:
                    st.error("🔒 **오류:** Firebase 연동 키가 없습니다. Streamlit Cloud Secrets에 `firebase_json` 키를 추가해주세요!")
                    st.stop()

        except Exception as e:
            st.error(f"Firebase 초기화 에러: {e}")
            st.stop()

def get_db():
    try:
        return firestore.client()
    except Exception as e:
        st.error(f"Firestore 연결 오류: 클라우드 접속 권한(Secrets 데이터)이 누락되었을 수 있습니다. 상세 에러: {e}")
        st.stop()

# --- Subject 관련 ---
def add_subject(mode, name, content):
    db = get_db()
    col_name = f"config_{mode}"
    doc_name = f"{mode}_subject"
    doc_ref = db.collection(col_name).document(doc_name)
    
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        subj_list = data.get("subjectList", [])
        subj_contents = data.get("subjectContents", {})
        
        if name not in subj_list:
            subj_list.append(name)
        subj_contents[name] = content
        
        doc_ref.update({
            "subjectList": subj_list,
            "subjectContents": subj_contents
        })
    else:
        doc_ref.set({
            "subjectList": [name],
            "subjectContents": {name: content}
        })

def get_subjects(mode):
    db = get_db()
    col_name = f"config_{mode}"
    doc_name = f"{mode}_subject"
    doc = db.collection(col_name).document(doc_name).get()
    
    if doc.exists:
        data = doc.to_dict()
        subj_list = data.get("subjectList", [])
        subj_contents = data.get("subjectContents", {})
        
        return [{"name": name, "content": subj_contents.get(name, "")} for name in subj_list]
    return []

def delete_subject(mode, name):
    db = get_db()
    col_name = f"config_{mode}"
    doc_name = f"{mode}_subject"
    doc_ref = db.collection(col_name).document(doc_name)
    
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        subj_list = data.get("subjectList", [])
        subj_contents = data.get("subjectContents", {})
        
        if name in subj_list:
            subj_list.remove(name)
        if name in subj_contents:
            del subj_contents[name]
            
        doc_ref.update({
            "subjectList": subj_list,
            "subjectContents": subj_contents
        })

# --- Course 관련 ---
def add_course(mode, course_name, password, time, subject_name, trainee_pw):
    db = get_db()
    col_name = f"course_{mode}"
    created_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    db.collection(col_name).document(course_name).set({
        "password": password,
        "time": time,
        "subject": subject_name,
        "traineePassword": trainee_pw,
        "createdDate": created_date,
        "submitted": False,
        "trainees": []
    })

def get_courses(mode):
    db = get_db()
    col_name = f"course_{mode}"
    docs = db.collection(col_name).stream()
    
    courses = []
    for doc in docs:
        d = doc.to_dict()
        courses.append({
            "name": doc.id,
            "password": d.get("password", ""),
            "time": d.get("time", ""),
            "subject_name": d.get("subject", ""),
            "trainee_password": d.get("traineePassword", ""),
            "created_date": d.get("createdDate", ""),
            "submitted": d.get("submitted", False)
        })
    return courses

def submit_course(mode, course_name):
    db = get_db()
    col_name = f"course_{mode}"
    db.collection(col_name).document(course_name).update({"submitted": True})

def delete_course(mode, course_name):
    db = get_db()
    col_name = f"course_{mode}"
    db.collection(col_name).document(course_name).delete()

# --- Trainee 관련 ---
def add_trainee(mode, course_name, team_name, emp_id, name, sig_data):
    db = get_db()
    col_name = f"course_{mode}"
    doc_ref = db.collection(col_name).document(course_name)
    
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        trainees = data.get("trainees", [])
        
        new_trainee = {
            "id": emp_id,
            "team": team_name,
            "name": name,
            "signature": sig_data
        }
        trainees.append(new_trainee)
        doc_ref.update({"trainees": trainees})

def get_trainees(mode, course_name):
    db = get_db()
    col_name = f"course_{mode}"
    doc = db.collection(col_name).document(course_name).get()
    
    if doc.exists:
        # 기존 코드 호환을 위해 고유 ID 필드 추가
        trainees_raw = doc.to_dict().get("trainees", [])
        ret = []
        for idx, t in enumerate(trainees_raw):
            ret.append({
                "id": t.get("id", ""),     # 실제 화면상의 employee_id로 취급 (React 코드 기준 t.id)
                "team": t.get("team", ""),
                "employee_id": t.get("id", ""), # app.py 호환용
                "name": t.get("name", ""),
                "signature": t.get("signature", ""),
                "_index": idx # 삭제 처리용도
            })
        return ret
    return []

def delete_trainee(mode, course_name, trainee_emp_id):
    # Trainee 삭제 시 employee_id (id) 매칭
    db = get_db()
    col_name = f"course_{mode}"
    doc_ref = db.collection(col_name).document(course_name)
    
    doc = doc_ref.get()
    if doc.exists:
        trainees = doc.to_dict().get("trainees", [])
        updated_trainees = [t for t in trainees if t.get("id") != trainee_emp_id]
        doc_ref.update({"trainees": updated_trainees})

# --- Session 관련 (Firestore 확장 기능으로 문서 내 저장) ---
def save_instructor_session(mode, course_name, company, inst_id, name, location, lect_date, sub_date, sig_data):
    db = get_db()
    col_name = f"course_{mode}"
    doc_ref = db.collection(col_name).document(course_name)
    
    doc_ref.update({
        "instructor_session": {
            "company": company,
            "instructor_id": inst_id,
            "name": name,
            "location": location,
            "lecture_date": lect_date,
            "submitted_date": sub_date,
            "signature": sig_data
        }
    })

def get_instructor_session(mode, course_name):
    db = get_db()
    col_name = f"course_{mode}"
    doc = db.collection(col_name).document(course_name).get()
    
    if doc.exists:
        sess = doc.to_dict().get("instructor_session")
        if sess:
            return sess
    return None
