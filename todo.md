## now what i want you to do is very improtant for this project okay so what we want to do is read the todo go and not make changes but understand each baby step and the read the files to check that if that logic already exists or it needs to updated or added from scratch and then mark it done 
## this is a previous todo of mine which i made alot of progress to but i want you to verify that everything is working correctly or some curropt part of the code was manually removed by my team since it was not upto the standards okay 
## so read file read dir list dir edit file tools to first understand the project structure and then under stand what the files contain and then proceed with the todo task i just gave you okay 

## General Notes (EDIT TEST)
- Make all changes without deleting existing code.
- Only edit files to make necessary modifications to avoid accidental code removal.
- Ensure all changes are fully backward-compatible with existing appointment and patient functionality.
- Based on all the changes we are making always look for contrasting code in the backend or front end which   can cause possible errors and prevent the app from running
- Read the project files for context starting with all the files in app folder for backend and root folder has front end html code
 


## bot features

-   we want the flow of the whatsapp bot to be 
users sends their first message hi or hello ( or litreally anything )
we send the greeting message either with name or the default greeting message with the menu of buttons to click either button for either of the task 
now the user selects an option ( for example booking an appointment )
now based on the appointment we take name dob reason etc as input 
now we dont take any text they send as the textual input if its name we confirm its their name with yes or no 
for dob we use DD/MM/YYYY to understand its their dob and use yes or no buttons again to make sure its the correct input 
the reason is optional we then present them with set dates to choose from and set locations
based on the date and locaiton we give them available slots for the option to choose from okay
now in this process at any time user send another message or they send hi or hello ( or like in my case in the evening while testing the bot i went upto to the slot booking process and then sttoped testing now whenever i text back the bot i still get stuck with the appointment slot message so if a certain amount of time has passed or the user clicks the go back buton we take the user back to the default input for menu and greeting message okay ?)
now this should be the flow and we have to make sure the buttons are working fine and are being displayed correctly to the user 



- now also add a feature before starting the main menu directly we ask user for hindi or english and which ever input they start with we send messages in that prefered language but one problem here is that if the users enters their name or anything in hindi our databse needs to translate to english and then store it because two languages storing will create problem in database ??

|1️⃣ Flow Design
Step 1: Ask Language Preference

On first contact:

Please choose your language / कृपया अपनी भाषा चुनें:
1️⃣ English
2️⃣ हिंदी


Store in session:

session['lang'] = 'english'  # or 'hindi'


This decides which template messages you send.

Step 2: Collect User Information

Ask for name, date of birth, reason for appointment, etc.

Inputs allowed:

English

Hinglish (Hindi typed using English letters)

Optional: Full Hindi script (if you want, translate to English before storing)

No conversion required for Hinglish → store as-is in DB.

Example:

Enter your reason for visit:
"Sir dard ho raha hai"  # Hinglish input, stored as-is

Step 3: Send Messages in Preferred Language

Use session variable to pick the message template:

def send_message(user, message_en):
    if user.session['lang'] == 'hi':
        # If you want, translate message_en to Hindi
        message_hi = translator.translate(message_en, src='en', dest='hi').text
        send_whatsapp(user.phone, message_hi)
    else:
        send_whatsapp(user.phone, message_en)


User responses can remain in English/Hinglish, no issues.

Step 4: Database Design

Store all user data as-is, except for cases where full Hindi script is used and you need an English version for consistency (optional).

Recommended table columns:

name          VARCHAR
dob           DATE
reason        TEXT  # accepts English or Hinglish
lang          VARCHAR(2)  # 'en' or 'hi'
original_text TEXT  # optional, stores raw input if translation occurs

Step 5: Booking / Menu Flow

After collecting initial info, show main menu in selected language.

Everything else (appointment details, confirmation, reminders) follows the selected language.

✅ Benefits of This Flow

Users can type naturally in Hinglish without conversion problems.

You maintain DB consistency without forcing translation for everything.

Messages still adapt to user preference (English/Hindi) professionally.

Handles future expansion if you want to support full Hindi translation for other messages.