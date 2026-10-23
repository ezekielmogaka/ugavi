"""SMS Provider — Abstract Interface (Adapter Pattern).

Supports Africa's Talking, Twilio, or any provider implementing this interface.
Configure in Ugavi Settings.
"""
from abc import ABC, abstractmethod
import frappe


class SMSProvider(ABC):
    """Abstract SMS provider interface."""
    
    @abstractmethod
    def send(self, phone_number: str, message: str) -> bool:
        """Send an SMS. Returns True on success."""
        ...
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance."""
        ...


class LogOnlyProvider(SMSProvider):
    """Development stub — logs messages instead of sending."""
    
    def send(self, phone_number: str, message: str) -> bool:
        frappe.logger().info(f"[SMS STUB] To: {phone_number}, Msg: {message}")
        return True
    
    def get_balance(self) -> float:
        return 999.99


class AfricasTalkingProvider(SMSProvider):
    """Africa's Talking SMS gateway."""
    
    def __init__(self, username: str, api_key: str):
        self.username = username
        self.api_key = api_key
    
    def send(self, phone_number: str, message: str) -> bool:
        try:
            import africastalking
            africastalking.initialize(self.username, self.api_key)
            sms = africastalking.SMS
            response = sms.send(message, [phone_number])
            frappe.logger().info(f"SMS sent via AT: {response}")
            return True
        except Exception as e:
            frappe.log_error(f"SMS failed: {e}", "SMS Provider")
            return False
    
    def get_balance(self) -> float:
        # Stub — requires API call in production
        return 0.0


def get_sms_provider() -> SMSProvider:
    """Factory: return configured SMS provider."""
    try:
        settings = frappe.get_single("Ugavi Settings")
        provider_type = settings.sms_provider or "LogOnly"
        
        if provider_type == "AfricasTalking":
            return AfricasTalkingProvider(
                settings.sms_username or "",
                settings.sms_api_key or "",
            )
        return LogOnlyProvider()
    except Exception:
        return LogOnlyProvider()