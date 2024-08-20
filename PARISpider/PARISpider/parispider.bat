@echo off
echo "Running parispider.bat" >> C:\Users\bradc\Downloads\historypari.txt


REM Run the Spider
set today=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set jsonFile=PARISpider-%today%.json
set destinationFolder=C:\Users\bradc\PycharmProjects\Work\PARISpider\PARISpider\spiders\outputs
echo "Today's date is %today%" >> C:\Users\bradc\Downloads\historypari.txt

pipenv run scrapy runspider .\spiders\PARISpider.py -O "%jsonFile%"

for %%A in ("%jsonFile%") do set "filesize=%%~zA"
if %filesize% GTR 0 (
  echo "PARISpider produced %filesize% bytes to import" >> C:\Users\bradc\Downloads\historypari.txt
  move "%jsonFile%" "%destinationFolder%"
)
echo "Finished." >> C:\Users\bradc\Downloads\historypari.txt
