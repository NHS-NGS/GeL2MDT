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
