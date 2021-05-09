# ex2db

__The Project:__
The program will download the daily quotation web pages which is made available
by Hong Kong Stock Exchange to the pubic via its website. The daily
summary of each listing will be extracted and be stored into a SQL database.

There is another project HKEX  do the same task but the data are stored in
csv (comma separated value) file.

1. Download the daily quotation webpage.
2. Extract summary of the day's performance of all stocks traded on the day.
3. Save the data into a SQL database. (sqlite in this case)

__The scripts:__
ex2db.py is the main script that will control the download and data extraction.  
functions.py contains all functions for the project.  

__Future work:__
1. Rework the comments to better explain the flow of the program.
2. Create more function to extract historical data for Individual security.
3. Add a data dictionary to this documentation.

Remarks:

__2021-05-09__
Initial commit, the python script can download and store the data in database.
