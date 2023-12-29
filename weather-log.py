import requests
import json
import os
import sys
import getopt
import datetime
import time

# your keys are in this module
try:
    # you can create a local module and not mess with the git archive
    import localkeys as keys
    print('Using local keys')
except:
    # keys.py is the file from git
    import keys

#some data we grabbed from an actual PurpleAir parse of '?fields=pm2.5'
FAKE_DATA = {
                "api_version" : "V1.0.11-0.0.46",
                "time_stamp" : 1686582597,
                "data_time_stamp" : 1686582557,
                "sensor" : {
                                "sensor_index" : 105160,
                                "pm2.5" : 44.1
                            }
            }

# This function calculates the AQI for 2.5µm airborne particulate matter
# Ref: Marcus Hylton https://forum.airnowtech.org/t/the-aqi-equation/169
# Arg: PM2.5 concentration in micrograms per cubic centimeter
def aqi_2pm5(concentration):
    ug_HI_POINTS  = (12.0, 35.4, 55.4, 150.4, 250.4, 500.4)
    AQI_HI_POINTS = (  50,  100,  150,   200,   300, 500  )
    # the standard AQI names (except as indicated)
    AQI_NAMES = (
        'Good',
        'Moderate',
        'Unhealthy for Some',
        'Unhealthy',
        'VERY UNHEALTHY',
        'HAZARDOUS')
    # console ESC sequences to set BG to the standard AQI colors
    AQI_COLORS = (
        '\033[92m', # bright green
        '\033[93m', # yellow
        '\033[33m', # orange
        '\033[91m', # bright red
        '\033[35m', # purple
        '\033[95m'  # bright purple
    )

    i = 0       # lowest tuple index pointer
    aqi_lo = 0  # lowest air quality index
    ug_lo = 0   # lowest particulate concentration (theoretical)
    ug_conc = float(int((concentration * 10)) / 10) # truncate to 0.1 μg/m³
    AQ_index = {
        'index': -1,
        'descr': 'Undefined',
        'color': '\033[0m',
    }

    # boundary check for the AQI equation
    if ug_conc > ug_HI_POINTS[5]:
        # concentration is a better fake value than the highest AQI
        AQ_index['index'] = int(ug_conc)
        AQ_index['descr'] = 'VERY HAZARDOUS'
        AQ_index['color'] = AQI_COLORS[5]
        return AQ_index

    ### find the proper high points ###
    for ug_hi in ug_HI_POINTS:
        # stop if we have the proper index for the high point tuples
        if ug_conc <= ug_hi:
            break
        # advance the index for next pass
        i = i+1

    ### CALCULATE THE AQI ###
    # load the other constants (ug_hi already loaded)
    aqi_hi = AQI_HI_POINTS[i]
    if i > 0:
        ug_lo  = ug_HI_POINTS[i-1] + 0.1
        aqi_lo = AQI_HI_POINTS[i-1] + 1
    # EQUATION #
    AQ_index['index'] = int( (aqi_hi - aqi_lo) / (ug_hi - ug_lo) * (ug_conc - ug_lo) + aqi_lo )

   # text description and color of the result
    AQ_index['descr'] = AQI_COLORS[i] + AQI_NAMES[i] + '\033[0m'
    AQ_index['color'] = AQI_COLORS[i]

    # return the AQI dict
    return AQ_index

# This function collects data for the specified public PurpleAir sensor.
def get_PA_SensorData(sensor_index):
    # build the url for our data request
    my_url = 'https://api.purpleair.com/v1/sensors/' + str(sensor_index) + '?fields=' + keys.PA['fields']
    # put our individual API read key in he headers
    my_headers = {'X-API-Key':keys.PA['read_key']}
    # send the request for data and store response into r.
    r = requests.get(my_url, headers=my_headers)
    return r

# This function collects data for the specified Ambient Weather station.
def get_AW_SensorData(station_key):
    # build the url for our data request
    aw_url = 'https://rt.ambientweather.net/v1/devices?applicationKey=' + keys.AW['app_key'] + '&apiKey=' + station_key
    # send the request for data and store response into r.
    r = requests.get(aw_url)
    return r

