## [0.4.4]- 24-06-08
### Added
- Added feature to generate positive reports based on selected variants which are Classed 3-5 and have been fully validated.
- Additional security to API/ajax interface to enforce authentication.
- Custom QuerySet manager for GELInterpretationReport objects to select latest incremented version by user (objects.latest_cases_by_user) or by sample_ type (objects.latest__cases_by_sample_type).
- Specification of 'artefact' for ACMG classification.
- Specification of 'In Progress' for variant validation.

### Changed
- Technical reports only count HighEvidence genes from PanelApp.

## [0.4.3]- 24-06-07
### Changed
- Bugfix for GELInterpretationReport models, solving issue where incrementing version number due to a change within GEL/CIP-API would result in erasure of important case tracking information.

## [0.4.2]- 24-05-11
### Added
- Validation outcomes and assignment to users
- Running run_batch_update from manage.py
- Priority and recruiting disease status to cancer main page
- Clinical info now present in clinical scientists view for cancer

### Changed
- Bugfix for audit panel where numbers and labels would not match up correctly.
- Removed role assignment for users

## [0.4.1] - 20-05-11
### Added
- Automated tracking of version and build stamps through {% version_number %} and {% build %} templatetags.

### Changed
- Bugfix for audit panel where numbers and labels would not match up correctly.

## [0.4.0] - 2018-05-05
### Added
- First public release of GeL2MDT!

## [0.3.3] - 2018-04-27
### Added
- gelclin: clinician app which is designed to give clinicians different views to clinical scientists
- Fields for Cancer patient history
- Written instructions and readme
- Ability to specify one sample for download to MCA
- Added ready_to_dispatch cases for cancer
- Variants in clinical report part of CIP API
- Cancer disease and subtype from CIP API
- Tumour content from CIP API
- Cancer specific version of MDT questions

### Changed
- Moved case_sent, pilot_case, case_status and mdt_status from Proband to GELInterpretationReport
- Changed the download of variants from GEL
- Improved sphinx documentation
- Removed easy-audit and added reversions audit module
- Specifying email address in config

### Removed
- Unused api urls
- Primer app

## [0.3.2] - 2018-04-13
### Added
- Start of Project Tracking
