########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\models.py total lines 397 
########################################################################

from .extensions import db
import time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Index, Text
import datetime
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash
import secrets

Base = declarative_base()
metadata = Base.metadata

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    status = db.Column(db.String, nullable=False, server_default='active')
    last_login_ip = db.Column(db.String, nullable=True)
    public_address = db.Column(db.String, unique=True, index=True, nullable=True)
    engines = db.relationship('RegisteredEngine', foreign_keys='RegisteredEngine.user_id', back_populates='owner')
    subscriptions = db.relationship('Subscription', back_populates='user')
    states = db.relationship('State', back_populates='user')
    variables = db.relationship('Variable', back_populates='user')
    backups = db.relationship('UserBackup', back_populates='user')
    workflows = db.relationship('Workflow', back_populates='user')
    episodes = db.relationship("Episode", back_populates="user", lazy="dynamic", cascade="all, delete-orphan", foreign_keys="Episode.user_id")
    agent_sessions = db.relationship("AgentSession", back_populates="user", lazy="dynamic", cascade="all, delete-orphan", foreign_keys="AgentSession.user_id")
    owned_workflow_shares = db.relationship("WorkflowShare", back_populates="owner", foreign_keys="WorkflowShare.owner_id")
    guest_workflow_shares = db.relationship("WorkflowShare", back_populates="guest_user", foreign_keys="WorkflowShare.user_id")


    audit_logs = db.relationship('AuditLog', back_populates='admin', foreign_keys='AuditLog.admin_id')
    marketplace_submissions = db.relationship('MarketplaceSubmission', back_populates='submitter', foreign_keys='MarketplaceSubmission.submitter_user_id')
    engine_shares = db.relationship('EngineShare', back_populates='user', foreign_keys='EngineShare.user_id')
    scheduled_tasks = db.relationship('ScheduledTask', back_populates='user', foreign_keys='ScheduledTask.user_id')
    execution_metrics = db.relationship('ExecutionMetric', back_populates='user', foreign_keys='ExecutionMetric.user_id')
    engine_sessions = db.relationship('UserEngineSession', back_populates='user', foreign_keys='UserEngineSession.user_id')

    @property
    def is_active(self):
        return self.status == 'active'

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), unique=True, nullable=False)
    tier = db.Column(db.String, db.ForeignKey('plans.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    provider_subscription_id = db.Column(db.String, unique=True, nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', back_populates='subscriptions')
    plan = db.relationship('Plan')

class RegisteredEngine(db.Model):
    __tablename__ = 'registered_engines'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    engine_token_hash = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(db.String, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    owner = db.relationship('User', foreign_keys=[user_id], back_populates='engines')
    shares = db.relationship('EngineShare', back_populates='engine', passive_deletes=True)
    episodes = db.relationship("Episode", back_populates="engine", lazy="dynamic", cascade="all, delete-orphan", foreign_keys="Episode.engine_id")
    agent_sessions = db.relationship("AgentSession", back_populates="engine", lazy="dynamic", cascade="all, delete-orphan", foreign_keys="AgentSession.engine_id")
    scheduled_tasks = db.relationship('ScheduledTask', back_populates='engine', foreign_keys='ScheduledTask.engine_id')
    execution_metrics = db.relationship('ExecutionMetric', back_populates='engine', foreign_keys='ExecutionMetric.engine_id')
    user_engine_sessions = db.relationship('UserEngineSession', back_populates='engine', foreign_keys='UserEngineSession.engine_id')

    @property
    def token(self):
        return self.engine_token_hash

Engine = RegisteredEngine

class EngineShare(db.Model):
    __tablename__ = 'engine_shares'
    id = db.Column(db.Integer, primary_key=True)
    engine_id = db.Column(db.String, db.ForeignKey('registered_engines.id', ondelete='CASCADE'), index=True, nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    role = db.Column(db.String, default='viewer', nullable=False)
    shared_at = db.Column(db.DateTime, default=db.func.now())
    engine = db.relationship('RegisteredEngine', back_populates='shares')
    user = db.relationship('User', foreign_keys=[user_id], back_populates='engine_shares')
    __table_args__ = (db.UniqueConstraint('engine_id', 'user_id', name='uq_engine_share'),)

    @property
    def shared_with_user_id(self):
        return self.user_id

class Preset(db.Model):
    __tablename__ = 'presets'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    workflow_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())
    versions = db.relationship('PresetVersion', back_populates='preset', passive_deletes=True)
    user = db.relationship('User')
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_user_preset_name'),)

class PresetVersion(db.Model):
    __tablename__ = 'preset_versions'
    id = db.Column(db.Integer, primary_key=True)
    preset_id = db.Column(db.String, db.ForeignKey('presets.id', ondelete='CASCADE'), nullable=False)
    workflow_data = db.Column(db.JSON, nullable=False)
    version_message = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    preset = db.relationship('Preset', back_populates='versions')

class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    key = db.Column(db.String, nullable=False)
    value = db.Column(db.JSON, nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', back_populates='states')
    __table_args__ = (db.UniqueConstraint('user_id', 'key', name='uq_user_state_key'),)

class Variable(db.Model):
    __tablename__ = 'variables'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    value_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', back_populates='variables')
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_user_variable_name'),)

class UserBackup(db.Model):
    __tablename__ = 'user_backups'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), unique=True, nullable=False)
    backup_file_path = db.Column(db.String, nullable=True)
    salt_b64 = db.Column(db.String, nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', back_populates='backups')

class Workflow(db.Model):
    __tablename__ = 'workflows'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    friendly_name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', back_populates='workflows')
    shares = db.relationship('WorkflowShare', back_populates='workflow')
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_owner_preset'),)

class WorkflowShare(db.Model):
    __tablename__ = 'workflow_shares'
    id = db.Column(db.String, primary_key=True)
    workflow_id = db.Column(db.String, db.ForeignKey('workflows.id'), nullable=False)
    share_token = db.Column(db.String, unique=True, nullable=False)
    permissions = db.Column(db.String, nullable=False)
    link_name = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    workflow = db.relationship('Workflow', back_populates='shares')
    owner = db.relationship('User', foreign_keys=[owner_id], back_populates='owned_workflow_shares')
    guest_user = db.relationship('User', foreign_keys=[user_id], back_populates='guest_workflow_shares')

class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    engine_id = db.Column(db.String, db.ForeignKey('registered_engines.id'), nullable=False)
    task_type = db.Column(db.String, nullable=False)
    scheduled_for = db.Column(db.DateTime, nullable=False)
    os_task_name = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', foreign_keys=[user_id], back_populates='scheduled_tasks')
    engine = db.relationship('RegisteredEngine', foreign_keys=[engine_id], back_populates='scheduled_tasks')

class ExecutionMetric(db.Model):
    __tablename__ = 'execution_metrics'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), index=True, nullable=False)
    engine_id = db.Column(db.String, db.ForeignKey('registered_engines.id'), nullable=False)
    workflow_context_id = db.Column(db.String, index=True, nullable=False)
    preset_name = db.Column(db.String, nullable=True)
    node_id = db.Column(db.String, nullable=False)
    node_name = db.Column(db.String, nullable=True)
    module_id = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)
    execution_time_ms = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], back_populates='execution_metrics')
    engine = db.relationship('RegisteredEngine', foreign_keys=[engine_id], back_populates='execution_metrics')

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    roles = db.relationship('Role', secondary='admin_roles', back_populates='admins')

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=True)
    admins = db.relationship('AdminUser', secondary='admin_roles', back_populates='roles')
    permissions = db.relationship('Permission', secondary='role_permissions', back_populates='roles')

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    roles = db.relationship('Role', secondary='role_permissions', back_populates='permissions')

