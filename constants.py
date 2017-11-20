DEBUG = True
DEBUG_STREAM= True
DEBUG_QUEUE_SIZE = False

# Warning: If you change the value, rerun the program again
UNIT_TESTS = False

LANGUAGE_SENTIMENT_WORKER_SPAWN_PROCESS_IF_QSIZE_GREATER_THAN = 1000
MAX_PROCESSES_PER_WORK = 5 # One is always running as default
PROCESS_SPAWN_DELAY = 5 # In seconds

WALLY_MESSAGE = "wally"

NEW_MESSAGE_TOKEN = '\n<br/>\n'

WALLY_SEND_ALERTS_URL = "http://localhost:5478/"

TEST_SERVER_PAYLOAD_FILE ="server_test_payload.txt"

MONGO_CLIENT_URI = 'mongodb://localhost:27017/'
MONGO_CLIENT_DATABASE = 'BSDECC-database'
MONGO_CLIENT_COLLECTION = 'BSDECC-collection'
MONGO_CLIENT_DATABASE_TEST = 'BSDECC-database-test'
MONGO_CLIENT_COLLECTION_TEST = 'BSDECC-collection-test'
