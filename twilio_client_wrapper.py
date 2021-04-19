from dataclasses import dataclass
from twilio.rest import Client


@dataclass
class TwilioClientWrapper:
    to_number: str
    from_number: str
    client: Client
