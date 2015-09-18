
input/CollegeScorecard_Raw_Data.zip: 
	mkdir -p input
	curl https://s3.amazonaws.com/ed-college-choice-public/CollegeScorecard_Raw_Data.zip -o input/CollegeScorecard_Raw_Data.zip
input: input/CollegeScorecard_Raw_Data.zip

working/raw/.sentinel: input/CollegeScorecard_Raw_Data.zip
	mkdir -p working
	unzip input/CollegeScorecard_Raw_Data.zip -d working/raw
	touch working/raw/.sentinel
unzip: working/raw/.sentinel

output/Scorecard.csv:
	mkdir -p output
	python scripts/scorecard.py

working/ScorecardNoHeader.csv: output/Scorecard.csv
	tail +2 $^ > $@

output/database.sqlite: working/ScorecardNoHeader.csv
	-rm output/database.sqlite
	sqlite3 -echo $@ < working/sqliteImport.sql
sqlite: output/database.sqlite

output/FullDataDocumentation.pdf: working/raw/.sentinel
	mkdir -p output
	cp -r working/raw/CollegeScorecard_Raw_Data/* output

output/hashes.txt: output/database.sqlite output/FullDataDocumentation.pdf
	-rm output/hashes.txt
	echo "Current git commit:" >> output/hashes.txt
	git rev-parse HEAD >> output/hashes.txt
	echo "\nCurrent ouput md5 hashes:" >> output/hashes.txt
	md5 output/*.csv >> output/hashes.txt
	md5 output/*.sqlite >> output/hashes.txt
hashes: output/hashes.txt

release: output/database.sqlite output/hashes.txt
	zip -r -X output/release-`date -u +'%Y-%m-%d-%H-%M-%S'` output/*

all: hashes

clean:
	-rm -rf working
	-rm -rf output
