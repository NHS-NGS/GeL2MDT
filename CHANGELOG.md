## [0.6.1]- 2019-02-26
### Added
- Preferred transcript selection
- Case comments
- 1st and 2nd check assignment
- Additional MDT tracking features
- Option to allow for 'ADDITIONAL_APPS' to be imported in settings file. Requires `ADDITIONAL_APPS = []` to be added to `local_settings.py` 

### Changed
- Format of MDT export

## [0.6.0]- 2018-11-22
### Added
- GTAB template export
- Docker support
- Further customisation for cancer cases
- Cases are now flagged if they are blocked in the CIPAPI

### Changed
- GEL2MDT backend now relies on GeLReportModels
- SQL instead of ORM for querying whether a model existing in the database
- GMC information now obtained from JSON

## [0.5.5]- 2018-10-25
### Added
- Case alert feature
- Case code flag

### Changed
- Made cancer tweaks to proband page
- Proband page now shows related GELIRs

## [0.5.4]- 2018-10-03
### Added
- Cancer germline selection

### Changes
- Improved MDT selection page

## [0.5.3]- 2018-09-14
### Added 
- Added binning to case updates

### Changed
- UI improvements
- Nicer display during update process
- Patched security flaws

## [0.5.2]- 2018-09-03
### Added 
- Report history feature

### Changed
- Fixed cancer MDT page bug

## [0.5.1]- 2018-07-26
### Changed 
- Updated reporting templates

## [0.5.0]- 2018-07-11
### Added
- PVFlag feature to describe variant flags

### Changed
- Labkey speed up
- Removed T0 feature
- speed improvements to updates

## [0.4.6]- 2018-06-18
### Changed
- Fixed minor bug where export buttons removed pagination

## [0.4.5]- 2018-06-18
### Added
- History tab to cases which shows history of changes to cases, ordered by oldest to newest

### Changed
- Fixed bug in the cancer proband MDT view which prevented saving working
- Added email alert for ListUpdate's
- Fixed ordering in main table for raredisease cases
- Added more info to the MDT export file

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
