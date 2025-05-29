import unittest
from ai_whisperer.commands.echo import EchoCommand
from ai_whisperer.commands.status import StatusCommand

class TestCommands(unittest.TestCase):
    def test_echo(self):
        cmd = EchoCommand()
        self.assertEqual(cmd.run('hello world'), 'hello world')
        self.assertEqual(cmd.run(''), '')

    def test_status(self):
        cmd = StatusCommand()
        result = cmd.run('')
        self.assertTrue(result.startswith('Status: OK'))
        self.assertIn('Version: 0.1.0', result)
        self.assertIn('Uptime:', result)

if __name__ == '__main__':
    unittest.main()
