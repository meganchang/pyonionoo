import datetime
import sqlite3

import logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

from pyonionoo.parser import Router

ARGUMENTS = ['type', 'running', 'search', 'lookup', 'country', 'order', 'offset', 'limit']

SUMMARY = '/home/mchang01/HFOSS2012/out/summary'

CURSOR = None
def database():
    logger.info('Creating database.')
    global CURSOR
    
    conn = sqlite3.connect('summary.db')
    CURSOR = conn.cursor()
    CURSOR.execute('DROP TABLE IF EXISTS summary')
    CURSOR.execute('CREATE TABLE summary(id integer primary key autoincrement, type character, nickname string, fingerprint string, time_listed string, OR_port integer, dir_port integer, flags string, consensus_weight integer, country_code string, hostname string, time_lookup string)')
    
    with open(SUMMARY) as f:
        for line in f.readlines():
            router = Router(line)
            logging.debug('Adding {} to database.'.format(router.nickname))
            
            if router.is_relay:
                router_type = 'r'
            elif not router.is_relay:
                router_type = 'b'
            
            info = (router_type, router.nickname, router.fingerprint, router.is_running)
            CURSOR.execute('INSERT INTO summary VALUES (null,?,?,?,?)', info)
        conn.commit()
        # CURSOR.close()

    logging.info('Finished creating database.')

def get_summary_routers(arguments, database):
    routers = []
    return_relays, return_bridges = True, True
    hex_fingerprint, running_filter = None, None
    return_type, return_country, return_search = False, False, False
    relay_timestamp = datetime.datetime(1900, 1, 1, 1, 0)
    bridge_timestamp = datetime.datetime(1900, 1, 1, 1, 0)
    for key, values in arguments.iteritems():
        if key in ARGUMENTS:
            if key == "running":
                for value in values:
                    running_filter = value
            if key == "type":
                return_type = True
                for value in values:
                    if value == "relay":
                        return_bridges = False
                    if value == "bridge":
                        return_relays = False
            if key == "lookup":
                for value in values:
                    hex_fingerprint = value
            if key == "country":
                for value in values:
                    return_country = True
                    country_code = value
            if key == "search":
                for value in values:
                    return_search = True
                    search_input = value            

    filtered_relays, filtered_bridges = [], []
    for row in CURSOR.execute('SELECT type, nickname, fingerprint, running FROM summary'):
        if row[0] == 'r' and return_relays:
            dest = filtered_relays
            time_dest = relay_timestamp
        elif row[0] == 'b' and return_bridges:
            dest = filtered_bridges
            time_dest = bridge_timestamp
        else:
            continue
        if return_type:
            dest.append(row)
        elif running_filter:
            if running_filter.title() == 'True':
                running_filter = True
            elif running_filter.title() == 'False':
                running_filter = False
            else: raise ValueError('Invalid boolean.')
            if row[3] == running_filter:
                dest.append(row)
        elif hex_fingerprint:
            if hex_fingerprint == row[2]:
                dest.append(row)
                break
        #elif return_country:
        #        if 
        elif return_search:
            if search_input in row[1]:
                dest.append(row)
            if search_input in row[2]:
                dest.append(row)
            # ADDRESS SEARCH
        else:
            dest.append(row)

    total_routers = (filtered_relays, filtered_bridges)
    return total_routers

#TODO: TIMESTAMP?? COUNTRY?? ADDRESS SEARCH??