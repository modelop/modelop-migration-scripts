# Migration Process for Upgrading StoredModels modelMetadata.custom to 3.3.2 standard

### Introduction:
This guide outlines the steps required to upgrade existing ModelOp Center (MOC) environments to use the new StoredModels.modelMetadata.custom format introduced in version 3.3.2.

## Prerequisites
- Before starting the migration process, ensure the following:

- MOC Environment: All MOC images are upgraded to version 3.3.2.

- Application Forms: All Application Forms are already migrated to the 3.3.2 format.

- Admin Access: You have admin access to the MOC Browser UI to generate the necessary input file.

- Backups: Back up the StoredModels collection and all Application Forms.

- Python: Python 3.8 or later is installed and properly configured.

- MongoDB Access: You have access to the MongoDB instance used by your MOC environment.

- DocumentDB Version Compatibility:

    - For DocumentDB version 5.0, use `storedmodels_metadata_custom_3-3-2_converter.py`

    - For DocumentDB version 4.0, use the script under `ONLY_DOCUMENT_DB_4_storedmodels_metadata_custom_3-3-2_converter.py`




### Overview

The migration process involves two main steps:

1- Generate MongoDB Migration Scripts: Use a Python script to convert application form metadata into MongoDB update scripts.

2- Execute the Migration Scripts: Run the generated scripts to apply updates to your database.


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


For MongoDB and DocumentDB 5.0.0:

```
python storedmodels_metadata_custom_3-3-2_converter.py applications-forms-dump.json 
```

For Document DB 4.0.0:

```
python ONLY_DOCUMENT_DB_4_storedmodels_metadata_custom_3-3-2_converter.py applications-forms-dump.json 
```

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
