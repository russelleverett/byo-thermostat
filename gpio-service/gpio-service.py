#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import logging.handlers
import redis
import sys
import traceback
import datetime

# setup constants
SYSTEM_STATE_IDLE = 0
SYSTEM_STATE_MANUAL_FAN = 1
SYSTEM_STATE_MANUAL_AIR = 2
SYSTEM_STATE_MANUAL_HEAT = 3
SYSTEM_STATE_AUTO_AIR = 4
SYSTEM_STATE_AUTO_HEAT = 5
SYSTEM_STATE_AUTO_ENERGY_SAVING = 6
SYSTEM_STATE_ERROR = 7

COMPONENT_FAN = 2
COMPONENT_AC = 3
COMPONENT_HEAT = 17
COMPONENT_PUMP = 27

SYSTEM_MODE_AUTO = 0
SYSTEM_MODE_FAN_ONLY = 1
SYSTEM_MODE_AC = 2
SYSTEM_MODE_HEAT = 3

# setup logging
LOG_FILENAME = '/tmp/gpio-service.log'
LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when='midnight', backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class ServiceLogger(object):
    def __init__(self, _logger, level):
        self.logger = _logger
        self.level = level

    def write(self, message):
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

sys.stdout = ServiceLogger(logger, logging.INFO)
sys.stderr = ServiceLogger(logger, logging.ERROR)

# setup redis
r = redis.Redis('127.0.0.1', port=6379)

# set the startup values
r.set('system_state', SYSTEM_STATE_IDLE)
r.set('system_ac_start', None)

# setup GPIO
GPIO.setmode(GPIO.BCM)
for _pin in [2, 3, 17, 27]:
    GPIO.setup(_pin, GPIO.OUT)


def get_state_string(state):
    if state == SYSTEM_STATE_IDLE:
        return 'IDLE'
    elif state == SYSTEM_STATE_MANUAL_FAN:
        return 'MANUAL FAN'
    elif state == SYSTEM_STATE_MANUAL_AIR:
        return 'MANUAL AIR'
    elif state == SYSTEM_STATE_MANUAL_HEAT:
        return 'MANUAL HEAT'
    elif state == SYSTEM_STATE_AUTO_AIR:
        return 'AUTO AIR'
    elif state == SYSTEM_STATE_AUTO_ENERGY_SAVING:
        return 'ENERGY SAVING'
    elif state == SYSTEM_STATE_AUTO_HEAT:
        return 'AUTO HEAT'
    elif state == SYSTEM_STATE_ERROR:
        return 'ERROR'
    else:
        return 'UNKNOWN'


def get_mode_string(mode):
    if mode == SYSTEM_MODE_AUTO:
        return 'AUTO'
    elif mode == SYSTEM_MODE_FAN_ONLY:
        return 'FAN ONLY'
    elif mode == SYSTEM_MODE_AC:
        return 'AC'
    elif mode == SYSTEM_MODE_HEAT:
        return 'HEAT'
    else:
        return 'UNKNOWN'


def get_with_default(key, default):
    """ helper method to get/setup values needed in redis """
    rvalue = r.get(key)
    if rvalue is None:
        logger.info('Setting default for key: %s, %s' % (key, str(default)))
        r.set(key, default)
        rvalue = default
    return rvalue


def set_pins(fan=False, ac=False, heat=False, pump=False):
    """ enable / disable components """
    set_pin(COMPONENT_FAN, 'fan_status', fan)
    set_pin(COMPONENT_AC, 'ac_status', ac)
    set_pin(COMPONENT_HEAT, 'heat_status', heat)
    set_pin(COMPONENT_PUMP, 'hp_status', pump)


def set_pin(pin, key, value):
    """ set the pin state and update the status in redis """
    GPIO.output(pin, GPIO.LOW if value else GPIO.HIGH)
    r.set(key, value)


