import logging
import os

import uptimerobotpy as ur
import config


def create_uptimerobot_api():
    try:
        ur_api_key = config.Config().UPTIMEROBOT_API_KEY
    except KeyError as error:
        msg = f'Required environment variable {error.args[0]} has not been provided'
        logging.error(msg)
        raise RuntimeError(msg)

    uptime_robot = ur.UptimeRobot(api_key=ur_api_key)
    resp = uptime_robot.get_account_details()

    if resp['stat'] != 'ok':
        logging.error('failed to authenticate against UptimeRobot API')
        raise RuntimeError(resp['error'])

    return uptime_robot
