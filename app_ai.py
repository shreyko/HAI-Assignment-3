import sys
import os
import time
import json
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
    if 'user_portions' not in st.session_state:
        st.session_state.user_portions = {}
    if 'live_predictions' not in st.session_state:
        st.session_state.live_predictions = {}
    if 'custom_items' not in st.session_state:
        st.session_state.custom_items = {}
    if 'add_item_error' not in st.session_state:
        st.session_state.add_item_error = {}

def auth_page():
    st.title("Visual Calorie Estimation Study")
    st.subheader("Condition 2: AI-Assisted (Human + Multimodal AI)")
    
    st.markdown("""
    Welcome to the **Human-AI Interaction (HAI)** in-class dietary estimation study.
    
    In this AI-assisted condition, you will evaluate photographs of cafeteria meal plates **paired with an AI multimodal nutritional parser**.
    
    The AI decomposes the plate into individual food items, estimates portion weights, and flags surface dressings/oils. **You can interactively adjust ingredient portions** if you judge that a food pile is too large, small, or buried.
    
    Please enter your name and uniqname to begin.
    """)
    
    with st.form("auth_form_ai"):
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
                st.session_state.user_portions = {}
                st.session_state.custom_items = {}
                st.session_state.add_item_error = {}
                st.session_state.page = "instructions"
                st.rerun()

