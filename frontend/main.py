import streamlit as st
import requests
import json
import uuid

st.set_page_config(layout="wide")

st.title("📄 Comprehensive AI Resume Parser")
st.markdown("Upload a candidate's PDF resume to extract their full profile or view previously parsed resumes.")

# Auto-generate unique session ID for this browser/user
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

tab1, tab2 = st.tabs(["📤 Parse New Resume", "📚 View Stored Resumes"])

with tab1:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if st.button("Extract Full Profile", type="primary"):
        if uploaded_file is not None:
            with st.spinner("AI is reading the PDF and extracting all data... this may take a moment."):
                
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                
                clean_string = ""  # Initialize to avoid NameError
                
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/parse",
                        files=files,
                        params={"user_id": st.session_state.session_id}
                    )
                    response_data = response.json()
                    
                    clean_string = response_data["result"].replace("```json", "").replace("```", "").strip()
                    ai_result = json.loads(clean_string)
                    
                    st.success("Extraction Complete!")
                    
                    # Create visual columns for the layout
                    col1, col2 = st.columns([1, 2])
                    
                    # --- LEFT COLUMN: Basics & Skills ---
                    with col1:
                        personal = ai_result.get("personal_info", {})
                        st.subheader("👤 Personal Info")
                        st.write(f"**Name:** {personal.get('name', 'N/A')}")
                        st.write(f"**Email:** {personal.get('email', 'N/A')}")
                        st.write(f"**Phone:** {personal.get('phone', 'N/A')}")
                        st.write(f"**Location:** {personal.get('location', 'N/A')}")
                        
                        st.subheader("🛠️ Skills")
                        skills = ai_result.get("skills", [])
                        # Display as tags using markdown code blocks
                        if skills:
                            st.markdown(" ".join([f"`{skill}`" for skill in skills]))
                        else:
                            st.write("None found")
                            
                        st.subheader("🎓 Education")
                        education = ai_result.get("education", [])
                        for edu in education:
                            st.markdown(f"**{edu.get('degree', 'Unknown Degree')}**")
                            st.markdown(f"*{edu.get('institution', 'Unknown Institution')}* | {edu.get('graduation_date', '')}")
                            st.divider()

                    # --- RIGHT COLUMN: Experience & Projects ---
                    with col2:
                        summary = ai_result.get("professional_summary", "")
                        if summary:
                            st.subheader("📝 Summary")
                            st.write(summary)
                        
                        st.subheader("💼 Work Experience")
                        experience = ai_result.get("work_experience", [])
                        for job in experience:
                            st.markdown(f"#### {job.get('job_title', 'Unknown Title')} at {job.get('company', 'Unknown Company')}")
                            st.markdown(f"*{job.get('dates', 'Unknown Dates')}*")
                            for resp in job.get('responsibilities', []):
                                st.write(f"- {resp}")
                            st.write("") # Add a little space between jobs
                            
                        projects = ai_result.get("projects", [])
                        if projects:
                            st.subheader("🚀 Projects")
                            for proj in projects:
                                st.markdown(f"**{proj.get('project_name', 'Unknown Project')}**")
                                st.write(proj.get('description', ''))
                    
                    # --- RAW JSON VIEWER ---
                    st.divider()
                    with st.expander("🛠️ View Raw JSON Output"):
                        st.json(ai_result)
                        
                except json.JSONDecodeError:
                    st.warning("⚠️ The AI struggled to format the output correctly, but here is what it found:")
                    st.code(clean_string)
                except Exception as e:
                    st.error(f"System Error: {e}")
        else:
            st.warning("Please upload a PDF resume first!")

with tab2:
    st.subheader("Previously Parsed Resumes")
    
    try:
        response = requests.get(
            "http://127.0.0.1:8000/stored",
            params={"user_id": st.session_state.session_id}
        )
        data = response.json()
        resumes = data.get("resumes", [])
        
        if resumes:
            # Create a selectbox for choosing a resume
            options = [f"{r['filename']} - {r['timestamp']}" for r in resumes]
            selected = st.selectbox("Select a parsed resume to view:", options)
            
            if selected:
                # Find the selected resume
                selected_resume = None
                for r in resumes:
                    if f"{r['filename']} - {r['timestamp']}" == selected:
                        selected_resume = r
                        break
                
                if selected_resume:
                    try:
                        ai_result = json.loads(selected_resume['json_data'].replace("```json", "").replace("```", "").strip())
                        
                        st.success(f"Loaded resume: {selected_resume['filename']}")
                        
                        # Display the same layout as parsing
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            personal = ai_result.get("personal_info", {})
                            st.subheader("👤 Personal Info")
                            st.write(f"**Name:** {personal.get('name', 'N/A')}")
                            st.write(f"**Email:** {personal.get('email', 'N/A')}")
                            st.write(f"**Phone:** {personal.get('phone', 'N/A')}")
                            st.write(f"**Location:** {personal.get('location', 'N/A')}")
                            
                            st.subheader("🛠️ Skills")
                            skills = ai_result.get("skills", [])
                            if skills:
                                st.markdown(" ".join([f"`{skill}`" for skill in skills]))
                            else:
                                st.write("None found")
                                
                            st.subheader("🎓 Education")
                            education = ai_result.get("education", [])
                            for edu in education:
                                st.markdown(f"**{edu.get('degree', 'Unknown Degree')}**")
                                st.markdown(f"*{edu.get('institution', 'Unknown Institution')}* | {edu.get('graduation_date', '')}")
                                st.divider()

                        with col2:
                            summary = ai_result.get("professional_summary", "")
                            if summary:
                                st.subheader("📝 Summary")
                                st.write(summary)
                            
                            st.subheader("💼 Work Experience")
                            experience = ai_result.get("work_experience", [])
                            for job in experience:
                                st.markdown(f"#### {job.get('job_title', 'Unknown Title')} at {job.get('company', 'Unknown Company')}")
                                st.markdown(f"*{job.get('dates', 'Unknown Dates')}*")
                                for resp in job.get('responsibilities', []):
                                    st.write(f"- {resp}")
                                st.write("")
                                
                            projects = ai_result.get("projects", [])
                            if projects:
                                st.subheader("🚀 Projects")
                                for proj in projects:
                                    st.markdown(f"**{proj.get('project_name', 'Unknown Project')}**")
                                    st.write(proj.get('description', ''))
                        
                        st.divider()
                        with st.expander("🛠️ View Raw JSON Output"):
                            st.json(ai_result)
                            
                    except json.JSONDecodeError:
                        st.warning("⚠️ Error parsing stored JSON data.")
                        st.code(selected_resume['json_data'])
        else:
            st.info("No stored resumes found. Parse some resumes first!")
            
    except Exception as e:
        st.error(f"Error loading stored resumes: {e}")