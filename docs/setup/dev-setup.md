# Development manual for Agent Zero
This guide will show you how to setup a local development environment for Agent Zero in a VS Code compatible IDE, including proper debugger.

[![Tutorial video](./res/devguide_vid.png)](https://www.youtube.com/watch?v=KE39P4qBjDk)

> [!WARNING]
> This guide is for developers and contributors. It assumes you have a basic understanding of how to use Git/GitHub, Docker, IDEs and Python.

> [!NOTE]
> - Agent Zero runs in a Docker container, this simplifies installation and ensures unified environment and behavior across systems.
> - Developing and debugging in a container would be complicated though, therefore we use a hybrid approach where the python framework runs on your machine (in VS Code for example) and only connects to a Dockerized instance when it needs to execute code or use other pre-installed functionality like the built-in search engine.

## To follow this guide you will need:
1. VS Code compatible IDE (VS Code, Cursor, Windsurf...)
2. Python environment (Conda, venv, uv...)
3. Docker (Docker Desktop, docker-ce...)
4. (optional) Git/GitHub

> [!NOTE]
> I will be using clean VS Code, Conda and Docker Desktop in this example on MacOS.

## Step 0: Install required software
- See the list above and install the software required if you don't already have it.
- You can choose your own variants, but Python, Docker and a VS Code compatible IDE are required.
- For Python you can choose your environment manager - base Python venv, Conda, uv...

## Step 1: Clone or download the repository
- Agent Zero is available on GitHub [github.com/jrmatherly/agent-zero](https://github.com/jrmatherly/agent-zero).
- You can download the files using a browser and extract or run `git clone https://github.com/jrmatherly/agent-zero` in your desired directory.

> [!NOTE]
> In my case, I used `cd ~/Desktop` and `git clone https://github.com/jrmatherly/agent-zero`, so my project folder is `~/Desktop/agent-zero`.

## Step 2: Open project folder in your IDE
- I will be using plain and clean VS Code for this example to make sure I don't skip any setup part, you can use any of it's variants like Cursor, Windsurf etc.
- Agent Zero comes with `.vscode` folder that contains basic setup, recommended extensions, and debugger profiles. These will help us a lot.

1. Open your IDE and open the project folder using `File > Open Folder` and select your folder, in my case `~/Desktop/agent-zero`.
2. You will probably be prompted to trust the directory, confirm that.
3. You should now have the project open in your IDE
![VS Code project](res/dev/devinst-1.png)

# Step 3: Prepare your IDE:
1. Notice the prompt in lower right corner of the screenshot above to install recommended extensions, this comes from the `.vscode/extensions.json` file. It contains Python language support, debugger and error helper, install them by confirming the popup or manually in Extensions tab of your IDE. These are the extensions mentioned:

```text
usernamehw.errorlens
ms-python.debugpy
ms-python.python
```

Now when you select one of the python files in the project, you should see proper Python syntax highlighting and error detection. It should immediately show some errors, because we did not yet install dependencies.
![VS Code Python](res/dev/devinst-2.png)

2. Prepare the python environment to run Agent Zero in. (⚠️ This step assumes you have some Python runtime installed.) By clicking the python version in lower right corner (3.13.1 in my example), you should get a list of available environments. You can click the `+ Create Virtual Environment` button. You might be prompted to select the environment manager if you have multiple installed. I have venv and Conda, I will select Conda here. I'm also prompted for desired python version, I will select 3.12, that is known to work well.
![VS Code Python environments](res/dev/devinst-3.png)
![VS Code Python environments](res/dev/devinst-4.png)

- Your new environment should be automatically activated. If not, select it in the lower right corner. You might need to open a new terminal in VS Code to reflect the changes with `Terminal > New Terminal` or clicking the `+` button in the terminal tab. Your terminal prompt should now start with your environment name/path, in my case `(/Users/frdel/Desktop/agent-zero/.conda)` This shows the environment is active in the terminal.

![VS Code env terminal](res/dev/devinst-5.png)

3. Install dependencies. Run these commands in the terminal:

```bash
# Recommended (uses uv — fast, reproducible):
uv sync
playwright install chromium

# Alternative (pip fallback):
pip install -r requirements.txt
playwright install chromium
```

These will install all the python packages and browser binaries for playwright (browser agent).
Errors in the code editor caused by missing packages should now be gone. If not, try reloading the window.

## Step 4: Run Agent Zero in the IDE
Great work! Now you should be able to run Agent Zero from your IDE including real-time debugging.
It will not be able to do code execution and few other features requiring the Docker container just yet, but most of the framework will already work.

1. The project is pre-configured for debugging. Go to Debugging tab, select "run_ui.py" and click the green play button (or press F5 by default). The configuration can be found at `.vscode/launch.json`.

![VS Code debugging](res/dev/devinst-6.png)

The framework will run at the default port 5000. If you open `http://localhost:5000` in your browser and see `ERR_EMPTY_RESPONSE`, don't panic, you may need to select another port like I did for some reason. If you need to change the default port, you can add `"--port=5555"` to the args in the `.vscode/launch.json` file or you can create a `.env` file in the root directory and set the `WEB_UI_PORT` variable to the desired port.

You can also set the bind host via `"--host=0.0.0.0"` (or `WEB_UI_HOST=0.0.0.0`).

It may take a while the first time. You should see output like the screenshot below. The RFC error is ok for now as we did not yet connect our local development to another instance in docker.
![First run](res/dev/devinst-7.png)

After inserting my API key in settings, my Agent Zero instance works. I can send a simple message and get a response.
⚠️ Some tools like code execution will not work yet as they need to be connected to a Dockerized instance.

![First message](res/dev/devinst-8.png)

## Debugging
- You can try out the debugger already by placing a breakpoint somewhere in the python code.
- Let's open `python/api/message.py` for example and place a breakpoint at the beginning of the `communicate` function by clicking on the left of the row number. A red dot should appear showing a breakpoint is set.

![Debugging](res/dev/devinst-9.png)

- Now when I send a message in the UI, the debugger will pause the execution at the breakpoint and allow me to inspect all the runtime variables and run the code step by step, even modify the variables or jump to another locations in the code. No more print statements needed!

![Debugging](res/dev/devinst-10.png)

## Step 5: Run another instance of Agent Zero in Docker
- Some parts of A0 require standardized linux environment, additional web services and preinstalled binaries that would be unneccessarily complex to set up in a local environment.
- To make development easier, we can use existing A0 instance in docker and forward some requests to be executed there using SSH and RFC (Remote Function Call).

1. Pull the docker image `ghcr.io/jrmatherly/agent-zero` from GHCR and run it with a web port (`80`) mapped and SSH port (`22`) mapped.
If you want, you can also map the `/a0` folder to our local project folder as well, this way we can update our local instance and the docker instance at the same time.
This is how it looks in my example: port `80` is mapped to `8880` on the host and `22` to `8822`, `/a0` folder mapped to `/Users/frdel/Desktop/agent-zero`:

![docker run](res/dev/devinst-11.png)
![docker run](res/dev/devinst-12.png)

## Step 6: Configure SSH and RFC connection
- The last step is to configure the local development (VS Code) instance and the dockerized instance to communicate with each other. This is very simple and can be done in the settings in the Web UI of both instances.
- In my example the dark themed instance is the VS Code one, the light themed one is the dockerized instance.

1. Open the "Settings" page in the Web UI of your dockerized instance and go in the "Development" section.
2. Set the `RFC Password` field to a new password and save.
3. Open the "Settings" page in the Web UI of your local instance and go in the "Development" section.
4. Here set the `RFC Password` field to the same password you used in the dockerized instance. Also set the SSH port and HTTP port the same numbers you used when creating the container - in my case `8822` for SSH and `8880` for HTTP. The `RFC Destination URL` will most probably stay `localhost` as both instances are running on the host machine.
5. Click save and test by asking your agent to do something in the terminal, like "Get current OS version". It should be able to communicate with the dockerized instance via RFC and SSH and execute the command there, responding with something like "Kali GNU/Linux Rolling".

My Dockerized instance:
![Dockerized instance](res/dev/devinst-14.png)

My VS Code instance:
![VS Code instance](res/dev/devinst-13.png)

## RFC Notes (Host IDE + Docker Execution)
Agent Zero runs code inside the container by default. If you are running the framework locally in your IDE but want tools (like code execution) to run in Docker, configure RFC in **Settings -> Development** and point it to a running Agent Zero container. This routes execution through SSH/RFC to the container while keeping the UI and agent loop on your host.

# Congratulations!

You have successfully set up a complete Agent Zero development environment! You now have:

- A local development instance running in your IDE with full debugging capabilities
- A dockerized instance for code execution and system operations
- RFC and SSH communication between both instances
- The ability to develop, debug, and test Agent Zero features seamlessly

You're now ready to contribute to Agent Zero, create custom extensions, or modify the framework to suit your needs. Happy coding!

## Next steps
- See [dependency management](dependency-management.md) for adding/removing packages, upstream merge strategy, and Docker compatibility.
- See [extensions](../developer/extensions.md) for instructions on how to create custom extensions.
- See [websocket infrastructure](websocket-infrastructure.md) for real-time handler patterns, client APIs, and troubleshooting tips.
- See [contribution](../guides/contribution.md) for instructions on how to contribute to the framework.

## Configuration via Environment Variables

For development and testing, you can override default settings using the `.env` file with `A0_SET_` prefixed variables:

```env
# Add to your .env file
A0_SET_chat_model_provider=ollama
A0_SET_chat_model_name=llama3.2
A0_SET_chat_model_api_base=http://localhost:11434
A0_SET_memory_recall_interval=5
```

These environment variables automatically override the hardcoded defaults in `get_default_settings()` without modifying code. Useful for testing different configurations or multi-environment setups.

## Building Docker Images

### Local Build

Build a local image from your working tree:

```bash
docker build -f DockerfileLocal -t agent-zero-local --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
```

The `CACHE_DATE` argument is optional — it caches most of the build and only rebuilds the last steps when files change.

### Pushing to GHCR (GitHub Container Registry)

Images are hosted on GHCR at `ghcr.io/jrmatherly/agent-zero` and `ghcr.io/jrmatherly/agent-zero-base`.

**1. Create a GitHub Personal Access Token (PAT)**

Go to **GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)** and create a token with `write:packages` and `read:packages` scopes.

**2. Authenticate to GHCR**

```bash
export GITHUB_TOKEN="ghp_YOUR_TOKEN_HERE"
echo "$GITHUB_TOKEN" | docker login ghcr.io -u jrmatherly --password-stdin
```

**3. Build and push the base image** (from `docker/base/`):

```bash
docker buildx build -t ghcr.io/jrmatherly/agent-zero-base:latest \
  --platform linux/amd64,linux/arm64 --push \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
```

**4. Build and push the app image** (from `docker/run/`):

```bash
docker buildx build -t ghcr.io/jrmatherly/agent-zero:latest \
  --platform linux/amd64,linux/arm64 --push \
  --build-arg BRANCH=main \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
```

See `docker/base/build.txt` and `docker/run/build.txt` for additional build variants (development, testing, no-cache).
