"""Add tasks and task_audit_log tables

Revision ID: 20260209212000
Revises: 20260208133000
Create Date: 2026-02-09 21:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260209212000'
down_revision = '20260208133000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for task status and frequency
    connection = op.get_bind()
    connection.execute(sa.text("""
        DO $$ BEGIN 
            CREATE TYPE taskstatus AS ENUM ('not_started', 'in_progress', 'completed', 'deviation'); 
        EXCEPTION WHEN duplicate_object THEN null; 
        END $$;
    """))
    connection.execute(sa.text("""
        DO $$ BEGIN 
            CREATE TYPE taskfrequency AS ENUM ('monthly', 'quarterly', 'yearly', 'ad_hoc'); 
        EXCEPTION WHEN duplicate_object THEN null; 
        END $$;
    """))
    connection.execute(sa.text("""
        DO $$ BEGIN 
            CREATE TYPE taskcategory AS ENUM ('avstemming', 'rapportering', 'bokføring', 'compliance'); 
        EXCEPTION WHEN duplicate_object THEN null; 
        END $$;
    """))
    connection.execute(sa.text("""
        DO $$ BEGIN 
            CREATE TYPE taskauditaction AS ENUM ('created', 'completed', 'marked_deviation', 'manually_checked', 'auto_completed'); 
        EXCEPTION WHEN duplicate_object THEN null; 
        END $$;
    """))
    connection.execute(sa.text("""
        DO $$ BEGIN 
            CREATE TYPE taskauditresult AS ENUM ('ok', 'deviation'); 
        EXCEPTION WHEN duplicate_object THEN null; 
        END $$;
    """))
    connection.commit()
    
    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', postgresql.ENUM('avstemming', 'rapportering', 'bokføring', 'compliance', 
                                             name='taskcategory', create_type=False), nullable=True),
        sa.Column('frequency', postgresql.ENUM('monthly', 'quarterly', 'yearly', 'ad_hoc', 
                                              name='taskfrequency', create_type=False), nullable=True),
        sa.Column('period_year', sa.Integer(), nullable=False),
        sa.Column('period_month', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('not_started', 'in_progress', 'completed', 'deviation', 
                                           name='taskstatus', create_type=False), 
                 nullable=False, server_default='not_started'),
        sa.Column('completed_by', sa.String(length=100), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('documentation_url', sa.Text(), nullable=True),
        sa.Column('ai_comment', sa.Text(), nullable=True),
        sa.Column('is_checklist', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for tasks
    op.create_index(op.f('ix_tasks_client_id'), 'tasks', ['client_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_category'), 'tasks', ['category'], unique=False)
    op.create_index(op.f('ix_tasks_period'), 'tasks', ['period_year', 'period_month'], unique=False)
    op.create_index(op.f('ix_tasks_parent_task_id'), 'tasks', ['parent_task_id'], unique=False)
    
    # Create task_audit_log table
    op.create_table('task_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', postgresql.ENUM('created', 'completed', 'marked_deviation', 'manually_checked', 'auto_completed',
                                           name='taskauditaction', create_type=False), nullable=False),
        sa.Column('performed_by', sa.String(length=100), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False),
        sa.Column('result', postgresql.ENUM('ok', 'deviation', name='taskauditresult', create_type=False), nullable=True),
        sa.Column('result_description', sa.Text(), nullable=True),
        sa.Column('documentation_reference', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for task_audit_log
    op.create_index(op.f('ix_task_audit_log_task_id'), 'task_audit_log', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_audit_log_performed_at'), 'task_audit_log', ['performed_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_task_audit_log_performed_at'), table_name='task_audit_log')
    op.drop_index(op.f('ix_task_audit_log_task_id'), table_name='task_audit_log')
    op.drop_index(op.f('ix_tasks_parent_task_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_period'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_category'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_status'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_client_id'), table_name='tasks')
    
    # Drop tables
    op.drop_table('task_audit_log')
    op.drop_table('tasks')
    
    # Drop enum types
    connection = op.get_bind()
    connection.execute(sa.text("DROP TYPE IF EXISTS taskauditresult"))
    connection.execute(sa.text("DROP TYPE IF EXISTS taskauditaction"))
    connection.execute(sa.text("DROP TYPE IF EXISTS taskcategory"))
    connection.execute(sa.text("DROP TYPE IF EXISTS taskfrequency"))
    connection.execute(sa.text("DROP TYPE IF EXISTS taskstatus"))
    connection.commit()