def instructions_page():
    st.title("AI-Assisted Study Instructions")
    st.write(f"Welcome, **{st.session_state.user_name}** (`{st.session_state.uniqname}`)!")
    
    st.subheader("How to Use the AI Assistance")
    st.markdown("""
    1. **Overhead Image:** Inspect the overhead meal photograph.
    2. **AI Nutritional Decomposition:** Below the photo, the AI displays identified food items, estimated gram portions, and individual calorie counts.
    3. **AI Visual Reasoning:** A brief note highlights detected surface oils, dressings, sauces, or pile stacking.
    4. **Interactive Portion Controls:** If you believe an AI portion estimate is inaccurate, adjust the gram input for that item. The total plate baseline will recalculate live!
    5. **Add Missed Ingredients:** If you spot an ingredient or sauce the AI missed, open the "Add an Ingredient Missed by the AI" panel to enter its name and grams. The AI will calculate its calories and add it to the plate total.
    6. **Final Judgment:** Enter your calibrated total calorie prediction and rate your confidence on a 1-5 scale.
    7. **Instruction Verification:** One of the trials includes an explicit instruction verification check. Please read each trial prompt carefully.
    8. **Post-Task Survey:** After the 6 trials, answer a brief questionnaire regarding your experience and trust in the AI.
    
    *Expected study completion time: 4 to 6 minutes.*
    """)
    
    st.divider()
    if st.button("I Understand the Instructions: Start AI-Assisted Study", type="primary", use_container_width=True):
        st.session_state.current_trial_idx = 0
        st.session_state.trial_start_time = time.time()
        st.session_state.user_portions = {}
        st.session_state.custom_items = {}
        st.session_state.add_item_error = {}
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
    st.title(f"Plate Evaluation {idx + 1} of {total} (AI-Assisted)")
    
    if trial['is_attention_check']:
        st.warning(
            "**Attention Check Trial:** To verify that you are reviewing trial instructions carefully, "
            "please **do not** estimate the food on this plate. Instead, enter **exactly 250 kcal** into the final calorie box "
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

    st.divider()

    dish_id = trial['dish_id']
    if dish_id not in st.session_state.live_predictions:
        fallback_data = {
            'model_predicted_calories': float(trial.get('model_predicted_calories', 0)),
            'model_confidence': float(trial.get('model_confidence', 0.85)),
            'model_reasoning': str(trial.get('model_reasoning', '')),
            'model_breakdown': trial.get('model_breakdown', [])
        }
        with st.spinner("Analyzing plate image with Gemini AI..."):
            pred_data, is_live_val = study_logic.get_live_ai_prediction(img_path, fallback_data)
            st.session_state.live_predictions[dish_id] = {
                'data': pred_data,
                'is_live': is_live_val
            }

    ai_entry = st.session_state.live_predictions[dish_id]
    ai_data = ai_entry['data']
    is_live_call = ai_entry['is_live']

    st.subheader("AI Nutritional Parser & Visual Reasoning")
    if is_live_call:
        st.success("Synchronous AI Output: Live API inference generated via Google Gemini 3.5 Flash")
    else:
        st.caption("AI Output: Calibrated multimodal nutritional model")

    if ai_data.get('model_reasoning'):
        st.info(f"**AI Visual Reasoning:** {ai_data['model_reasoning']}")

    breakdown = ai_data.get('model_breakdown', [])
    initial_ai_cals = float(ai_data.get('model_predicted_calories', 0))
    
    adjusted_items = []
    recalculated_cals = 0.0
    num_adjustments = 0

    custom_items = st.session_state.custom_items.get(dish_id, [])

    if breakdown and len(breakdown) > 0:
        st.markdown("**Itemized Food Decomposition (Edit portions below if needed):**")
        
        col_headers = st.columns([3, 2, 2, 2])
        col_headers[0].markdown("**Identified Food Item**")
        col_headers[1].markdown("**AI Grams (g)**")
        col_headers[2].markdown("**Adjusted (g)**")
        col_headers[3].markdown("**Calories (kcal)**")

        for item_i, item in enumerate(breakdown):
            name = item.get('item', f"Item {item_i+1}")
            orig_g = float(item.get('estimated_grams', 50))
            orig_cal = float(item.get('calories', 50))
            density = (orig_cal / orig_g) if orig_g > 0 else 1.0

            row_key = f"trial_{idx}_item_{item_i}"
            
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.write(f"• {name}")
            c2.write(f"{orig_g:.0f} g")
            
            user_g = c3.number_input(
                f"Weight for {name}",
                min_value=5.0,
                max_value=1200.0,
                value=orig_g,
                step=10.0,
                key=row_key,
                label_visibility="collapsed"
            )
            
            item_cals = round(user_g * density, 1)
            c4.write(f"**{item_cals:.0f}** kcal")
            
            if abs(user_g - orig_g) >= 1.0:
                num_adjustments += 1
                adjusted_items.append({
                    'item': name,
                    'original_grams': orig_g,
                    'adjusted_grams': user_g,
                    'calories': item_cals
                })
            
            recalculated_cals += item_cals

        for c_i, c_item in enumerate(custom_items):
            c_name = c_item['item']
            c_g = float(c_item['grams'])
            c_cal = float(c_item['calories'])
            num_adjustments += 1
            recalculated_cals += c_cal
            adjusted_items.append({
                'item': c_name,
                'original_grams': 0.0,
                'adjusted_grams': c_g,
                'calories': c_cal,
                'is_user_added': True
            })
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.write(f"• {c_name} (User Added)")
            c2.write("-")
            c3.write(f"{c_g:.0f} g")
            c4.write(f"**{c_cal:.0f}** kcal")
    else:
        recalculated_cals = initial_ai_cals
        for c_i, c_item in enumerate(custom_items):
            c_name = c_item['item']
            c_g = float(c_item['grams'])
            c_cal = float(c_item['calories'])
            num_adjustments += 1
            recalculated_cals += c_cal
            adjusted_items.append({
                'item': c_name,
                'original_grams': 0.0,
                'adjusted_grams': c_g,
                'calories': c_cal,
                'is_user_added': True
            })

    err_info = st.session_state.add_item_error.get(dish_id)
    if err_info:
        st.warning(f"Live AI calculation was unavailable for '{err_info['name']}'. Please enter your estimated calories below so you can proceed:")
        m_col1, m_col2 = st.columns([3, 2])
        manual_cals = m_col1.number_input(
            f"Calories for {err_info['grams']:.0f}g of {err_info['name']} (kcal):",
            min_value=5.0,
            max_value=2500.0,
            value=100.0,
            step=10.0,
            key=f"manual_cal_input_{dish_id}"
        )
        col_b1, col_b2 = st.columns([2, 2])
        if col_b1.button("Add Item with Your Calories", key=f"btn_add_manual_{dish_id}", type="primary"):
            if dish_id not in st.session_state.custom_items:
                st.session_state.custom_items[dish_id] = []
            st.session_state.custom_items[dish_id].append({
                'item': err_info['name'],
                'grams': float(err_info['grams']),
                'calories': float(manual_cals),
                'is_manual': True
            })
            st.session_state.add_item_error.pop(dish_id, None)
            st.rerun()
        if col_b2.button("Cancel", key=f"btn_cancel_manual_{dish_id}"):
            st.session_state.add_item_error.pop(dish_id, None)
            st.rerun()
    else:
        with st.expander("Add an Ingredient Missed by the AI"):
            add_col1, add_col2 = st.columns([3, 2])
            new_item_name = add_col1.text_input(
                "Ingredient Name:",
                placeholder="e.g. Ranch dressing, Butter, Guacamole",
                key=f"new_item_name_{dish_id}"
            )
            new_item_grams = add_col2.number_input(
                "Portion Grams (g):",
                min_value=5.0,
                max_value=1000.0,
                value=30.0,
                step=5.0,
                key=f"new_item_grams_{dish_id}"
            )
            if st.button("Calculate Calories with AI & Add to Plate", key=f"btn_calc_add_{dish_id}"):
                if new_item_name and new_item_name.strip():
                    with st.spinner("Calculating calories with Gemini AI..."):
                        calc_cals, calc_ok = study_logic.calculate_item_calories(
                            new_item_name.strip(),
                            float(new_item_grams)
                        )
                    if calc_ok and calc_cals is not None:
                        if dish_id not in st.session_state.custom_items:
                            st.session_state.custom_items[dish_id] = []
                        st.session_state.custom_items[dish_id].append({
                            'item': new_item_name.strip(),
                            'grams': float(new_item_grams),
                            'calories': round(calc_cals, 1),
                            'is_manual': False
                        })
                        st.success(f"Added {new_item_name.strip()} ({new_item_grams:.0f}g, {calc_cals:.0f} kcal) to plate total.")
                        st.rerun()
                    else:
                        st.session_state.add_item_error[dish_id] = {
                            'name': new_item_name.strip(),
                            'grams': float(new_item_grams)
                        }
                        st.rerun()
                else:
                    st.error("Please enter an ingredient name before calculating.")

    st.divider()
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Initial AI Baseline Total", f"{initial_ai_cals:.0f} kcal")
    delta_str = f"{recalculated_cals - initial_ai_cals:+.0f} kcal" if num_adjustments > 0 else "0 kcal"
    m_col2.metric("Recalculated Baseline (Your Portions)", f"{recalculated_cals:.0f} kcal", delta=delta_str)

    with st.form(f"trial_form_ai_{idx}"):
        st.subheader("Your Final Calorie Prediction")
        
        default_pred = round(recalculated_cals) if not trial['is_attention_check'] else None
        
        user_cals = st.number_input(
            "Enter your final calibrated calorie prediction (kcal):",
            min_value=10,
            max_value=3500,
            step=10,
            value=default_pred,
            help="You may accept the recalculated baseline or make any final adjustments."
        )
        
        confidence = st.select_slider(
            "How confident are you in this estimate?",
            options=[1, 2, 3, 4, 5],
            value=4,
            format_func=lambda x: CONFIDENCE_LABELS[x]
        )
        
        submitted = st.form_submit_button("Submit Estimate & Next Plate", type="primary", use_container_width=True)
        
        if submitted:
            if user_cals is None:
                st.error("Please enter a calorie prediction before submitting.")
                return

            elapsed_sec = round(time.time() - st.session_state.trial_start_time, 2)
            gt_cals = trial['ground_truth_calories']
            err_kcal = abs(user_cals - gt_cals)
            pct_err = round((err_kcal / gt_cals) * 100.0, 1) if gt_cals > 0 else 0.0

            passed_attn = True
            if trial['is_attention_check']:
                passed_attn = (user_cals == 250 and confidence == 5)

            record = {
                'participant_id': st.session_state.user_id,
                'participant_name': st.session_state.user_name,
                'uniqname': st.session_state.uniqname,
                'trial_num': idx + 1,
                'dish_id': trial['dish_id'],
                'tier': trial['tier'],
                'ground_truth_cals': gt_cals,
                'initial_ai_cals': initial_ai_cals,
                'user_adjusted_ai_cals': round(recalculated_cals, 1),
                'user_prediction': float(user_cals),
                'error_kcal': round(err_kcal, 1),
                'pct_error': pct_err,
                'num_adjustments': num_adjustments,
                'adjusted_items_json': json.dumps(adjusted_items),
                'confidence_1_to_5': confidence,
                'time_spent_sec': elapsed_sec,
                'is_attention_check': trial['is_attention_check'],
                'passed_attention_check': passed_attn,
                'is_live_ai_call': is_live_call
            }
            
            study_logic.log_trial_response(record, condition="AI-Assisted")
            st.session_state.completed_trials.append(record)
            
            st.session_state.current_trial_idx += 1
            st.session_state.trial_start_time = time.time()
            st.rerun()

def survey_page():
    st.title("Post-Task Experience Survey")
    st.write(f"Great job, **{st.session_state.user_name}**! You completed all 6 plates in the **AI-Assisted** condition.")
    st.write("Please answer the following brief questions regarding your subjective experience during this task:")
    
    with st.form("survey_form_ai"):
        mental_demand = st.select_slider(
            "1. Mental Demand: How mentally demanding was estimating meal calories with AI assistance?",
            options=[1, 2, 3, 4, 5],
            value=2,
            format_func=lambda x: {1: "1 - Very Low", 2: "2 - Low", 3: "3 - Moderate", 4: "4 - High", 5: "5 - Very High"}[x]
        )
        
        effort = st.select_slider(
            "2. Effort Required: How hard did you have to work to verify or adjust the AI's estimates?",
            options=[1, 2, 3, 4, 5],
            value=2,
            format_func=lambda x: {1: "1 - Very Low", 2: "2 - Low", 3: "3 - Moderate", 4: "4 - High", 5: "5 - Very High"}[x]
        )
        
        frustration = st.select_slider(
            "3. Frustration / Uncertainty: How insecure or frustrated did you feel completing the task with AI assistance?",
            options=[1, 2, 3, 4, 5],
            value=1,
            format_func=lambda x: {1: "1 - Very Low", 2: "2 - Low", 3: "3 - Moderate", 4: "4 - High", 5: "5 - Very High"}[x]
        )
        
        perceived_accuracy = st.select_slider(
            "4. Perceived Accuracy: How accurate do you feel your final predictions were with AI support?",
            options=[1, 2, 3, 4, 5],
            value=4,
            format_func=lambda x: {1: "1 - Not at all accurate", 2: "2 - Slightly accurate", 3: "3 - Moderately accurate", 4: "4 - Highly accurate", 5: "5 - Extremely accurate"}[x]
        )
        
        ai_trust = st.select_slider(
            "5. AI Reliance & Trust: How much did you rely on the AI's ingredient recognition and portion numbers?",
            options=[1, 2, 3, 4, 5],
            value=4,
            format_func=lambda x: {1: "1 - Completely Disregarded", 2: "2 - Rarely Relied", 3: "3 - Moderately Relied", 4: "4 - Mostly Relied", 5: "5 - Completely Relied"}[x]
        )

        ai_portion_help = st.select_slider(
            "6. Value of Interactive Portions: Did being able to edit individual ingredient gram weights help you improve upon the AI's estimate?",
            options=[1, 2, 3, 4, 5],
            value=4,
            format_func=lambda x: {1: "1 - Did not help", 2: "2 - Slightly helped", 3: "3 - Moderately helped", 4: "4 - Highly helped", 5: "5 - Crucial help"}[x]
        )
        
        comments = st.text_area(
            "7. Qualitative Feedback: What did you like or dislike about having AI assistance? How did it compare to estimating alone?",
            placeholder="e.g., Helpful baseline for hidden ingredients, but needed to bump up portions on rice."
        )
        
        submitted = st.form_submit_button("Submit Survey & Complete Study", type="primary", use_container_width=True)
        
        if submitted:
            survey_record = {
                'participant_id': st.session_state.user_id,
                'participant_name': st.session_state.user_name,
                'condition': 'AI-Assisted',
                'mental_demand': mental_demand,
                'effort': effort,
                'frustration': frustration,
                'perceived_accuracy': perceived_accuracy,
                'ai_trust': ai_trust,
                'ai_portion_help': ai_portion_help,
                'feedback_comment': comments.strip()
            }
            study_logic.log_survey_response(survey_record)
            st.session_state.page = "complete"
            st.rerun()

def complete_page():
    st.title("AI-Assisted Study Session Complete!")
    st.success("Thank you for participating! Your responses have been successfully recorded.")
    
    st.subheader("Participant Summary")
    st.markdown(f"""
    - **Participant:** {st.session_state.user_name} (`{st.session_state.uniqname}`)
    - **Condition:** AI-Assisted (Human + Multimodal AI)
    - **Plates Evaluated:** 6 / 6
    """)
    
    if st.button("Start New Session (or Switch Condition)", use_container_width=True):
        st.session_state.clear()
        st.session_state.page = "auth"
        st.rerun()

def run_ai():
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
        st.set_page_config(page_title="Calorie Estimation Study - AI Assisted", layout="centered")
    except Exception:
        pass
    run_ai()
