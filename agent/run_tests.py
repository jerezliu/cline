import sys
import os
import unittest
from unittest.mock import MagicMock

def main():
    """
    Custom test runner to set up the environment and run all agent tests.
    This script ensures that mocks are in place before any application code is imported.
    """
    # Add the project root to sys.path to allow for absolute imports like
    # 'from cline.agent.agent import Agent'.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Mock the 'anthropic' library globally. This must be done before any 'cline.agent'
    # modules are imported to prevent ModuleNotFoundError.
    sys.modules['anthropic'] = MagicMock()

    # Now that the environment is set up, we can import the test modules.
    from cline.agent import test_agent
    from cline.agent import test_api_handler
    from cline.agent import test_context_manager
    from cline.agent import test_parsers
    from cline.agent import test_tool_executor

    # Create a TestLoader and an empty TestSuite.
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests from each module to the suite.
    suite.addTests(loader.loadTestsFromModule(test_agent))
    suite.addTests(loader.loadTestsFromModule(test_api_handler))
    suite.addTests(loader.loadTestsFromModule(test_context_manager))
    suite.addTests(loader.loadTestsFromModule(test_parsers))
    suite.addTests(loader.loadTestsFromModule(test_tool_executor))

    # Create a TextTestRunner and run the suite.
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with a non-zero status code if any tests failed.
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    main()