class AdminRole(db.Model):
    __tablename__ = 'admin_roles'
    admin_user_id = db.Column(db.String, db.ForeignKey('admin_users.id'), primary_key=True)
    role_id = db.Column(db.String, db.ForeignKey('roles.id'), primary_key=True)

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    role_id = db.Column(db.String, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.String, db.ForeignKey('permissions.id'), primary_key=True)

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, nullable=False)
    max_executions = db.Column(db.Integer, nullable=True)
    features = db.Column(db.JSON, nullable=True)
    capabilities = db.relationship('Capability', secondary='plan_capabilities', back_populates='plans')
    prices = db.relationship('PlanPrice', back_populates='plan')

class Capability(db.Model):
    __tablename__ = 'capabilities'
    id = db.Column(db.String, primary_key=True)
    description = db.Column(db.Text, nullable=True)
    plans = db.relationship('Plan', secondary='plan_capabilities', back_populates='capabilities')

class PlanCapability(db.Model):
    __tablename__ = 'plan_capabilities'
    plan_id = db.Column(db.String, db.ForeignKey('plans.id'), primary_key=True)
    capability_id = db.Column(db.String, db.ForeignKey('capabilities.id'), primary_key=True)

class PlanPrice(db.Model):
    __tablename__ = 'plan_prices'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.String, db.ForeignKey('plans.id'), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    paypal_plan_id = db.Column(db.String, unique=True, nullable=True)
    plan = db.relationship('Plan', back_populates='prices')

