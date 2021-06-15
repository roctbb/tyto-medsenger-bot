import email
import imaplib
import uuid
from email.message import EmailMessage
from email.header import decode_header
from config import *
import re


def extract_contract_id(email):
    receivers = email.get_all('to', [])

    if not receivers:
        return None
    name, domain = receivers[0].split('@')
    parts = name.split('+')
    del parts[0]

    if not parts:
        return None

    return parts[0]


def decode_body(part):
    body_data = part.get_payload(decode=True)
    charset = part.get_param("charset", "ASCII")
    return body_data.decode(charset, errors="replace")


def extract_code(text):
    text = ''.join(text.split())
    regex = r"код(\ |\d*)"
    codes = re.findall(regex, text)

    if codes:
        return codes[0].replace('=', '').replace('"', '')
    else:
        return None


def extract_link(text):
    text = ''.join(text.split())
    regex = r"\"https:\/\/cloudeu.*?\""
    links = re.findall(regex, text)

    if links:
        return links[0].replace('=', '').replace('"', '')
    else:
        return None

def decode_string(value):
  if value.startswith('"=?'):
    value = value.replace('"', '')

  value, encoding = decode_header(value)[0]
  if encoding:
    value = value.decode(encoding)

  return value


def process_attachment(attachment):
    name = attachment.get_filename()

    if name:
        return (name, attachment.get_content_type(), attachment.get_payload())
    else:
        return None


def get_attachments(message):
    attachments = []

    for attachment in message.iter_attachments():
        data = process_attachment(attachment)

        if data:
            attachments.append(data)

    if message.is_multipart():
        for part in message.get_payload():
            attachments += get_attachments(part)

    return attachments


def get_messages(last_id=''):
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select('inbox')

    status, data = mail.search(None, 'ALL')

    mail_ids = []

    for block in data:
        mail_ids += block.split()

    mail_ids = list(map(lambda x:x.decode('ascii'), mail_ids))

    try:
        start = mail_ids.index(last_id) + 1
    except ValueError:
        start = 0

    messages = []

    if len(mail_ids) <= start:
        return (None, [])

    for i in mail_ids[start:]:
        status, data = mail.fetch(i, '(RFC822)')

        if status == 'OK':
            for response_part in data:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1], _class=EmailMessage)
                    messages.append(message)
    if messages:
        return (mail_ids[-1], messages)
    else:
        return (None, [])
