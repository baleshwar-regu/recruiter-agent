import phonenumbers


def normalize_phone(phone_str: str, default_country: str = "US") -> str:
    try:
        parsed = phonenumbers.parse(phone_str, default_country)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        print(f"[Phone Normalization] Error: {e}")
        return None
