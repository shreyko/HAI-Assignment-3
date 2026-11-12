import os
import json
import time
import uuid
import datetime
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATASET_PATH = os.path.join(DATA_DIR, "study_dataset_predictions.csv")
IMAGES_DIR = os.path.join(DATA_DIR, "raw_images")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

os.makedirs(LOGS_DIR, exist_ok=True)

@st.cache_data
def load_dataset():
    if not os.path.exists(DATASET_PATH):
        st.error(f"Dataset not found at {DATASET_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(DATASET_PATH)
    return df

def get_image_path(dish_id, image_filename):
    local_path = os.path.join(IMAGES_DIR, f"{dish_id}.png")
    if os.path.exists(local_path):
        return local_path
    alt_path = os.path.join(IMAGES_DIR, str(image_filename))
    if os.path.exists(alt_path):
        return alt_path
    return None

def sample_trials(df, seed=None):
    if seed is not None:
        sample_df = df.sample(frac=1, random_state=seed)
    else:
        sample_df = df.sample(frac=1)

    low = sample_df[sample_df['tier'] == 'Low'].head(1)
    med_low = sample_df[sample_df['tier'] == 'Medium-Low'].head(2)
    med_high = sample_df[sample_df['tier'] == 'Medium-High'].head(1)
    high = sample_df[sample_df['tier'] == 'High'].head(1)

    selected = pd.concat([low, med_low, med_high, high]).sample(frac=1).to_dict('records')

    trials = []
    for dish in selected:
        try:
            breakdown = json.loads(dish.get('model_breakdown_json', '[]'))
        except Exception:
            breakdown = []

        trials.append({
            'dish_id': dish['dish_id'],
            'tier': dish['tier'],
            'ground_truth_calories': float(dish['ground_truth_calories']),
            'total_mass_grams': float(dish.get('total_mass_grams', 0)),
            'total_fat_grams': float(dish.get('total_fat_grams', 0)),
            'total_carb_grams': float(dish.get('total_carb_grams', 0)),
            'total_protein_grams': float(dish.get('total_protein_grams', 0)),
            'num_ingredients': int(dish.get('num_ingredients', 1)),
            'ingredient_summary': str(dish.get('ingredient_summary', '')),
            'image_filename': str(dish.get('image_filename', f"{dish['dish_id']}.png")),
            'image_url': str(dish.get('image_url', '')),
            'model_predicted_calories': float(dish.get('model_predicted_calories', 0)),
            'model_confidence': float(dish.get('model_confidence', 0.8)),
            'model_reasoning': str(dish.get('model_reasoning', '')),
            'model_breakdown': breakdown,
            'is_attention_check': False
        })

    attn_candidate = sample_df.tail(1).iloc[0]
    attn_trial = {
        'dish_id': attn_candidate['dish_id'],
        'tier': 'Attention_Check',
        'ground_truth_calories': 250.0,
        'total_mass_grams': float(attn_candidate.get('total_mass_grams', 0)),
        'total_fat_grams': float(attn_candidate.get('total_fat_grams', 0)),
        'total_carb_grams': float(attn_candidate.get('total_carb_grams', 0)),
        'total_protein_grams': float(attn_candidate.get('total_protein_grams', 0)),
        'num_ingredients': int(attn_candidate.get('num_ingredients', 1)),
        'ingredient_summary': str(attn_candidate.get('ingredient_summary', '')),
        'image_filename': str(attn_candidate.get('image_filename', f"{attn_candidate['dish_id']}.png")),
        'image_url': str(attn_candidate.get('image_url', '')),
        'model_predicted_calories': 250.0,
        'model_confidence': 1.0,
        'model_reasoning': "Instruction Verification Check: Enter exactly 250 kcal.",
        'model_breakdown': [{'item': 'Attention Check Item', 'estimated_grams': 100, 'calories': 250}],
        'is_attention_check': True
    }

    insert_idx = 2
    trials.insert(insert_idx, attn_trial)
    return trials

def get_gspread_client():
    try:
        import gspread
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds = dict(st.secrets["connections"]["gsheets"])
            sheet_url = creds.pop("spreadsheet", None)
            gc = gspread.service_account_from_dict(creds)
            if sheet_url:
                return gc.open_by_url(sheet_url)
    except Exception:
        pass

    try:
        import tomllib
        import gspread
        local_secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
        if os.path.exists(local_secrets_path):
            with open(local_secrets_path, "rb") as f:
                s = tomllib.load(f)
            if "connections" in s and "gsheets" in s["connections"]:
                creds = dict(s["connections"]["gsheets"])
                sheet_url = creds.pop("spreadsheet", None)
                gc = gspread.service_account_from_dict(creds)
                if sheet_url:
                    return gc.open_by_url(sheet_url)
    except Exception as e:
        print(f"GSpread fallback connection note: {e}")

    return None

def log_trial_response(data_dict, condition):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_dict['timestamp'] = timestamp
    data_dict['condition'] = condition

    csv_name = "baseline_trials.csv" if condition.lower() == "baseline" else "ai_trials.csv"
    csv_path = os.path.join(LOGS_DIR, csv_name)
    df_row = pd.DataFrame([data_dict])
    if os.path.exists(csv_path):
        df_row.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df_row.to_csv(csv_path, mode='w', header=True, index=False)

    try:
        sh = get_gspread_client()
        if sh:
            ws_name = "A3_Baseline_Trials" if condition.lower() == "baseline" else "A3_AI_Trials"
            ws = sh.worksheet(ws_name)
            
            if condition.lower() == "baseline":
                row_vals = [
                    timestamp,
                    data_dict.get('participant_id', ''),
                    data_dict.get('participant_name', ''),
                    condition,
                    data_dict.get('trial_num', 0),
                    data_dict.get('dish_id', ''),
                    data_dict.get('tier', ''),
                    data_dict.get('ground_truth_cals', 0),
                    data_dict.get('user_prediction', 0),
                    data_dict.get('error_kcal', 0),
                    data_dict.get('pct_error', 0),
                    data_dict.get('confidence_1_to_5', 3),
                    data_dict.get('time_spent_sec', 0),
                    data_dict.get('is_attention_check', False),
                    data_dict.get('passed_attention_check', True)
                ]
            else:
                row_vals = [
                    timestamp,
                    data_dict.get('participant_id', ''),
                    data_dict.get('participant_name', ''),
                    condition,
                    data_dict.get('trial_num', 0),
                    data_dict.get('dish_id', ''),
                    data_dict.get('tier', ''),
                    data_dict.get('ground_truth_cals', 0),
                    data_dict.get('initial_ai_cals', 0),
                    data_dict.get('user_adjusted_ai_cals', 0),
                    data_dict.get('user_prediction', 0),
                    data_dict.get('error_kcal', 0),
                    data_dict.get('pct_error', 0),
                    data_dict.get('num_adjustments', 0),
                    data_dict.get('adjusted_items_json', '[]'),
                    data_dict.get('confidence_1_to_5', 3),
                    data_dict.get('time_spent_sec', 0),
                    data_dict.get('is_attention_check', False),
                    data_dict.get('passed_attention_check', True)
                ]
            ws.append_row(row_vals)
    except Exception as e:
        print(f"Error appending trial to Google Sheet: {e}")

def log_survey_response(data_dict):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_dict['timestamp'] = timestamp

    csv_path = os.path.join(LOGS_DIR, "surveys.csv")
    df_row = pd.DataFrame([data_dict])
    if os.path.exists(csv_path):
        df_row.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df_row.to_csv(csv_path, mode='w', header=True, index=False)

    try:
        sh = get_gspread_client()
        if sh:
            ws = sh.worksheet("A3_Surveys")
            row_vals = [
                timestamp,
                data_dict.get('participant_id', ''),
                data_dict.get('participant_name', ''),
                data_dict.get('condition', ''),
                data_dict.get('mental_demand', 3),
                data_dict.get('effort', 3),
                data_dict.get('frustration', 1),
                data_dict.get('perceived_accuracy', 3),
                data_dict.get('ai_trust', 3),
                data_dict.get('ai_portion_help', 3),
                data_dict.get('feedback_comment', '')
            ]
            ws.append_row(row_vals)
    except Exception as e:
        print(f"Error appending survey to Google Sheet: {e}")
