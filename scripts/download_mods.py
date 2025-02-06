#!/usr/bin/env python3
import os
import json
import requests

def main():
    # Determine paths relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Expect the manifest.json file to be in the same directory as the script.
    manifest_path = os.path.join(script_dir, "manifest.json")
    # The mods folder is in ../data/mods relative to scripts/
    mods_dir = os.path.join(script_dir, "..", "data", "mods")

    print("Using manifest file:", manifest_path)
    print("Mods directory:", mods_dir)

    # Ensure the mods directory exists.
    os.makedirs(mods_dir, exist_ok=True)

    # Load the manifest file
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print("Error loading manifest file:", e)
        return

    # Ensure the manifest contains a "files" key
    if "files" not in manifest:
        print("Error: Manifest file does not contain a 'files' key.")
        return

    # Build a dictionary of mods from the manifest.
    # If 'fileName' is missing, we generate one using the projectID and fileID.
    mods_in_manifest = {}
    for mod in manifest["files"]:
        project_id = mod.get("projectID") or mod.get("projectId")
        file_id = mod.get("fileID") or mod.get("fileId")
        # Generate a default file name if 'fileName' is not provided.
        file_name = mod.get("fileName") or f"{project_id}-{file_id}.jar"

        # Skip the mod entry only if project_id or file_id are missing.
        if not project_id or not file_id:
            print("Skipping mod entry (missing projectID or fileID):", mod)
            continue

        mods_in_manifest[file_name] = (project_id, file_id)

    print(f"Found {len(mods_in_manifest)} mod entries in the manifest.")

    # List current mod files in the mods folder (we expect .jar files)
    current_mod_files = {f for f in os.listdir(mods_dir) if f.lower().endswith(".jar")}

    # Remove any mods in the mods folder that are not in the manifest.
    for mod_file in current_mod_files:
        if mod_file not in mods_in_manifest:
            file_path = os.path.join(mods_dir, mod_file)
            try:
                print(f"Removing outdated mod: {mod_file}")
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {mod_file}: {e}")

    # Download mods that are listed in the manifest and missing from the mods folder.
    for file_name, (project_id, file_id) in mods_in_manifest.items():
        file_path = os.path.join(mods_dir, file_name)
        if os.path.exists(file_path):
            print(f"Mod already exists, skipping: {file_name}")
            continue

        print(f"Downloading mod: {file_name} (Project: {project_id}, File: {file_id})")
        # Construct the CurseForge API URL to get the direct download URL
        api_url = f"https://addons-ecs.forgesvc.net/api/v2/addon/{project_id}/file/{file_id}/download-url"

        try:
            response = requests.get(api_url, timeout=15)
            if response.status_code != 200:
                print(f"  Error: Received status {response.status_code} when fetching download URL for {file_name}")
                continue

            # The API returns the direct download URL as plain text.
            download_url = response.text.strip()
            if not download_url.startswith("http"):
                print(f"  Error: Invalid download URL for {file_name}: {download_url}")
                continue

            # Now download the mod file
            with requests.get(download_url, stream=True, timeout=60) as mod_response:
                mod_response.raise_for_status()
                with open(file_path, "wb") as mod_file:
                    for chunk in mod_response.iter_content(chunk_size=8192):
                        if chunk:
                            mod_file.write(chunk)
            print(f"  Successfully downloaded: {file_name}")
        except Exception as e:
            print(f"  Error downloading mod {file_name}: {e}")

    print("Mod update process complete.")

if __name__ == "__main__":
    main()


