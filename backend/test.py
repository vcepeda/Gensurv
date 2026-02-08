import json

json_str = '{"Illumina":["Sample_001.fastq","Sample_002.fastq"]}'
parsed_json = json.loads(json_str)  # Should work without errors
print(parsed_json)

