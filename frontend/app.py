import streamlit as st
import requests
import json

st.set_page_config(
    page_title="AI BPO Call QA Auditor",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 BPO Call Quality Assurance & Compliance Auditor")
st.markdown("Automated call auditing engine: Speech-to-Text, Policy Compliance, and Risk Flagging.")

st.divider()

# Sidebar: Config & Backend Status
with st.sidebar:
    st.header("System Settings")
    api_url = st.text_input("Backend API Endpoint", value="http://127.0.0.1:8000/api/v1/audit-call")
    st.info("Ensure the FastAPI backend is running on port 8000.")

# Main Layout
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    st.subheader("1. Upload Customer Call")
    uploaded_file = st.file_uploader("Select an audio recording (.mp3 / .wav)", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format="audio/mp3")
        
        audit_btn = st.button("🚀 Run QA & Compliance Audit", type="primary", use_container_width=True)

with col_right:
    st.subheader("2. Audit Report & Analysis")
    
    if uploaded_file and 'audit_btn' in locals() and audit_btn:
        with st.spinner("Processing speech transcription and compliance audit..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(api_url, files=files)

                if response.status_code == 200:
                    result = response.json().get("data", {})
                    
                    # Top Metric Row
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Compliance Score", f"{result.get('compliance_score_percentage', 0)}%")
                    m2.metric("Customer Sentiment", result.get("customer_sentiment", "N/A"))
                    m3.metric("Agent Professionalism", f"{result.get('agent_professionalism_score', 0)}/10")

                    st.write("")

                    # Risk / Human-in-the-loop Banner
                    if result.get("requires_human_review"):
                        st.error("⚠️ FLAGGED FOR MANUAL REVIEW: Compliance or performance below threshold.")
                    else:
                        st.success("✅ PASSED: Call adheres to standard compliance protocols.")

                    st.divider()

                    # Detailed Findings
                    st.markdown(f"**Call ID:** `{result.get('call_id')}`")
                    st.markdown(f"**Primary Issue:** {result.get('primary_issue')}")
                    st.markdown(f"**Solution Offered:** {result.get('solution_provided')}")
                    
                    greeting_status = "✅ Done" if result.get("mandatory_greeting_done") else "❌ Missed"
                    st.markdown(f"**Mandatory Greeting Protocol:** {greeting_status}")

                    st.subheader("Auditor Observations & Notes")
                    for note in result.get("audit_notes", []):
                        st.markdown(f"- {note}")

                else:
                    st.error(f"API Error {response.status_code}: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("Backend server unreachable. Make sure FastAPI server is running (`python -m uvicorn backend.main:app --reload`).")
            except Exception as ex:
                st.error(f"Error: {str(ex)}")