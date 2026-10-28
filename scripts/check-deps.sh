#!/usr/bin/env sh

# Check each workspace package's imports against the dependencies its pyproject lists
status=0
for project in packages/*/ services/*/; do
    uv run --quiet deptry "${project}src" --config "${project}pyproject.toml" --no-ansi || status=1
done
exit $status