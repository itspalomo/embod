---
name: embod-validate
description: Validate an Embod project file with the CLI and summarize issues, exports, and snapshots. Use after editing embod_project.py or when debugging invalid geometry, printability warnings, or robot graph issues.
argument-hint: [path-to-embod_project.py]
disable-model-invocation: true
---

Validate the target Embod project.

If no path is provided, ask for the project file path.

Run this loop:

1. `embod inspect $ARGUMENTS --json`
2. `embod validate $ARGUMENTS --json`
3. `embod build $ARGUMENTS --json`
4. If the project has a robot, run `embod simulate $ARGUMENTS --smoke`
5. If the user asked for visual confirmation, run `embod snapshot ... --json`

When reporting results:

- separate hard errors from warnings
- call out missing measurements or assumptions when they caused the problem
- mention which artifact paths were created
- suggest the smallest next edit that would unblock progress