def set_state(mode, state, power_saving):
    """ determine what components should be on/off """
    # logger.debug('mode: %s, state: %s, temp: %s' % (get_mode_string(mode), get_state_string(state), str(temp)))
    try:
        if mode == SYSTEM_MODE_FAN_ONLY:
            set_pins(fan=True)
            return SYSTEM_STATE_MANUAL_FAN
        elif mode == SYSTEM_MODE_AC:
            set_pins(ac=True)
            return SYSTEM_STATE_MANUAL_AIR
        elif mode == SYSTEM_MODE_HEAT:
            set_pins(fan=True, pump=True, heat=True)
            return SYSTEM_STATE_MANUAL_HEAT
        else:
            threshold = int(get_with_default('system_threshold', 70))
            raw_temp, last_temp, delta_temp = sample_temperature(threshold=threshold)
            if state == SYSTEM_STATE_IDLE:
                if raw_temp >= (threshold + 2):
                    logger.debug('Temp (%s) is greater than threshold (%s): Enabling AC' % (raw_temp, (threshold + 2)))
                    set_pins(fan=True, ac=True)
                    r.set('system_ac_start', datetime.datetime.now())
                    return SYSTEM_STATE_AUTO_AIR
                elif raw_temp <= (threshold - 2):
                    logger.debug('Temp (%s) is less than threshold (%s): Enabling Heat' % (raw_temp, (threshold - 2)))
                    set_pins(fan=True, ac=True, pump=True, heat=True)
                    r.set('system_ac_start', datetime.datetime.now())
                    return SYSTEM_STATE_AUTO_HEAT
                else:
                    logger.debug('Temp (%s) is within threshold (%s +/-2): Idling' % (raw_temp, threshold))
                    return SYSTEM_STATE_IDLE
            else:
                if ((state == SYSTEM_STATE_AUTO_AIR or state == SYSTEM_STATE_AUTO_ENERGY_SAVING) and raw_temp < threshold) or (state == SYSTEM_STATE_AUTO_HEAT and raw_temp > threshold):
                    logger.debug('Temp (%s) is within threshold (%s): Idling' % (raw_temp, threshold))
                    set_pins()
                    r.set('system_ac_start', None)
                    return SYSTEM_STATE_IDLE
                elif state == SYSTEM_STATE_AUTO_ENERGY_SAVING:
                    # Lets make sure we don't hit a a negative delta
                    logger.debug('Temp (%s) is outside threshold (%s): energy saving' % (raw_temp, threshold))
                    if delta_temp < 0:
                        # turn the ac back on
                        logger.warning(
                            'Temperature delta was negative: (%s - %s) = %s'
                            % (raw_temp, last_temp, delta_temp)
                        )
                        r.set('system_ac_start', datetime.datetime.now())
                        set_pins(fan=True, ac=True)

                        # adjust the coil cutoff time
                        cutoff = int(r.get('system_coil_shutoff')) - 1
                        r.set('system_coil_shutoff', cutoff)
                        logger.warning('Setting coil shutoff time to %s minutes.' % cutoff)
                        return SYSTEM_STATE_AUTO_AIR
                    return state
                else:
                    logger.debug(
                        'Temp (%s) is outside threshold (%s): %s'
                        % (raw_temp, threshold, 'heating' if state == SYSTEM_STATE_AUTO_HEAT else 'cooling'))

                    # check for energy saving optimizations
                    if state == SYSTEM_STATE_AUTO_AIR and power_saving is True:
                        can_optimize = check_system_optimizations(threshold)
                        if can_optimize:
                            logger.debug('Turning off the AC coils.')
                            set_pins(fan=True)
                            return SYSTEM_STATE_AUTO_ENERGY_SAVING
                    return state
    except Exception, e:
        logger.error(e.message)
        set_pins()
        return SYSTEM_STATE_ERROR


def sample_temperature(threshold=70):
    system_variance = float(get_with_default('system_variance', 0))
    raw_temp = float(get_with_default('curr_temp', threshold)) + system_variance
    last_temp = float(get_with_default('last_temp', raw_temp))
    delta_temp = last_temp - raw_temp

    return raw_temp, last_temp, delta_temp


def check_system_optimizations(threshold):
    start_time = datetime.datetime.strptime(r.get('system_ac_start'), '%Y-%m-%d %H:%M:%S.%f')
    raw_temp, last_temp, delta_temp = sample_temperature(threshold=threshold)
    coil_shutoff_time = int(get_with_default('system_coil_shutoff', 10))
    system_sample_rate = int(r.get('system_sample_rate'))

    try:
        if start_time is not None:
            curr_time = datetime.datetime.now()
            elapsed = curr_time - start_time

            running_at_efficiency = (elapsed > datetime.timedelta(minutes=1))
            if running_at_efficiency:
                if delta_temp != 0:
                    temp_to_threshold = raw_temp - threshold
                    minutes_left = ((temp_to_threshold / delta_temp) * system_sample_rate) / 60
                    logger.debug(
                        'Temperature Delta: %s, Degrees to go: %s, Estimated Time: %s'
                        % (delta_temp, temp_to_threshold, minutes_left)
                    )
                    if minutes_left < coil_shutoff_time:
                        logger.debug('Less than %s minutes remaining.' % coil_shutoff_time)
                        return True
                    return False
                return False
            else:
                logger.debug('System has not yet reached efficiency. Runtime: %s' % str(elapsed))
                return False
        return False
    except Exception, optimize_exc:
        logger.error('Optimization: %s' % optimize_exc.message)
        logger.error(traceback.format_exc(1))
        return False
    finally:
        r.set('last_temp', raw_temp)


def main_loop():
    logger.info('System starting...')
    while True:
        try:
            system_on = bool(get_with_default('system_on', 1))
            system_mode = int(get_with_default('system_mode', 0))
            system_last_mode = int(get_with_default('system_last_mode', system_mode))
            system_state = int(get_with_default('system_state', 0))
            system_power_saving = bool(get_with_default('system_power_saving', 1))
            system_sample_rate = int(get_with_default('system_sample_rate', 5))

            # Check system on
            if system_on is False:
                set_pins()
                time.sleep(system_sample_rate * 2)
                continue

            # check mode change
            if system_mode != system_last_mode:
                set_pins()
                system_state = SYSTEM_STATE_IDLE
                logger.info(
                    'Changing mode from %s to %s'
                    % (get_mode_string(system_last_mode), get_mode_string(system_mode))
                )
                r.set('system_last_mode', system_mode)

            # check temps
            new_system_state = set_state(system_mode, system_state, system_power_saving)
            if new_system_state is not None:
                r.set('system_state', new_system_state)
                if new_system_state != system_state:
                    logger.info('Entering State: %s' % get_state_string(new_system_state))
            else:
                logger.warning('Unknown State Returned!!!')

            time.sleep(system_sample_rate)
        except KeyboardInterrupt:
            logger.info('Shutting down...')
            GPIO.cleanup()
            sys.exit(3)
        except Exception, inner_exc:
            logger.error(inner_exc.message)
            logger.error(traceback.format_exc(1))
            sys.exit(3)

try:
    main_loop()
except Exception, critical_error:
    logger.error('Critical Error Occurred: %s' % critical_error.message)
    logger.error(traceback.format_exc(1))
    GPIO.cleanup()
    sys.exit(3)
