import json
import requests
import subprocess
import threading
from typing import Dict, Any
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER

class Notifier:
    def __init__(self, storage):
        self.storage = storage

    def notify(self, target: Dict[str, Any], check_result: Dict[str, Any]):
        """
        Dispatch notifications across active channels (OS Notification, Webhooks, SSE stream)
        """
        settings = self.storage.get_settings()
        movie_title = check_result.get("movie_title", target.get("movie_title"))
        theatre = target.get("theatre", "Cinema")
        booking_url = check_result.get("booking_url") or target.get("target_url")
        details = check_result.get("details", "")

        title = f"🎟️ TICKET RELEASE ALERT: {movie_title}"
        message = f"Tickets available at {theatre}!\n{details}\nBook now: {booking_url}"

        # 1. Desktop Notification (Windows PowerShell Toast)
        if settings.get("desktop_notifications", True):
            threading.Thread(target=self._send_windows_toast, args=(title, message), daemon=True).start()

        # 2. Telegram Webhook
        telegram_url = settings.get("telegram_webhook_url")
        if telegram_url:
            threading.Thread(target=self._send_telegram, args=(telegram_url, f"<b>{title}</b>\n\n{message}"), daemon=True).start()

        # 3. Discord Webhook
        discord_url = settings.get("discord_webhook_url")
        if discord_url:
            threading.Thread(target=self._send_discord, args=(discord_url, title, message, booking_url), daemon=True).start()

        # 4. ntfy Push Notification (ntfy.sh or self-hosted)
        ntfy_target = settings.get("ntfy_url") or settings.get("ntfy_topic")
        if ntfy_target:
            threading.Thread(target=self._send_ntfy, args=(ntfy_target, title, message, booking_url), daemon=True).start()

        # 5. Twilio Emergency Voice Call
        twilio_enabled = settings.get("twilio_enabled", False)
        account_sid = settings.get("twilio_account_sid") or TWILIO_ACCOUNT_SID
        auth_token = settings.get("twilio_auth_token") or TWILIO_AUTH_TOKEN
        from_num = settings.get("twilio_from_number") or TWILIO_FROM_NUMBER
        to_num = settings.get("twilio_to_number") or TWILIO_TO_NUMBER

        if (twilio_enabled or account_sid) and account_sid and auth_token and from_num and to_num:
            call_msg = f"Alert! Tickets for {movie_title} at {theatre} are officially open for booking! Secure your seats immediately."
            threading.Thread(
                target=self._send_twilio_call,
                args=(account_sid, auth_token, from_num, to_num, call_msg),
                daemon=True
            ).start()

        # 6. Custom Webhook
        custom_url = settings.get("custom_webhook_url")
        if custom_url:
            payload = {
                "event": "TICKET_AVAILABLE",
                "movie_title": movie_title,
                "theatre": theatre,
                "booking_url": booking_url,
                "details": details,
                "timestamp": check_result.get("timestamp")
            }
            threading.Thread(target=self._send_custom_webhook, args=(custom_url, payload), daemon=True).start()

    def _send_windows_toast(self, title: str, message: str):
        try:
            # Escape strings for PowerShell
            clean_title = title.replace('"', "'")
            clean_msg = message.replace('"', "'")
            ps_script = f'''
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            $notification = New-Object System.Windows.Forms.NotifyIcon
            $notification.Icon = [System.Drawing.SystemIcons]::Information
            $notification.BalloonTipTitle = "{clean_title}"
            $notification.BalloonTipText = "{clean_msg}"
            $notification.Visible = $True
            $notification.ShowBalloonTip(10000)
            '''
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        except Exception as e:
            print(f"Windows Toast Notification error: {e}")

    def _send_telegram(self, webhook_url: str, html_text: str):
        try:
            requests.post(webhook_url, json={"text": html_text, "parse_mode": "HTML"}, timeout=5)
        except Exception as e:
            print(f"Telegram webhook error: {e}")

    def _send_discord(self, webhook_url: str, title: str, message: str, url: str):
        try:
            embed = {
                "title": title,
                "description": message,
                "url": url,
                "color": 65280  # Green
            }
            requests.post(webhook_url, json={"embeds": [embed]}, timeout=5)
        except Exception as e:
            print(f"Discord webhook error: {e}")

    def _send_custom_webhook(self, webhook_url: str, payload: Dict[str, Any]):
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Custom webhook error: {e}")

    def _send_ntfy(self, target: str, title: str, message: str, booking_url: str):
        try:
            target = target.strip()
            if not target.startswith("http://") and not target.startswith("https://"):
                url = f"https://ntfy.sh/{target.lstrip('/')}"
            else:
                url = target

            headers = {
                "Title": title.encode("utf-8").decode("latin-1", "ignore"),
                "Priority": "high",
                "Tags": "tickets,clapper,tada",
                "Click": booking_url
            }

            if booking_url:
                headers["Actions"] = f"view, Book Tickets Now, {booking_url}, clear=true"

            requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=5)
            print(f"✅ ntfy push alert sent to {url}")
        except Exception as e:
            print(f"ntfy push alert error: {e}")

    def _send_twilio_call(self, account_sid: str, auth_token: str, from_number: str, to_number: str, voice_message: str):
        try:
            account_sid = account_sid.strip()
            auth_token = auth_token.strip()
            from_number = from_number.strip()
            to_number = to_number.strip()

            if not account_sid or not auth_token or not from_number or not to_number:
                print("Twilio call skipped: Missing SID, Token, From, or To number.")
                return

            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
            twiml_content = f'<Response><Say voice="alice" language="en-US">{voice_message}</Say></Response>'
            payload = {
                "To": to_number,
                "From": from_number,
                "Twiml": twiml_content
            }

            resp = requests.post(url, data=payload, auth=(account_sid, auth_token), timeout=10)
            if resp.status_code in (200, 201):
                print(f"📞 Twilio Emergency Voice Call placed to {to_number}!")
            else:
                print(f"Twilio Voice Call API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"Twilio Voice Call error: {e}")


