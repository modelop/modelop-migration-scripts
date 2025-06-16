db.getCollection('storedModel').find(
    {"modelMetaData.custom.mocApplicationFormId":{"$exists":1}}
).forEach(
    function(doc) {
        function toSnakeCase(str) {
            return str
                .replace(/\s+/g, '_')  // Replace spaces with underscores
                .replace(/[^\w]/g, '') // Remove special characters
                .toLowerCase();        // Convert to lowercase
        }

        function processQuestion(questionFormField, jsonSection) {
            // Identified issue is with multiselect fields
            if (questionFormField.multiselect == true) {
                if (!jsonSection[questionFormField.formFieldId]) {
                    // Confirming that the expected formFieldId was not found
                    // This needs to be fixed
                    let problematicKey = toSnakeCase(questionFormField.name)
                    let problematicSection = jsonSection[problematicKey]
                    print(`Part with issue: ${problematicKey} ${JSON.stringify(problematicSection)}`)
                    let fixedQuestionKey = questionFormField.formFieldId
                    delete problematicSection.name
                    let fixedArray = Object.values(problematicSection)
                    let fixedQuestionSection = {
                        "question" : questionFormField.name,
                        "answer" : fixedArray
                    }
                    print(`Fixed question ${fixedQuestionKey} = ${JSON.stringify(fixedQuestionSection)}`)
                    delete jsonSection[problematicKey]
                    jsonSection[fixedQuestionKey] = fixedQuestionSection
                }
            }
        }

        function processSection(sectionFormField, jsonSection) {
            // List the questions in the form:
            for (let child of sectionFormField.children) {
                if (child.type !== "section") {
                    // We are sending the whole section downstream, 
                    // and letting the function find the right question structure
                    processQuestion(child, jsonSection)
                } else {
                    processSection(child, jsonSection[child.formFieldId])
                }
            }
        }

        function navigateForm(formFields, customMetadata) {
            for (let formField of formFields) {
                print("Inspecting section: " + formField.name)
                if (formField.type === "section") {
                    processSection(formField, customMetadata[formField.formFieldId])
                } else {
                    print (`Unexpected type ${formField.type} found for ${formField.name}`)
                }
            }
        }

        try {
            
            let updatedCustomMetadata = {};
            let customMetadata = doc.modelMetaData.custom;
            let applicationFormId = doc.modelMetaData.custom.mocApplicationFormId;
            let applicationFormArray = db.getCollection('applicationForm').find({ "_id": JUUID(applicationFormId)}).toArray();
            let applicationForm = {};
            
            if (applicationFormArray && applicationFormArray.length) {
                applicationForm = applicationFormArray[0]
            }
            // print("App Form: " + JSON.stringify(applicationForm));
            print("\nInspecting StoredModel: "+ doc.modelMetaData.name)
            navigateForm(applicationForm.formFields, customMetadata);
            
            // Update the document in the collection after the updates
            db.getCollection('storedModel').updateOne(
              { "_id": doc._id }, // Query to find the document
              { $set: doc }// Update operation to set the new body
            );
            print("StoredModel successfully upgraded model "+ doc.modelMetaData.name +" with id: " + doc._id);

        } catch (err) { // Catch the error with a parameter
            printjson(err); // Print the document causing the error for debugging
        }
    }
);