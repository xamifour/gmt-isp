# Admin related settings
# These settings control details of the administration interface of openwisp-radius.
OPENWISP_RADIUS_EDITABLE_ACCOUNTING = False
OPENWISP_RADIUS_EDITABLE_POSTAUTH = False
OPENWISP_RADIUS_GROUPCHECK_ADMIN = False
OPENWISP_RADIUS_GROUPREPLY_ADMIN = False
OPENWISP_RADIUS_USERGROUP_ADMIN = False

# Model related settings
# These settings control details of the openwisp-radius model classes.
OPENWISP_RADIUS_DEFAULT_SECRET_FORMAT = 'NT-Password'
OPENWISP_RADIUS_DISABLED_SECRET_FORMATS = []
OPENWISP_RADIUS_BATCH_DEFAULT_PASSWORD_LENGTH = 8
OPENWISP_RADIUS_BATCH_DELETE_EXPIRED = 18
OPENWISP_RADIUS_EXTRA_NAS_TYPES = tuple()
OPENWISP_RADIUS_FREERADIUS_ALLOWED_HOSTS = []
OPENWISP_RADIUS_MAX_CSV_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
OPENWISP_RADIUS_PRIVATE_STORAGE_INSTANCE = 'openwisp_radius.private_storage.storage.private_file_system_storage'
OPENWISP_RADIUS_CALLED_STATION_IDS = {}
OPENWISP_RADIUS_CONVERT_CALLED_STATION_ON_CREATE = False
OPENWISP_RADIUS_OPENVPN_DATETIME_FORMAT = u'%a %b %d %H:%M:%S %Y'

# API and user token related settings
# These settings control details related to the API and the radius user token.
OPENWISP_RADIUS_API_URLCONF = None
OPENWISP_RADIUS_API_BASEURL = '/'
OPENWISP_RADIUS_API = True
OPENWISP_RADIUS_DISPOSABLE_RADIUS_USER_TOKEN = True
OPENWISP_RADIUS_API_AUTHORIZE_REJECT = False
OPENWISP_RADIUS_API_ACCOUNTING_AUTO_GROUP = True
OPENWISP_RADIUS_ALLOWED_MOBILE_PREFIXES = []
OPENWISP_RADIUS_OPTIONAL_REGISTRATION_FIELDS = {
    'first_name': 'disabled',
    'last_name': 'disabled',
    'birth_date': 'disabled',
    'location': 'disabled',
}
OPENWISP_RADIUS_PASSWORD_RESET_URLS = {
    'default': 'https://{site}/{organization}/password/reset/confirm/{uid}/{token}'
}
OPENWISP_RADIUS_REGISTRATION_API_ENABLED = True
OPENWISP_RADIUS_SMS_VERIFICATION_ENABLED = False
OPENWISP_RADIUS_NEEDS_IDENTITY_VERIFICATION = False

# Email related settings
# Emails can be sent to users whose usernames or passwords have been auto-generated. 
# The content of these emails can be customized with the settings explained below.
OPENWISP_RADIUS_BATCH_MAIL_SUBJECT = 'Credentials'
OPENWISP_RADIUS_BATCH_MAIL_MESSAGE = 'username: {}, password: {}'
OPENWISP_RADIUS_BATCH_MAIL_SENDER = 'settings.DEFAULT_FROM_EMAIL'

# counters
OPENWISP_RADIUS_COUNTERS = [
    # default counters for PostgreSQL, may be removed if not needed
    'openwisp_radius.counters.postgresql.daily_counter.DailyCounter',
    'openwisp_radius.counters.postgresql.daily_traffic_counter.DailyTrafficCounter',
    # custom counters
    # 'myproject.counters.CustomCounter1',
    # 'myproject.counters.CustomCounter2',
    ]
OPENWISP_RADIUS_TRAFFIC_COUNTER_CHECK_NAME = 'Max-Daily-Session-Traffic'
# OPENWISP_RADIUS_TRAFFIC_COUNTER_REPLY_NAME = 'ChilliSpot-Max-Total-Octets'
OPENWISP_RADIUS_TRAFFIC_COUNTER_REPLY_NAME = 'Mikrotik-Max-Total-Octets' # for Mikrotik
OPENWISP_RADIUS_SOCIAL_REGISTRATION_ENABLED = False

# SAML related settings
# The following settings are related to the SAML feature.
OPENWISP_RADIUS_SAML_REGISTRATION_ENABLED = False
OPENWISP_RADIUS_SAML_REGISTRATION_METHOD_LABEL = 'Single Sign-On (SAML)'
OPENWISP_RADIUS_SAML_IS_VERIFIED = False
OPENWISP_RADIUS_SAML_UPDATES_PRE_EXISTING_USERNAME = False

# SMS token related settings
# These settings allow to control aspects and limitations of the SMS tokens which are sent 
# to users for the purpose of verifying their mobile phone number.
# These settings are applicable only when SMS verification is enabled.
SENDSMS_BACKEND = '<python_path_to_sms_backend>'
OPENWISP_RADIUS_SMS_TOKEN_DEFAULT_VALIDITY = 30
OPENWISP_RADIUS_SMS_TOKEN_LENGTH = 6
OPENWISP_RADIUS_SMS_TOKEN_HASH_ALGORITHM = 'sha256'
OPENWISP_RADIUS_SMS_TOKEN_MAX_ATTEMPTS = 5
OPENWISP_RADIUS_SMS_TOKEN_MAX_USER_DAILY = 5
OPENWISP_RADIUS_SMS_TOKEN_MAX_IP_DAILY = 999