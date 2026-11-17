# Sample knowledge base (upload demo)

This document is a **500-word-style corpus slice** for trying upload and question
answering in rag-api-demo. It describes a fictional internal product called
**LedgerLite** so you can test retrieval without mixing facts from the main
project files.

## Product overview

LedgerLite is a small-business expense tracker. Teams record receipts, assign
categories, and export monthly summaries for accounting. The mobile app captures
photos; the web dashboard shows burn rate and pending approvals. LedgerLite targets
companies with five to fifty employees in the EU market.

The product launched in March 2024. The current release is version 2.3. Support
hours are Monday through Friday, 09:00 to 17:00 Eastern European Time, excluding
public holidays in Estonia.

## Pricing and plans

**Starter** costs nine euros per user per month. It includes five hundred receipt
scans, two export formats (CSV and PDF), and email support with a forty-eight hour
response target.

**Growth** costs nineteen euros per user per month. It adds unlimited scans,
approval workflows, Slack notifications, and API access with a rate limit of one
thousand requests per day.

**Enterprise** is price on request. It adds single sign-on, dedicated onboarding,
custom data retention rules, and a ninety-nine point nine percent uptime SLA in the
contract.

All plans include encryption at rest and in transit. Trial length is fourteen days;
no credit card is required to start a trial.

## Data and security

Customer data is stored in the `eu-central` region. Backups run every six hours with
thirty-day retention. Administrators can request a full data export within thirty
calendar days under GDPR.

Roles are **viewer**, **submitter**, **approver**, and **admin**. Only admins may
change billing or delete the organization. Audit logs retain field-level changes for
twelve months on Growth and Enterprise.

## Integrations

LedgerLite connects to QuickBooks Online and Xero for one-way export of approved
expenses. The Zapier connector triggers when a report is approved or rejected.
Webhooks deliver JSON payloads signed with HMAC-SHA256 using a secret shown once in
the admin console.

The public REST API version is **v1**. Authentication uses bearer tokens scoped to
read, write, or admin. Deprecated endpoints are announced ninety days before removal
in the changelog.

## Limits and fair use

Starter organizations may create up to three custom categories. Growth allows fifty.
File attachments per receipt must stay under ten megabytes. Bulk import accepts CSV
with at most ten thousand rows per job.

If daily API usage exceeds the plan limit, the API returns HTTP 429 with a
`Retry-After` header. Clients should backoff exponentially starting at two seconds.

## Support contacts

General support: **support@ledgerlite.example**. Security reports:
**security@ledgerlite.example** (PGP fingerprint published on the status page).
Status incidents are posted at **status.ledgerlite.example**.

## Sample facts for demo questions

- Product name: **LedgerLite**
- Cheapest paid plan: **Starter** (nine EUR per user per month)
- Trial length: **fourteen days**
- Primary region: **eu-central**
- API version: **v1**
- Enterprise SLA uptime: **99.9%**

Try questions like “What does Growth cost?” or “How long is the trial?” once this
file is in the index (upload via `/v1/upload` or copy into `data/raw/` and ingest).