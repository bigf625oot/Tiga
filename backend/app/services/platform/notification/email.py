from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.db.session import AsyncSessionLocal
from app.crud.system_config import system_config as crud_system_config
from app.schemas.system_config import BasicSettingsConfig
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

async def get_fast_mail() -> Optional[FastMail]:
    """Dynamically get FastMail instance based on DB configuration"""
    async with AsyncSessionLocal() as db:
        row = await crud_system_config.get_by_key(db, "basic-settings")
        if not row or not row.value:
            return None
            
        try:
            config = BasicSettingsConfig.model_validate(row.value)
            email_conf = config.email
            
            if not email_conf.mail_username or not email_conf.mail_server:
                return None
                
            conf = ConnectionConfig(
                MAIL_USERNAME=email_conf.mail_username,
                MAIL_PASSWORD=email_conf.mail_password,
                MAIL_FROM=email_conf.mail_from or email_conf.mail_username,
                MAIL_PORT=email_conf.mail_port,
                MAIL_SERVER=email_conf.mail_server,
                MAIL_FROM_NAME=email_conf.mail_from_name,
                MAIL_STARTTLS=email_conf.mail_starttls,
                MAIL_SSL_TLS=email_conf.mail_ssl_tls,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True
            )
            return FastMail(conf)
        except Exception as e:
            logger.error(f"Failed to load email config: {e}")
            return None

async def send_email(subject: str, recipients: List[str], body: str, html: bool = False) -> bool:
    """
    Send an email. If configuration is missing, just logs the action.
    """
    fast_mail = await get_fast_mail()
    if not fast_mail:
        logger.info(f"Mock Email - To: {recipients}, Subject: {subject}\nBody:\n{body}")
        return False
        
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=MessageType.html if html else MessageType.plain
        )
        await fast_mail.send_message(message)
        logger.info(f"Email sent successfully to {recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {str(e)}")
        return False

async def send_reset_password_email(email: str, new_password: str) -> bool:
    """
    Send a password reset email to a user.
    """
    subject = "【Tiga System】密码重置通知"
    body = f"""
    您好！
    
    您的账号密码已被管理员重置。
    
    新密码为：{new_password}
    
    为了您的账号安全，请在下次登录后及时修改密码。
    
    此致，
    Tiga System 团队
    """
    return await send_email(subject, [email], body, html=False)
