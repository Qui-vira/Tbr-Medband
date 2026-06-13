## MedBand Band Messaging Rules (enforced in code)

### One message per stage
Post exactly **one** band_send_message per workflow stage. The platform formats JSON into clean human-readable text automatically.

**Never post:**
- A second summary after JSON for the same stage
- Messages starting with `---`
- Legacy templates containing: "Verification passed", "Resource confirmed", "CASE READY FOR YOUR REVIEW", "Passing to Resource check now", "Passing full summary to Coordinator now", or "SUMMARY FOR HUMAN REVIEW"

If you already sent JSON for a stage, do not send any follow-up natural-language summary for that stage.

### Idempotency
Each case_id may only emit each workflow stage once:
CASE_OPENED, INTAKE_COMPLETE, VERIFY_REQUEST, CASE_CLEAR, CASE_CAUTION, CASE_ESCALATE, RESOURCE_REQUEST, RESOURCE_COMPLETE, CASE_READY, HUMAN_ALERT, CASE_APPROVED, CASE_REJECTED.

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
- Never post raw JSON to the Band room (send JSON in band_send_message content; formatting is applied automatically).
- Post one clean, human-readable message per stage.
- Never use em dashes. Use hyphens or colons instead.

### Resource context
Use institution_name and requested_service from the case payload (Postgres intake context). Do not invent a different hospital or shorten the drug name.

### HUMAN_ALERT
Send HUMAN_ALERT only when:
- Verification returns CASE_ESCALATE
- Verification failed
- A controlled substance is missing a valid prescription
- An AIML call fails
- Required patient data is missing
- Safety policy requires human escalation

Never send HUMAN_ALERT when Verification returns CASE_CLEAR or CASE_CAUTION.

### Expected visible stage messages (demo)
A complete case shows only these room messages in order:
1. CASE OPENED
2. INTAKE COMPLETE
3. VERIFICATION COMPLETE (or CAUTION / ESCALATION)
4. RESOURCE COMPLETE
5. CASE READY FOR HUMAN REVIEW
6. CASE APPROVED (after human types APPROVE)

### CASE APPROVED template (after human approval)
Send JSON with `"status": "CASE_APPROVED"` only. Do not add a second plain-English confirmation. The platform formats:

```
✅ CASE APPROVED

Case ID: {case_id}

Patient:
{name}

Request:
{requested_service}

Decision:
Approved by {human reviewer name}

Status:
Closed

Important:
No AI approved this case. Final approval was made by the human reviewer.
```

When calling band_send_message, put structured JSON in the content field. Do not paste duplicate summaries or legacy `---` blocks.
