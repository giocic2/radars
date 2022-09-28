import json
from datetime import datetime
import shutil

def main():

    # Load settings from *.json file.
    with open('unipg_prototype/settings.json') as f:
        settings = json.load(f)
    f.close()

    # Save current *.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_filename = "./sense2gol_pizero/raw_samples/" + timestamp + ".json"
    shutil.copyfile("./sense2gol_pizero/settings.json",json_filename)

if __name__ == "__main__":
    main()