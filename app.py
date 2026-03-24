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

    st.markdown(f"""
        <style>
        /* =========================================================
           🔒 LIGHT MODE LOCK — 다크 모드 완전 차단
           사용자가 수동으로 Dark를 선택해도 무력화
           ========================================================= */

        /* 1) 앱 전체 배경을 항상 밝은색으로 고정 */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: #f8fafc !important;
        }}

        /* 2) 다크 모드 data attribute가 붙어도 배경+텍스트 강제 덮어씌우기 */
        [data-theme="dark"] .stApp,
        [data-theme="dark"] [data-testid="stAppViewContainer"] {{
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }}

        /* 3) 다크 모드에서 모든 텍스트 요소 강제 어둡게 */
        [data-theme="dark"] p,
        [data-theme="dark"] span,
        [data-theme="dark"] label,
        [data-theme="dark"] div,
        [data-theme="dark"] [data-testid="stWidgetLabel"],
        [data-theme="dark"] [data-testid="stWidgetLabel"] p,
        [data-theme="dark"] [data-testid="stMarkdownContainer"] p {{
            color: #0f172a !important;
        }}

        /* 4) 다크 모드에서 입력 필드도 라이트 스타일 유지 */
        [data-theme="dark"] .stTextInput input,
        [data-theme="dark"] .stTextArea textarea,
        [data-theme="dark"] .stSelectbox [data-baseweb="select"] {{
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
        }}

        /* 5) 사이드바 및 폼 배경도 고정 */
        [data-theme="dark"] section[data-testid="stSidebar"],
        [data-theme="dark"] [data-testid="stForm"] {{
            background-color: #f1f5f9 !important;
        }}

        /* 🎨 포인트 컬러 변수 */
        :root {{ --accent: {theme_color}; }}

        /* 📱 폰트 */
        .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* 🔤 헤더 색상 - 포인트 컬러로만 지정 */
        h1, h2, h3, h4 {{
            color: {theme_color} !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
        }}

        /* 💡 카드 레이아웃 - 보더/쉐도우만, 색상은 Streamlit 위임 */
        div[data-testid="column"] {{
            border-radius: 1.25rem !important;
            border: 1px solid rgba(128,128,128,0.15) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
            transition: all 0.3s ease !important;
        }}
        div[data-testid="column"]:hover {{
            transform: translateY(-4px) !important;
            border-color: {theme_color} !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.1) !important;
        }}

        /* 메트릭 카드 */
        .metric-card {{
            border-radius: 1rem;
            border-left: 6px solid {theme_color} !important;
            border: 1px solid rgba(128,128,128,0.15);
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateX(5px);
        }}

        /* 🖋️ 입력 필드 - border-radius만 추가, 색상은 건드리지 않음 */
        .stTextInput input, .stTextArea textarea {{
            border-radius: 0.75rem !important;
            transition: border-color 0.2s ease !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{
            border-color: {theme_color} !important;
            box-shadow: 0 0 0 2px {theme_color}33 !important;
        }}

        /* 🔵 Primary 버튼 - 배경/글자색 지정 (버튼은 항상 색상 고정이 맞음) */
        button[kind="primary"], button[kind="primaryFormSubmit"] {{
            background: {theme_color} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 0.75rem !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important;
            transition: all 0.2s ease !important;
        }}
        button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.25) !important;
            filter: brightness(1.08) !important;
        }}

        /* 🟢 Secondary 버튼 - 배경/글자색 지정 */
        button[kind="secondary"], button[kind="secondaryFormSubmit"] {{
            border-radius: 0.75rem !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }}
        button[kind="secondary"]:hover, button[kind="secondaryFormSubmit"]:hover {{
            background: {theme_color} !important;
            color: #ffffff !important;
            border-color: {theme_color} !important;
            transform: translateY(-2px) !important;
        }}

        hr {{ opacity: 0.2; }}
        </style>
    """, unsafe_allow_html=True)


if "mode" not in st.session_state:
    st.session_state.mode = None
if "page" not in st.session_state:
    st.session_state.page = "main"

