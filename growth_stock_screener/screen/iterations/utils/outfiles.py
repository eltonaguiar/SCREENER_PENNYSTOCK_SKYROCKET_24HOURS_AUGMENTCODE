import pandas as pd
import os


def open_outfile(filename: str) -> pd.DataFrame:
    """Open json outfile data as pandas dataframe."""
    json_path = os.path.join(
        os.getcwd(), "json", f"{filename}.json"
    )
    df = pd.read_json(json_path)
    return df


def create_outfile(data: pd.DataFrame, filename: str) -> None:
    """Serialize a pandas dataframe in JSON format and save in the json directory."""
    serialized_json = data.to_json()
    json_dir = os.path.join(os.getcwd(), "json")
    outfile_path = os.path.join(json_dir, f"{filename}.json")

    # Create the json directory if it doesn't exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    with open(outfile_path, "w") as outfile:
        outfile.write(serialized_json)
