"""init

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # quizzes
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, server_default='Без названия'),
        sa.Column('timer_sec', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('shuffle_q', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shuffle_a', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quizzes_owner_id', 'quizzes', ['owner_id'])

    # questions
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_questions_quiz_id', 'questions', ['quiz_id'])

    # answers
    op.create_table(
        'answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(100), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_answers_question_id', 'answers', ['question_id'])

    # sessions
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('mode', sa.Enum('solo', 'group', name='sessionmode'), nullable=False),
        sa.Column(
            'status',
            sa.Enum('waiting', 'active', 'finished', name='sessionstatus'),
            nullable=False,
            server_default='waiting',
        ),
        sa.Column('current_question_idx', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sessions_quiz_id', 'sessions', ['quiz_id'])
    op.create_index('ix_sessions_chat_id', 'sessions', ['chat_id'])

    # session_users
    op.create_table(
        'session_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(64), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_session_users_session_id', 'session_users', ['session_id'])

    # responses
    op.create_table(
        'responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_responses_session_id', 'responses', ['session_id'])
    op.create_index('ix_responses_question_id', 'responses', ['question_id'])
    op.create_index('ix_responses_user_id', 'responses', ['user_id'])


def downgrade() -> None:
    op.drop_table('responses')
    op.drop_table('session_users')
    op.drop_table('sessions')
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('quizzes')
    op.execute('DROP TYPE IF EXISTS sessionmode')
    op.execute('DROP TYPE IF EXISTS sessionstatus')
