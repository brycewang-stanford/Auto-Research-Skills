# Contributing to Auto-Research-Skills

Thanks for helping grow the toolbox! Two ways to contribute:

## 1. Add a tool to the list

Edit [`README.md`](README.md), put the project in the most fitting category, and keep the table format:

```md
| [owner/repo](https://github.com/owner/repo) | ~⭐ | Stack | One-line description. |
```

Keep descriptions to a single sentence. Sort within a category by relevance, not stars.

## 2. Vendor a skill as a submodule

If the project is a reusable *skill* (markdown skills, agent plugins, etc.), vendor it under `skills/`:

```bash
git submodule add https://github.com/owner/repo skills/<short-name>
git commit -m "Add <short-name> skill submodule"
```

Then add a row to the **Bundled Skills** table in the README.

## Guidelines

- One project per PR keeps review easy.
- Link to the canonical repo, not a mirror.
- Star counts are approximate — no need to keep them perfectly current.
- Be kind. This is a community list.
