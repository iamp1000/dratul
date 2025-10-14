## General Notes
- Make all changes without deleting existing code.
- Only edit files to make necessary modifications to avoid accidental code removal.
- Ensure all changes are fully backward-compatible with existing appointment and patient functionality.
- Based on all the changes we are making always look for contrasting code in the backend or front end which   can cause possible errors and prevent the app from running
- Read the project files for context starting with all the files in app folder for backend and root folder has front end html code

## Appointment Form Modifications
- [ ] Modify appointment form to allow creating patients with required fields: first name, last name, DOB, date and time for appointment, city.
- [ ] Add manual name entry with algorithm suggesting patients from past database entries based on letters entered.
- [ ] For existing patients, build suggestion algorithm in the appointment form.
- [ ] Create form section for choosing existing patient (select date/time).
- [ ] Create form section for entering new patient and insert into database.
- [ ] Add fields for first name and last name.
- [ ] Add optional location field for city.
- [ ] Add field for date of birth (DOB).
- [ ] Add optional reason for visit field.
- [ ] Make first name, DOB, date, and time required.
- [ ] Make last name, city, and reason for visit optional.
- [ ] Change start/end time into only time, each appointment with 10-minute default gap.
- [ ] Add field for appointment date, defaulting to today or next available day.
- [ ] Show available hours for selected date.
- [ ] Add constraint to prevent double-booking or walk-in overbooking (limit online appointments).
- [ ] Ensure default 15-minute gap between appointments.
- [ ] Add ability to manually block online bookings for a day (hospital/home/clinic).
- [ ] Build schedule section with default/modifiable hour slots and "off" days.

## Backend and Data Handling
- [ ] Check expected backend appointment data: time, date, patient info, all optional fields.
- [ ] Review database for patient appointment fields required.
- [ ] Update backend and DB logic for compatibility.
- [ ] Implement logic to:
- [ ] Check doctor's available hours before booking.
- [ ] Enforce limits for walk-in and online bookings.
- [ ] Disallow appointment overlaps; maintain 10–15 min minimum gap.
- [ ] Link doctor schedule/availability to Google Calendar.
- [ ] Add function for manual slot blocking in backend.
- [ ] Match backend validations to frontend constraints for data integrity.

## Frontend Schedule and Calendar
- [ ] Convert frontend schedule to calendar view styled like Appointment tab.
- [ ] Link calendar to Google Calendar with dedicated button.
- [ ] Show daily schedules per date.
- [ ] Display available hours based on backend and Google Calendar.
- [ ] Edit only by adding/incremental change; don't delete code.

## Appointment Booking Algorithm
- [ ] Add time and date fields to appointments with 15-minute default gap.
- [ ] Build appointment booking algorithm to:
- [ ] Check doctor availability for chosen slot.
- [ ] Enforce gaps and booking limits.
- [ ] Honor walk-in reservations and manual appointment blocks.
- [ ] Adjust schedule logic so appointments always obey rules.

## Gmail Calendar Integration
- [ ] Integrate Gmail calendar into frontend and backend schedules.
- [ ] Block appointments based on Gmail calendar "Busy" slots.
- [ ] Ensure backend can't book during Google Calendar busy times.
- [ ] Treat Google Calendar as final source for availability.

## Prescription Section
- [ ] Add word-editor-like UI for prescription writing.
- [ ] Allow doctors to create new prescriptions.
- [ ] Enable inserting prescriptions into patient records.
- [ ] Add options for prescription email or WhatsApp sending.
- [ ] Add print button for prescriptions.

## Patient Database and SPA Instructions
- [ ] Build patient tab in frontend listing all patients.
- [ ] Implement opening any patient from appointment or patient tab.
- [ ] When a patient is opened:
- [ ] Show all patient details (name, DOB, city, contact info, etc.)
- [ ] Add option to write remarks for patient record.
- [ ] Enable direct creation of prescriptions from patient view.
- [ ] Show last prescriptions with details.
- [ ] Allow editing/saving patient details with validation.
- [ ] Sync all SPA changes with backend/database (preserve unrelated data).

## New Tasks & Improvements
- [ ] Fix appointment modal overflow UI bug.
- [ ] Improve validation error messages to specify exact fields.
- [ ] Implement backend for doctor schedule (working hours, days off).
- [ ] Create frontend UI to edit/manage doctor schedules.
- [ ] Link appointment form to live schedule data (replace mock).
- [ ] Block bookings outside available schedule/gaps.

## Additional Tasks from Testing
- [ ] Fix appointment form field overflow; prevent content being hidden.
- [ ] Build schedule section so appointments use schedule-picked times.
- [ ] In existing patient tab, improve error handling to mention only missing field, not all fields.
- [ ] Add new tasks at bottom of todo.md; keep previous tasks.
- [ ] Track tasks you add or are requested, never remove original items.

## Next Steps: Unified Schedule View
- [ ] Unify calendar display for hospital/home clinic
- [ ] Modify DoctorSchedule to fetch both schedules.
- [ ] Merge schedules into single data structure.
- [ ] Update ScheduleCalendar to show both locations' hours together.
- [ ] Remove hospital/clinic location tabs.
- [ ] Overhaul Edit Weekly Schedule modal.
- [ ] Redesign modal UI for schedule editing.
- [ ] Add tabs for Home Clinic and Hospital in modal.
- [ ] Make each tab editable for weekly schedule.
- [ ] Update save logic to send POST to /api/v1/schedules/1 and /api/v1/schedules/2
- [ ] Implement day-unavailable feature.
- [ ] Add backend POST /api/v1/unavailable-periods for UnavailablePeriod entries.
- [ ] On calendar date click, open simple modal (DailyUnavailabilityEditor).
- [ ] Modal lets user mark day unavailable for either/both Hospital and Home Clinic.
- [ ] Fetch/display UnavailablePeriod data and override weekly schedule on calendar.

## Immediate Debugging/Rate Limiting Tasks
- [ ] Review app/limiter.py and identify where DummyLimiter is used.
- [ ] Note DummyLimiter is only a placeholder and doesn't enforce rate limits.
- [ ] Decide to defer actual rate limiting to get app running now.
- [ ] Add a todo.md task for implementing rate limiting logic later.
- [ ] Read app/main.py code to debug startup errors.
- [ ] Investigate what startup errors occur.
- [ ] Identify/document causes of startup errors.
- [ ] Fix each startup error one by one.
- [ ] Test changes to verify that the application starts up correctly.
