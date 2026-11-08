# SearXNG plugin

This bundled plugin is a non-working placeholder for Agent Zero's former built-in SearXNG search service. The `search_engine` tool always returns:

```text
the searxng plugin is not yet fully implemented
```

It performs no network request, package installation, service startup, virtualenv creation, or configuration write. A future implementation should recreate SearXNG inside an Agent Zero sandbox rather than adding it back to the base or runtime image.

## Historical installation record

The former base image copied `docker/base/fs/` to `/`, installed Python 3.13, and then ran `/ins/install_searxng.sh`. That first stage:

1. Installed `git`, `build-essential`, `libxslt-dev`, `zlib1g-dev`, `libffi-dev`, and `libssl-dev` with apt.
2. Created a system user named `searxng` with `/bin/bash`, home `/usr/local/searxng`, and comment `Privacy-respecting metasearch engine`.
3. Added that user to the `sudo` group.
4. Created `/usr/local/searxng`, assigned it to `searxng:searxng`, and ran `/ins/install_searxng2.sh` through `su - searxng`.

The second stage ran as `searxng` and used this effective sequence:

```bash
git clone https://github.com/searxng/searxng /usr/local/searxng/searxng-src
python3.13 -m venv /usr/local/searxng/searx-pyenv
echo '. /usr/local/searxng/searx-pyenv/bin/activate' >> /usr/local/searxng/.profile
source /usr/local/searxng/searx-pyenv/bin/activate
pip install --no-cache-dir -U pip setuptools wheel pyyaml lxml msgspec typing_extensions
cd /usr/local/searxng/searxng-src
pip install --no-cache-dir --use-pep517 --no-build-isolation .
pip cache purge
```

The repository clone and Python packages were unpinned, so the old build was not fully reproducible. The SearXNG virtualenv lived entirely at `/usr/local/searxng/searx-pyenv`; deleting the installer from the image build removes that virtualenv and its pip-only dependencies from newly built images. The apt packages in the first-stage list were installed by that same deleted installer; some may still be present if another image component independently requires them.

## Historical runtime wiring

The runnable image overlaid its own `/etc/searxng/settings.yml` and `/etc/searxng/limiter.toml` on the base copy. Supervisor then started the service as the `searxng` user with:

```ini
[program:run_searxng]
command=/exe/run_searxng.sh
environment=SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
user=searxng
directory=/usr/local/searxng/searxng-src
stopwaitsecs=1
autorestart=true
startretries=3
stopasgroup=true
killasgroup=true
```

`/exe/run_searxng.sh` changed to `/usr/local/searxng/searxng-src`, exported `SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml`, activated `/usr/local/searxng/searx-pyenv`, and executed `python /usr/local/searxng/searxng-src/searx/webapp.py`. The former Agent Zero helper sent an HTTP `POST` to `http://localhost:55510/search` with form fields `q=<query>` and `format=json`.

Port `55510` was internal and was not listed in the runnable Dockerfile's `EXPOSE` instruction. The launcher, supervisor program, service user, install scripts, config files, virtualenv, source clone, and Dockerfile references have all been removed from the outer image design.

## Historical effective settings

The runnable image's overlay was the effective configuration. Preserve these values when designing the sandboxed replacement:

```yaml
use_default_settings:
  engines:
    remove:
      - radio browser
      - wikidata

general:
  debug: false
  instance_name: "SearXNG"

search:
  safe_search: 0
  formats:
    - json

server:
  secret_key: "dummy"  # overridable by SEARXNG_SECRET
  port: 55510
  limiter: false
  image_proxy: false
  # base_url was unset and could be overridden by SEARXNG_URL.

# Redis was disabled. The documented optional value, overridable by
# SEARXNG_REDIS_URL, was:
# redis:
#   url: unix:///usr/local/searxng-redis/run/redis.sock?db=0

ui:
  static_use_hash: true

enabled_plugins:
  - "Hash plugin"
  - "Self Informations"
  - "Tracker URL remover"

engines:
  - name: radio browser
    engine: radio_browser
    disabled: true
    inactive: true
  - name: ahmia
    disabled: true
    inactive: true
  - name: torch
    disabled: true
    inactive: true
```

`radio browser` was disabled because it crashed on x86 in `gethostbyaddr`; `wikidata` was disabled because variant payloads broke the SearXNG 2026.04 bootstrap initialization path. The older base-layer copy only removed `wikidata` and omitted the explicit `radio browser` engine block, but the runtime overlay above replaced it.

The copied limiter configuration was identical in both image contexts:

```toml
[botdetection]
trusted_proxies = ["127.0.0.1"]
ipv4_prefix = 32
ipv6_prefix = 48

[botdetection.ip_limit]
filter_link_local = false
link_token = false

[botdetection.ip_lists]
block_ip = []
pass_ip = []
pass_searxng_org = true
```

Although the limiter file existed, `server.limiter` was `false`. Future work should reevaluate the dummy secret, trusted proxy assumptions, disabled limiter, unpinned source, and `sudo` membership instead of copying them blindly into a sandbox.

## Future sandboxing checklist

- Pin a reviewed SearXNG revision and dependency set.
- Provision the source, virtualenv, settings, and writable state inside a sandbox-owned filesystem.
- Bind only the minimum loopback or mediated endpoint needed by the tool; do not expose the service publicly by default.
- Generate a real secret where required and avoid persisting it in source or image layers.
- Add sandbox lifecycle, health, timeout, cleanup, and request/response tests before replacing the placeholder.
