---
name: Exception request
about: Request an exception to project rules (e.g., `sqlite3.connect` outside storage)
title: '[exception] '
labels: ['exception-request']
assignees: []
---

## Summary

Explain the exception you are requesting and the files affected.

## Motivation

Why is an exception necessary? Why can't the storage layer or existing APIs be used?

## Scope

- Files impacted:
- Intended lifetime (temporary demo / long-term change):

## Mitigations

List any steps you will take to reduce risk (explicit close(), temp directories, test-only flags, limited scope).

## Reviewer checklist
- [ ] Justification provided
- [ ] Mitigations described
- [ ] Tests or manual validation steps included (if applicable)

Once ready, maintainers will review and respond.
