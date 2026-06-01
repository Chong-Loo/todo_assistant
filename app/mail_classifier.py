from email.utils import getaddresses


def extract_emails(address_text):
    if not address_text:
        return set()

    addresses = getaddresses([address_text])

    result = set()

    for _, email in addresses:
        email = email.strip().lower()

        if email:
            result.add(email)

    return result


def classify_delivery_type(mail, account_email):
    account_email = str(account_email or "").strip().lower()

    to_emails = extract_emails(mail.get("to", ""))
    cc_emails = extract_emails(mail.get("cc", ""))

    if account_email in to_emails:
        return "direct"

    if account_email in cc_emails:
        return "cc"

    return "other"


def delivery_type_label(delivery_type):
    mapping = {
        "direct": "直发",
        "cc": "抄送",
        "other": "其他"
    }

    return mapping.get(delivery_type, "其他")