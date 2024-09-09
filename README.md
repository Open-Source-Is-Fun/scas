# scas
Simple Crypto Accounting Script

This script fetches data from currently snowscan to gather information about wallet transactions to a specific wallet and put the data into a .ods file (Open Document format). Works for both Ethereum and Avalanche tokens. This is handy for keeping accounting records received in crypto currencies.

 This is a simple script that can be used as a baseline for other projects; a crypto accounting plugin for wordpress for example.

 Pre-requisites

 You need to have python installed with following dependencies:
 - pip install pytz
 - pip install pandas
 - pip install requests
 - pip install datetime
 - pip install tox

Initial Configuration:

Step 1: You have to edit following lines inside the python script:
- 211: address = "0x..." # The wallet address of interest
- 224: directory_path = "/path/to/file/" # Path where you want to put the .ods file

Step 2: Then you have to move the file Wallets.json to the directory where you want to store your .ods file. Then you can add MemberIDs with corresponding wallet addressess. This is however entirely up to you.

Step 3: Then run the script (Simple_Crypto_Accounting.py)

Notes:

When you run the script for the first time, a file called last_reference.json is created in the file directory. If you delete the .ods file, remember to also delete the last_reference.json aswell. Otherwise you may end up with an empty file next time you run the script.

The last_reference.json contains a timestamp of the last transaction recorderd when the script was run. This can be useful to manipulate for testing.

Known Caveat:

If a wallet address have more than a 100 transactions since the last run, you may end up missing some transactions. This is because the snowscan API have a limit of maximum 100 transactions per API call. The script has not been configured to support multiple API calls.