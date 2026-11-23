# HAI Assignment 3: Visual Calorie Estimation Web Interfaces
### Human-AI Interaction | University of Michigan (Fall 2026)
**Author:** Shrey Kohli (uniqname: `kohlishr`)

---

## 1. Project Overview

Building directly upon **Assignment 1** and **Assignment 2**, this repository contains two interactive web interfaces for visual dietary calorie estimation using Google's **Nutrition5k** benchmark dataset:

1. **Condition 1: Baseline Interface (Without AI)**  
   Participants inspect overhead meal photographs and estimate total calories (kcal) relying strictly on visual portion judgment and food density estimation.
2. **Condition 2: AI-Assisted Interface (With AI)**  
   Participants view overhead photographs paired with an **AI Nutritional Parser** (powered by multimodal Gemini 3.5 Flash). The assistant provides itemized food component identification, estimated gram masses, surface oil/dressing alerts, and **interactive portion controls** allowing participants to directly edit individual ingredient weights and recalculate the meal baseline in real time.

Both interfaces stream data in real time to a centralized Google Sheet backend and maintain local CSV backups.

---

## 2. Experimental Design & Measurements

### Trial Sampling (N = 6 Trials per Participant)
To ensure the study completes in under 10 minutes (including instructions and the survey), each participant is randomly assigned **6 trials**:
* **5 Calorie-Stratified Meals:**
  * 1 Low Calorie dish (100 to 350 kcal)
  * 2 Medium-Low Calorie dishes (350 to 650 kcal)
  * 1 Medium-High Calorie dish (650 to 950 kcal)
  * 1 High Calorie dish (950 to 1600 kcal)
* **1 Attention Check Trial:**
  * Inserted at trial position 3 to verify participant attentiveness.
  * Explicitly instructs the participant to enter exactly **250 kcal** and confidence **5** rather than estimating the food photo.

### Measurements Collected
1. **Primary Task Performance:**
   * Ground truth calories (measured by nutritionists on electronic scales in Nutrition5k).
   * Performer calorie estimate (kcal).
   * Absolute error ($|\text{predicted} - \text{actual}|$) and percentage error.
2. **Task Efficiency (Dwell Time):**
   * High-resolution elapsed time (seconds) recorded per trial from photo presentation to submission.
3. **Performer Confidence Rating:**
   * 1-to-5 Likert scale collected on every single trial (1 = Very Unconfident, 5 = Very Confident).
4. **Interactive Portion Logs (AI Condition):**
   * Initial AI baseline prediction.
   * User-adjusted baseline (after tweaking individual ingredient sliders/inputs).
   * Number of items modified and itemized JSON delta.
5. **Post-Task Subjective Workload & Experience Survey:**
   * **Mental Demand** (NASA-TLX 1 to 5)
   * **Effort Required** (NASA-TLX 1 to 5)
   * **Frustration / Uncertainty** (NASA-TLX 1 to 5)
   * **Perceived Prediction Accuracy** (1 to 5)
   * **AI Reliance & Trust** (1 to 5, AI condition)
   * **Value of Interactive Portion Editing** (1 to 5, AI condition)
   * **Qualitative Experience Reflection** (Open comment box)

---

## 3. Repository Structure

```
Assignment 3/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml
├── data/
│   ├── study_dataset_predictions.csv
│   ├── raw_images/
│   └── logs/
├── app.py
├── app_baseline.py
├── app_ai.py
├── study_logic.py
├── requirements.txt
├── .gitignore
└── README.md
```
