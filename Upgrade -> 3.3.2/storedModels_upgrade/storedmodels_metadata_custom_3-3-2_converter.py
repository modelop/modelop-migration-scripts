import json
import sys
import os

mongosh_header_js = """
db.getCollection('storedModel').find({"modelMetaData.custom.mocApplicationFormId":{"$exists":1},
"modelMetaData.custom.mocApplicationFormId":__APPLICATION_FORM_ID__}).forEach(
    function(doc) {
        try {
        """

mongosh_footer_js = """
            //Method to transform section name to lowercase snake case
           function toSnakeCase(str) {
                return str
                        .replace(/\s+/g, '_')  // Replace spaces with underscores
                        .replace(/[^\w]/g, '') // Remove special characters
                        .toLowerCase();        // Convert to lowercase
            }

            function toSectionWithNewFormat(jsonSection,sectionName){

               let sectionNameUpdated = toSnakeCase(sectionName);
               let sectionWithNewFormat = {};
               let questions = {};
               for (let questionsInSection in jsonSection) {
                  if (typeof jsonSection[questionsInSection] === "string"
                  || typeof jsonSection[questionsInSection] === "number") {
                    let questionInSectionWithOutDot = questionsInSection.replace(/\#/g, ".");
                    let mapKey = sectionNameUpdated + "." + questionInSectionWithOutDot;
                     questionIndexFromMap = jsonQuestionsArray[mapKey]
                      if(typeof questionIndexFromMap !== "undefined" ){

                        questions[""  + questionIndexFromMap + ""] = {
                                "question" :  questionInSectionWithOutDot ,
                                "answer" : jsonSection[questionsInSection]
                            }
                      }else{
                        //Note: internal section values will be fine, but section name will end up snake_cased..
                        //This is because a section can have some found and not found questons... and we need to support that
                        //thats why...
                        //Value did not match ... so It can't be migrated
                        questions[questionsInSection] = jsonSection[questionsInSection];
                      }
                   }else{
                        let questionsInSection_is_section_as_snake_case = toSnakeCase(questionsInSection);
                        let subsection_name = sectionNameUpdated + "." + questionsInSection_is_section_as_snake_case;
                        //Its a new section
                        questions[subsection_name] = toSectionWithNewFormat(jsonSection[questionsInSection],subsection_name);
                   }
                }
                questions["name"] = sectionName;
                return sectionWithNewFormat[sectionNameUpdated] = questions;
           }
            let updatedCustomMetadata = {};
            let customMetadata = doc.modelMetaData.custom;
            let applicationFormId = doc.modelMetaData.custom.mocApplicationFormId;
            // Iterate through the main keys (Risk Management, Accountability, etc.)
            for (let customMetadataField in customMetadata) {
                if (typeof customMetadata[customMetadataField] === "object") {
                    let customMetadataFieldSnakeCase = toSnakeCase(customMetadataField);
                    updatedCustomMetadata[customMetadataFieldSnakeCase] = toSectionWithNewFormat(customMetadata[customMetadataField],customMetadataField);
//                     print("field is a JSON object:" + customMetadataFieldSnakeCase);
                 } else if (typeof customMetadata[customMetadataField] === "string") {
                    questionIndexFromMap = jsonQuestionsArray[customMetadataField];
                    //If the question was found then we migrate to new format otherwise we kept the older value
                    if(typeof questionIndexFromMap !== "undefined" ){
                        updatedCustomMetadata[""  + questionIndexFromMap + ""] = {
                                "question" :  customMetadataField ,
                                "answer" : customMetadata[customMetadataField]
                            }
                    }else{
                        updatedCustomMetadata[customMetadataField] = customMetadata[customMetadataField];
                    }

                 }
            }
            updatedCustomMetadata["mocApplicationFormId"] = applicationFormId;
            doc.modelMetaData.custom = updatedCustomMetadata;

            // Update the document in the collection after the updates
            db.getCollection('storedModel').updateOne(
              { "_id": doc._id }, // Query to find the document
              { $set: doc }// Update operation to set the new fieldBody
            );

            print("StoredModel successfully upgraded with id: " + doc._id);

        } catch (err) { // Catch the error with a parameter
            printjson(err); // Print the document causing the error for debugging
        }
    }
);
"""



