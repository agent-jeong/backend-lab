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

## Comments And Reactions

Comments and reactions are prepared through Quartz's Giscus comments plugin.
The plugin is injected during build with the configured Giscus repository values.

To enable it:

1. Make sure the GitHub repository is public.
2. Enable GitHub Discussions for the repository.
3. Install the giscus GitHub app for the repository.
4. Open `https://giscus.app/` and select the repository and discussion category.
5. Run the build.

Default values are already configured:

- `repo`: `agent-jeong/backend-lab`
- `repoId`: `R_kgDOSn8Rqg`
- `category`: `Announcements`
- `categoryId`: `DIC_kwDOSn8Rqs4C-UvH`
- `mapping`: `pathname`
- `reactionsEnabled`: `true`
- `lang`: `ko`

Optional overrides:

- `GISCUS_REPO`
- `GISCUS_REPO_ID`
- `GISCUS_CATEGORY`
- `GISCUS_CATEGORY_ID`
- `GISCUS_LANG`
- `ENABLE_GISCUS_COMMENTS=false`

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
