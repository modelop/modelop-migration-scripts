// Jira Notifications
db.getCollection("notification").find({
    "assignment": { $exists: true },
    "assignment.assignmentType": "JIRA_NOTIFICATION_ASSIGNMENT"
}).forEach(function(doc) {
    try {
        if (doc.assignment && doc.assignment.jiraIssueObject) { // Check if both exist and are not null
            let dueDate = null
            if (doc.assignment.jiraIssueObject["Due Date"] && doc.assignment.jiraIssueObject["Due Date"] !== "") {
                if (doc.assignment.jiraIssueObject["Due Date"].length <= 10) {
                    dueDate = new Date(doc.assignment.jiraIssueObject["Due Date"] + "T12:00:00")
                } else {
                    dueDate = new Date(doc.assignment.jiraIssueObject["Due Date"])
                }
            }
            db.getCollection("notification").updateOne(
                { "_id": doc._id },
                {
                    "$set": {
                        "assignment.dueDate": dueDate,
                        "assignment.priority": doc.assignment.jiraIssueObject.Priority // Using dot notation for 'Priority' is fine
                    }
                }
            );
        } else {
            db.getCollection("notification").updateOne(
                { "_id": doc._id },
                {
                    "$set": {
                        "assignment.dueDate": null,
                        "assignment.priority": null
                    }
                }
            );
        }
    } catch (error) {
        console.log("Error processing notification "+ doc.id + " " + error)
    }
});

// ServiceNow Notifications
db.getCollection("notification").find({
    "assignment": { $exists: true },
    "assignment.assignmentType": "SERVICENOW_NOTIFICATION_ASSIGNMENT"
}).forEach(function(doc) {
    try {
        if (doc.assignment && doc.assignment.serviceNowIssueObject) {
            let dueDate = null
            if (doc.assignment.serviceNowIssueObject.due_date?.value && doc.assignment.serviceNowIssueObject.due_date?.value !== "") {
                if (doc.assignment.serviceNowIssueObject.due_date?.value.length <= 10) {
                    dueDate = new Date(doc.assignment.serviceNowIssueObject.due_date?.value + "T12:00:00")
                } else {
                    dueDate = new Date(doc.assignment.serviceNowIssueObject.due_date?.value)
                }
            }
            db.getCollection("notification").updateOne(
                { "_id": doc._id },
                { $set: {
                        "assignment.dueDate": dueDate,
                        "assignment.priority": doc.assignment.serviceNowIssueObject.priority?.display_value
                    }}
            );
        } else {
            db.getCollection("notification").updateOne(
                { "_id": doc._id },
                {
                    "$set": {
                        "assignment.dueDate": null,
                        "assignment.priority": null
                    }
                }
            );
        }
    } catch (error) {
        console.log("Error processing notification "+ doc.id + " " + error)
    }
});