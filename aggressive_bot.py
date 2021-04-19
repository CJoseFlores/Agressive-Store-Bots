import argparse
import configparser
import sys
from twilio.rest import Client

# Constant Strings
from amazon_bot import AmazonBot
from amazon_credentials import AmazonCredentials
from twilio_client_wrapper import TwilioClientWrapper

amazon_config_key = 'amazon-config'
twilio_config_key = 'twilio-config'
firefox_config_key = 'firefox-config'
amazon_bot_type_val = 'amazon'
best_buy_bot_type_val = 'best-buy'
new_egg_bot_type_val = 'newegg'

if __name__ == '__main__':
    # Load arguments
    parser = argparse.ArgumentParser(description='Bot that buys items from amazon storefronts.')
    parser.add_argument('-f', '--file', dest='file_path', default='bot-config.ini', help='The path to the bot '
                                                                                         'configuration file ('
                                                                                         'defaults to relative file: '
                                                                                         'bot-config.ini)')
    parser.add_argument('-b',
                        '--bot-type',
                        dest='bot_type',
                        default='amazon',
                        help="Choose the type of bot you want to use. Supported values: ['"
                             + amazon_bot_type_val + ", '" + best_buy_bot_type_val + "', '"
                             + new_egg_bot_type_val + "']. Defaults to 'amazon'. ")
    config_file_path = parser.parse_args().file_path

    # Load configuration file
    try:
        with open(config_file_path, 'r+') as f:
            config_file = f.read()

        config = configparser.ConfigParser()
        config.read(config_file_path, encoding='utf-8-sig')
    except configparser.MissingSectionHeaderError:
        print("There was an error loading the config file. Make sure your headers are enclosed in brackets '[]'. "
              "Exiting...")
        sys.exit(1)
    except FileNotFoundError:
        print("Could not find or open file referenced by path: " + config_file_path)
        sys.exit(1)

    # Parse the twilio configuration
    if twilio_config_key in config:
        try:
            twilio_client_wrapper = TwilioClientWrapper(to_number=config[twilio_config_key]['toNumber'],
                                                        from_number=config[twilio_config_key]['fromNumber'],
                                                        client=Client(config[twilio_config_key]['accountSid'],
                                                                      config[twilio_config_key]['authToken']))
        except KeyError:
            print("Missing one or all of the config keywords from the [" + twilio_config_key + "] config section:"
                  + "'toNumber', 'fromNumber', 'accountSid', 'authToken'.")
            sys.exit(1)
    else:
        print("Could not find the [" + twilio_config_key + "] config section. Exiting...")
        sys.exit(1)

        # Parse the firefox configuration
    if firefox_config_key in config:
        try:
            # Encode the profile path with unicode-escape to escape windows back slashes in the bath.
            firefox_profile_path = config[firefox_config_key]['profilePath'].encode('unicode-escape').decode()
        except KeyError:
            print("Missing config keyword 'profilePath' from the config section [" + firefox_config_key + "].")
            sys.exit(1)
    else:
        print("Could not find the [" + firefox_config_key + "] config section. Exiting...")

    # Launch one of the bot types.
    if parser.parse_args().bot_type == amazon_bot_type_val:
        print("Launching the '" + amazon_bot_type_val + "' bot type.")
        # Parse the amazon configuration
        if amazon_config_key in config:
            try:
                amazon_credentials = AmazonCredentials(config[amazon_config_key]['username'],
                                                       config[amazon_config_key]['password'])
                store_url = config[amazon_config_key]['storeUrl']
            except KeyError:
                print("Missing 'username', 'password' or 'storeUrl' keywords from the [" + amazon_config_key
                      + "] config section.")
                sys.exit(1)
        else:
            print("Could not find the [" + amazon_config_key + "] config section. Exiting...")
            sys.exit(1)

        # Launch the amazon bot.
        amazon_bot = AmazonBot(twilio_client_wrapper, firefox_profile_path, amazon_credentials, store_url)
        #amazon_bot.login_attempt()
        #amazon_bot.finding_cards()