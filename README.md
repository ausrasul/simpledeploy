# SimpleDeploy
SimpleDeploy is a unique Continuous Integration/Continuous Deployment (CI/CD) solution tailored for individual developers.
It operates directly on the deployment server, bringing the build process to the code,
rather than the traditional method of bringing the code to the build process.
This approach simplifies the deployment pipeline and offers a streamlined, efficient workflow for developers.
SimpleDeploy works with any Git source control provider, making it a versatile tool for various development environments.

## Usage

On the server where the deployment happens, clone this repository.

### Configure SimpleDeploy
Configure the config.ini file:
REPO_DIR: Where the code repo will be cloned. Path is relative to SimpleDeploy config file. example ../open_math
REPO_NAME: The link to the git repository. example https://github.com/ausrasul/open_math
REPO_MOUNT_DIR: Where in the podman container the repository will be mounted. example /open_math

### Configure your project
In your repository, create a file ci.ini and configure it:
[CI]
CI_IMAGE: podman/docker image name and version, example node:18
CI_COMMAND: commands to run on your repo (inside the container), example npm install && npm run build && node ./server.js
CI_PORT: port mapping to be exposed, example 8080:3001 where 3001 is the port served by the repo, 8080 is the port mapped on the host.

### Schedule SimpleDeploy to run in crontab

