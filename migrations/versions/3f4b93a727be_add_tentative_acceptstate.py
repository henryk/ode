"""Add tentative AcceptState

Revision ID: 3f4b93a727be
Revises: 2c669d7ec424
Create Date: 2018-01-03 01:27:10.740419

"""

# revision identifiers, used by Alembic.
revision = '3f4b93a727be'
down_revision = '2c669d7ec424'

from alembic import op
import sqlalchemy as sa
import enum
from sqlalchemy_enum34 import EnumType


class old_AcceptState(enum.Enum):
  UNKNOWN = "unknown"
  YES = "yes"
  NO = "no"

class new_AcceptState(enum.Enum):
  UNKNOWN = "unknown"
  YES = "yes"
  NO = "no"
  TENTATIVE = "tentative"

old_type = EnumType(old_AcceptState, name="accept_state")
new_type = EnumType(new_AcceptState, name="accept_state")


def upgrade():
    with op.batch_alter_table('recipient', schema=None) as batch_op:
      batch_op.alter_column('accept', type_=new_type, existing_type=old_type)


def downgrade():
    with op.batch_alter_table('recipient', schema=None) as batch_op:
      batch_op.alter_column('accept', type_=old_type, existing_type=new_type, default=old_AcceptState.UNKNOWN)
