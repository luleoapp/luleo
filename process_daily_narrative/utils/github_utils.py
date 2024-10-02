from github.InputGitTreeElement import InputGitTreeElement  # Add this import
import base64
import os
from github import Github

def full_github_resource_path(image_path):
    return "https://raw.githubusercontent.com/luleoapp/luleo/main/"+image_path


def upload_file_to_github(file_path, github_file_path):
    try:
        # Read the file in binary mode
        with open(file_path, 'rb') as file:
            content = file.read()

        # Initialize the GitHub client
        github_token = os.environ.get('GITHUB_TOKEN')
        repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        print(f"Attempting to upload to GitHub repository: {repo_name}")
        
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        if not repo_name:
            raise ValueError("GITHUB_REPO_NAME environment variable is not set")
        
        g = Github(github_token)
        
        try:
            repo = g.get_repo(repo_name)
        except Exception as repo_error:
            print(f"Error accessing repository: {str(repo_error)}")
            raise

        # Get the latest commit
        master_ref = repo.get_git_ref('heads/main')
        master_sha = master_ref.object.sha
        base_tree = repo.get_git_tree(master_sha)

        # Create a new blob with the file content
        blob = repo.create_git_blob(base64.b64encode(content).decode(), "base64")

        # Create a new tree with the new blob
        element = InputGitTreeElement(path=github_file_path, mode='100644', type='blob', sha=blob.sha)
        new_tree = repo.create_git_tree([element], base_tree)

        # Create a new commit
        parent = repo.get_git_commit(master_sha)
        commit = repo.create_git_commit(f"Update {github_file_path}", new_tree, [parent])

        # Update the reference
        master_ref.edit(commit.sha)

        print(f"File {github_file_path} uploaded to GitHub successfully.")
        return {"message": f"File {github_file_path} uploaded to GitHub successfully."}

    except Exception as e:
        error_message = f"Error uploading file to GitHub: {str(e)}"
        print(error_message)
        print(f"Repo Name: {repo_name}")
        print(f"GitHub File Path: {github_file_path}")
        return {"error": error_message}

