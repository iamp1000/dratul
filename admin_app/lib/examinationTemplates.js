// Examination templates for physical examination forms
const examinationTemplates = [
  {
    "templateName": "Diabetes (Standard Checkup)",
    "fields": {
      "thyroid_palpation": "",
      "thyroid_consistency": "",
      "thyroid_lymph_nodes": "",
      "thyroid_notes": "N/A",
      "foot_right_visual": "Check for ulcers/callus",
      "foot_right_pulses": "Check DP/PT",
      "foot_left_visual": "Check for ulcers/callus",
      "foot_left_pulses": "Check DP/PT",
      "foot_exam_notes": "Assess footwear. Check for sensation.",
      "neuropathy_monofilament": "Perform 10g test",
      "neuropathy_vibration": "Check at ankles",
      "neuropathy_notes": "",
      "fundus_right_eye": "Check for retinopathy",
      "fundus_left_eye": "Check for retinopathy",
      "fundus_exam_notes": "Refer to ophthalmologist if new findings."
    }
  },
  {
    "templateName": "Hypothyroidism (Follow-up)",
    "fields": {
      "thyroid_palpation": "Check for goiter/nodules",
      "thyroid_consistency": "Firm/Soft?",
      "thyroid_lymph_nodes": "Check cervical nodes",
      "thyroid_notes": "Assess for symptoms: fatigue, weight gain, hair loss.",
      "foot_right_visual": "N/A",
      "foot_right_pulses": "N/A",
      "foot_left_visual": "N/A",
      "foot_left_pulses": "N/A",
      "foot_exam_notes": "N/A",
      "neuropathy_monofilament": "N/A",
      "neuropathy_vibration": "N/A",
      "neuropathy_notes": "Check reflexes if symptomatic.",
      "fundus_right_eye": "N/A",
      "fundus_left_eye": "N/A",
      "fundus_exam_notes": "N/A"
    }
  },
  {
    "templateName": "Full Examination (Blank)",
    "fields": {
      "thyroid_palpation": "",
      "thyroid_consistency": "",
      "thyroid_lymph_nodes": "",
      "thyroid_notes": "",
      "foot_right_visual": "",
      "foot_right_pulses": "",
      "foot_left_visual": "",
      "foot_left_pulses": "",
      "foot_exam_notes": "",
      "neuropathy_monofilament": "",
      "neuropathy_vibration": "",
      "neuropathy_notes": "",
      "fundus_right_eye": "",
      "fundus_left_eye": "",
      "fundus_exam_notes": ""
    }
  }
];

window.examinationTemplates = examinationTemplates;

