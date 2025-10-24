# EMR Consultation Form - Feature TODO

## 1. Objective
Replace the current "Prescription Composer" tab with a comprehensive, multi-part EMR/Consultation form, based on the HealthPlix screenshots. This form will capture structured data for a single patient "encounter" or "consultation".

## 2. Backend / Database Model Changes
This requires a new database architecture. We will need to create:
- **`Consultation` (or `Encounter`) Model:**
  - `id`
  - `patient_id` (ForeignKey to Patient)
  - `user_id` (ForeignKey to User, the doctor)
  - `consultation_date` (DateTime)
  - `quick_notes` (Text/JSON for Quill Delta)
  - `complaints` (Text)
  - `next_visit_date` (Date, optional)
  - `next_visit_instructions` (String, optional)
  - `referral_doctor_name` (String, optional)
  - `referral_speciality` (String, optional)
  - `referral_phone` (String, optional)
  - `referral_email` (String, optional)
  - `usg_findings` (Text/JSON for Quill Delta)
  - `lab_tests_imaging` (Text/JSON for Quill Delta)
  - `advice` (Text/JSON for Quill Delta)

- **`Vitals` Model:**
  - `id`
  - `consultation_id` (ForeignKey to Consultation)
  - `bp_systolic` (Integer)
  - `bp_diastolic` (Integer)
  - `pulse` (Integer)
  - `height` (Float)
  - `weight` (Float)
  - `bmi` (Float)
  - `waist` (Float, optional)
  - `hip` (Float, optional)
  - `temperature` (Float, optional)
  - `spo2` (Integer, optional)

- **`Diagnosis` Model:** (This could be a many-to-many relationship with a `DiagnosisMaster` table)
  - `id`
  - `consultation_id` (ForeignKey to Consultation)
  - `diagnosis_name` (String)

- **`PrescribedMedication` Model:** (Replaces the current `Prescription` logic)
  - `id`
  - `consultation_id` (ForeignKey to Consultation)
  - `type` (String, e.g., "TAB", "INJ")
  - `medicine_name` (String)
  - `dosage` (String, e.g., "1-0-1")
  - `when` (String, e.g., "Before Food")
  - `frequency` (String, e.g., "daily")
  - `duration` (String, e.g., "20 days")
  - `notes` (String, optional)

- **`PatientMenstrualHistory` Model:** (This might be on the `Patient` model, not per-consultation)
  - `id`
  - `patient_id` (ForeignKey to Patient)
  - `age_at_menarche` (Integer, optional)
  - `lmp` (Date, optional)
  - `regularity` (String, e.g., "Regular", "Irregular")
  - `duration_of_bleeding` (String, optional)
  - `period_of_cycle` (String, optional)
  - `details_of_issues` (Text, optional)

- **`PatientObstetricHistory` Model:** (Similar to above)
  - `lmp` (Date)
  - `edd` (Date)
  - `gestational_age_weeks` (Integer)
  - `gestational_age_days` (Integer)

## 3. Frontend React Component Plan
We will create a new primary React component: `ConsultationEditor`.

- **`ConsultationEditor` (Main Component):**
  - Will be shown when a Patient is selected.
  - Will have a tabbed interface or a long scrolling form.
  - Will have a "Past Visits" sidebar (like `image_345b43.png`).

- **Sections within `ConsultationEditor`:**
  - **`VitalsForm` (image_345b5e.png):**
    - Inputs for: BP (systolic/diastolic), Pulse, Height, Weight, BMI (auto-calculated), Waist, Hip, Temperature, SPO2.
    - OB/GYN Inputs: LMP, EDD, Gestational Age (Weeks, Days).
  - **`ConsultationNotesForm` (image_345b5e.png):**
    - `Quick Notes` (Quill.js editor)
    - `Complaints` (Textarea)
    - `Diagnosis` (Tag-based input, ideally with autocomplete)
    - `Systemic Examination` (Textarea or Quill.js)
  - **`MedicationForm` (image_345b61.png):**
    - This is a dynamic table (repeater field).
    - State will hold an array of medicine objects.
    - Function to "Add Medicine" (pushes new empty object to array).
    - Function to "Remove Medicine" (splices from array by index).
    - Each row will have inputs for: Type, Medicine, Dosage, When, Frequency, Duration, Notes.
    - Buttons: "Load Prev", "Load Template", "Save as Template", "Clear All".
  - **`AdviceForm` (image_345b61.png):**
    - A single `quill.js` editor for free-text advice (e.g., "1400 KCAL DIET...").
  - **`InvestigationForm` (image_345b5b.png):**
    - `Tests Requested` (Textarea or tag input)
    - `Investigations` (Textarea)
    - `Referred to` (Inputs for Doctor Name, Speciality, Phone, Email)
    - `USG Findings` (Textarea or Quill.js)
    - `Lab Tests and Imaging` (Textarea or Quill.js)
  - **`FemaleHistoryForm` (image_345b45.png):**
    - This form should probably be part of the `PatientDetails` modal, as it's part of their history, not a per-consultation event.
    - Inputs for: Age at Menarche, LMP, Regularity, Duration, Period, Details.
  - **`FollowUpForm` (image_345b5b.png):**
    - Input for "No of" (Days/Weeks/Months)
    - A `flatpickr` input for "select date".

## 4. Implementation Steps
1.  **Backend:** Create and migrate the new database models (`Consultation`, `Vitals`, `PrescribedMedication`, `Diagnosis`, etc.).
2.  **Backend:** Create the new API endpoints (e.g., `POST /api/v1/consultations`, `GET /api/v1/patient/{id}/consultations`).
3.  **Frontend:** Read `admin_panel.html`.
4.  **Frontend:** Remove the old `Prescriptions` tab and `PrescriptionEditor` component logic.
5.  **Frontend:** Create the new `ConsultationEditor` component.
6.  **Frontend:** Build each sub-component one by one (`VitalsForm`, `MedicationForm`, etc.) and integrate them into `ConsultationEditor`.
7.  **Frontend:** Wire up the "Save Consultation" button to post the complex JSON object to the new backend endpoint.
8.  **Frontend:** Build the "Past Visits" sidebar to `GET` and display previous consultations.