"""
Method that generates a dict from an ApplicationForm section following the 3.3.2 ApplicationForm standard 
This method supports nested sections 
"""


def to_dict_of_questions_from_section(section_name, children):
    sec_dict_of_questions = {}
    for question in children:

        if question["type"] == "section":
            sub_section_name = section_name + "." + question["formFieldId"]
            # Its a section so I nned to extract questions and Id's
            sec_dict_of_questions.update(to_dict_of_questions_from_section(sub_section_name, question["children"]))
        else:
            key = section_name + "." + question["name"]
            sec_dict_of_questions[key] = question["formFieldId"]

    return sec_dict_of_questions


"""
Method in charge of generating a complete dict of question from an ApplicationForm.formFields
"""


def generate_dict_of_questions_from_app_form(application_form):
    dict_of_questions = {}
    for formfield in application_form["formFields"]:
        if formfield["type"] == "section":
            # Its a section so I need to extract questions and Id's
            dict_of_questions.update(to_dict_of_questions_from_section(formfield["formFieldId"], formfield["children"]))
        else:
            key = formfield["name"]
            dict_of_questions[key] = "" + str(formfield["formFieldId"]) + ""

    return dict_of_questions


"""
Method that writes the json_dict_of_questions from a given applicationForm into a Mongosh .js file
"""


def write_to_file(applicationFormId, json_dict_of_questions):
    print(f"Writing DB script from application Id: {applicationFormId} ")

    db_script_file_name = "storedmodel_db_fix_for_application_form_" + applicationFormId + "_.js"

    header_str = mongosh_header_js.replace("__APPLICATION_FORM_ID__", "\"" + applicationFormId + "\"")
    footer_str = mongosh_footer_js

    # Create the 'output' folder if it doesn't exist
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Construct the full file path
    db_script_file_path = os.path.join(output_folder, db_script_file_name)

    # Write both strings into a third file
    with open(db_script_file_path, "w", encoding="utf-8") as f3:
        f3.write(
            header_str + "\n" + "\n\t\t\t\t" + f"const jsonQuestionsArray = {json_dict_of_questions};\n" + "\n" + footer_str
        )



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Usage: python storedmodels_metadata_custom_3-3-2_converter.py <file_path>")
    else:
        try:
            file_path = sys.argv[1]
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

        num_processed_app_forms = 1
        num_of_skipped_app_forms = 0
        applications_form_array = data["_embedded"]["applicationForms"]
        total_app_forms = len(applications_form_array)

        for application_form in applications_form_array:

            app_form_id = application_form["id"]

            if "metadata" not in application_form or application_form["metadata"] == {}:
                print(f"Skipping - application_form_id:{app_form_id} because its empty, or likely was not migrated to "
                      f"the new standard yet")
                num_of_skipped_app_forms += 1

            else:
                print(f"Processing ({num_processed_app_forms}/{total_app_forms}) - application_form_id:{app_form_id}")
                try:

                    dict_quest = generate_dict_of_questions_from_app_form(application_form)
                    # Convert dictionary to a JSON string (ensuring double quotes)
                    json_dict_of_questions = json.dumps(dict_quest, indent=4)
                    write_to_file(app_form_id, json_dict_of_questions)
                    num_processed_app_forms += 1

                except Exception as e:
                    print(f"An error occurred: {e}")
                    sys.exit(1)

        print(f"Process successfully completed, total number of processed application forms:{num_processed_app_forms} "
              f"with skipped application_forms:{num_of_skipped_app_forms}")
