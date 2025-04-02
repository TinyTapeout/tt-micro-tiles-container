import re
import requests
import os
import zipfile
import shutil
import gdstk
import yaml



GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def download_tt_submission_artifact(repo_url, output_filename="tt_submission.zip"):
    """
    Downloads the latest GitHub Actions artifact named 'tt_submission' from a public repository.
    
    Parameters:
        repo_url (str): The GitHub repository URL (e.g., "https://github.com/user/repo").
        output_filename (str): The filename to save the artifact as (default: "tt_submission.zip").
    
    Returns:
        bool: True if the artifact was successfully downloaded, False otherwise.
    """
    # Extract owner and repo name from URL
    match = re.match(r"https://github.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        print("Invalid GitHub repository URL.")
        return False
    
    owner, repo = match.groups()

    # Get the latest workflow runs
    runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    runs_response = requests.get(runs_url, headers=HEADERS)
    if runs_response.status_code != 200:
        print("Failed to fetch workflow runs.")
        return False

    runs = runs_response.json().get("workflow_runs", [])
    if not runs:
        print("No workflow runs found.")
        return False

    # Iterate over workflow runs to find the artifact
    for run in runs:
        artifacts_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run['id']}/artifacts"
        artifacts_response = requests.get(artifacts_url, headers=HEADERS)
        
        if artifacts_response.status_code != 200:
            continue
        
        artifacts = artifacts_response.json().get("artifacts", [])
        for artifact in artifacts:
            if artifact["name"] == "tt_submission":
                print(f"Found artifact: {artifact['name']} (ID: {artifact['id']})")
                
                # Download the artifact
                download_url = artifact["archive_download_url"]
                artifact_response = requests.get(download_url, headers=HEADERS, stream=True)
                
                if artifact_response.status_code == 200:
                    with open(output_filename, "wb") as file:
                        for chunk in artifact_response.iter_content(chunk_size=8192):
                            file.write(chunk)
                    print(f"Downloaded artifact to {output_filename}")
                    return True
                else:
                    print("Failed to download artifact.")
                    print(f"HTTP {artifact_response.status_code}: {artifact_response.text}")
                    return False
    
    print("No 'tt_submission' artifact found.")
    return False

def unzip_tt_submission_artifact(input_filename="tt_submission.zip", output_dir="tt_submission"):
    """
    Unzips the 'tt_submission' artifact into a directory.
    
    Parameters:
        input_filename (str): The filename of the artifact to unzip (default: "tt_submission.zip").
        output_dir (str): The directory to unzip the artifact into (default: "tt_submission").
    
    Returns:
        bool: True if the artifact was successfully unzipped, False otherwise.
    """
    
    
    if not os.path.exists(input_filename):
        print(f"File not found: {input_filename}")
        return False
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with zipfile.ZipFile(input_filename, "r") as zip_ref:
        zip_ref.extractall(output_dir)
    
    print(f"Unzipped artifact to {output_dir}")

