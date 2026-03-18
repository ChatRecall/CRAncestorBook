# START HERE

## Basic Setup

1. Prepare your source material as plain text files.

2. Copy the example configuration:

```bash
cp project.toml.example project.toml
````

3. Edit `project.toml`:

   * set the subject's name and dates
   * set your working directory (`work_dir`)
   * set your source directories
   * list the source files you want included

4. Copy the environment file template:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys for the AI provider you plan to use.

---

## Run the Initial Setup

```bash
uv sync
uv run python CRAncestorBook/main_build_environment.py
uv run python CRAncestorBook/main_build_toc.py
```

This will:

* create the project workspace
* copy/sync your source files
* generate a proposed table of contents

---

## Review and Update the TOC

After running `CRAncestorBook/main_build_toc.py`:

1. Locate the generated TOC output (typically written to your workspace)
2. Copy the `[chapters]` section into your `project.toml`
3. Review and edit chapter titles, time ranges, and examples as needed

---

## Build Chapters and Book

```bash
uv run python CRAncestorBook/main_build_chapters.py
uv run python CRAncestorBook/main_build_book.py
```

This will:

* generate and refine chapter drafts
* assemble the final manuscript
* produce output files (e.g. Markdown, EPUB)

---

## Notes

* You do not need perfect source material to begin.
* Start simple: a few transcripts or notes are enough.
* You can iterate and improve the book over multiple runs.

```


