import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(
    page_title="AI BPO Call QA Auditor",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 BPO Quality Assurance & Compliance Engine")
st.markdown("Automated call compliance monitoring, sentiment evaluation, and policy auditing.")

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
AUDIT_ENDPOINT = f"{API_BASE_URL}/api/v1/audit-call"
HISTORY_ENDPOINT = f"{API_BASE_URL}/api/v1/audits"

tab1, tab2 = st.tabs(["🎙️ Live Call Audit", "📊 Audit History & Analytics"])

# ==================== TAB 1: LIVE CALL AUDIT ====================
with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("1. Audio Ingestion")
        uploaded_file = st.file_uploader(
            "Upload customer interaction recording (.mp3, .wav)", 
            type=["mp3", "wav", "m4a"]
        )

        if uploaded_file is not None:
            st.audio(uploaded_file, format="audio/mp3")
            audit_btn = st.button("🚀 Run QA & Compliance Audit", type="primary", use_container_width=True)

    with col_right:
        st.subheader("2. QA Audit Findings")
        
        if uploaded_file and 'audit_btn' in locals() and audit_btn:
            with st.spinner("Processing speech transcription and compliance audit..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(AUDIT_ENDPOINT, files=files)

                    if response.status_code == 200:
                        result = response.json().get("data", {})

                        # High-level KPIs
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Compliance Score", f"{result.get('compliance_score_percentage', 0)}%")
                        m2.metric("Customer Sentiment", result.get("customer_sentiment", "N/A"))
                        m3.metric("Agent Professionalism", f"{result.get('agent_professionalism_score', 0)}/10")

                        st.write("")

                        # Status Banner
                        if result.get("requires_human_review"):
                            st.error("⚠️ FLAGGED FOR HUMAN REVIEW: Compliance or performance below threshold.")
                        else:
                            st.success("✅ PASSED: Meets operational compliance requirements.")

                        st.divider()

                        st.markdown(f"**Call ID:** `{result.get('call_id')}`")
                        st.markdown(f"**Primary Issue:** {result.get('primary_issue')}")
                        st.markdown(f"**Solution Provided:** {result.get('solution_provided')}")

                        greeting_icon = "✅ Followed" if result.get("mandatory_greeting_done") else "❌ Missed"
                        st.markdown(f"**Mandatory Greeting Protocol:** {greeting_icon}")

                        st.subheader("Audit Observations")
                        for note in result.get("audit_notes", []):
                            st.markdown(f"- {note}")

                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Backend service unreachable. Verify FastAPI is running on port 8000.")
                except Exception as ex:
                    st.error(f"Error occurred: {str(ex)}")

# ==================== TAB 2: AUDIT HISTORY & ANALYTICS ====================
with tab2:
    st.subheader("Historical Call Audits")

    try:
        hist_response = requests.get(HISTORY_ENDPOINT)
        if hist_response.status_code == 200:
            data = hist_response.json().get("records", [])

            if not data:
                st.info("No audit records found in database yet. Process calls in the 'Live Call Audit' tab.")
            else:
                df = pd.DataFrame(data)

                # Summary Analytics Cards
                total_calls = len(df)
                avg_compliance = df["compliance_score_percentage"].mean()
                flagged_calls = df["requires_human_review"].sum()
                avg_professionalism = df["agent_professionalism_score"].mean()

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Total Calls Audited", total_calls)
                k2.metric("Avg Compliance", f"{avg_compliance:.1f}%")
                k3.metric("Avg Professionalism", f"{avg_professionalism:.1f}/10")
                k4.metric("Flagged for Review", int(flagged_calls))

                st.divider()

                # Table view
                display_cols = [
                    "call_id", 
                    "created_at", 
                    "compliance_score_percentage", 
                    "customer_sentiment", 
                    "agent_professionalism_score", 
                    "requires_human_review"
                ]
                st.dataframe(
                    df[display_cols].rename(columns={
                        "call_id": "Call ID",
                        "created_at": "Timestamp",
                        "compliance_score_percentage": "Compliance (%)",
                        "customer_sentiment": "Sentiment",
                        "agent_professionalism_score": "Professionalism",
                        "requires_human_review": "Needs Review"
                    }),
                    column_config={
                        "Compliance (%)": st.column_config.ProgressColumn(
                            "Compliance",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "Needs Review": st.column_config.CheckboxColumn("Needs Review")
                    },
                    hide_index=True,
                    use_container_width=True
                )

                st.subheader("Audit Detail Lookup")
                selected_call_id = st.selectbox("Select a Call ID to view full audit logs:", df["call_id"].tolist())
                
                selected_record = next(item for item in data if item["call_id"] == selected_call_id)
                st.json({
                    "Call ID": selected_record["call_id"],
                    "Timestamp": selected_record["created_at"],
                    "Primary Issue": selected_record["primary_issue"],
                    "Solution Provided": selected_record["solution_provided"],
                    "Mandatory Greeting": selected_record["mandatory_greeting_done"],
                    "Audit Notes": selected_record["audit_notes"]
                })

                st.divider()
                st.subheader("🛠️ Supervisor Review & Override")

                with st.form(key=f"review_form_{selected_call_id}"):
                    current_flag = bool(selected_record.get("requires_human_review", False))
                    new_flag_status = st.checkbox("Requires Manual Review Flag", value=current_flag)
                    supervisor_note = st.text_area(
                        "Supervisor Feedback / Justification",
                        placeholder="Add corrective feedback, coaching notes, or sign-off remarks..."
                    )
                    submit_review = st.form_submit_button("Save Supervisor Decision", type="primary")

                    if submit_review:
                        if not supervisor_note.strip():
                            st.warning("Please add feedback before submitting.")
                        else:
                            override_endpoint = f"{API_BASE_URL}/api/v1/audits/{selected_call_id}/review"
                            payload = {
                                "requires_human_review": new_flag_status,
                                "supervisor_feedback": supervisor_note
                            }
                            patch_res = requests.patch(override_endpoint, json=payload)
                            if patch_res.status_code == 200:
                                st.success("Review updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update review: {patch_res.text}")

        else:
            st.error(f"Failed to fetch records: {hist_response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("Backend service unreachable. Verify FastAPI is running on port 8000.")
    except Exception as ex:
        st.error(f"Error occurred: {str(ex)}")