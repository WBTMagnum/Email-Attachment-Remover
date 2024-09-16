# Usage

- Use Python 3
- Adjust config.ini sample, rename to config.ini
	- Set IMAP mailbox login configuration
	- Decide to run single folder (recursive) or all folders
	- Set operation mode ([test]|export|delete|detach)
- Run email_attachment_remover.py


# Hints

* Run it on a fast Internet connection as it has to download all mails and attachments and partly upload it again


# Ressources

## Email Parsing

## Standards & Specs
- [IMAP Protocol (RFC 2060)](https://tools.ietf.org/html/rfc2060.html)
- [IMAP Search Criteria](https://gist.github.com/martinrusev/6121028)
- [E-Mail Standard (RFC 822)](https://datatracker.ietf.org/doc/html/rfc822)

## Libraries
- [Python Library: imaplib — IMAP4 protocol client](https://docs.python.org/3.6/library/imaplib.html)
  - [Python — imaplib IMAP example with Gmail](https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/)
  - [PyMOTW: imaplib - IMAP4 client library](https://pymotw.com/2/imaplib/)
  - [PyMOTW: imaplib — IMAP4 Client Library](https://pymotw.com/3/imaplib/)
- [Python Library: email.message](https://docs.python.org/3.6/library/email.message.html)

## Code Examples
- [Python Script: download all gmail attachments](https://gist.github.com/baali/2633554)
- [Stack Overflow: Python IMAP locate emails with attachments in INBOX and move them to a folder](http://stackoverflow.com/questions/32885661/python-imap-locate-emails-with-attachments-in-inbox-and-move-them-to-a-folder)
- [Strip attachments from an email message (Python recipe)](http://code.activestate.com/recipes/302086-strip-attachments-from-an-email-message/)
- [IMAP mail server attachment handler (Python recipe)](http://code.activestate.com/recipes/498189-imap-mail-server-attachment-handler/)
- [Github: imap_detach](https://github.com/izderadicka/imap_detach/blob/master/src/imap_detach/mail_info.py)
- [Automatically Download Email Attachments Using Python. (Python3)](https://dev.to/shadow_b/download-email-attachments-using-python-3lji)
- [Python Script: imap-delete-attachments](https://github.com/caltabid/imap-delete-attachments)
- [Fetch emails before a given date](https://gist.github.com/zed/9336086)
- [pymap-copy: Copy and transfer IMAP mailboxes](https://github.com/Schluggi/pymap-copy/tree/master)
