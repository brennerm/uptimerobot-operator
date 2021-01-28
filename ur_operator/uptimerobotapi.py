import logging
import os

import uptimerobotpy as ur

def create_uptimerobot_api():
    try:
        ur_api_key = os.environ['UPTIMEROBOT_API_KEY']
    except KeyError as e:
        logging.error(
            f'Required environment variable {e.args[0]} has not been provided')
        raise e

    uptime_robot = ur.UptimeRobot(api_key=ur_api_key)
    resp = uptime_robot.get_account_details()

    if resp['stat'] != 'ok':
        logging.error(f'failed to authenticate against UptimeRobot API')
        raise RuntimeError(resp['error'])

    return uptime_robot