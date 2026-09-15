---
# badgersbay-lnz3
title: 'badgersbay: dashboard authentication through AWS Cognito'
status: todo
type: epic
priority: low
tags:
    - badgersbay
    - auth
    - aws
    - iso27001
created_at: 2026-09-15T21:17:18Z
updated_at: 2026-09-15T21:17:18Z
---

Replace the shared-password authentication on the badgersbay dashboard with AWS
Cognito, so dashboard actions can be attributed to a person.

One user with a shared password is fine for now. This epic becomes relevant once
more than one person uses the dashboard, or once the audit trail of dashboard
actions has to hold up.

## Trigger

`register-administration` adds a write path: an operator marks an asset as
accounted for in a round, with a reason. That record carries `marked_by`, but
the dashboard has a single shared password - so the field is self-reported and
labelled as such in the UI.

For ISO that is the weak point: a deviation approved by "somebody who knew the
password". With Cognito it becomes a person.

## Scope

1. Cognito user pool, hosted UI or own redirect
2. OIDC flow in badgersbay: login, callback, session cookie, logout
3. `marked_by` from the token rather than an input field; the "self-reported"
   label goes away
4. Existing bearer tokens for report submission stay as they are - clients are
   machines, not people, and do not belong in a browser flow
5. `/health` stays unauthenticated
6. Roles: who may mark exceptions versus who may only read

## Considerations

- Badgersbay runs on stdlib plus PyYAML. An OIDC flow means token validation,
  fetching and caching JWKS, and session management. That is the heaviest
  dependency the project would take on - heavier than the PostgreSQL step in
  badgersbay-8ylz.
- An alternative worth weighing before building this: a reverse proxy that
  handles authentication and passes the identity as a header. Badgersbay then
  stays dumb and needs no OIDC implementation. Given the project's design line
  ("deploy = copy one file"), that route deserves serious consideration over a
  built-in client.
- Touches the NixOS module in elastinix: new options, and the password file can
  go.

## Dependencies

- `register-administration` provides the write path whose attribution this
  corrects
- elastinix `service-badgersbay.nix` has to follow
