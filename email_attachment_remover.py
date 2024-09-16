#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This script will scan the mailbox or given folder (including sub-folders)
# for e-mails with attachments larger than `max_attachment_size`.
# Larger attachment will be extracted and stored in the given path `export`.
# Afterwards the attachments are removed from the email and replaced with
# a removal message.
#

import imaplib
import email
from email.header import decode_header
from email.policy import default
import time
import configparser
import humanfriendly
import os
import datetime
import logging
import sys
from imap_tools import MailBox, AND, A, U

logging.basicConfig(stream=sys.stderr, format='%(message)s', level=logging.INFO)
logging.debug('DEBUG ACTIVATED')

# read configuration
config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
config.sections()

# set global variables from configuration or use default values
MODE = config['DEFAULT'].get('mode', 'test')

EXPORT_FOLDER_NAME = config['EXPORT'].get('export_folder', 'export')

SERVER = config['MAILSERVER'].get('server', '')
USER = config['MAILSERVER'].get('user', '')
PASSWORD = config['MAILSERVER'].get('password', '')

MAIL_FOLDER = config['MAIL'].get('mail_folder', '')
EMAIL_AGE_DAYS = int(config['MAIL'].get('email_age_days', '365'))
MAX_ATTACHMENT_SIZE = config['MAIL'].get('max_attachment_size', '256')
MAX_MAIL_SIZE = config['MAIL'].get('max_mail_size', '2048')
IGNORE_FLAGGED = config['MAIL'].get('ignore_flagged', 'true')

# check if the given export folder exists and create it if now
if not os.path.exists(EXPORT_FOLDER_NAME):
    os.makedirs(EXPORT_FOLDER_NAME, mode=0o777)
EXPORT_FOLDER_PATH = os.path.abspath(EXPORT_FOLDER_NAME)

# replacement string for removed attachments
REPLACESTRING = """
The attachment %(filename)s has been detached.
"""
REPLACESTRING_LONG = """
This message contained an attachment that was stripped out.
The original type was: %(content_type)s
The filename was: %(filename)s,
(and it had additional parameters of:
%(params)s)
"""

count_attachments = 0
count_folders = 0
count_mail = 0


def retrieve_flags():
    """
    Use imap-tools[*] to retrieve the flags for the matching messages.
    the flags will be returned in a dict of ((int)message-id, (str)flags)

    [*] for reasons unknow, imaplib refuses to return the flags.

    Args:

    Returns:
        Dict
    """

    with MailBox(SERVER).login(USER, PASSWORD) as mailbox:
        flags_dict = {}

        # determine the date and size limits
        max_date = datetime.date.today() - datetime.timedelta(days=EMAIL_AGE_DAYS)
        max_mail_size_in_bytes = humanfriendly.parse_size(MAX_MAIL_SIZE)
        max_attachment_size_in_bytes = humanfriendly.parse_size(MAX_ATTACHMENT_SIZE)

        # select given folder as current folder
        mailbox.folder.set(MAIL_FOLDER.replace('"', ''))

        # get selected folder
        current_folder = mailbox.folder.get()

        # get current and all subfolders of the specified folder (root by default)
        for folder in mailbox.folder.list('', current_folder + '*'):
            logging.debug('retrieve_flags> Scanning %s for message flags ...', folder.name)

            # switch to folder and
            # retrieve messages matching criteria (age, size, unflagged)
            mailbox.folder.set(folder.name)
            messages = mailbox.fetch(AND(date_lt=max_date, size_gt=max_mail_size_in_bytes, flagged=False), mark_seen=False)
            for msg in messages:
                logging.debug('retrieve_flags> Processing message uid %s from %s: %s FROM %s TO %s [%s] (%s)', msg.uid, msg.date, msg.subject, msg.from_, msg.to, msg.flags, humanfriendly.format_size(msg.size_rfc822))

                msg_flags = ' '.join(msg.flags)
                flags_dict[msg.uid] = msg_flags

    return flags_dict


def has_attachment_larger_than_size(msg, max_attachment_size):
    """
    determine if the given message contains attachments larger than
    `max_attachment_size`
    """
    find = False
    for attachment in msg.iter_attachments():
        size_real = len(str(attachment)) / 4 * 3
        if (size_real > max_attachment_size):
            find = True
    return find


def expunge(msg, max_attachment_size, filename_prefix):
    """
    """
    global count_attachments

    size_real = len(str(msg)) / 4 * 3

    if msg.get_content_maintype() != 'multipart':
        if msg.is_attachment() is False:
            return msg

        # only remove attachments larger than max_attachment_size
        if size_real < max_attachment_size:
            return msg

        try:
            fn = msg.get_filename()
            ct = msg.get_content_type()
        except AttributeError:
            logging.debug('expunge> got string instead of filename for %s. Skipping.', fn)
            return msg

        # skip embedded email messages
        if ct == 'message/rfc822':
            return msg

        if fn:
            output_filename = filename_prefix + " " + fn
            filepath = os.path.join(EXPORT_FOLDER_PATH, output_filename)

            if MODE in ['test']:
                logging.debug('expunge> [TEST] would export "%s" to "%s" (%s)', fn, filepath, humanfriendly.format_size(size_real))
            if MODE in ['export', 'detach']:
                logging.debug('expunge> exporting "%s" (%s) to "%s" (%s)', fn, ct, filepath, humanfriendly.format_size(size_real))
                with open(filepath, 'wb') as f:
                    # TODO: check for duplicates!
                    f.write(msg.get_payload(decode=True))

        #logging.debug('expunge> content type: %s', ct)
        #logging.debug('expunge> %s (%s)', fn, humanfriendly.format_size(size_real))
        #logging.debug('--')

        # create new message with replaced attachment
        params = msg.get_params()[1:]
        params = ', '.join(['='.join(p) for p in params])
        replace = REPLACESTRING % dict(content_type=ct,
                                       filename=fn,
                                       params=params)
        msg.set_payload(replace)
        for k, v in msg.get_params()[1:]:
            msg.del_param(k)
        msg.set_type('text/plain')
        del msg['Content-Transfer-Encoding']
        del msg['Content-Disposition']
        count_attachments += 1
    else:
        if msg.is_multipart():
            # note: we have to use get_payload() to replace all parts of the e-mail.
            # iter_attachments() is not sufficient here.
            payload = [expunge(part, max_attachment_size, filename_prefix) for part in msg.get_payload()]
            msg.set_payload(payload)

    return msg


