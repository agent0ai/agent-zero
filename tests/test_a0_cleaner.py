import os
from pathlib import Path
import threading
import time

import pytest

from plugins._a0_cleaner.helpers.cleaner import Cleaner, CleanerError, DAY


@pytest.fixture
def cleaner(tmp_path):
    base, home, state = tmp_path/'a0', tmp_path/'home', tmp_path/'state'
    base.mkdir(); home.mkdir()
    now = time.time()+90*DAY
    return Cleaner(base, home, state, clock=lambda: now, chat_activity=lambda chat: now-60*DAY)


def put(path, content='disposable'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def group(report, name):
    return next(g for g in report['groups'] if g['id'] == name)


def test_scan_is_read_only_and_clean_requires_confirmation(cleaner):
    cache = put(cleaner.home/'.cache/pip/old.cache')
    fresh = put(cleaner.home/'.cache/pip/new.cache')
    os.utime(fresh, (cleaner.clock(), cleaner.clock()))
    report = cleaner.scan()
    assert group(report, 'pip')['files'] == 1
    assert cache.exists() and fresh.exists()
    preview = cleaner.preview(report['id'], ['pip'])
    assert preview['paths'] == [str(cache)]
    with pytest.raises(CleanerError, match='Confirm'):
        cleaner.clean(report['id'], ['pip'])
    result = cleaner.clean(report['id'], ['pip'], confirmed=True)
    assert result['result']['files'] == 1
    assert not cache.exists() and fresh.exists()


def test_automatic_defaults_clean_bulky_areas_but_leave_custom_and_paid_caches(cleaner):
    cache = put(cleaner.home/'.npm/_cacache/old')
    shot = put(cleaner.base/'usr/chats/old/screenshots/browser/shot.jpg')
    profile = put(cleaner.base/'tmp/browser/sessions/retired/Default/Cookies')
    shared = put(cleaner.base/'tmp/browser/sessions/shared/Default/Cookies')
    custom = put(cleaner.base/'usr/workdir/cache/data')
    embedding = put(cleaner.base/'tmp/memory/embeddings/cache')
    cleaner.config['custom_folders'] = [{'path':str(custom.parent),'days':30}]
    summary = cleaner.scheduled()
    assert summary['freed_bytes'] > 0 and summary['found_bytes'] > 0
    assert not cache.exists()
    assert not shot.exists() and not profile.exists()
    assert all(p.exists() for p in (shared, custom, embedding))
    latest = cleaner.latest()
    assert latest['activity'][0]['automatic']
    assert group(latest['report'], 'profiles')['files'] == 0


def test_explicit_area_opt_out_and_master_opt_out_are_respected(cleaner):
    cache = put(cleaner.home/'.cache/pip/old')
    profile = put(cleaner.base/'tmp/browser/sessions/retired/data')
    cleaner.config['automatic_areas'] = ['pip']
    cleaner.scheduled()
    assert not cache.exists() and profile.exists()
    cache.write_text('cache again')
    cleaner.config['automatic'] = False
    cleaner.scheduled()
    assert cache.exists() and profile.exists()


def test_browser_versions_preserve_required_and_running_installations(cleaner):
    cleaner.browser_revision = '1228'
    required = put(cleaner.base/'tmp/playwright/chromium-1228/chrome')
    retired = put(cleaner.base/'tmp/playwright/chromium-1234/chrome')
    running = put(cleaner.base/'tmp/playwright/chromium-1200/chrome')
    cleaner.process_inventory=lambda:{'paths':[str(running)], 'package_busy':False}
    cleaner.scheduled()
    assert not retired.exists() and required.exists() and running.exists()


def test_changed_files_and_replaced_parent_symlinks_are_not_deleted(cleaner, tmp_path):
    changed = put(cleaner.home/'.cache/pip/changed')
    victim = put(cleaner.home/'.cache/pip/sub/victim')
    outside = put(tmp_path/'outside/victim', 'keep')
    report = cleaner.scan()
    changed.write_text('changed after preview')
    victim.unlink(); victim.parent.rmdir(); victim.parent.symlink_to(outside.parent, target_is_directory=True)
    result = cleaner.clean(report['id'], ['pip'], confirmed=True)
    assert changed.exists() and outside.read_text() == 'keep'
    assert result['result']['files'] == 0 and result['result']['skipped'] == 2


def test_hard_links_and_symlinks_are_excluded(cleaner, tmp_path):
    original = put(tmp_path/'keep')
    root=cleaner.home/'.cache/pip'; root.mkdir(parents=True)
    os.link(original, root/'hardlink')
    (root/'symlink').symlink_to(original)
    (root/'dirlink').symlink_to(tmp_path, target_is_directory=True)
    assert group(cleaner.scan(), 'pip')['files'] == 0


def test_recent_or_active_profiles_and_resumed_chats_are_protected(cleaner):
    old = put(cleaner.base/'tmp/browser/sessions/old/Default/data')
    live = put(cleaner.base/'tmp/browser/sessions/live/Default/data')
    recent = put(cleaner.base/'tmp/browser/sessions/recent/Default/data')
    os.utime(recent,(cleaner.clock(),cleaner.clock()))
    shot = put(cleaner.base/'usr/chats/chat/screenshots/desktop/shot.png')
    cleaner.process_inventory=lambda:{'paths':[str(live)],'package_busy':False}
    report=cleaner.scan()
    assert group(report,'profiles')['files'] == 1
    assert group(report,'screenshots')['files'] == 1
    cleaner.chat_activity=lambda chat:cleaner.clock()
    os.utime(old,(cleaner.clock(),cleaner.clock()))
    result=cleaner.clean(report['id'],['profiles','screenshots'],confirmed=True)
    assert result['result']['files']==0
    assert all(p.exists() for p in (old,live,recent,shot))


def test_active_package_manager_defers_automatic_cleanup(cleaner):
    cache=put(cleaner.home/'.cache/pip/old')
    report=cleaner.scan()
    cleaner.process_inventory=lambda:{'paths':[],'package_busy':True}
    result=cleaner.clean(report['id'],['pip'],confirmed=True)
    assert cache.exists() and result['result']['files']==0
    assert group(result['report'],'pip')['busy']


def test_old_or_replayed_scan_and_changed_rules_are_rejected(cleaner):
    put(cleaner.home/'.cache/pip/old')
    report=cleaner.scan()
    newer=cleaner.scan()
    with pytest.raises(CleanerError,match='out of date'):
        cleaner.preview(report['id'],['pip'])
    cleaner.config['cache_days']=60
    with pytest.raises(CleanerError,match='settings changed'):
        cleaner.clean(newer['id'],['pip'],confirmed=True)


@pytest.mark.parametrize('suffix',['usr','usr/projects/project','usr/projects/project/.a0proj','tmp/browser','tmp/playwright','tmp','usr/workdir'])
def test_custom_folders_cannot_target_protected_roots(cleaner,suffix):
    path=cleaner.base/suffix;path.mkdir(parents=True,exist_ok=True)
    with pytest.raises(CleanerError): cleaner.custom_path(str(path))


def test_custom_cleanup_stays_in_selected_folder(cleaner):
    target=put(cleaner.base/'usr/workdir/scratch/old')
    keep=put(cleaner.base/'usr/workdir/important')
    metadata=put(target.parent/'.git/config','keep')
    cleaner.config['custom_folders']=[{'path':str(target.parent),'days':30}]
    report=cleaner.scan()
    assert group(report,'custom-0')['files']==1
    cleaner.clean(report['id'],['custom-0'],confirmed=True)
    assert not target.exists() and keep.exists() and metadata.exists()


def test_scan_fails_closed_when_process_ownership_unknown(cleaner):
    cache=put(cleaner.home/'.cache/pip/old')
    def denied():raise CleanerError('ownership unknown')
    cleaner.process_inventory=denied
    with pytest.raises(CleanerError,match='ownership'):cleaner.scheduled()
    assert cache.exists()


def test_cancellation_and_disable_stop_cleanup(cleaner):
    cache=put(cleaner.home/'.cache/pip/old')
    cleaner.cancel_event=threading.Event();cleaner.cancel_event.set()
    with pytest.raises(CleanerError,match='stopped'):cleaner.scheduled()
    cleaner.cancel_event.clear();cleaner.enabled=lambda:False
    with pytest.raises(CleanerError,match='disabled'):cleaner.scheduled()
    assert cache.exists()


def test_removed_custom_folder_does_not_block_automatic_housekeeping(cleaner):
    cache = put(cleaner.home/'.cache/pip/old')
    cleaner.config['custom_folders'] = [{'path':str(cleaner.base/'usr/workdir/removed'), 'days':30}]
    cleaner.scheduled()
    assert not cache.exists()


def test_files_with_uninspectable_owners_are_not_candidates(cleaner):
    cache = put(cleaner.home/'.cache/pip/old')
    cleaner.process_inventory=lambda:{'paths':[], 'package_busy':False, 'opaque_uids':[os.geteuid()]}
    assert group(cleaner.scan(),'pip')['files']==0
    assert cache.exists()


def test_nested_mounts_are_skipped_even_on_the_same_device(cleaner):
    cache = put(cleaner.home/'.cache/pip/mounted/keep')
    cleaner.process_inventory=lambda:{'paths':[], 'package_busy':False, 'mounts':[str(cache.parent)]}
    assert group(cleaner.scan(),'pip')['files']==0
    assert cache.exists()


def test_custom_zero_age_is_manual_and_requires_confirmation(cleaner):
    cleaner.clock = time.time
    file = put(cleaner.base/'usr/workdir/scratch/new')
    cleaner.config['custom_folders']=[{'path':str(file.parent),'days':0}]
    cleaner.scheduled()
    assert file.exists()
    report=cleaner.scan()
    assert group(report,'custom-0')['files']==1
    with pytest.raises(CleanerError, match='Confirm'):
        cleaner.clean(report['id'],['custom-0'])
    cleaner.clean(report['id'],['custom-0'],confirmed=True)
    assert not file.exists()
