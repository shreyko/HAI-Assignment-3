import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

import app_baseline
import app_ai

try:
    st.set_page_config(
        page_title="Visual Calorie Estimation Study",
        layout="centered"
    )
except Exception:
    pass

query_params = st.query_params
condition_param = query_params.get("condition", "").lower()

if condition_param == "baseline" or condition_param == "without_ai":
    app_baseline.run_baseline()

elif condition_param == "ai" or condition_param == "with_ai":
    app_ai.run_ai()

else:
    st.title("Visual Calorie Estimation Study")
    st.caption("Human-AI Interaction | University of Michigan | Assignment 3")
    
    st.markdown("""
    Welcome! This study investigates human dietary calorie assessment under two experimental conditions:
    1. **Without AI Assistance (Baseline):** You estimate meal calories based purely on visual inspection.
    2. **With AI Assistance:** You are supported by an AI nutritional parser with itemized ingredient breakdowns and interactive portion controls.
    """)
    
    st.divider()
    st.subheader("Select Your Assigned Condition:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Condition 1")
        st.write("Estimate calories with your own visual judgment.")
        if st.button("Start Without AI (Baseline)", use_container_width=True, type="primary"):
            st.query_params["condition"] = "baseline"
            st.rerun()

    with col2:
        st.subheader("Condition 2")
        st.write("Estimate calories with AI nutritional decomposition & interactive portions.")
        if st.button("Start With AI Assistance", use_container_width=True, type="primary"):
            st.query_params["condition"] = "ai"
            st.rerun()
