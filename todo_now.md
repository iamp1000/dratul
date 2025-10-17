prescription editor should be like a microsoft word where defaults can be set and then what ever data is entered always forms a new prescrption and furtoher more having option to create prescription send them via whatsapp or email to the patient with having ability to save it in a pateint's database like enter existing patinet or create patient from prescription now remember everything should be cross connected like parient create in prescription editor will use the same pateint creation which the appointment does so no extra code and the same goes for patient data or the patinets section in the dashboard where all the patients data will be stored where each patinetn can be clicked on and managed ie remarks of them can be editied or added like notes and then prescription can be added last prescription can be viewed and then additionaly all the patinetn data can be seen their including past appointments etc etc now before making new routs and functions for all of this check if something already exists realted to this and then make changes to the existing or create compeletley from new okay so yeah get started my idea is very vauge you build the logic and you do everything to make it production ready

Baby-step TODO Status (current project)

- [x] Add shared patient creation service (`create_or_get_patient_from_payload`)
- [x] Add rich prescription create endpoint (POST `/api/v1/prescriptions/rich`)
- [x] Word-like editor base (Quill) with template overlay and HTML save
- [ ] Editor patient panel (search existing or create new inline)
- [ ] Editor save → call `/prescriptions/rich` and show success with returned `document_id`
- [ ] Editor Send modal (WhatsApp/Email) and call send endpoints
- [ ] Editor Print/PDF button using `/prescriptions/editor/pdf/{document_id}`
- [x] API: list prescriptions for patient (GET `/api/v1/prescriptions/by-patient/{patient_id}`)
- [x] API: send prescription (existing `/api/v1/prescriptions/share`)
- [ ] Patient profile: list prescriptions with View/Send actions
- [ ] Dashboard: Recent Prescriptions widget with links
- [ ] Permissions: enforce stricter role checks on create/edit/send
- [ ] Error UX: surface backend field messages in toasts/forms
- [ ] Docs: README for templates/defaults and required envs


