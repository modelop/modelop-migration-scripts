db.getCollection('applicationForm').find({"metadata":{"$exists":false}}).forEach(
    function(doc) {
        try {
           let sectionsArray = {};
           //Method to transform section name to lowercase snake case 
           function toSnakeCase(str) {
                return str
                        .replace(/\s+/g, '_')  // Replace spaces with underscores
                        .replace(/[^\w]/g, '') // Remove special characters
                        .toLowerCase();        // Convert to lowercase
            }
           //Recursive method that generates the formFieldsIds for sections and children
           function updateSections(fields,sectionName) {
               if (!Array.isArray(fields)) return;
                let formFieldsIdIndex = 1;
                //We iterate over each element in the array
                fields.forEach(function(field) {
                    if (field.type === "section") {
                        field.formFieldId = toSnakeCase(field.name); // Copy name into formField
                        sectionName  = field.formFieldId;
                        sectionsArray[sectionName] = 1; // Store name as key, value as 0
                    }else{
                        field.formFieldId = "" + formFieldsIdIndex + "";
                        sectionsArray[sectionName] = field.formFieldId;
                        formFieldsIdIndex = formFieldsIdIndex + 1;
                    }
                    if (Array.isArray(field.children)) {
                        updateSections(field.children,sectionName); // Recursively process children
                    }
                });
            }
            //We Start from ROOT as default section
            updateSections(doc.formFields,"ROOT");
            doc.metadata = {}
            doc.metadata.lastUsedIds = sectionsArray;
            printjson(doc);
            //print(newSectionsFormsFields);
        // Update the document in the collection after the updates
            db.getCollection('applicationForm').updateOne(
              { "_id": doc._id }, // Query to find the document
              { $set: doc }// Update operation to set the new fieldBody
            );
        } catch (err) { // Catch the error with a parameter
            print("Error processing document with ID " + err._id + ": " + err);
            printjson(err); // Print the document causing the error for debugging
        }
    }
);
