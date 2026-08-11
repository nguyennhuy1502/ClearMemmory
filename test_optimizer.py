# -*- coding: utf-8 -*-
"""
test_optimizer.py — Test các hàm tối ưu mới trong optimizer.py.

Mục tiêu: verify hàm chạy được (read-only, không crash), cấu trúc dữ liệu đúng.
Không test side-effect thật (không apply tweak, không disable service).

Chạy:  python test_optimizer.py
       python -m pytest test_optimizer.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimizer


class TestPrivacyTweaks(unittest.TestCase):
    """privacy_tweaks() trả về 5 tweak với cấu trúc đầy đủ."""

    def test_returns_list(self):
        tw = optimizer.privacy_tweaks()
        self.assertIsInstance(tw, list)
        self.assertGreaterEqual(len(tw), 5)

    def test_structure(self):
        for t in optimizer.privacy_tweaks():
            self.assertIn("id", t)
            self.assertIn("name_vi", t)
            self.assertIn("name_en", t)
            self.assertIn("desc_vi", t)
            self.assertIn("desc_en", t)
            self.assertIn("needs_admin", t)
            self.assertIn("risk", t)
            self.assertIn("fn", t)
            self.assertIn("is_applied", t)
            self.assertIsInstance(t["is_applied"], bool)
            self.assertIn(t["risk"], ("low", "medium", "high"))

    def test_ids_unique(self):
        ids = [t["id"] for t in optimizer.privacy_tweaks()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_cortana_tweak_exists(self):
        ids = [t["id"] for t in optimizer.privacy_tweaks()]
        self.assertIn("disable_cortana", ids)
        self.assertIn("disable_telemetry", ids)
        self.assertIn("disable_advertising_id", ids)


class TestNetworkStatus(unittest.TestCase):
    """network_status() chạy không crash, trả dict."""

    def test_returns_dict(self):
        s = optimizer.network_status()
        self.assertIsInstance(s, dict)
        self.assertIn("tcp_autotuning", s)
        self.assertIn("lmhosts_enabled", s)

    def test_values_valid(self):
        s = optimizer.network_status()
        self.assertIn(s["tcp_autotuning"],
                      ("normal", "disabled", "restricted", "unknown"))
        # lmhosts_enabled có thể None/True/False
        self.assertIn(s["lmhosts_enabled"], (None, True, False))


class TestNetworkActions(unittest.TestCase):
    """network_actions() trả về ít nhất 4 action."""

    def test_returns_list(self):
        acts = optimizer.network_actions()
        self.assertIsInstance(acts, list)
        self.assertGreaterEqual(len(acts), 4)

    def test_structure(self):
        for a in optimizer.network_actions():
            self.assertIn("id", a)
            self.assertIn("name_vi", a)
            self.assertIn("name_en", a)
            self.assertIn("needs_admin", a)
            self.assertIn("fn", a)
            self.assertTrue(callable(a["fn"]))

    def test_known_ids(self):
        ids = [a["id"] for a in optimizer.network_actions()]
        self.assertIn("flush_dns", ids)
        self.assertIn("reset_winsock", ids)
        self.assertIn("tcp_autotune_on", ids)
        self.assertIn("disable_lmhosts", ids)


class TestServiceManager(unittest.TestCase):
    """list_services() liệt kê bloatware services."""

    def test_bloatware_dict_not_empty(self):
        self.assertGreaterEqual(len(optimizer.BLOATWARE_SERVICES), 10)
        self.assertIn("DiagTrack", optimizer.BLOATWARE_SERVICES)
        self.assertIn("WSearch", optimizer.BLOATWARE_SERVICES)

    def test_safe_service_name(self):
        self.assertTrue(optimizer._is_safe_service_name("DiagTrack"))
        self.assertTrue(optimizer._is_safe_service_name("WSearch"))
        self.assertTrue(optimizer._is_safe_service_name("a-b_c.1"))
        # Ký tự nguy hiểm → chặn
        self.assertFalse(optimizer._is_safe_service_name("foo&bar"))
        self.assertFalse(optimizer._is_safe_service_name("foo|bar"))
        self.assertFalse(optimizer._is_safe_service_name("foo;rm"))
        self.assertFalse(optimizer._is_safe_service_name(""))
        self.assertFalse(optimizer._is_safe_service_name(None))

    def test_list_services_returns_list(self):
        items = optimizer.list_services()
        self.assertIsInstance(items, list)
        for it in items:
            self.assertIn("name", it)
            self.assertIn("display", it)
            self.assertIn("status", it)
            self.assertIn("start_type", it)
            self.assertIn("is_bloatware", it)
            self.assertTrue(it["is_bloatware"])
            # Status phải là giá trị hợp lệ
            self.assertIn(it["status"],
                          ("running", "stopped", "absent", "unknown"))

    def test_toggle_service_rejects_unsafe_name(self):
        # Tên service có ký tự meta → phải bị chặn (trả False, không gọi sc)
        self.assertFalse(optimizer.toggle_service("foo&bar", disable=True))
        self.assertFalse(optimizer.toggle_service("", disable=True))


class TestDiskOptimization(unittest.TestCase):
    """Disk optimization info + helper."""

    def test_disk_optimization_info_returns_list(self):
        info = optimizer.disk_optimization_info()
        self.assertIsInstance(info, list)
        for d in info:
            self.assertIn("drive", d)
            self.assertIn("is_ssd", d)
            self.assertIn("percent", d)

    def test_run_defrag_rejects_unsafe_drive(self):
        # Drive có ký tự meta → chặn
        self.assertFalse(optimizer.run_defrag("C:&whoami"))
        self.assertFalse(optimizer.run_defrag(""))


class TestExistingTweaksStillWork(unittest.TestCase):
    """Regression: các hàm cũ vẫn hoạt động."""

    def test_suggested_tweaks(self):
        tw = optimizer.suggested_tweaks()
        self.assertGreaterEqual(len(tw), 8)  # 8 tweaks cũ

    def test_suggested_actions(self):
        acts = optimizer.suggested_actions()
        self.assertGreaterEqual(len(acts), 3)  # free_ram, explorer, clipboard


# ============================ Tests cho 13 hàm mới ============================
class TestBootTimeAnalyze(unittest.TestCase):
    def test_returns_dict(self):
        r = optimizer.boot_time_analyze()
        self.assertIsInstance(r, dict)
        self.assertIn("last_boot_seconds", r)
        self.assertIn("events", r)


class TestAppUninstaller(unittest.TestCase):
    def test_returns_list(self):
        items = optimizer.app_uninstaller_list()
        self.assertIsInstance(items, list)
        for it in items[:5]:
            self.assertIn("name", it)
            self.assertIn("uninstall_cmd", it)

    def test_no_dupes(self):
        items = optimizer.app_uninstaller_list()
        names = [it["name"] for it in items]
        self.assertEqual(len(names), len(set(names)))


class TestDuplicateFinder(unittest.TestCase):
    def test_empty_roots(self):
        r = optimizer.duplicate_finder(roots=[], min_size_mb=1)
        self.assertEqual(r, [])

    def test_returns_list(self):
        r = optimizer.duplicate_finder(roots=[], min_size_mb=10)
        self.assertIsInstance(r, list)


class TestHealthReport(unittest.TestCase):
    def test_keys(self):
        r = optimizer.health_report()
        self.assertIn("ram", r)
        self.assertIn("cpu", r)
        self.assertIn("disks", r)
        self.assertIn("top_issues", r)

    def test_issues_is_list(self):
        r = optimizer.health_report()
        self.assertIsInstance(r["top_issues"], list)


class TestBatteryReport(unittest.TestCase):
    def test_returns_dict(self):
        r = optimizer.battery_report()
        self.assertIsInstance(r, dict)
        self.assertIn("has_battery", r)


class TestScheduledTaskCleanup(unittest.TestCase):
    def test_dry_run_returns_list(self):
        r = optimizer.scheduled_task_cleanup(dry_run=True)
        self.assertIsInstance(r, list)


class TestPrefetchAnalyze(unittest.TestCase):
    def test_returns_list(self):
        r = optimizer.prefetch_analyze()
        self.assertIsInstance(r, list)


class TestWindowsUpdateStatus(unittest.TestCase):
    def test_returns_dict(self):
        r = optimizer.windows_update_status()
        self.assertIsInstance(r, dict)
        self.assertIn("pending_count", r)
        self.assertIn("last_install_date", r)


class TestThumbnailCache(unittest.TestCase):
    def test_returns_dict(self):
        r = optimizer.thumbnail_cache_clear()
        self.assertIn("removed_files", r)
        self.assertIn("total_freed", r)


class TestShaderCache(unittest.TestCase):
    def test_returns_dict(self):
        r = optimizer.shader_cache_clear()
        self.assertIn("removed_files", r)
        self.assertIn("total_freed", r)


class TestLargeAppsScan(unittest.TestCase):
    def test_returns_list(self):
        r = optimizer.large_apps_scan()
        self.assertIsInstance(r, list)

    def test_sorted_desc(self):
        r = optimizer.large_apps_scan(top_n=20)
        if len(r) >= 2:
            self.assertGreaterEqual(r[0]["size"], r[-1]["size"])


class TestSafePathGuard(unittest.TestCase):
    def test_blocks_system_paths(self):
        # Path ngoài user profile phải bị chặn
        self.assertFalse(optimizer._is_safe_path(r"C:\Windows\System32\cmd.exe"))
        self.assertFalse(optimizer._is_safe_path(r"C:\Program Files\app.exe"))

    def test_allows_user_paths(self):
        up = os.environ.get("USERPROFILE", "")
        if up:
            self.assertTrue(optimizer._is_safe_path(up))
            self.assertTrue(optimizer._is_safe_path(os.path.join(up, "Downloads")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
