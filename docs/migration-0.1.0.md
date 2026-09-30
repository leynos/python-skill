# Migration to 0.1.0

This note signposts the catalogue changes for the next minor release. The
catalogue is not published as a package; `pyproject.toml` still reports
`0.0.0`, and this document exists to guide a repository that refreshes its copy
of `skills/`.

## New skill: `skylos`

A dedicated [`skylos`](../skills/skylos/SKILL.md) skill now covers Skylos
dead-code management: `SKY-U001` triage, implicit runtime callers, Protocol and
callback false positives, precise entrypoint configuration, merge and rename
drift in a Skylos gate, and the documentation-liveness ceilings that can rescue
or expose a finding. See
[users-guide.md#when-to-reach-for-the-skylos-skill](users-guide.md#when-to-reach-for-the-skylos-skill).

## Routing changes

`python-router` and its
[routing matrix](../skills/python-router/references/routing-matrix.md) now send
Skylos findings, entrypoint rules, and Skylos gate repair to `skylos`. Choosing
a dead-code scanner, clone and complexity scans, and profiling stay with
`python-quality-tools`, which now points to `skylos` for Skylos-specific work
rather than covering it directly.

## Explicit invocation

Every catalogued skill except `python-router`, which carries no
`agents/openai.yaml`, sets `allow_implicit_invocation: false`; `skylos` follows
that same policy. It loads only when named explicitly or when the router
directs a task to it; adding the skill to a checkout does not change any
existing session's behaviour on its own.

## What the skill does not do

Loading `skylos` does not install Skylos, change a repository's pinned Skylos
version, alter scan roots, confidence thresholds, or CI gate policy, or add a
dependency. A consuming repository keeps its own pin and configuration; the
skill works within them.

## Required action

None for an existing catalogue user beyond reinstalling or refreshing the
catalogue, as described in
[users-guide.md#installation](users-guide.md#installation). A repository that
previously relied on `python-quality-tools` for Skylos triage should load
`skylos` instead.
