#!/bin/bash

# Collect each changed event directory exactly once.
declare -A changed_event_dirs
while IFS= read -r -d '' entry; do
    path="${entry:3}"
    [[ "$path" == events/*/* ]] || continue
    event="${path#events/}"
    event="${event%%/*}"
    changed_event_dirs["$event"]=1
done < <(git status --porcelain=v1 -z --untracked-files=all -- events/)

added_events=0
changed_events=0
for event in "${!changed_event_dirs[@]}"; do
    if git cat-file -e "HEAD:events/$event" 2>/dev/null; then
        ((changed_events += 1))
    else
        ((added_events += 1))
    fi
done

# Handle case where no changes
if [[ $added_events -eq 0 && $changed_events -eq 0 ]]; then
    echo "No changes in events directory"
    exit 0
fi

# Build commit message
message=""
if [[ $added_events -gt 0 ]]; then
    message="${added_events} added"
fi

if [[ $changed_events -gt 0 ]]; then
    if [[ -n "$message" ]]; then
        message="${message}, ${changed_events} updated"
    else
        message="${changed_events} updated"
    fi
fi

# Add all changes and commit
git add .
git commit -m "$message"