class GloballyDisabledComponent(db.Model):
    __tablename__ = 'globally_disabled_components'
    component_id = db.Column(db.String, primary_key=True)
    reason = db.Column(db.Text, nullable=False)
    disabled_at = db.Column(db.DateTime, server_default=db.func.now())

class MarketplaceSubmission(db.Model):
    __tablename__ = 'marketplace_submissions'
    id = db.Column(db.String, primary_key=True)
    submitter_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    component_id = db.Column(db.String, nullable=False)
    component_type = db.Column(db.String, nullable=False)
    version = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now())
    reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    staged_file_path = db.Column(db.String, nullable=True)
    submitter = db.relationship('User', foreign_keys=[submitter_user_id], back_populates='marketplace_submissions')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.String, primary_key=True)
    admin_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String, nullable=False)
    target_resource = db.Column(db.String, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    ip_address = db.Column(db.String, nullable=True)
    admin = db.relationship('User', foreign_keys=[admin_id], back_populates='audit_logs')

class FeatureFlag(db.Model):
    __tablename__ = 'feature_flags'
    id = db.Column(db.String, primary_key=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False)
    rollout_rules = db.Column(db.JSON, nullable=True)
    allowed_users = db.Column(db.JSON, nullable=True)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.String(128), primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    engine_id = db.Column(db.String, index=True, nullable=False)
    payload = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, default=100, nullable=False)
    status = db.Column(db.String(64), default='queued', nullable=False, index=True)
    retries = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    created_at = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)
    available_at = db.Column(db.Integer, default=lambda: int(time.time()), nullable=False)
    claimed_at = db.Column(db.Integer, nullable=True)
    worker_id = db.Column(db.String, nullable=True)
    version = db.Column(db.Integer, default=0, nullable=False)
    __table_args__ = (
        Index('idx_jobs_status_prio', 'status', 'priority', 'available_at', 'created_at'),
    )

def init_db_models():

    pass

class UserEngineSession(db.Model):

    __tablename__ = 'user_engine_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    engine_id = db.Column(db.String, db.ForeignKey('registered_engines.id'), nullable=False, index=True)
    session_start = db.Column(db.BigInteger, default=lambda: int(time.time()))
    is_active = db.Column(db.Boolean, default=True, index=True)
    last_activated_at = db.Column(db.BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))
    internal_url = db.Column(db.String, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], back_populates='engine_sessions')
    engine = db.relationship('RegisteredEngine', foreign_keys=[engine_id], back_populates='user_engine_sessions')


class Episode(db.Model):
    __tablename__ = "episodes"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    engine_id = db.Column(db.String(36), db.ForeignKey("registered_engines.id"), nullable=False, index=True)

    title = db.Column(db.String(255), nullable=False, default="New Chat")
    intent = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    core_timeline_ptr = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="episodes", foreign_keys=[user_id])
    engine = db.relationship("RegisteredEngine", back_populates="episodes", foreign_keys=[engine_id])
    sessions = db.relationship("AgentSession", back_populates="episode", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Episode {self.title} (ID: {self.id})>"

class AgentSession(db.Model):
    __tablename__ = "agent_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    engine_id = db.Column(db.String(36), db.ForeignKey("registered_engines.id"), nullable=False, index=True)

    episode_id = db.Column(db.String(36), db.ForeignKey("episodes.id"), nullable=True, index=True)

    ws_token_hash = db.Column(db.String(256), nullable=False, unique=True)

    status = db.Column(db.String(30), nullable=False, default="starting", index=True)

    created_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), index=True
    )
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="agent_sessions", foreign_keys=[user_id])
    engine = db.relationship("RegisteredEngine", back_populates="agent_sessions", foreign_keys=[engine_id])
    episode = db.relationship("Episode", back_populates="sessions")

    def __repr__(self):
        return f"<AgentSession {self.id} (User: {self.user_id})>"
