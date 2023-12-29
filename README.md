weather-log.py
Python program which contains functions to fetch data from Ambient Weather and
PurpleAir APIs. The main() function logs the Ambient Weather data in a CSV file
once per minute (maximum sample rate allowed). PurpleAir data is not used, but
the function works. You must edit keys.py and replace the Ambient Weather
"app_key" and the PurpleAir "read_key" values with your own personal keys.
Optionally, you can store these in a file called "localkeys.py" so that pulls
from the archive don't cause conflicts.
