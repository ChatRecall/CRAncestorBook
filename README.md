# CRAncestorBook

![Status](https://img.shields.io/badge/status-beta-orange)
![Python](https://img.shields.io/badge/python-3.x-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Type](https://img.shields.io/badge/type-application-lightgrey)

AI-assisted program for turning interviews, transcripts, and research material into a structured long-form biography.

## Start Here

If you want to preserve a family story but don’t know where to start, begin here:

- [Interview questions](./guide/interview/README.md)
- [Sample biography](./guide/sample_biography/README.md)
- [Getting started guide](./guide/START_HERE.md)

You do not need perfect materials to begin. A phone recording, a few documents,
and the right questions are enough to get started.

## Highlights

- Turns source text into a structured biography workflow
- Builds a table of contents, drafts chapters, and assembles a book
- Includes interview questions and a sample biography to help people start

## Why This Exists

A lot of family history is lost because people mean to record it later and never do.

This project was built to help turn recorded memories, transcripts, letters, and research notes into a readable biography. Instead of facing a blank page, the workflow helps organize the material, propose a structure, draft chapters, and assemble a book.

## Overview

CRAncestorBook is an AI-assisted program for building biographies from family history material.

The program takes source text files such as interview transcripts, letters, notes, and research documents, then processes them through a multi-stage pipeline. Instead of relying on one large prompt, it breaks the work into separate stages: environment setup, table of contents generation, chapter drafting, revision passes, and final book assembly.

The result is a more structured workflow for producing a biography from source material that would otherwise be difficult to organize and draft by hand.

## Current Status

CRAncestorBook is currently **beta** and actively evolving.

It is used for real book-building work and has already been used to produce a full family biography. However, it is still a personal-use project shared publicly as-is. It assumes a technical user who is comfortable running Python CLI programs, preparing text-based inputs, and reviewing generated outputs.

This is not a polished consumer application, and it should not be treated like one.

## Requirements

- Python 3.x
- Linux or another environment suitable for running Python CLI tools
- [uv](https://github.com/astral-sh/uv)
- Source material already converted to **plain text files**
- AI provider configuration supported by the linked libraries
- Pandoc for EPUB generation if you want final ebook output

## Installation

Requires [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

## Run

### CLI

This program currently uses four CLI entry points.

#### 1. Build the project environment

```bash
uv run python CRAncestorBook/main_build_environment.py
```

#### 2. Build the table of contents

```bash
uv run python CRAncestorBook/main_build_toc.py
```

#### 3. Build and refine chapters

```bash
uv run python CRAncestorBook/main_build_chapters.py
```

#### 4. Assemble the final book

```bash
uv run python CRAncestorBook/main_build_book.py
```

## What Happens When You Run It

When you run the workflow, the program:

* reads your project configuration
* prepares a workspace for the book
* synchronizes source files into the expected structure
* generates a proposed table of contents
* drafts and refines chapters through multiple pipeline phases
* assembles a final manuscript and export-ready book files

This is a batch-style CLI workflow, not an interactive GUI. You run each stage in order and review the outputs as you go.

## Basic Workflow

1. Prepare source material as plain text files
2. Create a project configuration describing the sources and book workspace
3. Run the environment setup step
4. Generate a table of contents
5. Run the chapter pipeline to draft and refine chapter text
6. Build the final manuscript and export files

## Inputs

* Interview transcripts
* Oral history transcripts
* Letters
* Research notes
* Archival text documents
* Other biography-related source material already converted to plain text
* Project configuration file (`project.toml`)

## Outputs

* Structured project workspace
* Proposed table of contents
* Draft chapter files
* Refined chapter files after pipeline passes
* Combined manuscript (`book.md`)
* Export-ready metadata files
* Final book outputs such as EPUB and PDF, depending on your local toolchain

## High-Level Workflow

```text
Sources
   ↓
Environment Setup
   ↓
Table of Contents Generation
   ↓
Draft Chapters
   ↓
Coverage Audit
   ↓
Duplicate Resolution
   ↓
Narrative Style Polish
   ↓
Episode Enrichment
   ↓
Paragraph Polish
   ↓
Final Book Assembly
```

## Workflow Stages

### 1. Environment Setup

Entry point: `CRAncestorBook/main_build_environment.py`

Purpose:

* load project configuration
* prepare workspace directories
* synchronize source files
* set up the project structure for the remaining stages

### 2. Table of Contents

Entry point: `CRAncestorBook/main_build_toc.py`

Purpose:

* generate or refine the table of contents for the book
* establish chapter structure before drafting begins

### 3. Chapter Pipeline

Entry point: `CRAncestorBook/main_build_chapters.py`

Purpose:

* generate initial chapter drafts
* improve factual coverage
* detect overlap across chapters
* refine voice and flow
* enrich selected narrative episodes from source material
* improve paragraph structure

Pipeline phases:

* `draft`
* `coverage`
* `dedup`
* `style`
* `enrichment`
* `paragraph`

### 4. Book Build

Entry point: `CRAncestorBook/main_build_book.py`

Purpose:

* combine chapters into a complete manuscript
* insert front matter or additional sections
* generate final metadata
* build export-ready book files such as EPUB and PDF


## Project Structure

```text
CRAncestorBook/

README.md
project.toml.example
guide/                  Public-facing guides, interview material, sample output, prompts
CRAncestorBook/         Main application code
```

## Configuration

The workflow is driven by a project configuration file, typically:

```text
project.toml
```

A starter configuration file is included in the repository as:

```text
project.toml.example
```

Copy it, rename it to project.toml, and then edit the paths, subject
information, and source lists for your own project.

This configuration defines things such as:

* source directories
* workspace location
* book metadata
* project-specific settings used during the workflow

You will also need environment variables for your AI provider.

A template file is included:

```text
.env.example
```
Copy it to `.env` and add your API keys.

## Supporting Libraries

This program uses lightweight supporting libraries developed separately:

| Library                   | Purpose                                                                    |
| ------------------------- | -------------------------------------------------------------------------- |
| [WrapAI](https://github.com/WrapTools/WrapAI)       | Prompt handling and AI provider interaction                                |
| [WrapEmbed](https://github.com/WrapTools/WrapEmbed) | Retrieval and embedding utilities used during evidence-grounded processing |
| [WrapEmit](https://github.com/WrapTools/WrapEmit)   | Runtime status, progress, and logging support                              |

CRAncestorBook intentionally keeps these pieces separate rather than bundling everything into a single framework.

## Sample Biography

A sample biography generated through this workflow is included in
[`guide/sample_biography/`](./guide/sample_biography/).

It shows the kind of long-form output this project can produce from archival
source material. This sample is based on a real family biography project that
inspired the development of CRAncestorBook.

The software and prompts are open source, but the sample biography content
itself is shared only as a demonstration and is not open source for reuse.

## Interview Questions

The repository includes a structured interview guide under [`guide/interview/`](./guide/interview/).

The interview material matters because many people do not get stuck on the
writing first. They get stuck earlier on what to ask, what to record, and how
to begin.

A phone recording and a good set of questions are often enough to start
building usable source material.

## Prompts

The repository includes the prompts used by the workflow under
[`guide/prompts/`](./guide/prompts/), so others can inspect, reproduce, or adapt
the process.

The goal is transparency. This project is not based on a hidden “magic
prompt.” It is a staged workflow built from many smaller prompts and processing
steps.

## Limitations
* Source ingestion is **not included** in this repository; files are expected to already be converted to text
* This is a CLI workflow for technical users, not a polished point-and-click application
* Output quality depends heavily on the quality, coverage, and clarity of the source material
* AI costs can add up during full runs, especially for longer books or repeated pipeline passes  
  (a full book run can cost ~$20–$30 depending on model and size)
* Human review and editing are still needed for the best final result

## Intended Audience
This is an end-user program built primarily for personal workflows and shared publicly because it may help others preserve family history.
It is best suited for technically inclined users who want to run the pipeline themselves, or for people who want to study the workflow, prompts, and example outputs before deciding whether to adapt it.

## Acknowledgements
This project would not have been possible without the team at **Venice.ai**.
Special thanks to **Erik Voorhees** for support shown to early adopters of the platform, which made large-scale inference for projects like this more practical.

## License
MIT — see [LICENSE](./LICENSE).

## Attribution
If you reuse or adapt this project, please keep the original copyright and
license notice as required by the MIT License.

A visible credit back to ChatRecall or the original repository is appreciated,
though not required.