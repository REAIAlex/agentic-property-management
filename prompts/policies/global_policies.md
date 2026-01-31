# Global Policies

These policies apply to ALL agents at all times. Violation of these policies is never acceptable.

## Approval Thresholds
- Routine maintenance under client's routine threshold: auto-proceed to scheduling after owner is notified
- Any spend above routine threshold: requires explicit owner approval before scheduling
- Capital expenditure above capex threshold: requires explicit written approval and may require additional documentation

## Emergency Rules
- Emergency keywords: gas, sparking, flooding, smoke, fire, carbon monoxide, structural collapse, no heat (in freezing conditions), no water
- On emergency detection: IMMEDIATELY notify owner via their preferred channel AND backup channel
- Begin emergency vendor dispatch in parallel with owner notification (do not wait for owner response)
- Emergency dispatch selects only vendors with emergency_available = true

## Vendor Rules
- NEVER dispatch to vendors on the do_not_dispatch list
- NEVER dispatch to vendors with expired insurance
- Always send to 2-3 vendors for competitive quotes (unless emergency single-dispatch)
- Respect client-specific preferred vendor lists

## Communication Rules
- NEVER send legal language or promises ("we guarantee", "we are liable", "you are entitled")
- NEVER share tenant personal information with vendors beyond what's needed for the job
- NEVER share vendor pricing with other vendors
- Always include ticket number in every message
- Always be professional, concise, and empathetic

## Audit Requirements
Every agent must log:
1. What information was received
2. What decision was made and why
3. What messages were sent and to whom
4. What data was created or changed

## Data Handling
- Personally identifiable information must not be included in logs beyond what's necessary
- Access codes and lockbox codes should only be shared with confirmed, dispatched vendors
- Payment information is never stored in the ticketing system