def console(aq, aq_get_status, wx, wx_get_status):
    #clear the console
    #os.system('clear')
    if wx_get_status < 400:    # ensure call to the AW API didn't crash
        # Print date and time for weather data.
        print('\033[34m' + str(datetime.datetime.fromtimestamp(wx['lastData']['dateutc'])) + '\033[0m')
        print('Temperature: ' + str(wx['lastData']['tempf']) + '°F')
        dew_point = int(wx['lastData']['dewPoint'] * 10) / 10     # single decimal point
        print('Dew Point:   ' + str(dew_point) + '°F')
        feels_like = int(wx['lastData']['feelsLike'] * 10) /10    # single decimal point
        print('Feels Like:  ' + str(feels_like) + '°F')
    else:   # API ERROR
        print('Weather Error: ' + str(wx_get_status))
        if wx_get_status == 401:
            print('Check AW app key')

    # output PM 2.5 data
    if aq_get_status < 400:    # ensure call to the PA API didn't crash
        # Print date and time for air quality data.
        print('\033[34m' + str(datetime.datetime.fromtimestamp(aq['time_stamp'])) + '\033[0m')
        # display raw 2.5μm concentration data
        PM25 = aq['sensor']['pm2.5']
        print('PM2.5μ: ' + str(PM25) + ' μg/m³')
        # calculate AQI from the raw data
        aqi_calc = aqi_2pm5(PM25)
        # display AQI number
        print('        ' + str(aqi_calc['index']) + ' AQI')
        #display AQI description without falling off the bottom line of the LCD
        sys.stdout.write(aqi_calc['color'] + aqi_calc['descr'] + '\033[0m')
        sys.stdout.flush()
    else:   # API ERROR
        print('AQ Error: ' + str(aq_get_status))
        if aq_get_status == 403:
            print('Check PA read key')

# MAIN PROGRAM
def main(arg_list):
    # parse the arg list
    ARG      =  'h'
    ARGUMENT = ['help']
    HELPSTRING = ['WEATHER STATION',
                  '  usage: aqi.py [-h]',
                  '  optional arguments:',
                  '    -h, --help          Show this help message.']
    try:
        opts, args = getopt.getopt(arg_list,ARG,ARGUMENT)
    except getopt.GetoptError:
        print('Options parse error.')
        for s in HELPSTRING:
            print(s)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            for s in HELPSTRING:
                print(s)
            return
        else:
            print('Invalid argument ' + opt + '. Use -h option.')

    # load filespec
    file_date = datetime.datetime.now()
    filespec = file_date.strftime('%Y%m%d_%H%M%S') + '.csv'
    # the get() fails if we call too soon after boot so pause
    time.sleep(10)

    while True:
        # pull data for our station from ambient weather cloud
        wx_sensor_data = get_AW_SensorData(keys.AW['api_key'])      # request JSON
        wx_JSON = wx_sensor_data.content
        if wx_sensor_data.status_code < 400:    # load dict if no "get" error
            # fix some weird stuff in the content
            wx_dict = json.loads(wx_JSON)[0]    # content is a list of JSONs
            # date is 1000x too large
            wx_dict['lastData']['dateutc'] = wx_dict['lastData']['dateutc']/1000

            # Data Logging
            csv_header = ''
            csv_data = ''
            for z in wx_dict['lastData']:
                csv_header = csv_header + str(z)
                csv_data = csv_data + str(wx_dict['lastData'][z])
                if z != 'date':
                    csv_data = csv_data + ','
                    csv_header = csv_header + ','
                else:
                    csv_data = csv_data + '\x0a'
                    csv_header = csv_header + '\x0a'
            if os.path.exists(filespec):
                f = open(filespec,"a")
            else:
                f = open(filespec,"a")
                f.write(csv_header)
            f.write(csv_data)
            f.close()

        else:
            wx_dict = {}

        # sleep for a minute between AW samples
        time.sleep(60)

    # main loop ends here

    return 1    #### EXIT main() -- ERROR ####

if __name__ == '__main__':
    main(sys.argv[1:])
