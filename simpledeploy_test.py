import shutil
import os
import simpledeploy
import unittest

class TestHook(unittest.TestCase):
    def test_clone_repo_if_not_exist(self):
        # Test if the function clones the repository if it does not exist
        # Arrange
        repo_name = 'test_repo'
        repo_dir = 'test_repo_dir'
        os.mkdir(repo_dir)
        # Act
        simpledeploy.clone_repo_if_not_exist(repo_name, repo_dir)
        # Assert
        self.assertIs(os.path.exists(repo_dir), True)
        shutil.rmtree(repo_dir)

        # Test if the function does not clone the repository if it exists
        # Arrange
        repo_dir = 'test_repo_dir'
        os.mkdir(repo_dir)
        os.mkdir(os.path.join(repo_dir, '.git'))
        # Act
        simpledeploy.clone_repo_if_not_exist(repo_name, repo_dir)
        # Assert
        self.assertIs(os.path.exists(repo_dir), True)
        shutil.rmtree(repo_dir)
    def test_read_config(self):
        config_file = 'test.json'
        with open(config_file, 'w') as f:
            f.write('{ "app": {"key1": "value1", "key2": "value2"} }')
        expected_result = {'key1': 'value1', 'key2': 'value2'}
        result = simpledeploy.read_config(config_file)
        self.assertEqual(result['app'], expected_result)
        os.remove(config_file)

if __name__ == '__main__':
    unittest.main()