## MedBand Band Messaging Rules (enforced in code)

### Idempotency
Each case_id may only emit each workflow stage once:
CASE_OPENED, INTAKE_COMPLETE, VERIFY_REQUEST, CASE_CLEAR, RESOURCE_REQUEST, RESOURCE_COMPLETE, CASE_READY, HUMAN_ALERT.

If a stage was already posted for that case_id, do not send it again.

### Routing
- Only the Coordinator routes work between agents.
- Intake responds only to the Coordinator.
- Verification responds only to the Coordinator.
- Resource responds only to the Coordinator.
- Resource must never message Verification.
- Verification must never message Resource.
- Never respond to your own messages.

### Visible messages
- Never post raw JSON to the Band room.
- Post one clean, human-readable message per stage.
- Do not post both JSON and a summary for the same stage.
- Never use em dashes. Use hyphens or colons instead.

### HUMAN_ALERT
Send HUMAN_ALERT only when:
- Verification returns CASE_ESCALATE
- Verification failed
- A controlled substance is missing a valid prescription
- An AIML call fails
- Required patient data is missing
- Safety policy requires human escalation

Never send HUMAN_ALERT when Verification returns CASE_CLEAR or CASE_CAUTION.

### CASE OPENED template
```
📋 CASE OPENED

Patient: {name}
Institution: {institution}
Request: {request}
Issue: {issue}
Urgency: {urgency}
Prescription Code: {code if any}

Next Step:
Intake agent will structure the request.
```

### CASE READY template
Use the full CASE READY FOR HUMAN REVIEW format from the Coordinator prompt with labeled sections and APPROVE / REJECT / MORE INFO options.

When calling band_send_message, put the final human-readable text in the content field. Structured data is tracked internally; do not paste JSON blocks into Band.
