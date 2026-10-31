# TODO

# 0001. NetBox Data Model Over PyNetBox

- Status: Accepted
- Date: 2026-10-31

## Context

Users need log fields that the core fields do not have, for example the application of a firewall log. Several data source types can log the same value in different vendor fields: `app` in Palo Alto, or a custom field in Aria.

## Decision

- Users define an extra field once: its key, label, kind and description.
- Each data source maps one of its vendor fields to the extra field.
- The catalog and the filters name the field `extra.<key>`.
- The key cannot change, because URLs and the search history use it.

## Consequences

- A value that several data source types log gets one column and one filter.
- A key has one kind for all data sources.
- A core field that Armada adds later cannot take the name of an extra field.
- Two tables hold the fields and the mappings (see [Log search](../architecture/log-search.md), §7).
- We did not choose fields that each data source defines for itself. That option gives duplicate columns, and one key could get two kinds.
