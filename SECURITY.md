# Security Policy

## Public Repository Boundary

This repository must never contain:

- broker or exchange API keys,
- Telegram API hashes or session files,
- account identifiers or balances tied to a person,
- `.env` files,
- live order responses,
- private paper/live databases,
- raw provider messages that cannot be redistributed, or
- proprietary strategy parameters intended for a private commercial plugin.

The tracked package contains research, portfolio construction, broker-neutral
order planning, dry-run evidence, and sanitized demonstrations only.

## Credential Handling

Broker plugins must load credentials from an operating-system credential store
or an injected secret manager. Credentials must not be accepted as command-line
arguments, written to reports, or committed to source control.

## Reporting A Vulnerability

Do not open a public issue containing secrets or account details. Contact the
repository owner privately with a minimal reproduction and redact all
credentials and personal trading data.
