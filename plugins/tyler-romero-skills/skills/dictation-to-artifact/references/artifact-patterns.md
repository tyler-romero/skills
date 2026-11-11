# Artifact patterns

Use these as compact starting points, not required templates. Omit irrelevant sections and prefer natural prose when headings add no value.

| Artifact | Possible structure | Important caution |
| --- | --- | --- |
| Reusable prompt | Objective, context, inputs, requirements, constraints, success criteria, output format | Use plain prose for a simple prompt; add placeholders only for reuse. |
| Report or brief | Takeaway, context, findings, decisions or recommendations, risks, open questions, next steps | Do not manufacture findings or recommendations to fill sections. |
| Plan | Outcome, projects, tasks, pending decisions, blockers, questions | Keep stated actions separate from suggested actions. |
| Meeting notes | Summary, decisions, action items, discussion, open questions | Do not invent attendees, owners, dates, or agreement. |
| Message or email | Audience-appropriate opening, purpose, necessary context, requested action, close | Preserve the intended relationship, directness, and certainty. |
| Product requirement or issue | Problem, context, requirements, non-goals, acceptance criteria, open questions | Do not invent repository facts, root causes, APIs, or implementation details. |

## Structured output

For JSON, YAML, CSV, XML, or another explicit schema:

- Follow the schema exactly.
- Use `null`, an empty collection, `TBD`, or an uncertainty field rather than fabricated values.
- Keep each field traceable to the dictation.
- Return only the payload when strict parsing is required.

## Information that does not fit

When the requested structure cannot represent meaningful source content without loss, use a small `Notes`, `Assumptions`, `Open questions`, or appendix section. Do not force content into the wrong category or drop it silently.
