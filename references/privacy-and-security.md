# Privacy and security boundaries

- Keep login material in OS keychain, protected credential files, or approved secret references. This repository accepts no credential values or private IDs.
- Never commit phone numbers, email addresses, names, child/school identifiers, school product brand names that identify a specific deployment, bot display names or agent ids tied to a household, exact personal schedules, addresses, booking references, customer/account IDs, device codes, tokens, cookies, local database contents, source photos, or face embeddings.
- Do not copy raw automation exports. They often contain live recipients, personal schedules, private paths, and authorization policy.
- Use placeholder keys such as `PRIVATE_TIMEZONE`, `PRIVATE_RECIPIENT_PRIMARY`, `PRIVATE_ARCHIVE_ROOT`, and `SECRET_REF_SCHOOL_LOGIN` only in local configuration. Do not populate them in tracked files.
- Keep family media and identity models on the authorized local device. Never send private media to cloud vision/classification services unless the data owner explicitly approves that destination.
- Prefer API and local tools when sufficient; open a browser only when required. Do not paste session cookies or auth headers into docs.
- Before publishing, scan the entire staged tree and inspect the staged diff. Review Git history as well as the current tree; deleting a secret in a later commit does not remove it from history.
- Default repository visibility to private. Public release requires separate review of the complete repository and history.
- Redaction validators are guardrails only. Manual review of every staged file remains mandatory.
