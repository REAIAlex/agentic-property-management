Maintenance Quote for Ticket {{ticket_number}}

Property: {{property_address}} {{unit_number}}
Issue: {{summary}}
Trade: {{trade}}

We received {{quote_count}} quote(s):

{{#each quotes}}
**{{vendor_name}}** - ${{total_amount}}
- Labor: ${{labor_amount}} | Materials: ${{materials_amount}}
- Warranty: {{warranty_terms}}
- Available: {{earliest_availability}}
{{#if red_flags}}- Flags: {{red_flags}}{{/if}}
{{/each}}

**Recommendation**: {{recommendation}}

Reply with the vendor number to approve, or "DECLINE" to pass.
