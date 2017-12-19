"""Initial version

Revision ID: bc3cdb39b6b7
Revises: None
Create Date: 2016-09-07 15:46:47.239674

"""

# revision identifiers, used by Alembic.
revision = 'bc3cdb39b6b7'
down_revision = None

from alembic import op
import sqlalchemy as sa
import sqlalchemy_enum34, sqlalchemy_utils.types.uuid
import ode.blueprints.isi.model

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('source',
    sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('contents', sa.Unicode(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source')),
    sa.UniqueConstraint('name', name=op.f('uq_source_name'))
    )
    op.create_table('template',
    sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('subject', sa.String(), nullable=True),
    sa.Column('text_html', sa.String(), nullable=True),
    sa.Column('sender', sa.String(), nullable=True),
    sa.Column('recipients_raw', ode.blueprints.isi.model.Json(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template'))
    )
    op.create_table('event',
    sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('source_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
    sa.Column('uid', sa.String(), nullable=True),
    sa.Column('upstream_event_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('contents', sa.Unicode(), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_event_source_id_source')),
    sa.ForeignKeyConstraint(['upstream_event_id'], ['event.id'], name=op.f('fk_event_upstream_event_id_event')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_event'))
    )
    op.create_table('invitation',
    sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('event_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
    sa.Column('subject', sa.String(), nullable=True),
    sa.Column('text_html', sa.String(), nullable=True),
    sa.Column('sender', sa.String(), nullable=True),
    sa.Column('recipients_raw', ode.blueprints.isi.model.Json(), nullable=True),
    sa.Column('state', sqlalchemy_enum34.Enum('open', 'preparing'), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], name=op.f('fk_invitation_event_id_event')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invitation'))
    )
    op.create_table('recipient',
    sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('invitation_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('state', sqlalchemy_enum34.Enum('deselected', 'new', 'pending', 'sent'), nullable=True),
    sa.Column('pending_address', sa.String(), nullable=True),
    sa.Column('send_time', sa.DateTime(), nullable=True),
    sa.Column('accept', sqlalchemy_enum34.Enum('no', 'unknown', 'yes'), nullable=True),
    sa.Column('accept_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['invitation_id'], ['invitation.id'], name=op.f('fk_recipient_invitation_id_invitation')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recipient'))
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recipient')
    op.drop_table('invitation')
    op.drop_table('event')
    op.drop_table('template')
    op.drop_table('source')
    ### end Alembic commands ###
