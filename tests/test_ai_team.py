"""Offline checks for the team runner's review and publication boundaries."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    'ai_team', Path(__file__).resolve().parents[1] / 'tools' / 'ai_team.py')
team = importlib.util.module_from_spec(spec)
spec.loader.exec_module(team)

APPROVED = {'approved': True, 'summary': 'Code und Befunde geprüft.', 'findings': []}
FINDING = {'file': 'main.py', 'severity': 'P1', 'reason': 'Reproduzierbarer Fehler',
           'suggestion': 'Regression beheben'}
REJECTED = {'approved': False, 'summary': 'Fehler bestätigt', 'findings': [FINDING]}


class ReviewBoundaryTests(unittest.TestCase):
    def test_tests_get_separate_writeable_directories_and_read_only_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(team.shutil, 'which', return_value='/usr/bin/bwrap'), \
                mock.patch.object(team, 'command') as execute, \
                mock.patch.object(team, 'test_plan', return_value=(
                    [team.ROOT / 'tests/test_one.py'], [team.ROOT / 'tests/smoke_two.py'])), \
                mock.patch.object(team.sys, 'platform', 'linux'):
            team.tests(Path(tmp), 'python')
            first, second = execute.call_args_list[1:]
            for call in (first, second):
                args = call.args[0]
                self.assertEqual(args[:5], ['/usr/bin/bwrap', '--die-with-parent',
                                           '--ro-bind', '/', '/'])
                self.assertIn('--bind', args)
                self.assertIn('XDG_STATE_HOME', call.kwargs['env'])
            self.assertNotEqual(first.kwargs['env']['XDG_CONFIG_HOME'],
                                second.kwargs['env']['XDG_CONFIG_HOME'])
            self.assertNotEqual(first.kwargs['env']['TMPDIR'], second.kwargs['env']['TMPDIR'])

    def test_nonlinux_stops_before_settings_or_processes_are_touched(self):
        with mock.patch.object(team.sys, 'platform', 'win32'), \
                mock.patch.object(team, 'command') as execute:
            with self.assertRaisesRegex(team.Stop, 'nur unter Linux'):
                team.tests(Path('/unused'), 'python')
            execute.assert_not_called()

    def test_smoke_plan_reads_ci_and_excludes_screenshot_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'tests').mkdir()
            (root / '.github/workflows').mkdir(parents=True)
            (root / 'tests/test_core.py').touch()
            (root / 'tests/smoke_current_ui.py').touch()
            (root / 'tests/smoke_old_ui.py').touch()
            workflow = root / '.github/workflows/unstable.yml'
            workflow.write_text('  PYTHONPATH=. python tests/smoke_current_ui.py\n'
                                '  PYTHONPATH=. python tests/capture_readme_screenshot.py\n')
            with mock.patch.object(team, 'ROOT', root):
                unit, smoke = team.test_plan()
                self.assertEqual([p.name for p in smoke], ['smoke_current_ui.py'])
                self.assertEqual([p.name for p in unit], ['test_core.py'])
                workflow.write_text('no smoke commands')
                with self.assertRaises(team.Stop):
                    team.test_plan()

    def test_missing_and_contradictory_reviews_fail_closed(self):
        for value in (None, {}, {'approved': True},
                      dict(APPROVED, approved='true'),
                      dict(APPROVED, findings=[FINDING]),
                      dict(REJECTED, findings=[{'file': 'main.py'}])):
            with self.subTest(value=value), self.assertRaises(team.Stop):
                team.validate_review(value)

    def test_main_and_unexpected_origin_are_rejected(self):
        def fake_git(*args):
            if args == ('rev-parse', '--show-toplevel'):
                return str(team.ROOT)
            if args == ('symbolic-ref', 'HEAD'):
                return 'refs/heads/main'
            self.fail('No further operation should run on main')
        with mock.patch.object(team, 'git', side_effect=fake_git):
            with self.assertRaises(team.Stop):
                team.guard()

    def test_wrong_push_url_rejected(self):
        with mock.patch.object(team, 'git', side_effect=[str(team.ROOT),
                'refs/heads/unstable', team.ORIGIN, 'https://example.com/wrong.git']):
            with self.assertRaises(team.Stop):
                team.guard()

    def test_fingerprint_includes_new_files_and_deletions(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(team, 'ROOT', Path(tmp)), \
                mock.patch.object(team, 'command', return_value='a.py\0new.py\0'):
            source = Path(tmp) / 'a.py'
            source.write_text('old')
            before = team.fingerprint()
            (Path(tmp) / 'new.py').write_text('new')
            self.assertNotEqual(before, team.fingerprint())
            before = team.fingerprint()
            source.unlink()
            self.assertNotEqual(before, team.fingerprint())

    def test_committed_deletions_keep_the_same_content_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(team, 'ROOT', Path(tmp)), \
                mock.patch.object(team, 'command', side_effect=['deleted.py\0', '']):
            self.assertEqual(team.fingerprint(), team.fingerprint())

    def test_read_only_claude_has_no_shell_write_or_mcp_tools(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(team, 'command',
                return_value=json.dumps({'structured_output': APPROVED})) as call:
            team.claude('review', Path(tmp))
            args = call.call_args.args[0]
            self.assertEqual(args[args.index('--tools') + 1], 'Read,Glob,Grep')
            self.assertIn('--restricted', args)
            self.assertIn('--strict-mcp-config', args)
            self.assertNotIn('--dangerously-skip-permissions', args)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.patcher = mock.patch.object(team, 'STATE', self.state)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.ready = {'head': 'a' * 40, 'fingerprint': 'snapshot', 'base': 'b' * 40,
                      'tests_passed': True, 'claude': APPROVED, 'codex': APPROVED}
        team.write_json(self.state / 'ready.json', self.ready)
        self.args = argparse.Namespace(approved_head='a' * 40)

    def git(self, *args):
        if args[0] == 'status':
            return ''
        if args[0] == 'rev-parse':
            return 'a' * 40
        if args[0] == 'ls-remote':
            return 'b' * 40 + '\trefs/heads/unstable'
        if args[0] == 'show':
            return 'b' * 40
        if args[0] == 'merge-base':
            return ''
        raise AssertionError(args)

    def test_changed_source_or_commit_never_pushes(self):
        for key, value in [('fingerprint', 'changed'),
                           ('tests_passed', False), ('codex', REJECTED),
                           ('claude', REJECTED)]:
            team.write_json(self.state / 'ready.json', dict(self.ready, **{key: value}))
            with self.subTest(key=key), mock.patch.object(team, 'git', side_effect=self.git), \
                    mock.patch.object(team, 'fingerprint', return_value='snapshot'), \
                    mock.patch.object(team, 'command') as push:
                with self.assertRaises(team.Stop):
                    team.publish(self.args)
                push.assert_not_called()

    def test_invalid_ancestry_missing_head_and_intermediate_commits_never_push(self):
        for kind in ('missing', 'not_ancestor', 'intermediate', 'merge'):
            ready = dict(self.ready, head='b' * 40)
            if kind == 'missing':
                del ready['head']
            team.write_json(self.state / 'ready.json', ready)
            def checked_git(*args):
                if args[0] == 'merge-base' and kind == 'not_ancestor':
                    raise team.Stop('Not an ancestor')
                if args[0] == 'show':
                    return 'c' * 40 if kind == 'intermediate' else 'b' * 40 + ' ' + 'c' * 40
                return self.git(*args)
            with self.subTest(kind=kind), mock.patch.object(team, 'git', side_effect=checked_git), \
                    mock.patch.object(team, 'fingerprint', return_value='snapshot'), \
                    mock.patch.object(team, 'command') as push:
                with self.assertRaises(team.Stop):
                    team.publish(self.args)
                push.assert_not_called()

    def test_wrong_approval_dirty_tree_and_moved_remote_never_push(self):
        for kind in ('approval', 'dirty', 'remote'):
            args = argparse.Namespace(approved_head=('c' * 40 if kind == 'approval' else 'a' * 40))
            def git(*parts):
                if kind == 'dirty' and parts[0] == 'status':
                    return ' M main.py'
                if kind == 'remote' and parts[0] == 'ls-remote':
                    return 'c' * 40 + '\trefs/heads/unstable'
                return self.git(*parts)
            with self.subTest(kind=kind), mock.patch.object(team, 'git', side_effect=git), \
                    mock.patch.object(team, 'fingerprint', return_value='snapshot'), \
                    mock.patch.object(team, 'command') as push:
                with self.assertRaises(team.Stop):
                    team.publish(args)
                push.assert_not_called()

    def test_only_exact_approved_sha_goes_to_unstable_without_force(self):
        with mock.patch.object(team, 'git', side_effect=self.git), \
                mock.patch.object(team, 'fingerprint', return_value='snapshot'), \
                mock.patch.object(team, 'command') as push:
            team.publish(self.args)
            args = push.call_args.args[0]
            self.assertEqual(args[-2:], [team.ORIGIN, 'a' * 40 + ':refs/heads/unstable'])
            self.assertNotIn('--force', args)
            self.assertNotIn('--no-verify', args)

    def test_committing_unchanged_reviewed_files_needs_no_second_review(self):
        team.write_json(self.state / 'ready.json', dict(self.ready, head='b' * 40))
        with mock.patch.object(team, 'git', side_effect=self.git) as git, \
                mock.patch.object(team, 'fingerprint', return_value='snapshot'), \
                mock.patch.object(team, 'command') as push:
            team.publish(self.args)
            git.assert_any_call('merge-base', '--is-ancestor', 'b' * 40, 'a' * 40)
            push.assert_called_once()


class LoopTests(unittest.TestCase):
    def run_loop(self, claude_result, codex_result, *, fix=False, changed=False):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        state = Path(tmp.name)
        args = argparse.Namespace(base='origin/unstable', rounds=2, python='python', fix=fix)
        with mock.patch.object(team, 'STATE', state), mock.patch.object(team, 'ROOT', state), \
                mock.patch.object(team, 'auth'), \
                mock.patch.object(team, 'git', return_value='b' * 40), \
                mock.patch.object(team, 'identity', return_value={'head': 'a' * 40}), \
                mock.patch.object(team, 'check_identity'), \
                mock.patch.object(team, 'fingerprint', side_effect=(['one', 'two'] if changed else None),
                                  return_value='snapshot'), \
                mock.patch.object(team, 'tests'), \
                mock.patch.object(team, 'claude', return_value=claude_result) as reviewer, \
                mock.patch.object(team, 'codex', return_value=codex_result) as verifier:
            try:
                team.review(args)
            except team.Stop:
                self.fix_prompts = [c.args[0] for c in verifier.call_args_list if c.kwargs.get('fix')]
                return state, reviewer.call_count, verifier.call_count, False
            return state, reviewer.call_count, verifier.call_count, True

    def test_unapproved_findings_stop_without_fix_permission(self):
        state, first, second, success = self.run_loop(REJECTED, REJECTED)
        self.assertFalse(success)
        self.assertFalse((state / 'ready.json').exists())
        self.assertEqual((first, second), (1, 1))

    def test_claude_rejection_cannot_be_overruled_for_publication(self):
        state, first, second, success = self.run_loop(REJECTED, APPROVED)
        self.assertFalse(success)
        self.assertFalse((state / 'ready.json').exists())
        self.assertEqual((first, second), (1, 1))

    def test_fix_round_limit_stops_and_no_ready_file_exists(self):
        state, first, second, success = self.run_loop(REJECTED, REJECTED, fix=True)
        self.assertFalse(success)
        self.assertFalse((state / 'ready.json').exists())
        self.assertEqual((first, second), (2, 3))
        self.assertEqual(len(self.fix_prompts), 1)
        self.assertIn('erlaubt Änderungen an Projektdateien', self.fix_prompts[0])
        self.assertIn('Keine Git-Mutationen', self.fix_prompts[0])
        self.assertNotIn('Ändere keine Dateien', self.fix_prompts[0])

    def test_changed_test_snapshot_stops_before_review(self):
        state, first, second, success = self.run_loop(APPROVED, APPROVED, changed=True)
        self.assertFalse(success)
        self.assertEqual((first, second), (0, 0))

    def test_both_reviews_and_tests_produce_ready_snapshot(self):
        state, first, second, success = self.run_loop(APPROVED, APPROVED)
        self.assertTrue(success)
        self.assertTrue((state / 'ready.json').exists())
        self.assertEqual((first, second), (1, 1))


if __name__ == '__main__':
    unittest.main()
