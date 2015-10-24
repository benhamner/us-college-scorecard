
input/CollegeScorecard_Raw_Data.zip: 
	mkdir -p input
	curl https://s3.amazonaws.com/ed-college-choice-public/CollegeScorecard_Raw_Data.zip -o input/CollegeScorecard_Raw_Data.zip
input: input/CollegeScorecard_Raw_Data.zip

working/.sentinel: input/CollegeScorecard_Raw_Data.zip
	mkdir -p working
	unzip input/CollegeScorecard_Raw_Data.zip -d working
	touch working/.sentinel
unzip: working/.sentinel

output/Scorecard.csv: working/.sentinel
	mkdir -p output
	python scripts/scorecard.py
scorecard: output/Scorecard.csv

output/FullDataDocumentation.pdf: working/.sentinel
	mkdir -p output
	cp -r working/CollegeScorecard_Raw_Data/* output

output/hashes.txt: output/Scorecard.csv output/FullDataDocumentation.pdf
	-rm output/hashes.txt
	echo "Current git commit:" >> output/hashes.txt
	git rev-parse HEAD >> output/hashes.txt
	echo "\nCurrent ouput md5 hashes:" >> output/hashes.txt
	md5 output/*.csv >> output/hashes.txt
	md5 output/*.sqlite >> output/hashes.txt
hashes: output/hashes.txt

release: output/Scorecard.csv output/hashes.txt
	zip -r -X output/release-`date -u +'%Y-%m-%d-%H-%M-%S'` output/*

all: hashes

clean:
	-rm -rf working
	-rm -rf output
