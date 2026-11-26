# 原生团队版 Docker 验收

团队版复用 Agent Zero 原生登录、Projects、聊天、模型预设、技能、Files、Browser、Desktop、Editor、Memory 和 Scheduled Tasks。每个安装使用一个 Compose 项目和一个 WebUI 进程。独立的用户卷同时保存成员与项目授权、审计、原生会话、项目资料、记忆和任务。

## 独立启动

下例把验收 UI 绑定到本机 `127.0.0.1:5081`。在团队版工作树执行。运行时版本由 [团队版 Compose](../../docker/team/compose.yaml) 固定。

```bash
export A0_TEAM_SOURCE="$(git rev-parse --show-toplevel)"
export A0_TEAM_GIT_COMMON="$(git rev-parse --path-format=absolute --git-common-dir)"
export A0_TEAM_PORT=5081
docker compose -p agent-zero-native-team-qa -f docker/team/compose.yaml config --quiet
```

首次使用新的用户卷时，在终端初始化管理员凭据。已有管理员凭据的卷可直接启动。

```bash
docker compose -p agent-zero-native-team-qa -f docker/team/compose.yaml run --rm --no-deps \
  --entrypoint /opt/venv-a0/bin/python webui -c '
from getpass import getpass
from pathlib import Path
from dotenv import set_key
path = Path("/a0/usr/.env")
username = input("Administrator username: ").strip()
password = getpass("Administrator password: ")
if not username or len(password) < 12:
    raise SystemExit("Enter an administrator username and a password of at least 12 characters.")
path.touch(mode=0o600, exist_ok=False)
set_key(str(path), "AUTH_LOGIN", username)
set_key(str(path), "AUTH_PASSWORD", password)
'
docker compose -p agent-zero-native-team-qa -f docker/team/compose.yaml up -d --wait --wait-timeout 105
```

