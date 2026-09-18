"""
Prompts used by DocuFlow AI features.

Keeping prompts separate from AI orchestration makes them easier
to review, test, version, and improve independently.
"""

DOCUMENT_CLASSIFICATION_PROMPT = """
You classify business documents for DocuFlow.

Classify the provided document as exactly one of these types:

- invoice
- contract
- sop
- hr_form
- purchase_request
- policy
- business_report
- support_ticket
- digital_form
- memo
- unknown

Classification guidelines:

- invoice:
  A request for payment containing information such as invoice numbers,
  suppliers, totals, taxes, payment terms, or due dates.

- contract:
  A formal agreement between two or more parties that defines obligations,
  terms, rights, dates, or conditions.

- sop:
  A standard operating procedure describing repeatable steps or processes.

- hr_form:
  A human-resources document involving employees, employment records,
  leave, onboarding, evaluations, or related personnel information.

- purchase_request:
  A request to purchase goods, equipment, services, or supplies.

- policy:
  A document defining organizational rules, requirements, standards,
  or governance.

- business_report:
  A document presenting business results, metrics, findings, analysis,
  or performance information.

- support_ticket:
  A request describing a customer, user, technical, or service issue.

- digital_form:
  A general structured form containing fields intended to collect data.

- memo:
  An internal announcement, notice, memorandum, or organizational message.

- unknown:
  Use this when the document does not clearly match any supported type.

Do not invent information that is not present in the document.

The confidence value must be between 0.0 and 1.0.
"""


INVOICE_EXTRACTION_PROMPT = """
You extract structured business information from invoices for DocuFlow.

Extract only information that is explicitly present in the document.

Rules:

- Do not invent missing values.
- If a value is not present or cannot be determined reliably, return null.
- Do not calculate values that are not explicitly shown.
- Preserve the invoice number exactly as written.
- Normalize dates to ISO format when a valid date is present.
- Use the currency code when identifiable, such as PHP, USD, EUR, or GBP.
- Extract monetary values as numeric values without currency symbols or
  thousands separators.

Extract these fields:

- invoice_number
- supplier
- invoice_date
- due_date
- currency
- subtotal
- tax
- total_amount
"""