# Main script
def run_saver(mail):
    """
    """
    global count_folders
    global count_mail

    # determine the date limit
    max_date = datetime.date.today() - datetime.timedelta(days=EMAIL_AGE_DAYS)
    max_date = max_date.strftime('%d-%b-%Y')
    max_mail_size_in_bytes = humanfriendly.parse_size(MAX_MAIL_SIZE)
    max_attachment_size_in_bytes = humanfriendly.parse_size(MAX_ATTACHMENT_SIZE)

    # retrieve flags for all messages matching our criteria (size, age, seen)
    flags_per_message = retrieve_flags()
    #print("FLAGS: ", flags_per_message)
    #print("Test: ", flags_per_message['648340'].decode("unicode_escape"))
    #sys.exit()

    if not MAIL_FOLDER:
        logging.info('Scanning for messages before %s and larger than %s in all folders.', max_date, MAX_MAIL_SIZE)
        res, folder_list = mail.list()
        folders = [item.split()[-1].decode() for item in folder_list]
    else:
        logging.info('Scanning for messages before %s and larger than %s in %s.', max_date, MAX_MAIL_SIZE, MAIL_FOLDER)
        folders = [MAIL_FOLDER]
        res, folder_list = mail.list(directory=MAIL_FOLDER)
        folders += [item.split()[-1].decode() for item in folder_list]

    for folder in folders:
        count_folders += 1
        logging.debug('run_saver> folder: %s', folder)
        mail.select(folder)

        # retreive all email messages matching our filter
        #result_mails, data_mails = mail.uid('search', '((BEFORE "' + max_date + '") (LARGER "' + MAX_MAIL_SIZE + '"))')
        #result_mails, data_mails = mail.uid('search', '(LARGER 6000000)')
        result_mails, data_mails = mail.uid('search', '(BEFORE "' + max_date + '" LARGER ' + str(max_mail_size_in_bytes) + ' UNFLAGGED)')

        msg_nums = data_mails[0].split()
        logging.info('Found %s messages in folder %s.', len(msg_nums), folder)

        for email_uid in data_mails[0].split():
            count_mail += 1
            mytime = imaplib.Time2Internaldate(time.time())
            logging.debug('run_saver> examining e-mail with `uid`: %s', email_uid)
            response, data = mail.uid('fetch', email_uid, '(RFC822)')

            try:
                raw_email = (data[0][1]).decode('utf-8')
            except:
                try:
                    raw_email = (data[0][1]).decode('iso-8859-1')
                except:
                    raw_email = (data[0][1]).decode('utf-8', 'backslashreplace')

            # retrieve flags (not working)
            #flags = imaplib.ParseFlags(data[0][0])
            #flag_str = " ".join(flags)
            #logging.info('run_saver> Flags for %s: %s', email_uid, flag_str)

            email_message = email.message_from_string(raw_email, policy=email.policy.default)
            #logging.debug('run_saver> email_message: %s', email_message)

            if has_attachment_larger_than_size(email_message, max_attachment_size_in_bytes):
                logging.debug('run_saver> optimizing email: %s', email_uid)

                date = decode_header(email_message["Date"])[0][0]
                date_object = datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
                filename_prefix = eval(folder) + "/" + date_object.strftime("%Y%m%d-%H%M")
                logging.debug('run_saver> email received: %s', filename_prefix)

                output_folder = EXPORT_FOLDER_NAME + "/" + eval(folder)
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder, mode=0o777)

                new_message = expunge(email_message, max_attachment_size_in_bytes, filename_prefix)

                # replace the original message with the expunged message
                if MODE in ['delete', 'detach']:
                    logging.debug('run_saver> removed attachment(s)')

                    # use flags retrieved via imap-tools
                    msg_flags = flags_per_message[email_uid.decode('UTF-8')]
                    logging.debug('run_saver> flags this message with: %s', msg_flags)

                    mail.append(folder, msg_flags, mytime, new_message.as_string().encode())
                    mail.uid('STORE', email_uid, '+FLAGS', r'(\Deleted)')
            else:
                logging.debug('run_saver> message to small')

        mail.expunge()
        logging.debug('run_saver> folder completed: %s', folder)

    logging.info('')
    logging.info('Summary:')
    logging.info('* Scanned %d folders', count_folders)
    logging.info('* Scanned %d e-mails', count_mail)
    logging.info('* Extracted %d attachments', count_attachments)


def main():
    """
    """
    try:
        while True:
            # open connection using imaplib
            imaplib_connection = imaplib.IMAP4_SSL(SERVER)
            r, d = imaplib_connection.login(USER, PASSWORD)
            assert r == 'OK', 'login failed'

            # open connection with imap-tools
            try:
                run_saver(imaplib_connection)
            except imaplib_connection.abort as e:
                continue
            imaplib_connection.logout()
            break
    except KeyboardInterrupt:
        logging.info('\nCancelling...')
    except (SystemExit):
        e = get_exception()
        if getattr(e, 'code', 1) != 0:
            raise SystemExit('ERROR: %s' % e)


if __name__ == '__main__':
    main()
