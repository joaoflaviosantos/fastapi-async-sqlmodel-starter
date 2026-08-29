# Built-in Dependencies
from datetime import datetime, timezone
from typing import Any

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.core.utils.email import get_email_sender
from src.apps.system.users.models import User
from src.core.db.session import local_session
from src.core.logger import logger_worker
from src.worker import app


@async_task(app, name="send_welcome_email", bind=True, max_retries=3)
async def send_welcome_email(self: Any, email: str, username: str) -> dict:
    """
    Task triggered when a new user is created.
    Simulates sending a welcome email by logging the action.

    Parameters
    ----------
    email : str
        The email address of the newly created user.
    username : str
        The username of the newly created user.

    Returns
    -------
    dict
        A dictionary with the task result status.
    """

    email_sender = (
        get_email_sender()
    )  # Get the email sender (FastApiMailSender or LoggingEmailSender)

    logger_worker.info(
        f"[send_welcome_email] Starting welcome email task for user '{username}' ({email})"
    )

    try:
        # Demonstrate async DB access within a Celery task
        async with local_session() as session:
            result = await session.exec(select(User).where(User.email == email))
            user = result.first()

            if user:
                # Send the email asynchronously using FastApiMailSender
                await email_sender.send_to_user(
                    to_email_addr=email,
                    subject="Welcome to FastAPI Async SQLModel Starter!",
                    html_content=f"""<p>Hi {username},</p>
<p>Welcome to our FastAPI Async SQLModel Starter! We're excited to have you on board. If you have any questions or need assistance, feel free to reach out to our support team.</p>
<p>Best regards,<br>The Team</p>""",
                )
                logger_worker.info(
                    f"[send_welcome_email] User '{username}' found in database. "
                    f"Created at: {user.created_at}"
                )
            else:
                logger_worker.warning(
                    f"[send_welcome_email] User '{username}' ({email}) not found in database."
                )

        # Simulate email sending (log only)
        logger_worker.info(
            f"[send_welcome_email] Sending welcome email to {email} for user {username}"
        )
        logger_worker.info(
            f"[send_welcome_email] Welcome email successfully sent to {email} "
            f"at {datetime.now(timezone.utc).isoformat()}"
        )

        return {
            "status": "success",
            "email": email,
            "username": username,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger_worker.error(f"[send_welcome_email] Failed to send welcome email to {email}: {exc}")
        raise self.retry(exc=exc, countdown=60)
