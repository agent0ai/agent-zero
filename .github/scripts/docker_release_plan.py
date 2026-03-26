#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}<<__EOF__\n{value}\n__EOF__\n")


def write_summary(lines: list[str]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path or not lines:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("## Docker publish plan\n\n")
        for line in lines:
            handle.write(f"- {line}\n")


def run_command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        command = " ".join(args)
        fail(f"Command failed ({command}):\n{result.stderr.strip()}")
    return result


def git(*args: str, check: bool = True) -> str:
    return run_command("git", *args, check=check).stdout.strip()


def docker_tag_exists(image_repo: str, tag: str) -> bool:
    result = run_command(
        "docker",
        "buildx",
        "imagetools",
        "inspect",
        f"{image_repo}:{tag}",
        check=False,
    )
    return result.returncode == 0


def split_branches(raw: str) -> list[str]:
    parts = re.split(r"[\s,]+", raw.strip())
    return [part for part in parts if part]


@dataclass(frozen=True)
class Config:
    allowed_branches: list[str]
    main_branch: str
    image_repo: str
    tag_pattern: re.Pattern[str]
    min_version: tuple[int, int]
    event_name: str
    source_tag: str
    manual_tag: str


@dataclass(frozen=True)
class BranchState:
    branch: str
    valid_tags: list[str]
    latest_tag: str | None


@dataclass
class Candidate:
    branch: str
    source_tag: str
    mode: str
    publish_version: bool
    publish_branch_tag: bool
    reason: str


def load_config() -> Config:
    allowed_branches = split_branches(os.environ["ALLOWED_BRANCHES"])
    if not allowed_branches:
        fail("ALLOWED_BRANCHES must not be empty.")
    main_branch = os.environ["MAIN_BRANCH"].strip()
    if main_branch not in allowed_branches:
        fail("MAIN_BRANCH must also be listed in ALLOWED_BRANCHES.")

    tag_regex = os.environ["RELEASE_TAG_REGEX"]
    return Config(
        allowed_branches=allowed_branches,
        main_branch=main_branch,
        image_repo=os.environ["DOCKER_IMAGE_REPO"].strip(),
        tag_pattern=re.compile(tag_regex),
        min_version=(
            int(os.environ["MIN_RELEASE_MAJOR"]),
            int(os.environ["MIN_RELEASE_MINOR"]),
        ),
        event_name=os.environ["EVENT_NAME"].strip(),
        source_tag=os.environ.get("SOURCE_TAG", "").strip(),
        manual_tag=os.environ.get("MANUAL_TAG", "").strip(),
    )


def parse_release_tag(config: Config, tag: str) -> tuple[int, int] | None:
    match = config.tag_pattern.fullmatch(tag)
    if not match:
        return None
    version = (int(match.group(1)), int(match.group(2)))
    if version < config.min_version:
        return None
    return version


def tag_exists(tag: str) -> bool:
    return run_command("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}", check=False).returncode == 0


def tag_commit(tag: str) -> str:
    return git("rev-list", "-n", "1", f"refs/tags/{tag}")


def branch_contains_commit(branch: str, commit: str) -> bool:
    return (
        run_command(
            "git",
            "merge-base",
            "--is-ancestor",
            commit,
            f"origin/{branch}",
            check=False,
        ).returncode
        == 0
    )


def collect_branch_states(config: Config, branches: list[str] | None = None) -> dict[str, BranchState]:
    states: dict[str, BranchState] = {}
    for branch in branches or config.allowed_branches:
        if run_command("git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}", check=False).returncode != 0:
            fail(f"Allowed branch origin/{branch} was not fetched.")

        tagged_versions: list[tuple[tuple[int, int], str]] = []
        merged_tags = git("tag", "--merged", f"origin/{branch}")
        for tag in merged_tags.splitlines():
            version = parse_release_tag(config, tag.strip())
            if version is None:
                continue
            tagged_versions.append((version, tag.strip()))

        tagged_versions.sort(key=lambda item: item[0])
        valid_tags = [tag for _, tag in tagged_versions]
        states[branch] = BranchState(
            branch=branch,
            valid_tags=valid_tags,
            latest_tag=valid_tags[-1] if valid_tags else None,
        )
    return states


def add_or_merge_candidate(candidates: dict[tuple[str, str, str], Candidate], candidate: Candidate) -> None:
    key = (candidate.branch, candidate.source_tag, candidate.mode)
    existing = candidates.get(key)
    if existing is None:
        candidates[key] = candidate
        return
    existing.publish_version = existing.publish_version or candidate.publish_version
    existing.publish_branch_tag = existing.publish_branch_tag or candidate.publish_branch_tag
    if candidate.reason not in existing.reason:
        existing.reason = f"{existing.reason}; {candidate.reason}"


def plan_push(config: Config, branch_states: dict[str, BranchState]) -> tuple[list[Candidate], list[str]]:
    source_tag = config.source_tag
    notes: list[str] = []
    version = parse_release_tag(config, source_tag)
    if version is None:
        return [], [f"Skipped `{source_tag}` because it does not match `v{{X}}.{{Y}}` or is below v{config.min_version[0]}.{config.min_version[1]}."]
    if not tag_exists(source_tag):
        return [], [f"Skipped `{source_tag}` because the tag is not present after checkout."]

    commit = tag_commit(source_tag)
    candidates: list[Candidate] = []
    found_branch = False
    for branch, state in branch_states.items():
        if not branch_contains_commit(branch, commit):
            continue
        found_branch = True
        if state.latest_tag != source_tag:
            notes.append(
                f"Skipped `{source_tag}` on `{branch}` because `{state.latest_tag}` is the highest release tag currently reachable from that branch."
            )
            continue
        candidates.append(
            Candidate(
                branch=branch,
                source_tag=source_tag,
                mode="push_latest_only",
                publish_version=branch == config.main_branch,
                publish_branch_tag=True,
                reason=f"Automatic build for the latest release tag on `{branch}`.",
            )
        )

    if not found_branch:
        notes.append(f"Skipped `{source_tag}` because it is not reachable from any allowed branch.")
    return candidates, notes


def plan_manual_exact(config: Config, branch_states: dict[str, BranchState]) -> tuple[list[Candidate], list[str]]:
    manual_tag = config.manual_tag
    if parse_release_tag(config, manual_tag) is None:
        fail(
            f"Manual tag `{manual_tag}` is invalid. Expected `v{{X}}.{{Y}}` with a minimum of v{config.min_version[0]}.{config.min_version[1]}."
        )
    if not tag_exists(manual_tag):
        fail(f"Manual tag `{manual_tag}` does not exist in the repository.")

    commit = tag_commit(manual_tag)
    notes: list[str] = []
    candidates: list[Candidate] = []
    for branch, state in branch_states.items():
        if not branch_contains_commit(branch, commit):
            continue
        if branch == config.main_branch:
            candidates.append(
                Candidate(
                    branch=branch,
                    source_tag=manual_tag,
                    mode="manual_exact",
                    publish_version=True,
                    publish_branch_tag=state.latest_tag == manual_tag,
                    reason=f"Manual rebuild for `{manual_tag}` on `{branch}`.",
                )
            )
            continue
        if state.latest_tag != manual_tag:
            notes.append(
                f"Skipped `{manual_tag}` on `{branch}` because non-main branches only publish their current branch tag and `{state.latest_tag}` is newer."
            )
            continue
        candidates.append(
            Candidate(
                branch=branch,
                source_tag=manual_tag,
                mode="manual_exact",
                publish_version=False,
                publish_branch_tag=True,
                reason=f"Manual rebuild for the current branch image on `{branch}`.",
            )
        )

    if not candidates:
        notes.append(f"No eligible images were found for manual tag `{manual_tag}`.")
    return candidates, notes


def plan_manual_backfill(config: Config, branch_states: dict[str, BranchState]) -> tuple[list[Candidate], list[str]]:
    notes: list[str] = []
    candidates: dict[tuple[str, str, str], Candidate] = {}

    for branch, state in branch_states.items():
        if not state.valid_tags:
            notes.append(f"Branch `{branch}` has no releasable tags.")
            continue

        if branch == config.main_branch:
            for tag in state.valid_tags:
                if docker_tag_exists(config.image_repo, tag):
                    continue
                add_or_merge_candidate(
                    candidates,
                    Candidate(
                        branch=branch,
                        source_tag=tag,
                        mode="manual_backfill",
                        publish_version=True,
                        publish_branch_tag=False,
                        reason=f"Missing Docker Hub tag `{tag}`.",
                    ),
                )

            latest_tag = state.latest_tag
            if latest_tag and not docker_tag_exists(config.image_repo, "latest"):
                add_or_merge_candidate(
                    candidates,
                    Candidate(
                        branch=branch,
                        source_tag=latest_tag,
                        mode="manual_backfill",
                        publish_version=False,
                        publish_branch_tag=True,
                        reason="Missing Docker Hub tag `latest`.",
                    ),
                )
            continue

        if not docker_tag_exists(config.image_repo, branch):
            add_or_merge_candidate(
                candidates,
                Candidate(
                    branch=branch,
                    source_tag=state.latest_tag,
                    mode="manual_backfill",
                    publish_version=False,
                    publish_branch_tag=True,
                    reason=f"Missing Docker Hub tag `{branch}`.",
                ),
            )

    if not candidates:
        notes.append("No missing Docker Hub tags were found.")
    return list(candidates.values()), notes


def plan_command() -> None:
    config = load_config()
    branch_states = collect_branch_states(config)

    if config.event_name == "workflow_dispatch":
        if config.manual_tag:
            candidates, notes = plan_manual_exact(config, branch_states)
        else:
            candidates, notes = plan_manual_backfill(config, branch_states)
    elif config.event_name == "push":
        candidates, notes = plan_push(config, branch_states)
    else:
        fail(f"Unsupported event: {config.event_name}")

    summary_lines = [candidate.reason for candidate in candidates]
    summary_lines.extend(notes)

    matrix = {"include": [asdict(candidate) for candidate in candidates]}
    write_output("has_work", "true" if candidates else "false")
    write_output("matrix", json.dumps(matrix))
    write_summary(summary_lines)

    print(json.dumps(matrix, indent=2))
    for line in summary_lines:
        print(f"- {line}")


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def resolve_release_command() -> None:
    config = load_config()
    branch = os.environ["TARGET_BRANCH"].strip()
    source_tag = os.environ["TARGET_TAG"].strip()
    notes_dir = os.environ["RELEASE_NOTES_DIR"].strip()

    if branch != config.main_branch:
        write_output("should_release", "false")
        write_output("skip_reason", f"Branch `{branch}` does not publish GitHub releases.")
        return

    branch_state = collect_branch_states(config, [branch])[branch]
    if branch_state.latest_tag is None:
        write_output("should_release", "false")
        write_output("skip_reason", f"Branch `{branch}` has no releasable tags.")
        return

    if parse_release_tag(config, source_tag) is None or not tag_exists(source_tag):
        write_output("should_release", "false")
        write_output("skip_reason", f"Tag `{source_tag}` is not a releasable tag.")
        return

    commit = tag_commit(source_tag)
    if not branch_contains_commit(branch, commit):
        write_output("should_release", "false")
        write_output("skip_reason", f"Tag `{source_tag}` is no longer reachable from `{branch}`.")
        return

    if branch_state.latest_tag != source_tag:
        write_output("should_release", "false")
        write_output(
            "skip_reason",
            f"Tag `{source_tag}` is not the highest release tag on `{branch}`.",
        )
        return

    notes_path = os.path.join(notes_dir, f"{source_tag}.md")
    if not os.path.exists(notes_path):
        fail(
            f"Expected release notes file `{notes_path}` for GitHub release `{source_tag}`."
        )

    with open(notes_path, "r", encoding="utf-8") as handle:
        body = handle.read().strip()

    write_output("should_release", "true")
    write_output("release_tag", source_tag)
    write_output("release_name", source_tag)
    write_output("release_notes_path", notes_path)
    write_output("release_body", body or "No release notes.")
    print(source_tag)


def resolve_build_command() -> None:
    config = load_config()
    branch = os.environ["TARGET_BRANCH"].strip()
    source_tag = os.environ["TARGET_TAG"].strip()
    mode = os.environ["TARGET_MODE"].strip()
    publish_version = os.environ["TARGET_PUBLISH_VERSION"].strip().lower() == "true"
    publish_branch_tag = os.environ["TARGET_PUBLISH_BRANCH_TAG"].strip().lower() == "true"

    branch_state = collect_branch_states(config, [branch])[branch]
    if branch_state.latest_tag is None:
        write_output("should_build", "false")
        write_output("skip_reason", f"Branch `{branch}` has no releasable tags.")
        return

    if parse_release_tag(config, source_tag) is None or not tag_exists(source_tag):
        write_output("should_build", "false")
        write_output("skip_reason", f"Tag `{source_tag}` is no longer available.")
        return

    commit = tag_commit(source_tag)
    if not branch_contains_commit(branch, commit):
        write_output("should_build", "false")
        write_output("skip_reason", f"Tag `{source_tag}` is no longer reachable from `{branch}`.")
        return

    mutable_tag = "latest" if branch == config.main_branch else branch
    tags_to_push: list[str] = []

    if mode == "push_latest_only":
        if branch_state.latest_tag != source_tag:
            write_output("should_build", "false")
            write_output(
                "skip_reason",
                f"Tag `{source_tag}` is no longer the highest release tag on `{branch}`.",
            )
            return
        if publish_version:
            tags_to_push.append(f"{config.image_repo}:{source_tag}")
        if publish_branch_tag:
            tags_to_push.append(f"{config.image_repo}:{mutable_tag}")

    elif mode == "manual_exact":
        if publish_version:
            tags_to_push.append(f"{config.image_repo}:{source_tag}")
        if publish_branch_tag and branch_state.latest_tag == source_tag:
            tags_to_push.append(f"{config.image_repo}:{mutable_tag}")

    elif mode == "manual_backfill":
        if publish_version and not docker_tag_exists(config.image_repo, source_tag):
            tags_to_push.append(f"{config.image_repo}:{source_tag}")
        if publish_branch_tag:
            if branch != config.main_branch and branch_state.latest_tag != source_tag:
                write_output("should_build", "false")
                write_output(
                    "skip_reason",
                    f"Tag `{source_tag}` is no longer the newest release tag on `{branch}`.",
                )
                return
            if branch == config.main_branch and branch_state.latest_tag != source_tag:
                publish_branch_tag = False
            if publish_branch_tag and not docker_tag_exists(config.image_repo, mutable_tag):
                tags_to_push.append(f"{config.image_repo}:{mutable_tag}")
    else:
        fail(f"Unsupported resolve-build mode: {mode}")

    tags_to_push = unique(tags_to_push)
    if not tags_to_push:
        write_output("should_build", "false")
        write_output("skip_reason", "All requested Docker tags already exist or are no longer eligible.")
        return

    write_output("should_build", "true")
    write_output("tags", "\n".join(tags_to_push))
    write_output("display_tags", ", ".join(tag.rsplit(":", 1)[1] for tag in tags_to_push))
    print("\n".join(tags_to_push))


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: docker_release_plan.py <plan|resolve-build|resolve-release>")

    command = sys.argv[1]
    if command == "plan":
        plan_command()
        return
    if command == "resolve-build":
        resolve_build_command()
        return
    if command == "resolve-release":
        resolve_release_command()
        return
    fail(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
