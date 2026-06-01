# AGENTS.md

## Repository Purpose

This repository is an Obsidian + GitHub based backend engineering playbook.

It is used to organize long-term practical knowledge about Java, Spring, JPA, Database, Redis, Network, OS, Performance, Transaction, Concurrency, Idempotency, Batch, Security, Architecture, Observability, CI/CD, Testing, and AI workflows for backend engineers.

The normal workflow is:

- Pick one topic from [[mastery-map]].
- Improve one or a few related Markdown documents.
- Keep the knowledge public-safe, practical, and reusable.

This repository may later become public, so every committed document must be safe to share.

## Writing Principles

- Write in Markdown.
- Keep explanations concise, practical, and connected to backend engineering work.
- Prefer clear definitions, operating principles, trade-offs, failure modes, and practical examples.
- Explain both advantages and limitations.
- Generalize examples so they do not expose company-specific details.
- Do not create large batches of detailed documents at once.
- Do not reorganize the repository unless the user explicitly asks for it.
- Preserve the existing structure and style when they are clear.
- AI-generated content must be treated as a draft and checked for correctness.

## File And Folder Naming

- Use `kebab-case` for file and folder names.
- Use `.md` for documents.
- Keep topic index files close to their existing folders, for example:
  - `01-core/java/java.md`
  - `02-practical-backend/performance/performance.md`
- Do not rename existing files or folders unless there is a clear reason.
- Avoid spaces, uppercase naming, and mixed naming styles in new paths.
- Keep `_private` separate from public notes.

## Obsidian Link Rules

- Use Obsidian internal links in the `[[document-name]]` format.
- Link to the note name, not the full path, unless a path is required to disambiguate.
- Prefer stable topic notes such as [[java]], [[spring]], [[jpa]], [[database]], [[performance]], [[transaction]], [[concurrency]], and [[idempotency]].
- Add related links only when they help navigation.
- Do not create placeholder links in bulk.

## Security And Private Information

Never write or commit:

- Company-internal information.
- Internal system names.
- Real table names.
- Real API URLs.
- Raw production logs.
- Account names, user identifiers, emails, or customer data.
- Tokens, keys, credentials, certificates, or secrets.
- Private incident details that could identify an organization, product, or user.

Use generalized names instead, such as:

- `order`
- `payment`
- `user`
- `example-service`
- `https://api.example.com`

The `_private` directory is a local-only personal note area and is ignored by Git. Do not mix `_private` content into public documents without anonymizing and generalizing it first.

## Documentation Edit Priorities

When modifying documents, prioritize in this order:

1. Fix incorrect or misleading technical content.
2. Remove or generalize sensitive information.
3. Improve clarity and structure.
4. Connect concepts to practical backend scenarios.
5. Add trade-offs, limitations, and failure cases.
6. Add Obsidian links to relevant existing notes.
7. Add examples only when they improve understanding.

Prefer improving an existing document over creating a new one.

## New Document Criteria

Create a new document only when:

- The topic does not fit well in an existing note.
- The content would make an existing note too broad or hard to scan.
- The topic is likely to be referenced independently from [[mastery-map]] or another index.
- The user explicitly asks for a new document.

Do not create many new topic files in a single pass. Start with one focused document and link it from the most relevant existing note if useful.

## Template Usage

Use `_templates/concept-template.md` for concept notes.

Use `_templates/case-study-template.md` only for public-safe, generalized case studies. Any real project detail must be anonymized before it appears in a public document.

Use `_templates/interview-answer-template.md` for interview-oriented answers.

Use `_templates/daily-note-template.md` for daily learning notes when the user asks for daily tracking.

Templates are starting points. Remove empty sections when they do not help the note.

## Commit Message Rules

Use short, descriptive commit messages.

Preferred format:

```text
docs: update transaction notes
docs: add redis cache-aside summary
docs: refine mastery map links
```

Guidelines:

- Use `docs:` for normal wiki changes.
- Use imperative or concise noun-style wording.
- Keep the subject line focused on the changed topic.
- Do not mention private company names, internal systems, issue IDs, or sensitive context.

## Required Codex Report After Work

After modifying this repository, Codex must report:

- Files changed.
- Summary of the intent of each change.
- Whether any sensitive or private information was added, removed, or intentionally avoided.
- Verification performed, such as `git status` or document review.
- Any follow-up suggestions, only when they are directly useful.

Codex must not create commits unless the user explicitly asks for a commit.
