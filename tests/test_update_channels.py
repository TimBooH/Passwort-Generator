"""No network: enforce isolation, release-channel safety and digest checks."""
import unittest
from update_channels import (
    UNSTABLE_API, STABLE_API, channel_api, has_channel_update,
    select_unstable_asset, unstable_asset_name,
)


def sample_release(sha='abcdef012345', platform='linux'):
    from update_channels import RELEASE_PREFIX
    name = unstable_asset_name('nt' if platform == 'windows' else 'posix', sha)
    return {
        'name': 'PasswortGenerator Unstable ' + sha,
        'tag_name': 'unstable',
        'prerelease': True,
        'draft': False,
        'assets': [{
            'name': name,
            'size': 72_000_000,
            'digest': 'sha256:' + 'a1'*32,
            'browser_download_url': RELEASE_PREFIX + 'unstable/' + name,
        }],
    }


class UpdateChannelTests(unittest.TestCase):
    def test_channel_urls(self):
        self.assertTrue(channel_api('stable').endswith('/releases/latest'))
        self.assertEqual(channel_api('unstable'), UNSTABLE_API)
        self.assertTrue(UNSTABLE_API.endswith('/releases/tags/unstable'))
        self.assertEqual(UNSTABLE_API, 'https://api.github.com/repos/TimBooH/Passwort-Generator/releases/tags/unstable')
        self.assertEqual(STABLE_API, 'https://api.github.com/repos/TimBooH/Passwort-Generator/releases/latest')
        self.assertEqual(channel_api('stable'), STABLE_API)
        with self.assertRaises(ValueError):
            channel_api('nightly')

    def test_reject_other_unsafe_release_paths(self):
        response = sample_release()
        filename = response['assets'][0]['name']
        for wrong_url in (
            'https://raw.githubusercontent.com/TimBooH/Passwort-Generator/unstable-downloads/' + filename,
            'https://github.com/TimBooH/Passwort-Generator/releases/download/v0.22.0/' + filename,
            'https://github.com/other/Passwort-Generator/releases/download/unstable/' + filename,
        ):
            with self.subTest(url=wrong_url), self.assertRaises(ValueError):
                response['assets'][0]['browser_download_url'] = wrong_url
                select_unstable_asset(response, 'posix')

    def test_prerelease_validation_on_both_systems(self):
        for platform in ('nt', 'posix'):
            release = sample_release(platform='windows' if platform == 'nt' else 'linux')
            sha, asset = select_unstable_asset(release, platform)
            self.assertEqual(sha, 'abcdef012345')
            self.assertIn(sha, asset['name'])

    def test_tampered_or_draft_asset_rejected(self):
        for key, value in (
            ('prerelease', False), ('draft', True), ('tag_name', 'v0.22.0'),
            ('name', 'Invalid name'), ('assets', []),
        ):
            response = sample_release()
            response[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                select_unstable_asset(response, 'posix')
        for key, value in (
            ('size', 123), ('digest', 'sha256:' + 'x'*64),
            ('browser_download_url', 'https://attacker.invalid/appimage'),
            ('name', '../fake.AppImage'),
        ):
            response = sample_release()
            response['assets'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                select_unstable_asset(response, 'posix')
        with self.assertRaises(ValueError):
            unstable_asset_name('posix', '../malware')

    def test_channel_switching_preserves_stable(self):
        newer = lambda tag, old: tag == 'v0.22.0'
        self.assertFalse(has_channel_update(
            'stable', 'stable', 'v0.21.1', '0.21.1', '0.21.1', '', newer))
        self.assertTrue(has_channel_update(
            'stable', 'stable', 'v0.22.0', '0.21.1', '0.21.1', '', newer))
        self.assertTrue(has_channel_update(
            'unstable', 'stable', 'abcdef012345', '0.21.1', '0.21.1', '', newer))
        self.assertFalse(has_channel_update(
            'unstable', 'unstable', 'abcdef012345', '0.21.1',
            '0.21.1', 'abcdef012345', newer))
        self.assertTrue(has_channel_update(
            'unstable', 'unstable', 'abcdef012346', '0.21.1',
            '0.21.1', 'abcdef012345', newer))
        self.assertTrue(has_channel_update(
            'stable', 'unstable', 'v0.21.1', '0.21.1', '0.21.1',
            'abcdef012345', newer))


if __name__ == '__main__':
    unittest.main()
