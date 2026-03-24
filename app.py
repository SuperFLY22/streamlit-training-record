import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import database
import export

# Firebase DB 초기화
database.init_db()

st.set_page_config(page_title="Training Record Webapp", page_icon="📝", layout="wide")

def inject_custom_css():
    # 현재 모드에 따른 포인트 색상 결정
    theme_color = "#334155"
    if st.session_state.get("mode") == "overseas":
        theme_color = "#0284c7"
    elif st.session_state.get("mode") == "domestic":
        theme_color = "#10b981"

    # ✅ 핵심 원칙:
    # 1) 배경색/텍스트색은 절대 건드리지 않음 → Streamlit 엔진(라이트/다크)이 각 모드에 맞게 자동 처리
    # 2) CSS는 오직 버튼 색상, 보더, 그림자, 포인트 컬러 같은 "디자인 장식"만 담당
    st.markdown(f"""
        <style>
        /* 📱 폰트 및 기본 여백 */
        html, body, .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }}

        /* 🔤 헤더: 모드 포인트 컬러 적용 */
        h1, h2, h3, h4 {{
            color: {theme_color} !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
        }}

        /* 💡 카드 레이아웃 스타일링 (보더와 그림자만 추가) */
        div[data-testid="column"] {{
            border-radius: 1.25rem !important;
            border: 1px solid rgba(128,128,128,0.1) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
            transition: all 0.3s ease !important;
        }}
        div[data-testid="column"]:hover {{
            transform: translateY(-4px) !important;
            border-color: {theme_color}33 !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
        }}

        /* 사이드바/폼 섹션 둥글게 */
        [data-testid="stForm"] {{
            border-radius: 1rem !important;
            border: 1px solid rgba(128,128,128,0.1) !important;
            padding: 2rem !important;
        }}

        /* 메트릭 카드: 심플 디자인 */
        .metric-card {{
            border-radius: 1rem;
            border-left: 6px solid {theme_color} !important;
            padding: 1.2rem;
            margin-bottom: 1rem;
            background: rgba(128,128,128,0.03);
            transition: transform 0.2s ease;
        }}
        .metric-card:hover {{ transform: scale(1.01); }}

        /* 🖋️ 입력 필드 테두리 반경 */
        .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {{
            border-radius: 0.75rem !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{
            border-color: {theme_color} !important;
        }}

        /* 🔵 Primary 버튼 (모드 불문 포인트 배경 + 흰색 글자 고정) */
        button[kind="primary"], button[kind="primaryFormSubmit"] {{
            background: {theme_color} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 0.75rem !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            transition: all 0.2s ease !important;
        }}
        button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{
            transform: translateY(-2px) !important;
            filter: brightness(1.1) !important;
            box-shadow: 0 6px 10px rgba(0,0,0,0.2) !important;
        }}

        /* 🟢 Secondary 버튼: Hover 전까지는 일반 디자인 유지 */
        button[kind="secondary"], button[kind="secondaryFormSubmit"] {{
            border-radius: 0.75rem !important;
            font-weight: 600 !important;
        }}
        button[kind="secondary"]:hover, button[kind="secondaryFormSubmit"]:hover {{
            background: {theme_color} !important;
            color: #ffffff !important;
            border-color: {theme_color} !important;
            transform: translateY(-1px) !important;
        }}

        hr {{ opacity: 0.15; }}
        </style>
    """, unsafe_allow_html=True)

if "mode" not in st.session_state:
    st.session_state.mode = None
if "page" not in st.session_state:
    st.session_state.page = "main"

def reset_to_main():
    # 로그아웃(인증 초기화) 방어 코드
    keys_to_clear = [k for k in st.session_state.keys() if "auth" in k]
    for k in keys_to_clear:
        st.session_state.pop(k) # 키 자체를 제거하여 완전 초기화
    st.session_state.page = "main"

def show_mode_selection():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Training Record System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.8; font-size: 1.2rem; margin-bottom: 3rem;'>Please select your operating mode to continue</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
    
    with col2:
        st.markdown("<h3>🌍 Overseas Mode</h3>", unsafe_allow_html=True)
        st.markdown("<p style='opacity: 0.8; margin-bottom: 2rem;'>Manage records and sessions for international training programs.</p>", unsafe_allow_html=True)
        if st.button("Access Overseas ➔", use_container_width=True, type="primary"):
            st.session_state.mode = "overseas"
            st.rerun()
            
    with col3:
        st.markdown("<h3>🏢 Domestic Mode</h3>", unsafe_allow_html=True)
        st.markdown("<p style='opacity: 0.8; margin-bottom: 2rem;'>Manage records and sessions for local domestic training programs.</p>", unsafe_allow_html=True)
        if st.button("Access Domestic ➔", use_container_width=True, type="secondary"):
            st.session_state.mode = "domestic"
            st.rerun()

