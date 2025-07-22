#!/bin/bash

# Get all changes in the events directory
changes=$(git status --porcelain | grep events/)

# Count added events (directories that are new)
added_events=$(echo "$changes" | grep "^A" | sed 's|^A.*events/||' | cut -d'/' -f1 | sort -u | wc -l)

# Count modified events (directories with modified files)
changed_events=$(echo "$changes" | grep "^M" | sed 's|^M.*events/||' | cut -d'/' -f1 | sort -u | wc -l)

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