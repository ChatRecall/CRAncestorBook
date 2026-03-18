# CHANGELOG

## [0.6.14] - 2026/03/15
- minor changes resulting in version 15_2 of book

## [0.6.13] - 2026/03/11
- production ready test version (excluding a potential qa step at end)

## [0.6.12] - 2026/03/11
- renamed pipeline_runtime to chapter_pipeline_runtime
- updated the readme for updated structure

## [0.6.11] - 2026/03/11
- Embedding and enrichment done
- Update README.md for program structure and flow

## [0.6.10] - 2026/03/10
- Full working draft of enrichment phase complete, before breaking up code into modules to complete phase

## [0.6.9] - 2026/03/10
- Implemented episode_retrieval_review

## [0.6.8] - 2026/03/10
- Embedding implemented

## [0.6.7] - 2026/03/09
- Continued Phase Enrichment step complete and starting new prompt for next steps.  This is through:
  - episode decompose
  - episode eligibility
  - episode index

## [0.6.6] - 2026/03/09
- Initial Phase Enrichment step started but needs retuning

## [0.6.5] - 2026/03/09
- Table of contents implemented

## [0.6.4] - 2026/03/07
- Tested TOC before adding --auto-approve flag for development

## [0.6.3] - 2026/03/07
- initial untested toc code and related file updates (to back up for night)

## [0.6.2] - 2026/03/07
- Misc pipe_config organization and notes

## [0.6.1] - 2026/02/18
- Full file reorg and testing

## [0.7.0] - 2026/02/17
- Reorg in main branch

## [0.6.0] - 2026/02/17
- Ready for next branch to reorganize

## [0.5.6] - 2026/02/11
- Final completeness tests
- Implementing streaming from WrapAI

## [0.5.5] - 2026/02/10
- Post Milestone 5 and all steps/phases and files updated to eliminate numbers except toml starting numbers referenced in pipeline_plan

## [0.5.4] - 2026/02/10
- Post renaming Milestone 4 prior to Milestone 5

## [0.5.3] - 2026/02/09
- Minor updates to eliminate remaining hard paths and updating with some better path_patterns
- Draft prior to eliminating numbers.  constants updated to hold both in transition path

## [0.5.2] - 2026/02/09
- refactor: normalize path handling via stems + path_patterns

## [0.5.1] - 2026/02/08
- Initial step update adding step_validation, path_patterns and updating constants by substep
- Updated by number with CODE in each step and centralizing file names to CODE

## [0.5.0] - 2026/02/06
- Merge into master and ready for new branch

## [0.4.9] - 2026/02/06
- final branch commit before merge
- remove pipeline_layout_FUTURE
- add .env.example

## [0.4.8] - 2026/02/05
- massive changes...
- Inserted new step 5 demoting ending 5 to 6 to polish chapters for readability
- Updated for env builder from shared location

## [0.4.7] - 2026/02/05
- implemented 402 stop in runner with try in main run script
- Wrote and initial tests of book_builder_3

## [0.4.6] - 2026/02/04
- eliminated dry run from toml and steps
- added env_prep and eliminated ensure_output_dirs_for_step
- put in guardrail so input toml must match toml working directory

## [0.4.5] - 2026/02/04
- updated runner to eliminate debug statements like FILES
- Added step 5 paragraph polish

## [0.4.4] - 2026/02/02
- baseline before unifying steps with a standard run_plan orchestrator.

## [0.4.3] - 2026/02/02
- proof of work completed and code works for steps 2-4 in new directory structure.

## [0.4.2] - 2026/02/02
- moved constants to a separate module to make updates easier

## [0.4.1] - 2026/02/02
- First working with 3rd party narratives and new by chapter directory structures

## [0.4.0] - 2026/02/01
- 3rd party refactor branch

## [0.3.1] - 2026/02/01
- Final commit before migrating to 3rd party voice and streamlined code

## [0.3.0] - 2026/01/31
- Merge into master and ready for new branch

## [0.2.9] - 2026/01/31
- Rough template of pipeline layout
- Final commit before merge to master for code restructure and start of new branch
- second commit to update .gitignore

## [0.2.8] - 2026/01/31
- Initial of steps 1-4 with book builder

## [0.2.7] - 2026/01/30
- Initial drafts for step 2 - step 4

## [0.2.6] - 2026/01/30
- Implement duplicate detection

## [0.2.5] - 2026/01/28
- Initial draft of Step 2 to write Initial Drafts of Chapters

## [0.2.4] - 2026/01/28
- Updated code to use WrapEmit and not the print statements in runner or step3

## [0.2.3] - 2026/01/28
- converted to using WrapAI

## [0.2.2] - 2026/01/28
- added book_context.py and removed book_structure.py to use toml consistently

## [0.2.1] - 2026/01/28
- TOML implementation

## [0.2.0] - 2026/01/28
- initial before code structure

## [0.1.4] - 2026/01/22
- step3 complete

## [0.1.3] - 2026/01/22
- restructure for prompts and steps

## [0.1.2] - 2026/01/21
- implemented retry logic

## [0.1.1] - 2026/01/20
- book_structure.py added to break out chapters and lower and upper ranges of chapters
- miscellaneous linter fixes

## [0.1.0] - 2026/01/19
- Initial working copy