def grab_relevant_submission_files(search_directory, output_directory, new_basename):
    """
    Grab the GDS, LEF, and Verilog (.v) files from the search directory and copy them to the output directory.
    Rename the files to have the specified new_basename while keeping their original extensions.

    :param search_directory: Directory to search for relevant files.
    :param output_directory: Directory where the files should be copied.
    :param new_basename: New base name for the copied files.
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)  # Ensure output directory exists

    valid_extensions = {".lef", ".gds", ".v"}

    for file in os.listdir(search_directory):
        file_path = os.path.join(search_directory, file)
        file_ext = os.path.splitext(file)[1]

        if file_ext in valid_extensions:
            print(f"Found relevant file: {file}")
            new_file = os.path.join(output_directory, f"{new_basename}{file_ext}")

            # Copy instead of move to preserve the original files
            shutil.copy2(file_path, new_file)
            print(f"Copied {file} to {new_file}")

def clean_up(directory, zip_file):
    if os.path.exists(zip_file):
        os.remove(zip_file)
    if os.path.exists(directory):
        shutil.rmtree(directory)

def rename_top_cell(input_gds: str, output_gds: str, new_top_name: str):
    """
    Renames the top cell of a GDSII file and saves the modified file.

    Parameters:
    input_gds (str): Path to the input GDSII file.
    output_gds (str): Path to save the modified GDSII file.
    new_top_name (str): New name for the top cell.

    Returns:
    None
    """
    # Load the GDS file
    lib = gdstk.read_gds(input_gds)

    # Identify the top cell (the one not referenced by any other cell)
    all_cells = {cell.name: cell for cell in lib.cells}
    referenced_cells = {ref.cell.name for cell in lib.cells for ref in cell.references if isinstance(ref, gdstk.Reference)}

    top_cells = [cell for name, cell in all_cells.items() if name not in referenced_cells]

    if not top_cells:
        raise ValueError("No top cell found in the GDS file.")

    if len(top_cells) > 1:
        print("Warning: Multiple top cells found. Renaming the first one detected.")

    top_cell = top_cells[0]
    old_top_name = top_cell.name

    # Rename the top cell
    top_cell.name = new_top_name

    # Create a new GDS library and add all cells to it
    new_lib = gdstk.Library(name=lib.name)
    for cell in lib.cells:
        new_lib.add(cell)

    # Save the modified GDS file
    new_lib.write_gds(output_gds)

    print(f"Renamed top cell '{old_top_name}' to '{new_top_name}' and saved to '{output_gds}'.")

def rename_verilog_module(input_verilog_file, output_verilog_file, new_module_name):
    """
    Renames the module in a Verilog file and saves the modified file.

    Parameters:
    input_verilog_file (str): Path to the input Verilog file.
    output_verilog_file (str): Path to save the modified Verilog file.
    new_module_name (str): New name for the module.

    Returns:
    None
    """
    with open(input_verilog_file, "r") as file:
        lines = file.readlines()

    with open(output_verilog_file, "w") as file:
        for line in lines:
            if line.strip().startswith("module "):
                line = re.sub(r"module\s+\w+", f"module {new_module_name}", line)
            file.write(line)

    print(f"Renamed module in '{input_verilog_file}' to '{new_module_name}' and saved to '{output_verilog_file}'.")

def update_lef_file(input_lef_file,output_lef_file, new_name):
    """
        Update the LEF file to have the new name for the cell.
    """
    with open(input_lef_file, "r") as file:
        lines = file.readlines()

    old_name = ""
    with open(output_lef_file, "w") as file:
        for line in lines:
            if line.strip().startswith("MACRO "):
                old_name = line.split()[1]
                line = re.sub(r"MACRO\s+\w+", f"MACRO {new_name}", line)
                
            if line.strip().startswith("END "):
                if line.split()[1] == old_name:
                    line = re.sub(r"END\s+\w+", f"END {new_name}", line)
            if line.strip().startswith("FOREIGN"):
                if line.split()[1] == old_name:
                    line = re.sub(r"FOREIGN\s+\w+", f"FOREIGN {new_name}", line)
            file.write(line)

    print(f"Renamed module in '{input_lef_file}' to '{new_name}' and saved to '{output_lef_file}'.")

def extract_micro_tiles(info_yaml = "../info.yaml"):
    """
    Extract the micro tiles from the info.yaml file.
    """
    with open(info_yaml, "r") as file:
        info = yaml.safe_load(file)
    micro_tiles = info.get("project", {}).get("micro_tiles", [])
    return micro_tiles

giturl_1, giturl_2, giturl_3, giturl_4 = extract_micro_tiles()
top_gds_name1 = "tt_um_micro1"
top_gds_name2 = "tt_um_micro2"
top_gds_name3 = "tt_um_micro3"
top_gds_name4 = "tt_um_micro4"

for i, (giturl, top_gds_name) in enumerate(zip(
    [giturl_1, giturl_2, giturl_3, giturl_4],
    [top_gds_name1, top_gds_name2, top_gds_name3, top_gds_name4]
)):
    zip_filename = f"{top_gds_name}.zip"
    dir_name = top_gds_name

    download_tt_submission_artifact(giturl, zip_filename)
    unzip_tt_submission_artifact(zip_filename, dir_name)
    grab_relevant_submission_files(f"{dir_name}/tt_submission", ".", top_gds_name)
    rename_top_cell(f"{top_gds_name}.gds", f"{top_gds_name}.gds", top_gds_name)
    update_lef_file(f"{top_gds_name}.lef", f"{top_gds_name}.lef", top_gds_name)
    rename_verilog_module(f"{top_gds_name}.v", f"{top_gds_name}.v", top_gds_name)
    clean_up(dir_name, zip_filename)
