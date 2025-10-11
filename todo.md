## General Notes
-   Make all changes without deleting existing code.
-   Only edit files to make necessary modifications to avoid accidental code removal.
-   Ensure all changes are fully backward-compatible with existing appointment and patient functionality.
-   Based on all the changes we are making always look for contrasting code in the backend or front end which can cause possible errors and prevernt the app from running 
-   Read the project files for context starting with all the files in app folder for backend and root folder has front end html code 

## Appointment Form Modifications
- [x] Modify appointment form to allow creating patients with required fields: first name, last name, DOB, date and time for appointment, city.
- [x] Add manual name entry with an algorithm suggesting patients from past database entries based on letters entered.
- [ ] For existing patients in the database, the suggestion algorithm will take place. The appointment form will have two sections:
  - [x] Default: choosing an existing patient with date and time.
  - [x] Creating a new patient with all the same fields, who will also be inserted into the patient database.
- [x] Include first name and last name fields.
- [x] Add a location/address feature that takes the city they belong to (optional).
- [x] Add a date of birth (DOB) field.
- [x] Add a reason for visit field (optional).
- [x] Make first name, DOB, date, and time necessary fields.
- [x] Make last name, city, and reason for visit optional fields.
- [x] Convert start time and end time into time only for appointment, with each appointment having a 10-minute gap by default.
- [x] Add a field for the date of appointment, defaulting to the current day or next day if active schedule time for the day is over.
- [x] Show available hours for the day.
- [ ] Add a constraint to prevent booking if an appointment already exists for the same time or if booking exceeds a time slot reserved for walk-in patients. Limit the number of online appointments accordingly.
- [x] Ensure a default 15-minute gap between each appointment.
- [ ] Add a field to manually block the appointment booking system for a day (e.g., if walk-in patients are flooded) for hospital/home/clinic.
- [ ] Schedule section when built like the calendar it should also have an option for default available schedule slots where the hospital hours and clinic hours can be modified with a off option to display either on certain days 

## Backend and Data Handling
- [ ] Check the backend for the type of data it expects for appointments, including time, date, patient info, and optional fields.
- [ ] Check what kind of patient appointment data the database expects.
- [ ] Make necessary changes for backend and database compatibility.
- [ ] Add logic to:
  - [ ] Check doctor’s available hours before booking an appointment.
  - [ ] Respect limits for walk-in patients and maximum online bookings.
  - [ ] Prevent double-booking and maintain minimum 10–15 minute gaps.
  - [ ] Link doctor schedule and availability with Google Calendar.
  - [ ] Allow manual blocking of appointment slots in the backend.
- [ ] Ensure all backend validations match frontend constraints for consistent data integrity.

## Frontend Schedule and Calendar
- [ ] Convert the current frontend schedule into a calendar view similar to the appointment tab which will be linked to Google Calendar with a button to show Google Calendar as well.
- [ ] Display schedule for each date.
- [ ] Show available hours dynamically based on backend availability and Google Calendar.
- [ ] Ensure no code is deleted while editing; make only incremental changes.

## Appointment Booking Algorithm
- [ ] Add time and date to appointments with a 15-minute gap by default.
- [ ] Create a robust appointment booking algorithm that:
  - [ ] Checks doctor availability.
  - [ ] Enforces booking limits and gaps.
  - [ ] Respects walk-in reservations and manual blocks.
- [ ] Setup schedule to ensure appointments are always available according to rules.

## Gmail Calendar Integration
- [ ] Integrate Gmail calendar link with frontend and backend schedules.
- [ ] Block days/times based on unavailability on Gmail calendar.
- [ ] Ensure backend does not book appointments during Google Calendar busy slots.
- [ ] Use Google Calendar as the final source of truth for availability.

## Prescription Section
- [ ] Add a word-editor like UI for prescriptions.
- [ ] Enable prescriptions to be created by doctors.
- [ ] Insert prescriptions into patient records.
- [ ] Add functionality to send prescriptions via email or WhatsApp.
- [ ] Add option to print prescriptions directly.

## Patient Database and SPA Instructions
- [ ] Create a patient tab in the frontend where all patients are displayed in a list.
- [ ] Enable opening any patient from either the appointments tab or the patients tab.
- [ ] When a patient is opened:
  - [ ] Display patient details including first name, last name, DOB, city, contact info, and other relevant fields.
  - [ ] Allow adding remarks to the patient record.
  - [ ] Allow creating and adding new prescriptions directly from the patient view.
  - [ ] Display the patient’s last prescriptions with details.
  - [ ] Enable editing and saving patient details with proper validation.
  - [ ] Ensure any changes made in the SPA are synced with the backend and database without overwriting unrelated data.

## New Tasks & Improvements
- [ ] Fix appointment modal overflow issue.
- [ ] Improve form validation error messages to be more specific.
- [ ] Implement backend logic for doctor scheduling (e.g., working hours, days off).
- [ ] Create frontend UI to manage doctor schedules.
- [ ] Connect appointment form to live schedule data instead of mock data.
- [ ] Add constraints to prevent double-booking or booking outside of available hours.


## addtional tasks based on testing 
- [ ] as you can see in create new appointment form because of all the fields in the container the content is flowing out on the bottom and ending up as hidden and secondly well have to build the schdule section as well so the appointment can be booked for available time which is taken from the schedule if you get me 


- [ ] and secondly in the existing patient tab when i click on submit the logic is correct since the fileld is empty the form should not submit but it should mention the specific field which i need to fill and not mention everything so improve on error handling as well thourghout the system 

- [ ] additonlay you can also add stuff in todo.md remember to only edit and add new stuff you want on the bottom and not delete mine so you can also keep track of additional things you want to do or i made you do 

## Next Steps: Unified Schedule View

- [ ] **Task 1: Unify Calendar Display**
  - [ ] Modify `DoctorSchedule` to fetch schedules for both "Home Clinic" and "Hospital".
  - [ ] Combine the two schedules into a single data structure to pass to the calendar component.
  - [ ] Update the `ScheduleCalendar` cell rendering logic to display hours for both locations simultaneously (e.g., "Clinic: 9-5, Hospital: 10-6").
  - [ ] Remove the location tabs.

- [ ] **Task 2: Overhaul "Edit Weekly Schedule" Modal**
  - [ ] Redesign the `ScheduleEditor` modal.
  - [ ] Add tabs within the modal: "Home Clinic" and "Hospital".
  - [ ] Each tab will contain the 7-day weekly schedule editor for that specific location.
  - [ ] Update the `onSave` function to send two separate `POST` requests to update the schedules for each location (`/api/v1/schedules/1` and `/api/v1/schedules/2`).

- [ ] **Task 3: Implement "Mark Day as Unavailable" Feature**
  - [ ] Create a new backend endpoint `POST /api/v1/unavailable-periods` to create `UnavailablePeriod` entries. This will block off specific dates.
  - [ ] When a user clicks on a date in the `ScheduleCalendar`, open a new, simple modal (`DailyUnavailabilityEditor`).
  - [ ] This modal will allow the user to mark the selected date as unavailable for "Home Clinic", "Hospital", or both.
  - [ ] Update the `DoctorSchedule` component to also fetch `UnavailablePeriod` data from the backend and display these days as "Unavailable" on the calendar, overriding the regular weekly schedule.