打开 [本机 WebUI](http://127.0.0.1:5081)，使用平台管理员在原生设置配置 Main、Utility 和 Embedding 模型。复制其他实例的模型凭据须得到凭据所有人的授权，并保存到本次验收的独立用户卷。

### 使用本机 HTTP 代理的网络

如果宿主机的网络代理为域名返回合成地址，可给项目 Browser 加载 [本机代理配置](../../docker/team/compose.host-browser-proxy.yaml)。将 `A0_TEAM_HOST_PROXY_PORT` 设置为已有代理在宿主机 `127.0.0.1` 上的 HTTP 或混合端口。代理需支持连接到公网 IP。浏览器代理在遇到合成地址时，通过 `A0_TEAM_BROWSER_DNS_HTTPS` 配置的 HTTPS DNS 服务解析公网地址，默认使用 Cloudflare。

```bash
export A0_TEAM_HOST_PROXY_PORT=7897
docker compose -p agent-zero-native-team-qa \
  -f docker/team/compose.yaml -f docker/team/compose.host-browser-proxy.yaml \
  up -d --wait --wait-timeout 105
```

## 签收路径

1. 管理员在 **Projects** 建立 P1、P2，从 **More options → Team accounts** 建立 A、B，给 A 分配 P1 和 P2，给 B 分配 P1。
2. 使用两个独立浏览器会话尝试 A、B。A 从原生首页选 P1，发送一条合成消息，确认真实模型回复及重载后的历史。B 从 P1 打开同一会话，核对发起人、运行人和历史。
3. 验证同会话互斥、项目内不同会话并行、占用时草稿保留和持有人停止。管理员和项目成员看到相同的原标题及消息，按运行权限继续、暂停或停止。新建空白会话保存在当页，发送第一条消息后才入库。复验中断后的同一请求 ID 时，核对原运行 ID 和状态。
4. 在成员的 **Chats** 中展开已分配项目，打开其中的共享会话。首页 **Quick Actions** 提供 **Memory**、**Scheduled Tasks**、**Projects** 和 **Files**。尚未选择项目时，从 **Files** 先选项目，再进入原生文件浏览器。用两个成员账号打开同一项目的配置和文件，复验共享和版本冲突。用 **Memory** 搜索记忆并重建知识索引，再用 **Scheduled Tasks** 创建并执行项目文本任务。
5. 从 **Team audit** 查操作事件，单独授予正文权限再打开会话。撤销 B 的 P1 授权后，检查会话、文件、记忆、任务和审计是否都按新权限处理。
6. 在原生聊天里输入 `@` 选择技能或项目文件，切换已有模型预设并使用 **Compact**。用侧栏 **Files** 上传文件，使用 **Editor** 修改并保存。用 **Browser** 打开网页，或通过 **Desktop** 打开项目文档。在桌面应用里保存修改，再点击 **Save to Project** 将新版本写回共享项目。

### 角色与执行范围

| 入口 | 范围 |
| --- | --- |
| 平台管理 | 管理员管理全局配置、插件、模型凭据和连接，以及实例级桌面与浏览器。 |
| 项目和聊天 | 已有明确原生项目归属的聊天自动共享。无项目和归属不明的历史保留原归属。原生历史随项目读取，审计正文仍通过独立权限追踪。 |
| Agent 工具 | Response、Goal、原生 Text Editor 和 Memory。文本工具只处理当前项目内的相对路径，覆盖及补丁对照最近读取的修订。 |
| 项目 Browser 和 Desktop | 每个账号在每个项目有独立的 Linux 图形会话。Browser 通过公共网络代理访问网站。Desktop 的项目文档通过带版本检查的保存操作发布。宿主内核需支持 Linux Landlock ABI 6 及以上。 |
| 记忆和任务 | 每项目独立索引。知识索引手动重建，并读取项目知识目录中的 UTF-8 文本。手动任务使用发起成员身份，到期任务使用创建者当前授权。 |

项目文件与索引通过受控接口访问。容器内管理员、Docker 主机管理员及备份操作者处于运行环境的管理权限范围内。

## 备份、升级与回滚

将镜像摘要、确切源码版本和预升级用户卷作为同一次备份记录。工作树存在未提交改动时，同步保存实际运行的源码。备份目录采用受限权限，验收使用合成数据。

```bash
export A0_TEAM_QA_PROJECT=agent-zero-native-team-qa
export A0_TEAM_BACKUP_DIR=/absolute/path/to/private-backup
export A0_TEAM_BACKUP_IMAGE=agent0ai/agent-zero@sha256:28a9a19e3168d44d53c78fb1a6c7cf086c9e7d6d621d906660d5ec1170d065c1

docker compose -p "$A0_TEAM_QA_PROJECT" -f docker/team/compose.yaml stop webui
docker run --rm --network none \
  --mount "type=volume,source=${A0_TEAM_QA_PROJECT}_usr,target=/source,readonly" \
  --mount "type=bind,source=${A0_TEAM_BACKUP_DIR},target=/backup" \
  --entrypoint /bin/bash "$A0_TEAM_BACKUP_IMAGE" \
  -c 'set -eu; umask 077; set -o noclobber; tar -C /source -cpf - . > /backup/usr-before-upgrade.tar'
```

先把备份恢复到新的 QA 用户卷。运行选定的新版本，核对登录、权限、历史和文件 SHA-256，并复验模型、任务和审计。执行回滚时，使用备份对应的镜像和源码启动恢复卷。单用户基线用它自己的 Compose 配置挂载恢复卷。

```bash
export A0_TEAM_RESTORE_PROJECT=agent-zero-native-team-restore
export A0_TEAM_PORT=5082
docker compose -p "$A0_TEAM_RESTORE_PROJECT" -f docker/team/compose.yaml create webui
docker run --rm --network none \
  --mount "type=volume,source=${A0_TEAM_RESTORE_PROJECT}_usr,target=/restore" \
  --mount "type=bind,source=${A0_TEAM_BACKUP_DIR},target=/backup,readonly" \
  --entrypoint /bin/bash "$A0_TEAM_BACKUP_IMAGE" \
  -c 'set -eu; test -z "$(find /restore -mindepth 1 -maxdepth 1 -print -quit)"; tar -C /restore -xpf /backup/usr-before-upgrade.tar'
docker compose -p "$A0_TEAM_RESTORE_PROJECT" -f docker/team/compose.yaml up -d --wait --wait-timeout 105
```

先确认恢复实例的登录、项目资料和历史，再切换用户。保留升级后的用户卷供核对升级期间的数据。
