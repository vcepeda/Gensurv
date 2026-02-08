-- Drop the old constraint pointing to auth_user
ALTER TABLE gensurvapp_submission 
DROP CONSTRAINT gensurvapp_submission_user_id_5c47cc02_fk_auth_user_id;

-- Add new constraint pointing to register_customuser
ALTER TABLE gensurvapp_submission 
ADD CONSTRAINT gensurvapp_submission_user_id_5c47cc02_fk_register_customuser_id 
FOREIGN KEY (user_id) REFERENCES register_customuser(id) DEFERRABLE INITIALLY DEFERRED;
