import os
import subprocess
import configparser

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return {k: v for k, v in config.items()}

def clone_repo_if_not_exist(repo_name, repo_dir):
    if not os.path.exists(repo_dir):
        # Clone the repo if it doesn't exist
        subprocess.run(['git', 'clone', repo_name, repo_dir], check=True)

def git_clone_or_pull(repo_name, repo_dir):
    # Change to the directory specified in the configuration file
    clone_repo_if_not_exist(repo_name, repo_dir)

    os.chdir(repo_dir)
    prev_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout.strip()
    subprocess.run(['git', 'pull'], check=True)
    this_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout.strip()
    return prev_hash,this_hash

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(script_dir, 'config.ini')
    script_reader = os.path.join(script_dir, 'read_config.py')

    # Source the configuration file
    repo_config = read_config(config_file)['REPO']
    # Check if the repo directory exists
    repo_dir = os.path.join(script_dir, repo_config['REPO_DIR'])
    repo_mount_dir = repo_config['REPO_MOUNT_DIR']

    prev_hash, this_hash = git_clone_or_pull(repo_config['REPO_NAME'], repo_dir)

    os.chdir(repo_dir)
    print(prev_hash, this_hash)
    # Check if there are any new commits since the last run
    if prev_hash == this_hash:
        ci_config = read_config('./ci.ini')['CI']
        print(ci_config['CI_COMMAND'])
        subprocess.run(['podman', 'run',
                        '-d',
                        '-p', ci_config['CI_PORT'],
                        '-v', f"{repo_dir}:{repo_mount_dir}",
                        '-w', repo_mount_dir,
                        ci_config['CI_IMAGE'],
                        'bash', '-c', ci_config['CI_COMMAND']], check=True)



if __name__ == '__main__':
    main()