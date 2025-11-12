import json
from datetime import datetime, timezone
from typing import Optional, Any
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app import models


class ComplianceLogger:
	"""Unified compliance logger that stores all compliance events directly in the AuditLog database table."""

	def __init__(self, institution_id: str = 'DR-ATUL-CLINIC', geo_region: str = 'IN', standard: str = 'HIPAA+NMC'):
		self.institution_id = institution_id
		self.geo_region = geo_region
		self.standard = standard
		# Use in-memory null logger (no file, no stdout)
		self.logger = logging.getLogger('NullComplianceLogger')
		self.logger.addHandler(logging.NullHandler())
		self.logger.setLevel(logging.INFO)

	def log_event(
		self,
		user_id: Optional[int],
		role: Optional[str],
		action: str,
		category: str,
		details: Optional[str] = None,
		severity: str = 'INFO',
		resource_type: Optional[str] = None,
		resource_id: Optional[int] = None,
		username: Optional[str] = None,
		user_agent: Optional[str] = None,
		**_: Any
	) -> None:
		"""Logs an event into the AuditLog table directly via SQLAlchemy.
		Accepts and ignores extra kwargs for backward compatibility.
		"""
		# Normalize action to match DB Enum values (DB enum may not include new extended actions)
		action_upper = (action or '').upper()
		standard_actions = {'CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'MFA_SETUP', 'MFA_VERIFY', 'PASSWORD_RESET', 'ACCESS_DENIED', 'EXPORT', 'PRINT', 'BULK_ACTION'}
		action_db = None
		if action_upper in standard_actions:
			action_db = action_upper
		else:
			# Pattern-based reductions to standard enum values
			if 'LOGIN' in action_upper:
				action_db = 'LOGIN'
			elif 'LOGOUT' in action_upper:
				action_db = 'LOGOUT'
			elif action_upper.endswith('_CREATE') or action_upper.startswith('CREATE_'):
				action_db = 'CREATE'
			elif action_upper.endswith('_UPDATE') or action_upper.startswith('UPDATE_'):
				action_db = 'UPDATE'
			elif action_upper.endswith('_DELETE') or action_upper.startswith('DELETE_'):
				action_db = 'DELETE'
			elif 'DENIED' in action_upper:
				action_db = 'ACCESS_DENIED'
			elif 'EXPORT' in action_upper:
				action_db = 'EXPORT'
			elif 'PRINT' in action_upper:
				action_db = 'PRINT'
			elif 'BULK' in action_upper:
				action_db = 'BULK_ACTION'
			elif 'BLOCK' in action_upper or 'BOOK' in action_upper or 'SLOT' in action_upper or 'SCHEDULE' in action_upper:
				# Mutations that are not strictly create/delete fall back to UPDATE
				action_db = 'UPDATE'
			else:
				action_db = 'READ'

		db = SessionLocal()
		try:
			# Coerce action to Enum if possible
			try:
				action_enum = models.AuditAction[action_db] if isinstance(action_db, str) else action_db
			except Exception:
				try:
					action_enum = models.AuditAction(action_db)  # allow direct value lookup
				except Exception:
					action_enum = models.AuditAction.READ

			db_log = models.AuditLog(
				user_id=user_id,
				username=username if username else (str(user_id) if user_id else 'System'),
				action=action_enum,
				category=category or 'GENERAL',
				severity=severity or 'INFO',
				resource_type=resource_type,
				resource_id=resource_id,
				details=details,
				ip_address='127.0.0.1',  # placeholder until request context injection
				user_agent=user_agent,
				timestamp=datetime.now(timezone.utc),
			)
			db.add(db_log)
			db.commit()
			db.refresh(db_log)
		except SQLAlchemyError as e:
			db.rollback()
			self.logger.error(f"Failed to save compliance log to DB: {e}")
		finally:
			db.close()

	def log_access(
		self,
		user_id: Optional[int],
		role: Optional[str],
		resource_type: str,
		resource_id: str,
		purpose: str,
		severity: str = 'INFO',
		**kwargs: Any
	) -> None:
		"""Logs a data access event into the AuditLog table."""
		self.log_event(
			user_id=user_id,
			role=role,
			action='ACCESS',
			category='DATA_ACCESS',
			details=f"Accessed {resource_type}:{resource_id} for {purpose}",
			severity=severity,
			resource_type=resource_type,
			resource_id=resource_id,
			**kwargs
		)


# Singleton instance for global import
compliance_logger = ComplianceLogger()
