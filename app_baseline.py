import sys
import os
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from PIL import Image

import study_logic

CONFIDENCE_LABELS = {
    1: "1 - Very Unconfident",
    2: "2 - Somewhat Unconfident",
    3: "3 - Neutral",
    4: "4 - Somewhat Confident",
    5: "5 - Very Confident"
}

def init_state():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'uniqname' not in st.session_state:
        st.session_state.uniqname = ""
    if 'page' not in st.session_state:
        st.session_state.page = "auth"
    if 'trials' not in st.session_state:
        st.session_state.trials = []
    if 'current_trial_idx' not in st.session_state:
        st.session_state.current_trial_idx = 0
    if 'trial_start_time' not in st.session_state:
        st.session_state.trial_start_time = None
    if 'completed_trials' not in st.session_state:
        st.session_state.completed_trials = []

def auth_page():
    st.title("Visual Calorie Estimation Study")
    st.subheader("Condition 1: Baseline (Human-Only Estimation)")
    
    st.markdown("""
    Welcome to the **Human-AI Interaction (HAI)** in-class dietary estimation study.
    
    In this baseline condition, you will evaluate photographs of cafeteria meal plates and estimate their total caloric energy **without AI assistance**.
    
    Please enter your name and uniqname to begin.
    """)
    
    with st.form("auth_form"):
        name_input = st.text_input("Your Full Name (or Classmate Name):", placeholder="e.g. Jane Doe")
        uniqname_input = st.text_input("Your Uniqname / Email:", placeholder="e.g. jdoe@umich.edu")
        submitted = st.form_submit_button("Continue to Instructions", use_container_width=True)
        
        if submitted:
            if not name_input.strip() or not uniqname_input.strip():
                st.error("Please fill in both your name and uniqname.")
            else:
                st.session_state.user_name = name_input.strip()
                st.session_state.uniqname = uniqname_input.strip()
                
                df = study_logic.load_dataset()
                if df.empty:
                    st.error("Could not load study dataset. Please check data files.")
                    return
                st.session_state.trials = study_logic.sample_trials(df)
                st.session_state.current_trial_idx = 0
                st.session_state.page = "instructions"
                st.rerun()

def instructions_page():
    st.title("Study Instructions")
    st.write(f"Welcome, **{st.session_state.user_name}** (`{st.session_state.uniqname}`)!")
    
    st.markdown("""
    ### Task Description
    1. **Overview:** You will evaluate **6 overhead photographs** of real plated cafeteria meals from Google's *Nutrition5k* benchmark.
    2. **Your Goal:** Estimate the **total caloric energy in kilocalories (kcal)** for each plate.
    3. **Strategy:** Carefully inspect the visible food items, portion masses, and apparent ingredient density. Note that camera angles flatten food depth and absorb oils.
    4. **Confidence Rating:** For every trial, rate your confidence in your calorie estimate on a 1-5 scale.
    5. **Instruction Verification:** One of the trials includes an explicit instruction verification check. Please read each trial prompt carefully.
    6. **Post-Task Survey:** After the 6 trials, you will answer a brief 1-minute questionnaire regarding your experience.
    
    *Expected study completion time: 4 to 6 minutes.*
    """)
    
    st.divider()
    if st.button("I Understand the Instructions: Start Baseline Study", type="primary", use_container_width=True):
        st.session_state.current_trial_idx = 0
        st.session_state.trial_start_time = time.time()
        st.session_state.page = "trial"
        st.rerun()

