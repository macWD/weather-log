# weather-log

Python module which contains functions to fetch data from Ambient Weather and
PurpleAir APIs. The *main()* function logs the Ambient Weather data in a CSV file
once per minute (maximum sample rate allowed).

You must edit keys.py and replace the Ambient Weather "app_key" and the PurpleAir "read_key" values with your own personal keys. Optionally, you can store these in a file called "localkeys.py" so that pulls from the archive don't cause conflicts.

## Functions:
- **main()** Reads Ambient Weather data once per minute and writes it in a CSV file
- **get_AW_SensorData(*station_key*)** Returns get containing JSON of JSONs from Ambient Weather station *station_key* using your app_key
- **get_PA_SensorData(*sensor_index*)** Returns get containing JSON of air quality data from PurpleAir station *sensor_index* using your read_key

Higher-level functions to deal with this data have not been written. They will be broken out of  *main()* at a later date.