def reset_to_main():
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
        st.markdown("<div class='metric-card'><h4>⚙️ Admin Panel</h4><p style='opacity:0.8; font-size:0.9rem;'>Manage subjects & courses</p></div>", unsafe_allow_html=True)
        if st.button("Open Admin", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()
    with col2:
        st.markdown("<div class='metric-card'><h4>👨‍🎓 Trainee Mode</h4><p style='opacity:0.8; font-size:0.9rem;'>Add trainee signatures</p></div>", unsafe_allow_html=True)
        if st.button("Open Trainee", use_container_width=True):
            st.session_state.page = "trainee"
            st.rerun()
    with col3:
        st.markdown("<div class='metric-card'><h4>👨‍🏫 Instructor Mode</h4><p style='opacity:0.8; font-size:0.9rem;'>Close sessions & reports</p></div>", unsafe_allow_html=True)
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
                st.success("Deleted!")
                st.rerun()
        else:
            st.info("No subjects found.")
            
        st.markdown("---")
        with st.form("add_sub_form"):
            new_sub = st.text_input("New Subject Name")
            new_cont = st.text_area("Subject Content")
            if st.form_submit_button("Add Subject"):
                if new_sub and new_cont:
                    database.add_subject(st.session_state.mode, new_sub, new_cont)
                    st.success("Subject Added!")
                    st.rerun()
                    
    with tab2:
        st.subheader("Manage Courses")
        courses = database.get_courses(st.session_state.mode)
        if courses:
            st.dataframe(courses, use_container_width=True)
            sel_crs = st.selectbox("Select course to delete", [c['name'] for c in courses], index=None)
            if st.button("Delete Course") and sel_crs:
                database.delete_course(st.session_state.mode, sel_crs)
                st.success("Deleted!")
                st.rerun()
        else:
            st.info("No courses found.")
            
        st.markdown("---")
        subs = database.get_subjects(st.session_state.mode)
        sub_names = [s['name'] for s in subs]
        with st.form("add_crs_form"):
            c_name = st.text_input("Course Name")
            c_pwd = st.text_input("Instructor Password", type="password")
            c_time = st.text_input("Course Time (e.g. 2H)")
            c_sub = st.selectbox("Subject", sub_names)
            c_tpwd = st.text_input("Trainee Password", type="password")
            if st.form_submit_button("Add Course"):
                if c_name and c_pwd and c_time and c_sub:
                    database.add_course(st.session_state.mode, c_name, c_pwd, c_time, c_sub, c_tpwd)
                    st.success("Course Added!")
                    st.rerun()

def show_trainee():
    st.button("🔙 Back", on_click=reset_to_main)
    st.header("Trainee Mode")
    
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
        with st.form("trainee_form"):
            t_team = st.text_input("Team Name")
            t_id = st.text_input("Employee ID")
            t_name = st.text_input("Name")
            st.write("Signature:")
            canvas_result = st_canvas(
                stroke_width=2, stroke_color="#000000", background_color="#ffffff",
                height=150, width=400, drawing_mode="freedraw", key=f"canvas_t_{sel_crs}"
            )
            if st.form_submit_button("Submit"):
                if t_team and t_id and t_name and canvas_result.image_data is not None:
                    import io, base64
                    from PIL import Image
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    b64_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    database.add_trainee(st.session_state.mode, sel_crs, t_team, t_id, t_name, b64_str)
                    st.success("Trainee Added successfully!")

def show_instructor():
    st.button("🔙 Back", on_click=reset_to_main)
    st.header("Instructor Mode")

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
            st.dataframe(pd.DataFrame(trainees)[['team', 'employee_id', 'name']], use_container_width=True)
            
            del_id = st.selectbox("Select Trainee to Remove", [t['employee_id'] for t in trainees], format_func=lambda x: next((t['name'] for t in trainees if t['employee_id']==x), ""), index=None)
            if st.button("Delete Selected Trainee") and del_id:
                # Firestore의 delete_trainee 함수에 맞게 파라미터 전달
                database.delete_trainee(st.session_state.mode, sel_crs, del_id)
                st.rerun()
        else:
            st.info("No trainees added yet.")

        st.markdown("---")
        st.subheader("Submit Session")
        with st.form("inst_form"):
            i_comp = st.text_input("Company")
            i_id = st.text_input("Instructor ID")
            i_name = st.text_input("Name")
            i_loc = st.text_input("Location")
            l_date = st.text_input("Lecture Date (e.g. YYYY-MM-DD)")
            s_date = st.text_input("Submitted Date (e.g. YYYY-MM-DD)")
            
            st.write("Instructor Signature:")
            canvas_inst = st_canvas(
                stroke_width=2, stroke_color="#000000", background_color="#ffffff",
                height=150, width=400, drawing_mode="freedraw", key=f"canvas_i_{sel_crs}"
            )
            
            if st.form_submit_button("Submit & Generate Report"):
                if i_comp and i_id and i_name and i_loc and l_date and s_date and canvas_inst.image_data is not None:
                    import io, base64
                    from PIL import Image
                    img = Image.fromarray(canvas_inst.image_data.astype('uint8'), 'RGBA')
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    b64_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    database.save_instructor_session(st.session_state.mode, sel_crs, i_comp, i_id, i_name, i_loc, l_date, s_date, b64_str)
                    database.submit_course(st.session_state.mode, sel_crs)
                    st.success("Session Submitted Successfully!")
                    st.rerun()
                else:
                    st.error("Please fill all required fields and sign.")

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
