from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table('sites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uid', sa.String(64), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sites_uid', 'sites', ['uid'])

    op.create_table('viewer_sites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id')),
        sa.UniqueConstraint('user_id','site_id', name='uq_viewer_site')
    )

    op.create_table('sensor_types',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(32), nullable=False, unique=True),
        sa.Column('unit', sa.String(32), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
    )

    op.create_table('sensor_devices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('modbus_addr', sa.Integer(), nullable=True),
        sa.Column('model', sa.String(128), nullable=True),
        sa.Column('serial_no', sa.String(128), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table('sensor_data',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('sensor_devices.id'), nullable=True, index=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('ph', sa.Float(), nullable=True),
        sa.Column('tss', sa.Float(), nullable=True),
        sa.Column('debit', sa.Float(), nullable=True),
        sa.Column('nh3n', sa.Float(), nullable=True),
        sa.Column('cod', sa.Float(), nullable=True),
        sa.Column('temp', sa.Float(), nullable=True),
        sa.Column('rh', sa.Float(), nullable=True),
        sa.Column('wind_speed_kmh', sa.Float(), nullable=True),
        sa.Column('wind_deg', sa.Float(), nullable=True),
        sa.Column('noise', sa.Float(), nullable=True),
        sa.Column('co', sa.Float(), nullable=True),
        sa.Column('so2', sa.Float(), nullable=True),
        sa.Column('no2', sa.Float(), nullable=True),
        sa.Column('o3', sa.Float(), nullable=True),
        sa.Column('pm25', sa.Float(), nullable=True),
        sa.Column('pm10', sa.Float(), nullable=True),
        sa.Column('tvoc', sa.Float(), nullable=True),
        sa.Column('voltage', sa.Float(), nullable=True),
        sa.Column('current', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingest_source', sa.String(32), nullable=True),
        sa.Column('ingest_idempotency_key', sa.String(64), nullable=True, unique=True),
    )
    op.create_index("ix_sensor_data_site_ts_desc", "sensor_data", ["site_id","ts"])

    op.create_table('ingest_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_ip', sa.String(64), nullable=True),
        sa.Column('api_key_or_user_id', sa.String(128), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('error_msg', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ingest_logs_created_at', 'ingest_logs', ['created_at'])

    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('scopes', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table('auth_token_blacklist',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('jti', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
    )

def downgrade():
    op.drop_table('auth_token_blacklist')
    op.drop_table('api_keys')
    op.drop_index('ix_ingest_logs_created_at', table_name='ingest_logs')
    op.drop_table('ingest_logs')
    op.drop_index("ix_sensor_data_site_ts_desc", table_name="sensor_data")
    op.drop_table('sensor_data')
    op.drop_table('sensor_devices')
    op.drop_table('sensor_types')
    op.drop_table('viewer_sites')
    op.drop_index('ix_sites_uid', table_name='sites')
    op.drop_table('sites')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