def show_main():
    mode_str = "🌍 Overseas" if st.session_state.mode == "overseas" else "🏢 Domestic"
    st.markdown(f"<h2>{mode_str} Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='opacity: 0.8; margin-bottom: 2rem;'>Choose a module to start managing training records.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='metric-card'><h4>⚙️ Admin Panel</h4><p style='opacity:0.8; font-size:0.9rem;'>Manage subjects &amp; courses</p></div>", unsafe_allow_html=True)
        if st.button("Open Admin", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()
    with col2:
        st.markdown("<div class='metric-card'><h4>👨‍🎓 Trainee Mode</h4><p style='opacity:0.8; font-size:0.9rem;'>Add trainee signatures</p></div>", unsafe_allow_html=True)
        if st.button("Open Trainee", use_container_width=True):
            st.session_state.page = "trainee"
            st.rerun()
    with col3:
        st.markdown("<div class='metric-card'><h4>👨‍🏫 Instructor Mode</h4><p style='opacity:0.8; font-size:0.9rem;'>Close sessions &amp; reports</p></div>", unsafe_allow_html=True)
        if st.button("Open Instructor", use_container_width=True):
            st.session_state.page = "instructor"
            st.rerun()
            
    st.markdown("<br><hr>", unsafe_allow_html=True)
    if st.button("← Switch Mode (Overseas / Domestic)"):
        st.session_state.mode = None
        st.rerun()

def show_admin():
    st.button("🔙 Back", on_click=reset_to_main)
    st.header("Admin Panel")
    
    if "flash_msg" in st.session_state:
        st.success(st.session_state["flash_msg"])
        del st.session_state["flash_msg"]
    
    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False
        
    if not st.session_state.admin_auth:
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if pwd == "0990":
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Incorrect Password")
        return

    tab1, tab2 = st.tabs(["Subjects", "Courses"])
    
    with tab1:
        st.subheader("Manage Subjects")
        subs = database.get_subjects(st.session_state.mode)
        if subs:
            st.dataframe(subs, use_container_width=True)
            sel_sub = st.selectbox("Select subject to delete", [s['name'] for s in subs], index=None)
            if st.button("Delete Subject") and sel_sub:
                database.delete_subject(st.session_state.mode, sel_sub)
                st.session_state["flash_msg"] = "Subject Deleted!"
                st.rerun()
        else:
            st.info("No subjects found.")
            
        st.markdown("---")
        fk_sub = st.session_state.get("fk_sub", 0)
        with st.form(f"add_sub_form_{fk_sub}"):
            new_sub = st.text_input("New Subject Name")
            new_cont = st.text_area("Subject Content")
            if st.form_submit_button("Add Subject"):
                if new_sub and new_cont:
                    database.add_subject(st.session_state.mode, new_sub, new_cont)
                    st.session_state["flash_msg"] = "Subject Added successfully!"
                    st.session_state["fk_sub"] = fk_sub + 1
                    st.rerun()
                else:
                    st.error("Please fill all fields.")
                    
    with tab2:
        st.subheader("Manage Courses")
        courses = database.get_courses(st.session_state.mode)
        if courses:
            st.dataframe(courses, use_container_width=True)
            sel_crs = st.selectbox("Select course to delete", [c['name'] for c in courses], index=None)
            if st.button("Delete Course") and sel_crs:
                database.delete_course(st.session_state.mode, sel_crs)
                st.session_state["flash_msg"] = "Course Deleted!"
                st.rerun()
        else:
            st.info("No courses found.")
            
        st.markdown("---")
        subs = database.get_subjects(st.session_state.mode)
        sub_names = [s['name'] for s in subs]
        fk_crs = st.session_state.get("fk_crs", 0)
        with st.form(f"add_crs_form_{fk_crs}"):
            c_name = st.text_input("Course Name")
            c_pwd = st.text_input("Instructor Password", type="password")
            c_time = st.text_input("Course Time (e.g. 2H)")
            c_sub = st.selectbox("Subject", sub_names)
            c_tpwd = st.text_input("Trainee Password", type="password")
            if st.form_submit_button("Add Course"):
                if c_name and c_pwd and c_time and c_sub and c_tpwd:
                    database.add_course(st.session_state.mode, c_name, c_pwd, c_time, c_sub, c_tpwd)
                    st.session_state["flash_msg"] = "Course Added successfully!"
                    st.session_state["fk_crs"] = fk_crs + 1
                    st.rerun()
                else:
                    st.error("Please fill all fields.")

        # ==========================================================
        # 📂 추가된 기능: 완료된 교육(Course)의 템플릿(보고서) 다운로드 영역
        # ==========================================================
        st.markdown("---")
        st.subheader("📥 Download Completed Reports")
        if courses:
            submitted_courses = [c for c in courses if c.get('submitted', False)]
            if submitted_courses:
                dl_crs = st.selectbox("Select completed course to download", [c['name'] for c in submitted_courses], key="admin_dl_crs")
                if dl_crs:
                    c_info = next(c for c in courses if c['name'] == dl_crs)
                    sess = database.get_instructor_session(st.session_state.mode, dl_crs)
                    trainees = database.get_trainees(st.session_state.mode, dl_crs)
                    sub_content = next((s['content'] for s in subs if s['name'] == c_info['subject_name']), "")
                    
                    if sess:
                        inst_info = {
                            "company": sess['company'],
                            "instructor_id": sess['instructor_id'],
                            "name": sess['name'],
                            "location": sess['location'],
                            "course_name": dl_crs,
                            "signature": sess['signature']
                        }
                        try:
                            excel_bytes = export.generate_excel_bytes(
                                subject_name=c_info['subject_name'],
                                subject_content=sub_content,
                                course_time=c_info['time'],
                                lecture_date=sess['lecture_date'],
                                submitted_date=sess['submitted_date'],
                                instructor_info=inst_info,
                                trainees=trainees
                            )
                            st.download_button(
                                label="📄 Download XLSX", data=excel_bytes,
                                file_name=f"{dl_crs}_TrainingRecord.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                        except Exception as e:
                            st.error(f"Error generating Excel: {e}")
            else:
                st.info("No courses have been submitted yet. Once instructors submit their course reports, you can download them here.")

def show_trainee():
    st.button("🔙 Back", on_click=reset_to_main)
    st.header("Trainee Mode")
    
    if "flash_msg" in st.session_state:
        st.success(st.session_state["flash_msg"])
        del st.session_state["flash_msg"]
    
    courses = database.get_courses(st.session_state.mode)
    course_opts = {c['name']: c for c in courses}
    sel_crs = st.selectbox("Select Course", list(course_opts.keys()))
    
    if sel_crs:
        c_info = course_opts[sel_crs]
        if f"trainee_auth_{sel_crs}" not in st.session_state:
            st.session_state[f"trainee_auth_{sel_crs}"] = False
            
        if not st.session_state[f"trainee_auth_{sel_crs}"]:
            pwd = st.text_input("Trainee Password", type="password")
            if st.button("Login"):
                if pwd == c_info['trainee_password']:
                    st.session_state[f"trainee_auth_{sel_crs}"] = True
                    st.rerun()
                else:
                    st.error("Incorrect Password")
            return
            
        st.subheader("Add Trainee Information")
        fk_t = st.session_state.get(f"fk_t_{sel_crs}", 0)
        with st.form(f"trainee_form_{fk_t}"):
            t_team = st.text_input("Team Name")
            t_id = st.text_input("Employee ID")
            t_name = st.text_input("Name")
            st.write("Signature:")
            canvas_result = st_canvas(
                stroke_width=2, stroke_color="#000000", background_color="#ffffff",
                height=150, width=400, drawing_mode="freedraw", key=f"canvas_t_{sel_crs}_{fk_t}",
                display_toolbar=True
            )
            if st.form_submit_button("Submit"):
                valid_sig = canvas_result.json_data is not None and len(canvas_result.json_data.get("objects", [])) > 0
                if not (t_team and t_id and t_name and valid_sig):
                    st.error("🚫 Please fill all text fields and provide your signature.")
                else:
                    import io, base64
                    from PIL import Image
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    b64_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    database.add_trainee(st.session_state.mode, sel_crs, t_team, t_id, t_name, b64_str)
                    st.session_state["flash_msg"] = "✅ Trainee Added successfully!"
                    st.session_state[f"fk_t_{sel_crs}"] = fk_t + 1
                    st.rerun()

def show_instructor():
    st.button("🔙 Back", on_click=reset_to_main)
    st.header("Instructor Mode")

    if "flash_msg" in st.session_state:
        st.success(st.session_state["flash_msg"])
        del st.session_state["flash_msg"]

    courses = database.get_courses(st.session_state.mode)
    course_opts = {c['name']: c for c in courses}
    sel_crs = st.selectbox("Select Course", list(course_opts.keys()))
    
    if sel_crs:
        c_info = course_opts[sel_crs]
        if f"inst_auth_{sel_crs}" not in st.session_state:
            st.session_state[f"inst_auth_{sel_crs}"] = False
            
        if not st.session_state[f"inst_auth_{sel_crs}"]:
            pwd = st.text_input("Instructor Password", type="password")
            if st.button("Login"):
                if pwd == c_info['password']:
                    st.session_state[f"inst_auth_{sel_crs}"] = True
                    st.rerun()
                else:
                    st.error("Incorrect Password")
            return

        st.subheader("Current Trainees")
        trainees = database.get_trainees(st.session_state.mode, sel_crs)
        if trainees:
            df = pd.DataFrame(trainees)[['team', 'employee_id', 'name']]
            df.index = df.index + 1  # 인덱스를 1부터 시작하도록 조작
            st.dataframe(df, use_container_width=True)
            
            del_id = st.selectbox("Select Trainee to Remove", [t['employee_id'] for t in trainees], format_func=lambda x: next((t['name'] for t in trainees if t['employee_id']==x), ""), index=None)
            if st.button("Delete Selected Trainee") and del_id:
                database.delete_trainee(st.session_state.mode, sel_crs, del_id)
                st.rerun()
        else:
            st.info("No trainees added yet.")

        st.markdown("---")
        st.subheader("Submit Session")
        fk_i = st.session_state.get(f"fk_i_{sel_crs}", 0)
        with st.form(f"inst_form_{fk_i}"):
            i_comp = st.text_input("Company")
            i_id = st.text_input("Instructor ID")
            i_name = st.text_input("Name")
            i_loc = st.text_input("Location")
            l_date = st.text_input("Lecture Date (e.g. YYYY-MM-DD)")
            s_date = st.text_input("Submitted Date (e.g. YYYY-MM-DD)")
            
            st.write("Instructor Signature:")
            canvas_inst = st_canvas(
                stroke_width=2, stroke_color="#000000", background_color="#ffffff",
                height=150, width=400, drawing_mode="freedraw", key=f"canvas_i_{sel_crs}_{fk_i}",
                display_toolbar=True
            )
            
            if st.form_submit_button("Submit & Generate Report"):
                valid_sig = canvas_inst.json_data is not None and len(canvas_inst.json_data.get("objects", [])) > 0
                if not (i_comp and i_id and i_name and i_loc and l_date and s_date and valid_sig):
                    st.error("🚫 Please fill all required fields and provide your signature.")
                else:
                    import io, base64
                    from PIL import Image
                    img = Image.fromarray(canvas_inst.image_data.astype('uint8'), 'RGBA')
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    b64_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    database.save_instructor_session(st.session_state.mode, sel_crs, i_comp, i_id, i_name, i_loc, l_date, s_date, b64_str)
                    database.submit_course(st.session_state.mode, sel_crs)
                    st.session_state["flash_msg"] = "✅ Session Submitted Successfully!"
                    st.session_state[f"fk_i_{sel_crs}"] = fk_i + 1
                    st.rerun()

        if c_info['submitted']:
            st.success("This course has been submitted.")
            sess = database.get_instructor_session(st.session_state.mode, sel_crs)
            if sess and st.button("Download Excel Report"):
                subs = database.get_subjects(st.session_state.mode)
                sub_content = next((s['content'] for s in subs if s['name'] == c_info['subject_name']), "")
                
                inst_info = {
                    "company": sess['company'],
                    "instructor_id": sess['instructor_id'],
                    "name": sess['name'],
                    "location": sess['location'],
                    "course_name": sel_crs,
                    "signature": sess['signature']
                }

                try:
                    excel_bytes = export.generate_excel_bytes(
                        subject_name=c_info['subject_name'],
                        subject_content=sub_content,
                        course_time=c_info['time'],
                        lecture_date=sess['lecture_date'],
                        submitted_date=sess['submitted_date'],
                        instructor_info=inst_info,
                        trainees=trainees
                    )
                    st.download_button(
                        label="📄 Download XLSX", data=excel_bytes,
                        file_name=f"{sel_crs}_TrainingRecord.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Error generating Excel: {e}")

if st.session_state.mode is None:
    inject_custom_css()
    show_mode_selection()
else:
    inject_custom_css()
    if st.session_state.page == "main":
        show_main()
    elif st.session_state.page == "admin":
        show_admin()
    elif st.session_state.page == "trainee":
        show_trainee()
    elif st.session_state.page == "instructor":
        show_instructor()
