# Email-Attachment-Remover

## Documentation
* [ ] update README.md

## Scripting
* [ ] improve error handling
* [ ] splitup functions better
* [x] handle flags ("\Answered \Flagged \Draft \Deleted \Seen \Forwarded")
      properly (see https://stackoverflow.com/a/28748807)
* [x] configuration options: add default values
* [x] add folder, mail and attachment count

## Features & Functions
* [ ] export: check for file duplicates and handle dupes nicely
* [ ] add mode to scan folder structure and report folder sizes sorted by size
* [ ] handle commandline arguments
* [ ] add prompts for username/password
* [x] ignore eml attachments
* [x] add mail size limit (additionally to attachment limit)
* [x] limit removal on older e-mail (e.g. older than 365d)
