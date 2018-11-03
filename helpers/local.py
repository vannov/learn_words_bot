import os


def set_env_viariables():
    """ Sets environment variables for the word bot when running on a local machine """

    # TODO: Set environment variables when running locally.
    # !!! DO NOT COMMIT YOUR REAL TOKENS ANS KEYS TO PUBLIC REPOSITORIES !!!

    # Telegram bot token
    os.environ['TELEGRAM_BOT_TOKEN'] = ''

    # Bot webhook server URL
    os.environ['WEBHOOK_URL'] = ''

    # Redis storage URL
    os.environ['REDIS_URL'] = ''

    # Words API token (see https://www.wordsapi.com/)
    os.environ['MASHAPE_KEY'] = ''
