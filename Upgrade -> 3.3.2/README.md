# Migration Process for Upgrading StoredModels modelMetadata.custom to 3.3.2 standard

### Introduction:

This document provides the necessary steps to upgrade existing MOC environments that use the previous StoredModel modelMetaData.custom  format to the new 3.3.2 standard. 

### Prerequisites

- MOC images must already be migrated to 3.3.2.
- All Application Forms must already be migrated to the new 3.3.2 format.
- Admin ModelOp Center Browser Access: You must have access to the MOC admin browser access to generate the input file with existing ApplicationForms.
- Backup: Ensure you have a backup of both the StoredModel collection and Application Forms before proceeding.
- Python: Ensure Python 3.8 or + ,   is installed and configured on your system.
- MongoDB Access: You must have access to the MongoDB instance that contains the application forms and stored models.
- If the underlaying DB is DocumentDB, then the supported version is 5.0 , if its 4.0 please use the script labeled only_for_document_db_4/storedmodels_metadata_custom_3-3-2_converter_doc_4.py


### Overview

The migration process is divided into two main steps:

Generate MongoDB Migration Scripts: A Python script (storedmodels_metadata_custom_3-3-2_converter.py) receives an input file containing existing application forms and generates a set of MongoDB migration scripts (one script per application form).

Execute Migration Scripts: The generated MongoDB migration scripts are executed on the target environment to perform the necessary database updates.


---

### Steps

- Generate Input File for Migration Script: To generate the input file for the migration, you’ll need to fetch the current list of application forms. Execute the following API call:

http://<MOC_BASE_URL>/model-manage/api/applicationForms?size=100 

- Replace <MOC_BASE_URL> with your MOC base URL (e.g., localhost:8090).

Set size to the total number of application forms + 1 (e.g., if there are 99 application forms, use size=100).

Example request:

http://localhost:8090/model-manage/api/applicationForms?size=100

- Save the full response of the API call as a JSON file (e.g., applications-forms-dump.json).

- Clone the Repository: Clone or download the migration repository from GitHub:

git clone this reposiroty.

- Run the Python Migration Script: With the input file (applications-forms-dump.json) ready, run the Python script to generate the migration scripts:

python storedmodels_metadata_custom_3-3-2_converter.py applications-forms-dump.json 

If everything is successful, an output directory will be created. This directory contains one migration script for each application form.

--- 
### Execute the MongoDB Migration Scripts:

Run the generated migration scripts against your MongoDB instance.

Validate that the stored models are correctly upgraded by checking the corresponding data in your database.

---

### Validation

Once the migration scripts have been executed, verify the following:

StoredModels should reflect the changes as expected.

If any issues arise, review the generated migration scripts or consult the backup for rollback options.
