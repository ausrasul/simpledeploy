SimpleDeploy
============

**SimpleDeploy** is a pull-based CI/CD engine designed for individual developers.

It shifts the build process from external pipelines directly onto the deployment server, eliminating the need for inbound webhooks or external runner access.

By monitoring a Git repository locally, it automates the pulling, building, and orchestration of Podman-based containerized applications.

1\. Prerequisites
-----------------

Ensure the deployment server has the following installed:

*   **Python 3.x**
    
*   **Podman**
    
*   **Git**
    

### Server Environment Setup

To ensure persistent container execution and image resolution, run:

```bash

# Keep user processes running after logout  
$ loginctl enable-linger $USER

# Ensure Podman searches Docker Hub
$ vi /etc/containers/registries.conf

# Add: unqualified-search-registries = ["docker.io"]
```

2\. Installation
----------------

Clone the SimpleDeploy utility to your deployment server:
```bash

$ git clone https://github.com/ausrasul/simpledeploy.git
$ cd simpledeploy
```

3\. Configuration
-----------------

### Step A: Configure the Engine (config.json)

Create or edit config.json in the SimpleDeploy directory to define the target source code.

|Key|Description|
|---|---|
|dir|Relative path where the application code will be cloned.|
|cfg_file|Path to the CI/CD instructions (relative to the app repo).|
|url|Git repository URL.|
|branch|Target branch for deployment (default: main).|
|git_auth|Credentials for private repositories.|
|mount_dir|Internal container path for mounting the repository.|


### Step B: Configure the Pipeline (ci.json)

In your application repository, create the JSON file referenced in cfg_file above.
```json

{
    "name": "project_pod_name",
    "volumes": ["data_volume"],
    "app": {
        "name": "main_container",
        "image": "node:18",
        "command": "node ./server.js",
        "ports": ["8080:3001"],
        "env": ["NODE_ENV=production"],
        "secrets": [
            { "secret": "db_password", "type": "env", "target": "DB_PASS" }
        ]
    },
    "services": [
        {
            "name": "cache_service",
            "image": "redis",
            "volumes": ["data_volume:/data"]
        }
    ]
}
```

4\. Secret Management
---------------------

SimpleDeploy utilizes host-level Podman secrets. These must be created manually before the first run:
```bash
$ echo "your_secret_value" | podman secret create db_password -
```

*   **Type mount**: Exposes secret at /run/secrets/ (default).
    
*   **Type env**: Maps secret to an environment variable via target.
    

5\. Deployment & Automation
---------------------------

### Manual Execution

Run the engine manually to verify the configuration:
```bash
# Standard run (pulls if changes detected)
$ python3 simpledeploy.py

# Force deployment even without new commits
$ python3 simpledeploy.py --deploy-anyway

# Rerun the workflow using existing local code
$ python3 simpledeploy.py --rerun-only   `
```
### Automation via Cron

To enable "Continuous Deployment," schedule the script to check for updates every minute:
```cron
* * * * * /usr/bin/python3 /path/to/simpledeploy/simpledeploy.py >> /tmp/simpledeploy.log 2>&1
```

6\. Advanced Command Chains
---------------------------

For complex builds, the command field in ci.json accepts an array.

Each string must terminate with a semicolon:

```json
"command": [
    "npm install;",
    "npm run build;",
    "node ./dist/index.js"
]
```