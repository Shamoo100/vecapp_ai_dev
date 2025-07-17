As an Admin, I want to submit feedback on the AI-generated visitor insight note so that the system can improve future recommendations and track the usefulness of AI insights.

Add

Apps

Description

Precondition:
A follow-up task has been created for the visitor
An AI-generated visitor insight note is present and visible under the task and the Visitor Profile (Admin View only)
Admin has permission to view and manage visitor follow-up records
Acceptance Criteria:
Admin must see a feedback prompt on any AI-generated visitor insight note displayed in:
The Follow-Up Task Notes section
The Visitor Profile → “AI Insights” tab
The system must allow Admin to submit the following structured feedback:
Was this recommendation helpful? (Yes / No / Partially)
Optional Comment field (free-text, max 100 characters)
The feedback interface must only be available for AI-generated notes.
Once submitted:
The system must persist the response and link it to the visitor ID and AI note ID
The note must be marked as “Feedback Received” for audit purposes
Admin can only submit feedback once per AI note.
The system must store this feedback securely and keep it scoped to the tenant.
Feedback must not be visible to members or other Admins unless they also have permission to manage AI recommendations.
If an error occurs during feedback submission:
Admin sees a non-blocking error message
The system logs the issue for system administrators
Postcondition:
Admin feedback is saved and associated with the specific AI note
The system marks the note as having received feedback
Feedback is available for analysis to evaluate AI recommendation effectiveness
The AI note remains visible and unaltered after submission
Sequence Diagram Steps:
Admin opens a Follow-Up Task or Visitor Profile
Admin reviews the AI-generated visitor insight note
System displays feedback interface below the note:
“Was this recommendation helpful?” (Yes / No / Partially)
Optional comment input field
Admin selects a response and (optionally) enters a comment
Admin clicks “Submit Feedback”
System:
Stores feedback linked to Visitor ID + AI Note ID + Admin ID
Updates note status to “Feedback Received”
Confirms success to Admin
If submission fails:
Admin sees a friendly error message
System logs error internally
