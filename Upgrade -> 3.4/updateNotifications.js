// Jira Notifications update
db.getCollection("notification").find({
    "assignment": { $exists: true },
    "assignment.assignmentType": "JIRA_NOTIFICATION_ASSIGNMENT"
}).forEach(function(doc) {
    db.getCollection("notification").updateOne(
        { "_id": doc._id },
        { $set: {
                "assignment.dueDate": doc.assignment.jiraIssueObject["Due Date"],
                "assignment.priority": doc.assignment.jiraIssueObject.Priority
            }}
    );
});

// ServiceNow Notifications update
db.getCollection("notification").find({
    "assignment": { $exists: true },
    "assignment.assignmentType": "SERVICENOW_NOTIFICATION_ASSIGNMENT"
}).forEach(function(doc) {
    db.getCollection("notification").updateOne(
        { "_id": doc._id },
        { $set: {
                "assignment.dueDate": doc.assignment.serviceNowIssueObject.due_date.display_value,
                "assignment.priority": doc.assignment.serviceNowIssueObject.priority.display_value
            }}
    );
});
