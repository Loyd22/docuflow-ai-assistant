"""Evaluation examples for DocuFlow RAG retrieval and question answering."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RAGCase:
    """One expected document question-answering example."""

    name: str
    question: str
    expected_answer_terms: tuple[str, ...]
    expected_source_terms: tuple[str, ...]
    expected_answer_any_terms: tuple[str, ...] = ()


RAG_DOCUMENT_TEXT = """
DOCUFLOW TECHNOLOGIES INC.
EMPLOYEE HANDBOOK

Annual Leave

Employees receive 15 days of annual leave per year.
Unused annual leave may be carried forward with manager approval.
Annual leave requests should be submitted before the planned absence.
Managers are responsible for reviewing leave requests based on staffing needs.

Password Security

Employees must use passwords containing at least twelve characters.
Passwords must not be shared with coworkers or external parties.
Compromised passwords must be changed immediately.
Multi-factor authentication must be used when required by company systems.

Company Equipment

All company equipment remains the property of DocuFlow Technologies Inc.
Employees are responsible for protecting laptops, mobile devices,
accessories, and other equipment issued to them.
Lost or stolen company equipment must be reported immediately
to the employee's manager and the IT department.

Expense Reimbursement

Employees may request reimbursement for approved business expenses.
Receipts must be submitted with the reimbursement request.
Expenses above PHP 5,000 require manager approval before reimbursement.
Personal purchases are not eligible for reimbursement.

Remote Work

Employees may work remotely up to two days per week with manager approval.
Remote employees must remain available during normal working hours.
Employees working remotely must protect confidential company information
and use approved company systems when accessing internal resources.

Workplace Conduct

Employees are expected to behave professionally and respectfully.
Harassment, discrimination, threats, and abusive behavior are prohibited.
Workplace concerns should be reported through the appropriate
management or human-resources channels.

Training

Employees may be required to complete training related to security,
compliance, workplace safety, or their assigned responsibilities.
Required training must be completed before the stated deadline.
Managers are responsible for ensuring required training is completed.

Termination

Employees who resign should provide appropriate notice to their manager.
Company property must be returned before the employee's final working day.
Access to company systems may be disabled as part of the offboarding process.
Outstanding company equipment must be returned during offboarding.
"""


RAG_CASES = [
    RAGCase(
        name="annual_leave_direct",
        question="How many annual leave days do employees receive?",
        expected_answer_terms=(
            "15",
            "annual leave",
        ),
        expected_source_terms=(
            "15 days",
            "annual leave",
        ),
    ),
    RAGCase(
        name="equipment_paraphrase",
        question="What should I do if my company laptop goes missing?",
        expected_answer_terms=(
            "report",
            "immediately",
        ),
        expected_source_terms=(
            "lost or stolen",
            "reported immediately",
        ),
    ),
    RAGCase(
        name="remote_work",
        question="How many days per week can employees work remotely?",
        expected_answer_terms=(
            "two",
            "days",
        ),
        expected_source_terms=(
            "two days per week",
            "remote",
        ),
    ),
    RAGCase(
        name="expense_approval",
        question="When does an expense need manager approval?",
        expected_answer_terms=(
            "5,000",
            "manager approval",
        ),
        expected_source_terms=(
            "PHP 5,000",
            "manager approval",
        ),
    ),
    RAGCase(
        name="password_requirement",
        question="What is the minimum password length?",
        expected_answer_terms=("characters",),
        expected_source_terms=(
            "twelve characters",
            "password",
        ),
        expected_answer_any_terms=(
            "12",
            "twelve",
        ),
    ),
]
