import os
import streamlit as st

import app_baseline
import app_ai
import study_logic

query_params = st.query_params
condition_param = query_params.get("condition", "").lower()

if condition_param == "baseline" or condition_param == "without_ai":
    app_baseline.st.session_state['app_condition'] = "Baseline"
    if app_baseline.st.session_state.page == "auth":
        app_baseline.auth_page()
    elif app_baseline.st.session_state.page == "instructions":
        app_baseline.instructions_page()
    elif app_baseline.st.session_state.page == "trial":
        app_baseline.trial_page()
    elif app_baseline.st.session_state.page == "survey":
        app_baseline.survey_page()
    elif app_baseline.st.session_state.page == "complete":
        app_baseline.complete_page()

elif condition_param == "ai" or condition_param == "with_ai":
    app_ai.st.session_state['app_condition'] = "AI-Assisted"
    if app_ai.st.session_state.page == "auth":
        app_ai.auth_page()
    elif app_ai.st.session_state.page == "instructions":
        app_ai.instructions_page()
    elif app_ai.st.session_state.page == "trial":
        app_ai.trial_page()
    elif app_ai.st.session_state.page == "survey":
        app_ai.survey_page()
    elif app_ai.st.session_state.page == "complete":
        app_ai.complete_page()

else:
    st.set_page_config(
        page_title="HAI A3: Calorie Estimation Study",
        page_icon="🥗",
        layout="centered"
    )

    st.title("🥗 Visual Calorie Estimation Study")
    st.caption("Human-AI Interaction | University of Michigan | Assignment 3")
    
    st.markdown("""
    Welcome! This study investigates human dietary calorie assessment under two experimental conditions:
    1. **Without AI Assistance (Baseline):** You estimate meal calories based purely on visual inspection.
    2. **With AI Assistance:** You are supported by an AI nutritional parser with itemized ingredient breakdowns and interactive portion controls.
    
    ---
    ### Select Your Assigned Condition:
    *(As specified in class, please complete both conditions so counterbalanced order effects are minimized).*
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Condition 1")
        st.write("Estimate calories with your own visual judgment.")
        if st.button("👉 Start Without AI (Baseline)", use_container_width=True, type="primary"):
            st.query_params["condition"] = "baseline"
            st.rerun()

    with col2:
        st.subheader("Condition 2")
        st.write("Estimate calories with AI nutritional decomposition & interactive portions.")
        if st.button("👉 Start With AI Assistance", use_container_width=True, type="primary"):
            st.query_params["condition"] = "ai"
            st.rerun()

    st.markdown("---")
    with st.expander("📊 In-Class Study Administration & Live Data Export"):
        st.write("**Real-Time Data Collection Status:**")
        logs_dir = os.path.join(os.path.dirname(__file__), "data", "logs")
        base_log = os.path.join(logs_dir, "baseline_trials.csv")
        ai_log = os.path.join(logs_dir, "ai_trials.csv")
        survey_log = os.path.join(logs_dir, "surveys.csv")

        b_count = 0
        a_count = 0
        s_count = 0
        import pandas as pd
        if os.path.exists(base_log):
            b_df = pd.read_csv(base_log)
            b_count = len(b_df)
            st.write(f"• Baseline Trials Logged: **{b_count}**")
            st.download_button("Download Baseline Trials CSV", b_df.to_csv(index=False), "baseline_trials.csv")
        else:
            st.write("• Baseline Trials Logged: 0 (local cache empty; streaming to Google Sheet)")

        if os.path.exists(ai_log):
            a_df = pd.read_csv(ai_log)
            a_count = len(a_df)
            st.write(f"• AI-Assisted Trials Logged: **{a_count}**")
            st.download_button("Download AI Trials CSV", a_df.to_csv(index=False), "ai_trials.csv")
        else:
            st.write("• AI-Assisted Trials Logged: 0 (local cache empty; streaming to Google Sheet)")

        if os.path.exists(survey_log):
            s_df = pd.read_csv(survey_log)
            s_count = len(s_df)
            st.write(f"• Post-Study Surveys Logged: **{s_count}**")
            st.download_button("Download Surveys CSV", s_df.to_csv(index=False), "surveys.csv")
        else:
            st.write("• Post-Study Surveys Logged: 0")

        st.info("All responses are automatically synchronized in real time to the Google Sheet `Emotion_Labeling_DB` across worksheets `A3_Baseline_Trials`, `A3_AI_Trials`, and `A3_Surveys`.")
