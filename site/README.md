# Wiki Site

This directory contains the Quartz configuration and helper scripts for publishing the Markdown vault as a static wiki.

## Local Preview

```bash
npm run wiki:dev
```

The preview server runs at `http://localhost:8080` by default.

## Static Build

```bash
npm run wiki:build
```

The generated site is written to `.quartz-work/quartz/public`.

## Quartz Override

`site/quartz.template` is copied to `.quartz-work/quartz/quartz.ts` during build.
It is kept without a `.ts` extension because its imports are valid only after the file is copied into the Quartz working directory.

## Publishing Scope

The build scripts copy only public-safe folders into Quartz's temporary `content` directory:

- `00-home`
- `01-core`
- `02-practical-backend`
- `03-case-studies`
- `04-interview`
- `05-ai-workflows`
- `_assets`

The private note area, templates, IDE files, and agent instructions are intentionally excluded.
