"""
Integration tests for the command-line interface.
"""

import os
import json
import sys
import pytest
from unittest.mock import patch
from pathlib import Path

import fit_sync.__main__ as main_module


class TestCommandLine:
    """Tests for the command-line interface."""

    def test_auth_command(self, mock_config_file, temp_cache_dir):
        """Test the auth command."""
        with patch.object(sys, 'argv', ['fit_sync', 'auth', '--config', str(mock_config_file)]):
            with patch('fit_sync.sync.SyncManager.authenticate_all', return_value=True) as mock_auth:
                with pytest.raises(SystemExit) as e:
                    main_module.main()
                
                # Check that the authentication was called
                mock_auth.assert_called_once()
                # Should exit with code 0 on success
                assert e.value.code == 0

    def test_list_command(self, mock_config_file, temp_cache_dir, mock_activity_data):
        """Test the list command."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'list', '--account', 'garmin_us', '--limit', '5',
            '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.platforms.garmin.GarminPlatform.authenticate', return_value=True):
                with patch('fit_sync.platforms.garmin.GarminPlatform.list_activities', return_value=mock_activity_data):
                    # Capture stdout to check output
                    with patch('builtins.print') as mock_print:
                        with pytest.raises(SystemExit) as e:
                            main_module.main()
                        
                        # Check that print was called with activity info
                        assert mock_print.call_count > 0
                        # Should exit with code 0 on success
                        assert e.value.code == 0

    def test_download_command_with_id(self, mock_config_file, temp_cache_dir, mock_fit_file):
        """Test downloading an activity by ID."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'download', '--account', 'garmin_us', '--id', 'activity_1',
            '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.platforms.garmin.GarminPlatform.authenticate', return_value=True):
                with patch('fit_sync.platforms.garmin.GarminPlatform.download_activity', return_value=mock_fit_file):
                    with pytest.raises(SystemExit) as e:
                        main_module.main()
                    
                    # Should exit with code 0 on success
                    assert e.value.code == 0

    def test_download_command_with_index(self, mock_config_file, temp_cache_dir, mock_activity_data, mock_fit_file):
        """Test downloading an activity by index."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'download', '--account', 'garmin_us', '--index', '1',
            '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.platforms.garmin.GarminPlatform.authenticate', return_value=True):
                with patch('fit_sync.platforms.garmin.GarminPlatform.list_activities', return_value=mock_activity_data):
                    with patch('fit_sync.platforms.garmin.GarminPlatform.download_activity', return_value=mock_fit_file):
                        with pytest.raises(SystemExit) as e:
                            main_module.main()
                        
                        # Should exit with code 0 on success
                        assert e.value.code == 0

    def test_download_command_list_only(self, mock_config_file, temp_cache_dir, mock_activity_data):
        """Test displaying activity list when no index is provided."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'download', '--account', 'garmin_us',
            '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.platforms.garmin.GarminPlatform.authenticate', return_value=True):
                with patch('fit_sync.platforms.garmin.GarminPlatform.list_activities', return_value=mock_activity_data):
                    with patch('builtins.print') as mock_print:
                        with pytest.raises(SystemExit) as e:
                            main_module.main()
                        
                        # Check that print was called with activity list
                        assert mock_print.call_count > 0
                        # Should exit with code 0 on success
                        assert e.value.code == 0

    def test_download_command_with_output_dir(self, mock_config_file, temp_cache_dir, mock_activity_data, mock_fit_file):
        """Test downloading to a specific output directory."""
        output_dir = temp_cache_dir / "downloads"
        os.makedirs(output_dir, exist_ok=True)
        
        with patch.object(sys, 'argv', [
            'fit_sync', 'download', '--account', 'garmin_us', '--index', '1',
            '--output-dir', str(output_dir), '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.platforms.garmin.GarminPlatform.authenticate', return_value=True):
                with patch('fit_sync.platforms.garmin.GarminPlatform.list_activities', return_value=mock_activity_data):
                    with patch('fit_sync.platforms.garmin.GarminPlatform.download_activity', return_value=mock_fit_file):
                        with patch('shutil.copy') as mock_copy:
                            with pytest.raises(SystemExit) as e:
                                main_module.main()
                            
                            # Check that copy was called to the output directory
                            mock_copy.assert_called_once()
                            # Should exit with code 0 on success
                            assert e.value.code == 0

    def test_sync_command(self, mock_config_file, temp_cache_dir):
        """Test the sync command."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'sync', '--dry-run',
            '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.sync.SyncManager.authenticate_all', return_value=True):
                with patch('fit_sync.sync.SyncManager.sync', return_value=5) as mock_sync:
                    with pytest.raises(SystemExit) as e:
                        main_module.main()
                    
                    # Check that sync was called with dry_run=True
                    mock_sync.assert_called_once()
                    assert mock_sync.call_args[1]['dry_run'] is True
                    # Should exit with code 0 on success
                    assert e.value.code == 0

    def test_sync_with_filters(self, mock_config_file, temp_cache_dir):
        """Test the sync command with filters."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'sync',
            '--source', 'garmin_us',
            '--destination', 'garmin_cn',
            '--activity-type', 'running,cycling',
            '--start-date', '2023-01-01',
            '--config', str(mock_config_file)
        ]):
            with patch('fit_sync.sync.SyncManager.authenticate_all', return_value=True):
                with patch('fit_sync.sync.SyncManager.sync', return_value=3) as mock_sync:
                    with pytest.raises(SystemExit) as e:
                        main_module.main()
                    
                    # Check that sync was called with correct parameters
                    mock_sync.assert_called_once()
                    call_kwargs = mock_sync.call_args[1]
                    assert call_kwargs['source'] == 'garmin_us'
                    assert call_kwargs['destination'] == 'garmin_cn'
                    assert call_kwargs['activity_types'] == ['running', 'cycling']
                    assert call_kwargs['start_date'] == '2023-01-01'
                    # Should exit with code 0 on success
                    assert e.value.code == 0

    def test_clear_cache_command(self, mock_config_file, temp_cache_dir):
        """Test the clear-cache command."""
        # Create some mock files in the cache directory
        test_file = temp_cache_dir / "test_file.fit"
        test_file.touch()
        
        with patch.object(sys, 'argv', [
            'fit_sync', 'clear-cache',
            '--config', str(mock_config_file)
        ]):
            with patch('shutil.rmtree') as mock_rmtree:
                with pytest.raises(SystemExit) as e:
                    main_module.main()
                
                # Check that rmtree was called
                mock_rmtree.assert_called_once()
                # Should exit with code 0 on success
                assert e.value.code == 0

    def test_auth_failure(self, mock_config_file, temp_cache_dir):
        """Test handling of authentication failure."""
        with patch.object(sys, 'argv', ['fit_sync', 'auth', '--config', str(mock_config_file)]):
            with patch('fit_sync.sync.SyncManager.authenticate_all', return_value=False):
                with pytest.raises(SystemExit) as e:
                    main_module.main()
                
                # Should exit with non-zero code on auth failure
                assert e.value.code != 0

    def test_download_command_with_sync_manager(self, mock_config_file, temp_cache_dir, mock_fit_file):
        """Test downloading an activity using SyncManager directly."""
        with patch.object(sys, 'argv', [
            'fit_sync', 'download', '--account', 'garmin_us', '--id', 'activity_1',
            '--config', str(mock_config_file), '--output-dir', str(temp_cache_dir)
        ]):
            with patch('fit_sync.sync.SyncManager.download_activity', return_value=mock_fit_file) as mock_download:
                with pytest.raises(SystemExit) as e:
                    main_module.main()
                
                # Check that SyncManager.download_activity was called with the right parameters
                mock_download.assert_called_once_with('garmin_us', 'activity_1', output_dir=str(temp_cache_dir))
                
                # Should exit with code 0 on success
                assert e.value.code == 0 