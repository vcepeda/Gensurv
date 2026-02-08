### backend/gensurvapp/scripts/serializers.py
It defines DRF (django-rest framework) serializers which validate upload requests and shape API responses. It contains request validators for `uploads` and `dashboard`. 

### backend/gensurvapp/services/__pycache__
It splits the former views.py logic and contains the business logic for the dashboard page i.e. fetching the entries and files from the database to display it on the dasboard.

### backend/gensurvapp/services/upload_service.py
Similar to dashboard_service.py, it splits the business logic of the upload function from the former views.py i.e. checking for the validity of the metadata file and then checking the consistency of other files w.r.t the metadata file.

### backend/gensurvapp/models_old.py
Old models.py file

### backend/gensurvapp/models.py
Modifications made to the models by me, such as 
- removing `save_files` method from the `Submission` model
- removing `metadata_file` filed from the `Submission` model as it was already being saved in `UploadedFile` model. Added `submit_to_pipeline` file as it was not present before.
- dropped `SampleFile` as it was redundant and `UploadFile` was enough by itself, made the corresponding changes in models to not point to `SampleFile` as a forigen key. 

### backend/gensurvapp/models_LLM.py
Asked an LLM to make the most optimal and efficient models.py, the changes are documented in `models_LLM.py`.

### backend/gensurvapp/urls.py
Contains the new urls for the api views.

### backend/gensurvapp/utils.py
Contains helper functions which are used by the business logic files (files in the `services` folder), such as `validate_csv`, etc.

### backend/gensurvapp/views.py
Conatins the new rest-api code to make the backend have api endpoints, uses files from the services folder as the initial function from the old views.py (now `views_non-api.py`) are split to make it easier to understand.

### backend/gensurvapp/views2.py / backend/gensurvapp/views copy.py
Old code

### backend/gensurv_project_nginx
Changes the nginx config to support both frontend and backend, not tested yet!