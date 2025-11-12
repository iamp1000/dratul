# Component Extraction Plan

From admin_panel.html (7686 lines), we need to extract:

## Core Utilities (DONE)
- [x] api.js - API helper
- [x] toast.js - Toast notifications
- [x] LoadingSpinner.jsx
- [x] Modal.jsx

## Shared Components (PARTIAL)
- [x] Sidebar.jsx
- [x] StatCard.jsx
- [x] TimeRangePicker.jsx
- [x] EmergencyBlockModal.jsx
- [x] DashboardServices.jsx

## Page Components (TODO)
- [ ] Dashboard.jsx (IN PROGRESS - needs Quick Actions buttons)
- [ ] Appointments.jsx
- [ ] DoctorSchedule.jsx
- [ ] Patients.jsx
- [ ] ConsultationEditor.jsx
- [ ] TemplateEditorView.jsx
- [ ] Users.jsx
- [ ] LogViewer.jsx

## Sub-Components for Pages (TODO)
- [ ] Calendar.jsx (for Appointments)
- [ ] DaySlotsViewer.jsx
- [ ] DailyViewModalContent.jsx
- [ ] AppointmentDetails.jsx
- [ ] DateAppointments.jsx
- [ ] ScheduleCalendar.jsx
- [ ] ScheduleEditor.jsx
- [ ] DayEditorModal.jsx
- [ ] SingleDayScheduleEditor.jsx
- [ ] DailyUnavailabilityEditor.jsx
- [ ] PatientDetails.jsx
- [ ] PatientListView.jsx
- [ ] ConsultationView.jsx
- [ ] VisitPadView.jsx
- [ ] ConsultationNotesForm.jsx
- [ ] MedicationForm.jsx
- [ ] AdviceForm.jsx
- [ ] InvestigationFollowUpForm.jsx
- [ ] PatientMenstrualHistoryForm.jsx
- [ ] PhysicalExaminationForm.jsx
- [ ] InvestigationResultsModal.jsx
- [ ] InvestigationSelectModal.jsx
- [ ] TemplateSearchModal.jsx
- [ ] PrescriptionEditor.jsx
- [ ] AppointmentEditor.jsx
- [ ] PatientEditor.jsx
- [ ] UserEditor.jsx
- [ ] PermissionCheckboxes.jsx
- [ ] FormInput.jsx
- [ ] FormTextArea.jsx
- [ ] EditableExamSection.jsx
- [ ] InvestigationResultsContent.jsx

## App-Level Components (TODO)
- [ ] App.jsx - Main app with routing
- [ ] QuickActions.jsx

## Data/Constants (TODO)
- [ ] samplePatientData (if needed)
- [ ] examinationTemplates (if needed)

