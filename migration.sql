-- SQL migration script to update the 'patients' table

ALTER TABLE patients
ADD COLUMN first_name_encrypted BYTEA NOT NULL,
ADD COLUMN last_name_encrypted BYTEA NOT NULL,
ADD COLUMN city_encrypted BYTEA NOT NULL,
ADD COLUMN phone_number_encrypted BYTEA,
ADD COLUMN email_encrypted BYTEA,
ADD COLUMN address_encrypted BYTEA,
ADD COLUMN phone_hash VARCHAR(64),
ADD COLUMN email_hash VARCHAR(64),
ADD COLUMN first_name_hash VARCHAR(64) NOT NULL,
ADD COLUMN last_name_hash VARCHAR(64) NOT NULL;

-- Add indexes for the new hash columns to improve lookup performance
CREATE INDEX idx_patients_phone_hash ON patients (phone_hash);
CREATE INDEX idx_patients_email_hash ON patients (email_hash);
CREATE INDEX idx_patients_dob ON patients (date_of_birth);
CREATE INDEX idx_patients_created ON patients (created_at);

-- It looks like you're also using fields that may not be in the original table.
-- The following are based on the full Patient model in your app/models.py file.
-- If these columns already exist, you can remove them from this script.

ALTER TABLE patients
ADD COLUMN IF NOT EXISTS blood_type VARCHAR(5),
ADD COLUMN IF NOT EXISTS allergies TEXT,
ADD COLUMN IF NOT EXISTS emergency_contact_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS emergency_contact_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS insurance_provider VARCHAR(100),
ADD COLUMN IF NOT EXISTS insurance_number_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS insurance_number_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS preferred_communication VARCHAR(20) DEFAULT 'phone',
ADD COLUMN IF NOT EXISTS communication_preferences JSON,
ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS whatsapp_opt_in BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS whatsapp_opt_in_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS hipaa_authorization BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS hipaa_authorization_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS consent_to_treatment BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS consent_to_treatment_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS vip_status BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS last_visit_date TIMESTAMPTZ;