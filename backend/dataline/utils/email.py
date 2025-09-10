from fastapi import HTTPException
import requests
from pydantic import BaseModel, EmailStr
from dataline.config import config



class EmailMessage(BaseModel):
    from_email: EmailStr
    from_name: str = "Dataline App"
    to_email: EmailStr
    to_name: str = "Recipient"
    subject: str
    text: str
    html: str = None

def send_email(message: EmailMessage):
    if not config.has_email_notification():
        return None
    payload = {
        "key": config.MANDRILL_API_KEY,
        "message": {
            "html": message.html if message.html else message.text,
            "text": message.text,
            "subject": message.subject,
            "from_email": message.from_email,
            "from_name": message.from_name,
            "to": [{
                "email": message.to_email,
                "name": message.to_name,
                "type": "to"
            }],
        }
    }

    response = requests.post(config.MANDRILL_URL, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Email sending failed")

    return {"message": "Email sent successfully", "response": response.json()}


def new_db_addition_html(db_name):
    return f"""<!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0" />
    <title>New Database Connection</title>
    </head>
    <body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color:#f5f7fa;">
    
    <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
    
    <!-- Header -->
    <tr>
      <td style="background-color:#4a90e2; padding:20px; text-align:center; color:#ffffff; font-size:20px; font-weight:bold;">
        🔔 New Database Connection Added
      </td>
    </tr>
    
    <!-- Body -->
    <tr>
      <td style="padding:30px; color:#333333; font-size:16px; line-height:1.5;">
        <p>Hello,</p>
        <p>A new database connection has been successfully added to your account.</p>
    
        <!-- Dynamic Info -->
        <div style="margin:20px 0; padding:15px; background-color:#f0f4f9; border-radius:6px; text-align:center; font-size:16px; font-weight:bold; color:#4a90e2;">
          Database Name: {db_name}
        </div>
    
        <p>If this wasn’t you, please review your account security immediately.</p>
    
        <p style="margin-top:30px;">Thanks,<br>The D Squad</p>
      </td>
    </tr>
    
    </table>
    
    </body>
    </html>
    """
