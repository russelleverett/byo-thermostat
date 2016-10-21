import redis
import time
import sys

r = redis.Redis('127.0.0.1', port=6379)
# r.set('curr_temp', 72.1)


def main():
    delta = float('0.0139')
    while True:
        try:
            curr_temp = float(r.get('curr_temp'))
            ac_status = r.get('ac_status')

            # if ac_status == 'False':
            #     print 'setting temp to %s' % (curr_temp + delta)
            #     r.set('curr_temp', curr_temp + delta)
            # else:
            print 'setting temp to %s' % (curr_temp - delta)
            r.set('curr_temp', curr_temp - delta)

            time.sleep(1)
        except KeyboardInterrupt:
            print 'Exiting'
            sys.exit(1)
        except Exception, exc:
            print exc.message
            continue

if __name__ == '__main__':
    main()
