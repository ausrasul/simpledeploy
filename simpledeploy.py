import os
import subprocess
import json
import sys
def log(msg, level='INFO'):
    time = os.popen('date').read().strip()
    print(f"{time} [{level}]: {msg}")
    
def run_command(command, **kwargs):
    try:
        result = subprocess.run(command, check=True, **kwargs)
        log(f"command output: {result.stdout}")
        if result.stderr:
            log(f"command error: {result.stderr}", 'ERROR')
        return result
    except subprocess.CalledProcessError as e:
        log(f"command '{' '.join(command)}' failed with return code {e.returncode}", 'ERROR')
        log(f"command error: {e.stderr}", 'ERROR')
        raise

def this_script_dir():
    return os.path.dirname(os.path.realpath(__file__))

def read_config(filename):
    # reads json config file
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

class Repo:
    def __init__(self, config_file):
        script_dir = this_script_dir()
        config_file = os.path.join(script_dir, config_file)
        config = read_config(config_file)
        
        self.dir = os.path.join(script_dir, config['repo']['dir'])
        self.url = config['repo']['url']
        self.branch = config['repo'].get('branch', 'main')
        auth = config['repo'].get('git_auth', {})
        if auth['require_auth']:
            username = auth['username']
            access_token = auth['access_token']
            self.url = self.url.replace('https://', f'https://{username}:{access_token}@')
        self.mount_dir = config['repo']['mount_dir']
        self.cfg_file = config['repo']['cfg_file']

class Container:
    def __init__(self, cfg):
        self.name = cfg['name']
        self.image = cfg.get('image', 'ubuntu:latest')
        self.command = cfg.get('command')
        self.ports = cfg.get('ports', [])
        self.volume_names = cfg.get('volume_names', [])
        self.volumes = cfg.get('volumes', [])
        self.work_dir = cfg.get('work_dir')
        self.envs = cfg.get('env', [])
    def _get_command(self):
        if isinstance(self.command, list):
            return ' '.join(self.command)
        return self.command
    def _remove(self):
        try:
            log(f"Removing container {self.name}")
            run_command(['podman', 'rm', '-f', self.name])
        except:
            log(f"Failed to remove container {self.name}", 'ERROR')
            pass
        
    def stop(self):
        try:
            log(f"Stopping container {self.name}")
            run_command(['podman', 'stop', self.name])
        except:
            log(f"Failed to stop container {self.name}", 'ERROR')
            pass
        finally:
            self._remove()
    
    def start(self, podname):
        self._create_volumes()
        command = [
            'podman', 'run', '-d',
            '--name', self.name,
            '--pod', podname,
        ]
        for volume in self.volumes:
            command.extend(['-v', volume])
        if self.work_dir:
            command.extend(['-w', self.work_dir])
        for env in self.envs:
            command.extend(['-e', env])
        # add options before this line
        command.append(self.image)
        if self.command:
            command.extend(['bash', '-c', self._get_command()])
        log(f"Starting container {self.name}")
        run_command(command)

    def _create_volumes(self):
        for volume in self.volume_names:
            log(f"Creating volume {volume}")
            run_command(['podman', 'volume', 'create', volume])

class App:
    def __init__(self, repo):
        script_dir = this_script_dir()
        abs_file_name = os.path.join(script_dir, repo.dir, repo.cfg_file)
        config = read_config(abs_file_name)

        self.name = config['name']
        app = config.get('app', {})
        app['volumes_names'] = config.get('volumes', [])
        app['volumes'] = app.get('volumes', [])
        app['volumes'].extend([
            f"{repo.dir}:{repo.mount_dir}"
        ])
        app['work_dir'] = repo.mount_dir
        self.container = Container(app)

        services = config.get('services', [])
        self.services = []
        for service in services:
            self.services.append(Container(service))
    
    def _create_pod(self):
        command = ['podman', 'pod', 'create', '--name', self.name]
        for port in self.container.ports:
            command.extend(['-p', port])
        for service in self.services:
            for port in service.ports:
                command.extend(['-p', port])
        log(f"Creating pod {self.name}")
        run_command(command)
    def _remove_pod(self):
        command = ['podman', 'pod', 'rm', '-f', self.name]
        for _ in range(3):  # Retry the command 3 times
            try:
                log(f"Removing pod {self.name}")
                run_command(command, timeout=5)
                break  # Break the loop if the command succeeds
            except:
                log(f"Failed to remove pod {self.name}, retry", 'ERROR')
                continue  # Retry the command if it fails

    def start(self):
        self._create_pod()
        self._services_start()
        self.container.start(podname=self.name)
    def stop(self):
        self.container.stop()
        self._services_stop()
        self._remove_pod()
    def _services_start(self):
        for service in self.services:
            service.start(podname=self.name)
    def _services_stop(self):
        for service in self.services:
            service.stop()

def clone_repo_if_not_exist(repo_name, repo_dir, repo_branch):
    if not os.path.exists(repo_dir):
        # Clone the repo if it doesn't exist
        log(f"Cloning {repo_name} to {repo_dir}")
        run_command(['git', 'clone', '-c http.sslVerify=false', '-b', repo_branch, repo_name, repo_dir])
        return True
    else:
        return False

def git_clone_or_pull(repo_name, repo_dir, repo_branch):
    # Change to the directory specified in the configuration file
    cloned = clone_repo_if_not_exist(repo_name, repo_dir, repo_branch)
    if cloned:
        return 1, 2
    else:
        os.chdir(repo_dir)
        prev_hash = run_command(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout.strip()
        subprocess.run(['git', 'pull', 'origin', repo_branch], check=True)
        this_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout.strip()
        return prev_hash, this_hash

def main():
    log("Starting deployment")
    deploy_anyway = False
    rerun_only = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d' or sys.argv[1] == '--deploy-anyway':
            deploy_anyway = True
        elif sys.argv[1] == '-r' or sys.argv[1] == '--rerun-only':
            rerun_only = True

    prev_hash = ''
    this_hash = ''
    repo = Repo('config.json')
    if not rerun_only:
        prev_hash, this_hash = git_clone_or_pull(repo.url, repo.dir, repo.branch)
        os.chdir(repo.dir)
        log(f"{prev_hash}, {this_hash}")

    # Check if there are any new commits since the last run
    if prev_hash != this_hash or deploy_anyway or rerun_only:
        app = App(repo)
        app.stop()
        app.start()


if __name__ == '__main__':
    main()