def trial_page():
    trials = st.session_state.trials
    idx = st.session_state.current_trial_idx
    total = len(trials)
    
    if idx >= total:
        st.session_state.page = "survey"
        st.rerun()
        return

    trial = trials[idx]
    
    st.progress((idx) / float(total), text=f"Trial {idx + 1} of {total}")
    st.title(f"Plate Evaluation {idx + 1} of {total}")
    
    if trial['is_attention_check']:
        st.warning(
            "**Attention Check Trial:** To verify that you are reviewing trial instructions carefully, "
            "please **do not** estimate the food on this plate. Instead, enter **exactly 250 kcal** into the box below "
            "and set your confidence rating to **5 (Very Confident)**."
        )

    img_path = study_logic.get_image_path(trial['dish_id'], trial['image_filename'])
    if img_path and os.path.exists(img_path):
        image = Image.open(img_path)
        st.image(image, caption=f"Overhead Plate Photo (Trial {idx + 1})", use_column_width=True)
    elif trial.get('image_url'):
        st.image(trial['image_url'], caption=f"Overhead Plate Photo (Trial {idx + 1})", use_column_width=True)
    else:
        st.error(f"Image not found for dish: {trial['dish_id']}")

    st.markdown("---")
    
    with st.form(f"trial_form_{idx}"):
        st.subheader("Your Calorie Judgment")
        
        user_cals = st.number_input(
            "Enter your estimated total calories for this plate (kcal):",
            min_value=10,
            max_value=3500,
            step=10,
            value=None,
            help="Type your best integer calorie guess based on the visual photo."
        )
        
        confidence = st.select_slider(
            "How confident are you in this estimate?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: CONFIDENCE_LABELS[x]
        )
        
        submitted = st.form_submit_button("Submit Estimate & Next Plate", type="primary", use_container_width=True)
        
        if submitted:
            if user_cals is None:
                st.error("Please enter a calorie estimate before submitting.")
                return
            
            elapsed_sec = round(time.time() - st.session_state.trial_start_time, 2)
            gt_cals = trial['ground_truth_calories']
            err_kcal = abs(user_cals - gt_cals)
            pct_err = round((err_kcal / gt_cals) * 100.0, 1) if gt_cals > 0 else 0.0

            passed_attn = True
            if trial['is_attention_check']:
                passed_attn = (240 <= user_cals <= 260)

            record = {
                'participant_id': st.session_state.user_id,
                'participant_name': st.session_state.user_name,
                'uniqname': st.session_state.uniqname,
                'trial_num': idx + 1,
                'dish_id': trial['dish_id'],
                'tier': trial['tier'],
                'ground_truth_cals': gt_cals,
                'user_prediction': float(user_cals),
                'error_kcal': round(err_kcal, 1),
                'pct_error': pct_err,
                'confidence_1_to_5': confidence,
                'time_spent_sec': elapsed_sec,
                'is_attention_check': trial['is_attention_check'],
                'passed_attention_check': passed_attn
            }
            
            study_logic.log_trial_response(record, condition="Baseline")
            st.session_state.completed_trials.append(record)
            
            st.session_state.current_trial_idx += 1
            st.session_state.trial_start_time = time.time()
            st.rerun()

def survey_page():
    st.title("Post-Task Experience Survey")
    st.write(f"Great job, **{st.session_state.user_name}**! You completed all 6 plates in the **Baseline (Without AI)** condition.")
    st.write("Please answer the following brief questions regarding your subjective experience during this task:")
    
    with st.form("survey_form"):
        mental_demand = st.select_slider(
            "1. Mental Demand: How mentally demanding was estimating meal calories by sight alone?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Very Low", 2: "2 - Low", 3: "3 - Moderate", 4: "4 - High", 5: "5 - Very High"}[x]
        )
        
        effort = st.select_slider(
            "2. Effort Required: How hard did you have to work to mentally estimate ingredients and portions?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Very Low", 2: "2 - Low", 3: "3 - Moderate", 4: "4 - High", 5: "5 - Very High"}[x]
        )
        
        frustration = st.select_slider(
            "3. Frustration / Uncertainty: How insecure or frustrated did you feel guessing calories without reference values?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Very Low", 2: "2 - Low", 3: "3 - Moderate", 4: "4 - High", 5: "5 - Very High"}[x]
        )
        
        perceived_accuracy = st.select_slider(
            "4. Perceived Accuracy: How accurate do you feel your predictions were?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Not at all accurate", 2: "2 - Slightly accurate", 3: "3 - Moderately accurate", 4: "4 - Highly accurate", 5: "5 - Extremely accurate"}[x]
        )
        
        comments = st.text_area(
            "5. Qualitative Feedback: What was most challenging about estimating calories without assistance? Any thoughts on your experience?",
            placeholder="e.g., Hard to judge depth of rice bowls, invisible salad dressings, etc."
        )
        
        submitted = st.form_submit_button("Submit Survey & Complete Study", type="primary", use_container_width=True)
        
        if submitted:
            survey_record = {
                'participant_id': st.session_state.user_id,
                'participant_name': st.session_state.user_name,
                'condition': 'Baseline',
                'mental_demand': mental_demand,
                'effort': effort,
                'frustration': frustration,
                'perceived_accuracy': perceived_accuracy,
                'ai_trust': None,
                'ai_portion_help': None,
                'feedback_comment': comments.strip()
            }
            study_logic.log_survey_response(survey_record)
            st.session_state.page = "complete"
            st.rerun()

def complete_page():
    st.title("Study Session Complete!")
    st.success("Thank you for participating! Your responses have been successfully recorded.")
    
    st.markdown(f"""
    ### Participant Summary
    - **Participant:** {st.session_state.user_name} (`{st.session_state.uniqname}`)
    - **Condition:** Baseline (Without AI Assistance)
    - **Plates Evaluated:** 6 / 6
    """)
    
    if st.button("Start New Session (or Switch Condition)", use_container_width=True):
        st.session_state.clear()
        st.session_state.page = "auth"
        st.rerun()

def run_baseline():
    init_state()
    if st.session_state.page == "auth":
        auth_page()
    elif st.session_state.page == "instructions":
        instructions_page()
    elif st.session_state.page == "trial":
        trial_page()
    elif st.session_state.page == "survey":
        survey_page()
    elif st.session_state.page == "complete":
        complete_page()

if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Calorie Estimation Study - Baseline", layout="centered")
    except Exception:
        pass
    run_baseline()
