import os
import requests

def download_file_from_url(url, local_filename):
    os.makedirs("temp_files", exist_ok=True)  # create folder to save file
    local_path = os.path.join("temp_files", local_filename)

    # Download the file from the URL
    response = requests.get(url)
    response.raise_for_status()  # raise error if download failed

    # Save to local path
    with open(local_path, "wb") as f:
        f.write(response.content)

    return local_path

# Example usage:
url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
local_file = download_file_from_url(url, "policy.pdf")

print(f"Downloaded file saved at: {local_file}")

# Now pass this `local_file` path to your document loader
